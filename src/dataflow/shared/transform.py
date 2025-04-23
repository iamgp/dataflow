"""Shared utilities for data transformation.

This module provides reusable components for transforming data, including cleaning,
mapping, enrichment, and validation utilities.
"""
# type: ignore

import re
from abc import ABC, abstractmethod
from collections.abc import Callable
from datetime import UTC, datetime
from typing import Any, Generic, Literal, TypeVar

import pandas as pd
from pydantic import BaseModel, ValidationError

from dataflow.shared.logging import get_logger

log = get_logger("dataflow.shared.transform")

# Type variables for generic transformation types
InputType = TypeVar("InputType")
OutputType = TypeVar("OutputType")
T = TypeVar("T")


class TransformationError(Exception):
    """Base exception for all transformation-related errors."""

    pass


class MappingError(TransformationError):
    """Exception raised when data cannot be mapped to the target schema."""

    pass


class EnrichmentError(TransformationError):
    """Exception raised when data enrichment fails."""

    pass


class Transformer(Generic[InputType, OutputType], ABC):
    """Base class for data transformers."""

    def __init__(self, name: str | None = None):
        """Initialize the transformer.

        Args:
            name: Optional name for the transformer, used for logging
        """
        self.name = name or self.__class__.__name__
        self.log = get_logger(f"dataflow.transform.{self.name}")

    @abstractmethod
    def transform(self, data: InputType) -> OutputType:
        """Transform the input data.

        Args:
            data: Input data to transform

        Returns:
            Transformed data

        Raises:
            TransformationError: If transformation fails
        """
        pass

    def __call__(self, data: InputType) -> OutputType:
        """Make the transformer callable.

        Args:
            data: Input data to transform

        Returns:
            Transformed data

        Raises:
            TransformationError: If transformation fails
        """
        return self.transform(data)


class TransformerPipeline(Transformer[InputType, OutputType]):
    """A pipeline of transformers to be applied sequentially.

    The output of each transformer is passed as input to the next transformer.
    The input type of the pipeline is the input type of the first transformer,
    and the output type is the output type of the last transformer.
    """

    def __init__(self, transformers: list[Transformer], name: str | None = None):
        """Initialize the transformer pipeline.

        Args:
            transformers: List of transformers to apply in sequence
            name: Optional name for the pipeline, used for logging
        """
        super().__init__(name=name)
        if not transformers:
            raise ValueError("Transformer pipeline must have at least one transformer")
        self.transformers = transformers

    def transform(self, data: Any) -> Any:
        """Apply each transformer in sequence.

        Args:
            data: Input data to transform

        Returns:
            Transformed data

        Raises:
            TransformationError: If any transformer fails
        """
        self.log.debug(
            f"Starting transformation pipeline with {len(self.transformers)} transformers"
        )
        result = data

        for i, transformer in enumerate(self.transformers):
            try:
                self.log.debug(
                    f"Applying transformer {i + 1}/{len(self.transformers)}: {transformer.name}"
                )
                result = transformer(result)
            except Exception as e:
                self.log.error(
                    f"Transformer {i + 1}/{len(self.transformers)} failed",
                    transformer=transformer.name,
                    error=str(e),
                )
                if isinstance(e, TransformationError):
                    raise
                raise TransformationError(f"Transformation failed at step {i + 1}: {e}") from e

        self.log.debug("Transformation pipeline completed successfully")
        return result


class FunctionTransformer(Transformer[InputType, OutputType]):
    """A transformer that applies a function to the input data."""

    def __init__(self, func: Callable[[InputType], OutputType], name: str | None = None):
        """Initialize the function transformer.

        Args:
            func: Function to apply to the input data
            name: Optional name for the transformer, used for logging
        """
        super().__init__(name=name or func.__name__)
        self.func = func

    def transform(self, data: InputType) -> OutputType:
        """Apply the function to the input data.

        Args:
            data: Input data to transform

        Returns:
            Transformed data

        Raises:
            TransformationError: If the function raises an exception
        """
        try:
            return self.func(data)
        except Exception as e:
            if isinstance(e, TransformationError):
                raise
            raise TransformationError(f"Function transformer failed: {e}") from e


