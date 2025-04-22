# 🚀 DATAFLOW

> **Data Architecture for Transformation, Analytics, File storage, Layered Orchestration, and Warehousing**

[![CI](https://github.com/iamgp/dataflow/actions/workflows/ci.yml/badge.svg)](https://github.com/iamgp/dataflow/actions/workflows/ci.yml)
[![Integration Tests](https://github.com/iamgp/dataflow/actions/workflows/integration-tests.yml/badge.svg)](https://github.com/iamgp/dataflow/actions/workflows/integration-tests.yml)
[![codecov](https://codecov.io/gh/iamgp/dataflow/branch/main/graph/badge.svg)](https://codecov.io/gh/iamgp/dataflow)
[![Docs](https://img.shields.io/badge/docs-mkdocs-blue)](docs/)
[![License](https://img.shields.io/github/license/iamgp/dataflow)](LICENSE)

---

## 🌟 Overview

**DATAFLOW** is a modern, modular data warehouse platform for seamless extraction, transformation, orchestration, storage, semantic enrichment, and visualization of data.
Built with best-in-class open-source tools, DATAFLOW empowers teams to build robust, scalable, and maintainable data infrastructure for analytics, reporting, and advanced applications.

---

## 🏗️ Architecture

`mermaid
flowchart TD
DLT[DLT: Extractor/Ingestor]
Dagster[Dagster: Orchestrator]
DBT[DBT: Transformation]
DuckDB[DuckDB or Postgres: Table Storage]
Minio[Minio: File Storage]
OWL[OWL Ontology]
Embeddings[Semantic Layer / Embeddings]
FastAPI[FastAPI: REST API]
Click[Click: CLI]
Evidence[Evidence: Visualization]
Deequ[Deequ: Data Quality]
Amundsen[Amundsen: Data Catalog]
Prometheus[Prometheus: Monitoring]

    DLT --> Dagster
    Dagster --> DBT
    DBT --> DuckDB
    DBT --> Minio
    DuckDB --> FastAPI
    Minio --> FastAPI
    FastAPI --> Evidence
    FastAPI --> Click
    DuckDB --> Evidence
    Minio --> Evidence
    DuckDB --> Embeddings
    Embeddings --> FastAPI
    OWL --> Embeddings
    Amundsen -.-> DuckDB
    Amundsen -.-> Minio
    Deequ -.-> DuckDB
    Prometheus -.-> Dagster
    Prometheus -.-> FastAPI

`

---

## ⚡ Quickstart

1. **Clone the repo:**
   `git clone https://github.com/iamgp/dataflow.git && cd dataflow`

2. **Set up your environment:**

   - Install [uv](https://github.com/astral-sh/uv) or [hatch](https://hatch.pypa.io/)
   - `uv venv` or `hatch shell`
   - `uv pip install -r requirements.txt` or `hatch run pip install .`

3. **Start all services:**

   ```bash
   # Using docker-compose directly
   docker-compose up -d

   # Or using the CLI (after installing)
   python -m dataflow.cli service start --all -d
   ```

4. **Access the platform:**
   - Dagster UI: [localhost:3000](http://localhost:3000)
   - FastAPI docs: [localhost:8000/docs](http://localhost:8000/docs)
   - Evidence dashboards: [localhost:9002](http://localhost:9002)
   - Grafana: [localhost:3001](http://localhost:3001) (login: admin/admin)
   - MinIO console: [localhost:9001](http://localhost:9001) (login: minioadmin/minioadmin)

---

## 🧩 Key Features

- **Unified Data Pipeline:** Ingest, transform, and store data from diverse sources.
- **Workflow-Centric:** Modular, self-contained workflows for ETL, analytics, and more.
- **Modern Python Stack:** FastAPI, Dagster, DBT, Minio, DuckDB/Postgres, Evidence, and more.
- **CLI & API:** Manage everything from the command line or REST API.
- **Observability:** Structured logging (Loguru + structlog), Loki, Prometheus, Grafana.
- **Extensible:** Add new workflows, data sources, and dashboards with ease.

---

## 🛠️ Developer Guide

- **Onboarding Guide:** [docs/onboarding.md](docs/onboarding.md)
- **Troubleshooting:** [docs/troubleshooting.md](docs/troubleshooting.md)
- **Environment Variables:** [docs/environment_variables.md](docs/environment_variables.md)
- **CLI Usage:** [docs/cli_usage.md](docs/cli_usage.md) or run `python -m dataflow.cli --help`
- **Testing Guide:** [docs/testing.md](docs/testing.md)
- **Workflow Authoring:** [docs/workflows.md](docs/workflows.md)
- **Product Requirements:** [docs/prd.md](docs/prd.md)
- **Implementation Task List:** [docs/tasks.md](docs/tasks.md)
- **Full Documentation:** Run `mkdocs serve` to view all docs locally

---

## 📦 Service Management

You can manage the services using either Docker Compose directly or the DATAFLOW CLI:

### Using Docker Compose

```bash
# Start all services
docker-compose up -d

# Check service status
docker-compose ps

# View logs
docker-compose logs -f <service_name>

# Stop all services
docker-compose down
```

### Using the CLI

```bash
# Start all services in background mode
python -m dataflow.cli service start --all -d

# Start specific services
python -m dataflow.cli service start api dagster

# Check status
python -m dataflow.cli service status

# View logs (follow mode)
python -m dataflow.cli service logs -f api

# Restart services
python -m dataflow.cli service restart dagster

# Stop all services
python -m dataflow.cli service stop --all
```

---

## 🧪 Testing

DATAFLOW has comprehensive test coverage to ensure code quality and reliability:

```bash
# Run unit tests
pytest -m "not integration"

# Run integration tests (requires Docker Compose)
INTEGRATION_TESTS=true pytest tests/integration/

# Run tests with coverage report
pytest --cov=src/dataflow

# Run specific tests
pytest tests/shared/test_logging.py
```

See the [Testing Guide](docs/testing.md) for more details on writing and running tests.

---

## 🤖 AI-Assisted Development

We use AI tools (Cursor, GPT, Claude, Copilot, etc.) to accelerate development.
See `docs/prd.md` and `docs/tasks.md` for project requirements and implementation planning.

---

## 📚 Resources

- [Onboarding Guide](docs/onboarding.md)
- [Troubleshooting Guide](docs/troubleshooting.md)
- [Environment Variables](docs/environment_variables.md)
- [CLI Usage](docs/cli_usage.md)
- [Testing Guide](docs/testing.md)
- [Workflow Authoring](docs/workflows.md)
- [Product Requirements](docs/prd.md)
- [Implementation Task List](docs/tasks.md)
- [GitHub Actions CI](https://github.com/iamgp/dataflow/actions)
