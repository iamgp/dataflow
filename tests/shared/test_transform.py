"""Tests for shared transform utilities.

This module tests the shared transform utilities including base transformers,
data cleaning, and validation components.
"""

from typing import Any, cast

import pandas as pd
import pytest
from pydantic import BaseModel, ValidationError

from dataflow.shared.transform import (
    ColumnMapper,
    DataCleaner,
    DataEnricher,
    DataFrameTransformer,
    DateTimeNormalizer,
    FunctionTransformer,
    SchemaValidator,
    TextCleaner,
    TransformationError,
    Transformer,
    TransformerPipeline,
    TypeConverter,
    camel_to_snake,
    merge_dataframes,
    normalize_timestamp,
    snake_to_camel,
)

# Test Data
SAMPLE_DF = pd.DataFrame(
    {
        "id": [1, 2, 3, None],
        "name": ["John ", "Jane", "  Bob  ", None],
        "age": [25, 30, None, 40],
        "created_at": ["2024-01-01", "2024-01-02", "2024-01-03", None],
    }
)


# Test Models
class TestModel(BaseModel):
    """Test model for schema validation."""

    name: str
    age: int


# Test Classes
class SimpleTransformer(Transformer[str, str]):
    """Simple transformer for testing."""

    def transform(self, data: str) -> str:
        return data.upper()


class TestEnricher(DataEnricher[dict, dict]):
    """Test enricher for testing."""

    def _enrich_data(self, data: dict) -> dict:
        data["enriched"] = True
        return data


# Tests for Base Classes
class TestTransformer:
    """Tests for the base Transformer class."""

    def test_transformer_name(self):
        """Test transformer name initialization."""
        transformer = SimpleTransformer(name="test")
        assert transformer.name == "test"

        transformer_no_name = SimpleTransformer()
        assert transformer_no_name.name == "SimpleTransformer"

    def test_transformer_call(self):
        """Test transformer callable interface."""
        transformer = SimpleTransformer()
        assert transformer("test") == "TEST"
        assert transformer.transform("test") == "TEST"


class TestTransformerPipeline:
    """Tests for the TransformerPipeline class."""

    def test_empty_pipeline(self):
        """Test pipeline initialization with no transformers."""
        with pytest.raises(ValueError):
            TransformerPipeline([])

    def test_pipeline_transform(self):
        """Test successful pipeline transformation."""

        def double(x: int) -> int:
            return x * 2

        def add_one(x: int) -> int:
            return x + 1

        pipeline = TransformerPipeline(
            [
                FunctionTransformer(double),
                FunctionTransformer(add_one),
            ]
        )

        assert pipeline.transform(2) == 5  # (2 * 2) + 1

    def test_pipeline_error(self):
        """Test pipeline error handling."""

        def raise_error(_: Any) -> Any:
            raise ValueError("Test error")

        pipeline = TransformerPipeline(
            [
                FunctionTransformer(raise_error),
            ]
        )

        with pytest.raises(TransformationError) as exc_info:
            pipeline.transform(1)
        assert "Test error" in str(exc_info.value)


class TestFunctionTransformer:
    """Tests for the FunctionTransformer class."""

    def test_function_transform(self):
        """Test function transformer with simple function."""

        def square(x: int) -> int:
            return x * x

        transformer = FunctionTransformer(square)
        assert transformer.transform(2) == 4

    def test_function_error(self):
        """Test function transformer error handling."""

        def raise_error(_: Any) -> Any:
            raise ValueError("Test error")

        transformer = FunctionTransformer(raise_error)
        with pytest.raises(TransformationError) as exc_info:
            transformer.transform(1)
        assert "Test error" in str(exc_info.value)


class TestDataFrameTransformer:
    """Tests for the DataFrameTransformer class."""

    class TestDFTransformer(DataFrameTransformer):
        """Test implementation of DataFrameTransformer."""

        def _transform_dataframe(self, df: pd.DataFrame) -> pd.DataFrame:
            return df * 2

    def test_invalid_input(self):
        """Test handling of non-DataFrame input."""
        transformer = self.TestDFTransformer()
        with pytest.raises(TransformationError):
            transformer.transform(cast(pd.DataFrame, "not a dataframe"))

    def test_invalid_output(self):
        """Test handling of invalid output type."""

        class BadTransformer(DataFrameTransformer):
            def _transform_dataframe(self, df: pd.DataFrame) -> pd.DataFrame:
                return cast(pd.DataFrame, "not a dataframe")

        transformer = BadTransformer()
        with pytest.raises(TransformationError):
            transformer.transform(pd.DataFrame({"a": [1]}))


class TestSchemaValidator:
    """Tests for the SchemaValidator class."""

    def test_valid_data(self):
        """Test validation of valid data."""
        validator = SchemaValidator(TestModel)
        data = {"name": "John", "age": 30}
        result = validator.transform(data)
        assert result == data

    def test_invalid_data(self):
        """Test validation of invalid data."""
        validator = SchemaValidator(TestModel)
        data = {"name": "John", "age": "not an int"}
        with pytest.raises(ValidationError):
            validator.transform(data)