class DataFrameTransformer(Transformer[pd.DataFrame, pd.DataFrame]):
    """Base class for transformers that operate on DataFrames."""

    def transform(self, data: pd.DataFrame) -> pd.DataFrame:
        """Transform a DataFrame.

        Args:
            data: Input DataFrame

        Returns:
            Transformed DataFrame

        Raises:
            TransformationError: If transformation fails
        """
        if not isinstance(data, pd.DataFrame):
            raise TransformationError(f"Input must be a DataFrame, got {type(data).__name__}")

        try:
            # Call the implementation-specific transformation method
            result = self._transform_dataframe(data)
            # Ensure we always return a proper DataFrame
            if not isinstance(result, pd.DataFrame):
                raise TransformationError(f"Expected DataFrame result, got {type(result).__name__}")
            return result
        except Exception as e:
            if isinstance(e, TransformationError):
                raise
            self.log.error("Failed to transform DataFrame", error=str(e))
            raise TransformationError(f"Failed to transform DataFrame: {e}") from e

    @abstractmethod
    def _transform_dataframe(self, df: pd.DataFrame) -> pd.DataFrame:
        """Transform the DataFrame.

        This method must be implemented by subclasses to provide the actual
        transformation logic.

        Args:
            df: Input DataFrame

        Returns:
            Transformed DataFrame
        """
        pass


class SchemaValidator(Transformer[InputType, InputType]):
    """Validates data against a Pydantic model schema."""

    def __init__(self, model: type[BaseModel], name: str | None = None):
        """Initialize the schema validator.

        Args:
            model: Pydantic model class to validate against
            name: Optional name for the validator, used for logging
        """
        super().__init__(name=name or f"{model.__name__}Validator")
        self.model = model

    def transform(self, data: InputType) -> InputType:
        """Validate the input data against the schema.

        Args:
            data: Input data to validate

        Returns:
            The input data if valid

        Raises:
            ValidationError: If the data is not valid
        """
        try:
            if isinstance(data, list):
                # Validate each item in the list
                for i, item in enumerate(data):
                    try:
                        self.model.model_validate(item)
                    except Exception as e:
                        raise ValidationError(f"Validation failed for item {i}: {e}") from e
            else:
                # Validate a single item
                self.model.model_validate(data)

            return data
        except Exception as e:
            if isinstance(e, ValidationError):
                raise
            raise ValidationError(f"Schema validation failed: {e}") from e


class DataCleaner(DataFrameTransformer):
    """Cleans data in a DataFrame by applying various cleaning operations."""

    def __init__(
        self,
        drop_duplicates: bool = True,
        drop_null_columns: float | None = None,
        drop_null_rows: float | None = None,
        fill_null_values: dict[str, Any] | None = None,
        strip_strings: bool = True,
        name: str | None = None,
    ):
        """Initialize the data cleaner.

        Args:
            drop_duplicates: Whether to drop duplicate rows
            drop_null_columns: Drop columns with more than this fraction of null values (0-1),
                               or None to keep all columns
            drop_null_rows: Drop rows with more than this fraction of null values (0-1),
                            or None to keep all rows
            fill_null_values: Dictionary mapping column names to fill values for nulls,
                              or None to not fill any nulls
            strip_strings: Whether to strip whitespace from string columns
            name: Optional name for the cleaner, used for logging
        """
        super().__init__(name=name)
        self.drop_duplicates = drop_duplicates
        self.drop_null_columns = drop_null_columns
        self.drop_null_rows = drop_null_rows
        self.fill_null_values = fill_null_values or {}
        self.strip_strings = strip_strings

    def _transform_dataframe(self, df: pd.DataFrame) -> pd.DataFrame:
        """Transform the DataFrame by cleaning data.

        Args:
            df: Input DataFrame

        Returns:
            Cleaned DataFrame
        """
        result = df.copy()
        original_shape = result.shape

        # Drop duplicate rows
        if self.drop_duplicates:
            result = result.drop_duplicates()
            if result.shape[0] < original_shape[0]:
                self.log.info(
                    "Dropped duplicate rows",
                    original_rows=original_shape[0],
                    new_rows=result.shape[0],
                    dropped=original_shape[0] - result.shape[0],
                )

        # Drop columns with too many nulls
        if self.drop_null_columns is not None:
            # Calculate null fractions per column and ensure it's a Series
            null_fractions = pd.Series(result.isnull().mean())
            # Convert to Series to ensure we have .index
            high_null_cols = pd.Series(null_fractions > self.drop_null_columns)
            cols_to_drop = result.columns[high_null_cols].tolist()

            if cols_to_drop:
                result = result.drop(columns=cols_to_drop)
                self.log.info(
                    "Dropped columns with too many nulls",
                    threshold=self.drop_null_columns,
                    dropped_columns=cols_to_drop,
                )

        # Drop rows with too many nulls
        if self.drop_null_rows is not None:
            original_rows = result.shape[0]
            # Calculate null fractions per row and ensure it's a Series
            row_null_fractions = pd.Series(result.isnull().mean(axis=1))
            result = result[row_null_fractions <= self.drop_null_rows]

            if result.shape[0] < original_rows:
                self.log.info(
                    "Dropped rows with too many nulls",
                    threshold=self.drop_null_rows,
                    original_rows=original_rows,
                    new_rows=result.shape[0],
                    dropped=original_rows - result.shape[0],
                )

        # Fill null values
        if self.fill_null_values:
            for col, value in self.fill_null_values.items():
                if col in result.columns:
                    # Get the column as a Series
                    col_series = pd.Series(result[col])
                    null_count = col_series.isnull().sum()
                    if null_count > 0:
                        result[col] = col_series.fillna(value)
                        self.log.info(
                            f"Filled {null_count} null values in column '{col}'",
                            value=str(value),
                        )

        # Strip whitespace from string columns
        if self.strip_strings:
            # Get string columns
            string_cols = result.select_dtypes(include=["object", "string"]).columns
            for col in string_cols:
                # Get the column as a Series and ensure it's string type
                col_series = pd.Series(result[col])
                if pd.api.types.is_string_dtype(col_series.dtype):
                    try:
                        result[col] = col_series.str.strip()
                    except AttributeError:
                        # Column might contain non-string objects
                        pass

        # Ensure we're returning a DataFrame
        if not isinstance(result, pd.DataFrame):
            result = pd.DataFrame(result)

        return result


