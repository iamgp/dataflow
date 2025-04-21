###############
# Base Stage
###############
FROM python:3.11-slim AS base

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=off \
    PIP_DISABLE_PIP_VERSION_CHECK=on \
    POETRY_VERSION=1.4.2 \
    PYTHONPATH=/app/src:$PYTHONPATH

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/*

# Install uv for dependency management
RUN pip install uv

# Create app directory
WORKDIR /app

###############
# Dependencies Stage
###############
FROM base AS dependencies

# Copy files needed for building
COPY pyproject.toml README.md ./

# Initialize a Git repository for dynamic versioning
RUN git init && \
    git config --global user.email "build@example.com" && \
    git config --global user.name "Docker Build" && \
    git add . && \
    git commit -m "Initial commit for build"

# Copy the entire project to ensure proper installation
COPY . .

# Install all dependencies directly with pip
RUN pip install -e .

###############
# Development Stage
###############
FROM dependencies AS development

# Install development dependencies
RUN pip install -e ".[dev]"

###############
# API Stage
###############
FROM dependencies AS api

# Expose port for API
EXPOSE 8000

# Command to run the API server
CMD ["uvicorn", "dataflow.api:app", "--host", "0.0.0.0", "--port", "8000"]

###############
# Dagster Stage
###############
FROM dependencies AS dagster

# Install Dagster explicitly
RUN pip install dagster dagster-webserver

# Create dagster home directory and ensure permissions
RUN mkdir -p /opt/dagster/dagster_home && \
    touch /opt/dagster/dagster_home/dagster.yaml

# Expose port for Dagster UI
EXPOSE 3000

# Command to run the Dagster server
CMD ["dagster", "dev", "-m", "dataflow.workflows", "-h", "0.0.0.0", "-p", "3000"]

###############
# CLI Stage
###############
FROM dependencies AS cli

# Set entrypoint to the CLI
ENTRYPOINT ["dataflow"]
CMD ["--help"]
