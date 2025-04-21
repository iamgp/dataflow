###############
# Base Stage
###############
FROM python:3.11-slim AS base

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=off \
    PIP_DISABLE_PIP_VERSION_CHECK=on \
    POETRY_VERSION=1.4.2

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/*

# Install uv for dependency management
RUN pip install uv

# Set up Python path
ENV PYTHONPATH=/app:$PYTHONPATH

# Create app directory
WORKDIR /app

###############
# Dependencies Stage
###############
FROM base AS dependencies

# Copy only pyproject.toml and related files first for better caching
COPY pyproject.toml ./

# Install all dependencies
RUN uv venv --python 3.11
RUN uv pip install -e .

###############
# Development Stage
###############
FROM dependencies AS development

# Install development dependencies
RUN uv pip install -e ".[dev]"

# Copy the rest of the code
COPY . .

###############
# API Stage
###############
FROM dependencies AS api

# Copy the rest of the application code
COPY . .

# Expose port for API
EXPOSE 8000

# Command to run the API server
CMD ["uvicorn", "dataflow.api:app", "--host", "0.0.0.0", "--port", "8000"]

###############
# Dagster Stage
###############
FROM dependencies AS dagster

# Copy the rest of the application code
COPY . .

# Expose port for Dagster UI
EXPOSE 3000

# Command to run the Dagster server
CMD ["dagster", "dev", "-h", "0.0.0.0", "-p", "3000"]

###############
# CLI Stage
###############
FROM dependencies AS cli

# Copy the rest of the application code
COPY . .

# Set entrypoint to the CLI
ENTRYPOINT ["dataflow"]
CMD ["--help"]