class DateTimeNormalizer(DataFrameTransformer):
    """Normalizes datetime columns in a DataFrame."""

    def __init__(
        self,
        columns: list[str],
        target_format: str | None = None,
        target_timezone: str | None = None,
        errors: Literal["raise", "ignore", "coerce"] = "raise",
        name: str | None = None,
    ):
        """Initialize the datetime normalizer.

        Args:
            columns: List of column names to normalize
            target_format: Output datetime format string (or None for datetime objects)
            target_timezone: Target timezone name (e.g., 'UTC', 'America/New_York')
            errors: How to handle errors ('raise', 'ignore', 'coerce')
            name: Optional name for the normalizer, used for logging
        """
        super().__init__(name=name)
        self.columns = columns
        self.target_format = target_format
        self.target_timezone = target_timezone
        self.errors = errors

    def _transform_dataframe(self, df: pd.DataFrame) -> pd.DataFrame:
        """Normalize datetime columns in the DataFrame.

        Args:
            df: Input DataFrame

        Returns:
            DataFrame with normalized datetime columns
        """
        result = df.copy()

        for col in self.columns:
            if col not in result.columns:
                if self.errors == "raise":
                    raise ValueError(f"Column '{col}' not found in DataFrame")
                self.log.warning(f"Column '{col}' not found in DataFrame, skipping")
                continue

            try:
                # Convert to datetime objects - pandas to_datetime only accepts 'raise' or 'coerce'
                if self.errors == "ignore":
                    # For 'ignore', we'll try conversion but catch exceptions
                    try:
                        result[col] = pd.to_datetime(result[col])
                    except Exception as e:
                        self.log.warning(
                            f"Error converting column '{col}' to datetime, ignoring: {e}"
                        )
                else:
                    # Use the pandas-supported error modes ('raise' or 'coerce')
                    result[col] = pd.to_datetime(
                        result[col], errors="coerce" if self.errors == "coerce" else "raise"
                    )

                # Convert timezone if specified
                if self.target_timezone:
                    result[col] = result[col].dt.tz_convert(self.target_timezone)

                # Format as string if specified
                if self.target_format:
                    result[col] = result[col].dt.strftime(self.target_format)

                self.log.info(f"Normalized datetime column '{col}'")
            except Exception as e:
                if self.errors == "raise":
                    raise TransformationError(f"Failed to normalize column '{col}': {e}") from e
                self.log.error(f"Failed to normalize column '{col}'", error=str(e))

        return result