class TestDataCleaner:
    """Tests for the DataCleaner class."""

    def test_drop_duplicates(self):
        """Test duplicate row removal."""
        df = pd.DataFrame({"a": [1, 1, 2], "b": ["x", "x", "y"]})
        cleaner = DataCleaner(drop_duplicates=True)
        result = cleaner.transform(df)
        assert len(result) == 2

    def test_drop_null_columns(self):
        """Test null column removal."""
        df = pd.DataFrame({"a": [1, 2, None], "b": [None, None, None], "c": [1, 2, 3]})
        cleaner = DataCleaner(drop_null_columns=0.5)
        result = cleaner.transform(df)
        assert "b" not in result.columns

    def test_strip_strings(self):
        """Test string stripping."""
        df = pd.DataFrame({"name": [" John ", "Jane  ", "  Bob"]})
        cleaner = DataCleaner(strip_strings=True)
        result = cleaner.transform(df)
        assert all(not s.startswith(" ") and not s.endswith(" ") for s in result["name"])


class TestDateTimeNormalizer:
    """Tests for the DateTimeNormalizer class."""

    def test_datetime_normalization(self):
        """Test datetime normalization."""
        df = pd.DataFrame({"date": ["2024-01-01", "2024-01-02"], "other": [1, 2]})
        normalizer = DateTimeNormalizer(
            columns=["date"], target_format="%Y-%m-%d", target_timezone="UTC"
        )
        result = normalizer.transform(df)
        assert isinstance(result["date"].iloc[0], str)
        assert result["date"].iloc[0] == "2024-01-01"

    def test_invalid_date(self):
        """Test handling of invalid dates."""
        df = pd.DataFrame(
            {
                "date": ["not a date", "2024-01-02"],
            }
        )
        normalizer = DateTimeNormalizer(columns=["date"], errors="raise")
        with pytest.raises(TransformationError):
            normalizer.transform(df)


class TestColumnMapper:
    """Tests for the ColumnMapper class."""

    def test_column_mapping(self):
        """Test column name mapping."""
        df = pd.DataFrame({"old_name": [1, 2], "keep_this": [3, 4]})
        mapper = ColumnMapper({"old_name": "new_name"})
        result = mapper.transform(df)
        assert "new_name" in result.columns
        assert "old_name" not in result.columns
        assert "keep_this" in result.columns

    def test_drop_unmapped(self):
        """Test dropping unmapped columns."""
        df = pd.DataFrame({"keep": [1, 2], "drop": [3, 4]})
        mapper = ColumnMapper({"keep": "new_keep"}, drop_unmapped=True)
        result = mapper.transform(df)
        assert list(result.columns) == ["new_keep"]


class TestTypeConverter:
    """Tests for the TypeConverter class."""

    def test_type_conversion(self):
        """Test data type conversion."""
        df = pd.DataFrame({"number": ["1", "2"], "text": [1, 2]})
        converter = TypeConverter({"number": int, "text": str})
        result = converter.transform(df)
        assert result["number"].dtype == "int64"
        assert result["text"].dtype == "object"

    def test_conversion_error(self):
        """Test handling of conversion errors."""
        df = pd.DataFrame({"number": ["not a number", "2"]})
        converter = TypeConverter({"number": int}, errors="raise")
        with pytest.raises(TransformationError):
            converter.transform(df)


class TestTextCleaner:
    """Tests for the TextCleaner class."""

    def test_text_cleaning(self):
        """Test text cleaning operations."""
        df = pd.DataFrame({"text": ["Hello, World! 123", "TEST string"]})
        cleaner = TextCleaner(
            columns=["text"], lower=True, remove_punctuation=True, remove_digits=True
        )
        result = cleaner.transform(df)
        assert result["text"].iloc[0] == "hello world"
        assert result["text"].iloc[1] == "test string"


# Tests for Utility Functions
def test_normalize_timestamp():
    """Test timestamp normalization."""
    timestamp = "2024-01-01 12:00:00"
    result = normalize_timestamp(timestamp, target_format="%Y-%m-%d")
    assert result == "2024-01-01"


def test_camel_to_snake():
    """Test camelCase to snake_case conversion."""
    assert camel_to_snake("camelCase") == "camel_case"
    assert camel_to_snake("ThisIsATest") == "this_is_a_test"


def test_snake_to_camel():
    """Test snake_case to camelCase conversion."""
    assert snake_to_camel("snake_case") == "snakeCase"
    assert snake_to_camel("this_is_a_test", pascal=True) == "ThisIsATest"


def test_merge_dataframes():
    """Test DataFrame merging utility."""
    df1 = pd.DataFrame({"key": [1, 2], "value1": ["a", "b"]})
    df2 = pd.DataFrame({"key": [1, 3], "value2": ["x", "y"]})

    result = merge_dataframes(df1, df2, on="key", how="left")
    assert len(result) == 2
    assert "value1" in result.columns
    assert "value2" in result.columns