class ColumnMapper(DataFrameTransformer):
    """Maps columns in a DataFrame to a new schema."""

    def __init__(
        self,
        mapping: dict[str, str],
        drop_unmapped: bool = False,
        name: str | None = None,
    ):
        """Initialize the column mapper.

        Args:
            mapping: Dictionary mapping source column names to target column names
            drop_unmapped: Whether to drop columns not in the mapping
            name: Optional name for the mapper, used for logging
        """
        super().__init__(name=name)
        self.mapping = mapping
        self.drop_unmapped = drop_unmapped

    def _transform_dataframe(self, df: pd.DataFrame) -> pd.DataFrame:
        """Map columns in the DataFrame.

        Args:
            df: Input DataFrame

        Returns:
            DataFrame with mapped columns
        """
        # Create a copy of the DataFrame
        result = df.copy()

        # Check if all source columns exist
        missing_cols = [col for col in self.mapping.keys() if col not in df.columns]
        if missing_cols:
            self.log.warning(
                "Some source columns are missing from the DataFrame",
                missing_columns=missing_cols,
            )

        # Rename columns according to the mapping
        valid_mapping = {k: v for k, v in self.mapping.items() if k in df.columns}
        result = result.rename(columns=valid_mapping)

        # Drop unmapped columns if requested
        if self.drop_unmapped:
            cols_to_keep = list(self.mapping.values())
            cols_to_drop = [col for col in result.columns if col not in cols_to_keep]

            if cols_to_drop:
                result = result.drop(columns=cols_to_drop)
                self.log.info(
                    "Dropped unmapped columns",
                    dropped_columns=cols_to_drop,
                )

        return result


class TypeConverter(DataFrameTransformer):
    """Converts column types in a DataFrame."""

    def __init__(
        self,
        type_mapping: dict[str, Any],
        errors: Literal["raise", "ignore"] = "raise",
        name: str | None = None,
    ):
        """Initialize the type converter.

        Args:
            type_mapping: Dictionary mapping column names to dtype objects or strings
            errors: How to handle errors ('raise', 'ignore')
            name: Optional name for the converter, used for logging
        """
        super().__init__(name=name)
        self.type_mapping = type_mapping
        self.errors = errors

    def _transform_dataframe(self, df: pd.DataFrame) -> pd.DataFrame:
        """Convert column types in the DataFrame.

        Args:
            df: Input DataFrame

        Returns:
            DataFrame with converted column types
        """
        result = df.copy()

        for col, dtype in self.type_mapping.items():
            if col not in result.columns:
                if self.errors == "raise":
                    raise ValueError(f"Column '{col}' not found in DataFrame")
                self.log.warning(f"Column '{col}' not found in DataFrame, skipping")
                continue

            try:
                result[col] = result[col].astype(dtype)
                self.log.info(f"Converted column '{col}' to type '{dtype}'")
            except Exception as e:
                if self.errors == "raise":
                    raise TransformationError(
                        f"Failed to convert column '{col}' to type '{dtype}': {e}"
                    ) from e
                self.log.error(f"Failed to convert column '{col}' to type '{dtype}'", error=str(e))

        return result


class TextCleaner(DataFrameTransformer):
    """Cleans text columns in a DataFrame."""

    def __init__(
        self,
        columns: list[str],
        lower: bool = True,
        remove_punctuation: bool = False,
        remove_digits: bool = False,
        remove_whitespace: bool = True,
        errors: str = "ignore",
        name: str | None = None,
    ):
        """Initialize the text cleaner.

        Args:
            columns: List of column names to clean
            lower: Whether to convert text to lowercase
            remove_punctuation: Whether to remove punctuation
            remove_digits: Whether to remove digits
            remove_whitespace: Whether to normalize whitespace
            errors: How to handle errors ('raise', 'ignore')
            name: Optional name for the cleaner, used for logging
        """
        super().__init__(name=name)
        self.columns = columns
        self.lower = lower
        self.remove_punctuation = remove_punctuation
        self.remove_digits = remove_digits
        self.remove_whitespace = remove_whitespace
        self.errors = errors

    def _transform_dataframe(self, df: pd.DataFrame) -> pd.DataFrame:
        """Clean text columns in the DataFrame.

        Args:
            df: Input DataFrame

        Returns:
            DataFrame with cleaned text columns
        """
        result = df.copy()

        for col in self.columns:
            if col not in result.columns:
                if self.errors == "raise":
                    raise ValueError(f"Column '{col}' not found in DataFrame")
                self.log.warning(f"Column '{col}' not found in DataFrame, skipping")
                continue

            try:
                # Apply text cleaning operations
                if self.lower:
                    result[col] = result[col].str.lower()

                if self.remove_punctuation:
                    result[col] = result[col].str.replace(r"[^\w\s]", "", regex=True)

                if self.remove_digits:
                    result[col] = result[col].str.replace(r"\d", "", regex=True)

                if self.remove_whitespace:
                    result[col] = result[col].str.replace(r"\s+", " ", regex=True).str.strip()

                self.log.info(f"Cleaned text column '{col}'")
            except Exception as e:
                if self.errors == "raise":
                    raise TransformationError(f"Failed to clean column '{col}': {e}") from e
                self.log.error(f"Failed to clean column '{col}'", error=str(e))

        return result


class DataEnricher(Transformer[InputType, OutputType]):
    """Base class for data enrichment transformers."""

    def transform(self, data: InputType) -> OutputType:
        """Enrich the input data.

        Args:
            data: Input data to enrich

        Returns:
            Enriched data

        Raises:
            EnrichmentError: If enrichment fails
        """
        try:
            return self._enrich_data(data)
        except Exception as e:
            if isinstance(e, EnrichmentError):
                raise
            raise EnrichmentError(f"Data enrichment failed: {e}") from e

    @abstractmethod
    def _enrich_data(self, data: InputType) -> OutputType:
        """Implement the data enrichment logic.

        Args:
            data: Input data to enrich

        Returns:
            Enriched data
        """
        pass


# Utility functions for common transformation tasks


def normalize_timestamp(
    timestamp: str | datetime,
    target_format: str | None = None,
    target_timezone: str = "UTC",
) -> str | datetime:
    """Normalize a timestamp to a consistent format and timezone.

    Args:
        timestamp: Input timestamp (string or datetime object)
        target_format: Output format (e.g., '%Y-%m-%dT%H:%M:%SZ'), or None to return datetime
        target_timezone: Target timezone name

    Returns:
        Normalized timestamp as string or datetime object
    """
    if isinstance(timestamp, str):
        # Parse string timestamp
        dt = pd.to_datetime(timestamp)
    else:
        # Use provided datetime object
        dt = timestamp

    # Ensure timezone is set
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=UTC)

    # Convert to target timezone
    dt = dt.astimezone(UTC)

    # Format if requested
    if target_format:
        return dt.strftime(target_format)

    return dt


def camel_to_snake(name: str) -> str:
    """Convert camelCase or PascalCase to snake_case.

    Args:
        name: Input string in camelCase or PascalCase

    Returns:
        String in snake_case
    """
    # Insert underscore before uppercase letters and convert to lowercase
    s1 = re.sub("(.)([A-Z][a-z]+)", r"\1_\2", name)
    return re.sub("([a-z0-9])([A-Z])", r"\1_\2", s1).lower()


def snake_to_camel(name: str, pascal: bool = False) -> str:
    """Convert snake_case to camelCase or PascalCase.

    Args:
        name: Input string in snake_case
        pascal: Whether to convert to PascalCase instead of camelCase

    Returns:
        String in camelCase or PascalCase
    """
    parts = name.split("_")
    if pascal:
        return "".join(word.title() for word in parts)
    else:
        return parts[0] + "".join(word.title() for word in parts[1:])


def merge_dataframes(
    left_df: pd.DataFrame,
    right_df: pd.DataFrame,
    on: str | list[str] | None = None,
    left_on: str | list[str] | None = None,
    right_on: str | list[str] | None = None,
    how: Literal["left", "right", "outer", "inner", "cross"] = "left",
    suffixes: tuple[str, str] = ("_x", "_y"),
) -> pd.DataFrame:
    """Merge two DataFrames with error handling.

    Args:
        left_df: Left DataFrame
        right_df: Right DataFrame
        on: Column name(s) to join on (if same in both DataFrames)
        left_on: Column name(s) from left DataFrame to join on
        right_on: Column name(s) from right DataFrame to join on
        how: Type of merge ('left', 'right', 'outer', 'inner', 'cross')
        suffixes: Suffixes to apply to overlapping columns

    Returns:
        Merged DataFrame
    """
    try:
        return pd.merge(
            left_df,
            right_df,
            on=on,
            left_on=left_on,
            right_on=right_on,
            how=how,
            suffixes=suffixes,
        )
    except Exception as e:
        log.error("DataFrame merge failed", error=str(e))
        raise TransformationError(f"DataFrame merge failed: {e}") from e
