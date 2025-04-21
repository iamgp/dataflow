# 🚀 DATAFLOW

> **Data Architecture for Transformation, Analytics, File storage, Layered Orchestration, and Warehousing**

[![CI](https://github.com/iamgp/dataflow/actions/workflows/ci.yml/badge.svg)](https://github.com/iamgp/dataflow/actions/workflows/ci.yml)
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
   `docker-compose up`

4. **Access the platform:**
   - Dagster UI: [localhost:3000](http://localhost:3000)
   - FastAPI docs: [localhost:8000/docs](http://localhost:8000/docs)
   - Evidence dashboards: [localhost:9000](http://localhost:9000)
   - Grafana: [localhost:3001](http://localhost:3001)

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

- **Product Requirements:** See [`PRD.md`](PRD.md)
- **Implementation Task List:** See [`TASKS.md`](TASKS.md)
- **Docs:** See [`docs/`](docs/) or run `mkdocs serve`
- **Workflow Authoring:** See the [Workflow Authoring Checklist](PRD.md#15-workflow-authoring-checklist)
- **CLI Usage:** Run `python -m dataflow.cli --help` or see [CLI docs](docs/cli.md)
- **Testing:** Run `pytest` (see [CI status](https://github.com/iamgp/dataflow/actions/workflows/ci.yml))

---

## 🤖 AI-Assisted Development

We use AI tools (Cursor, GPT, Claude, Copilot, etc.) to accelerate development.
See `PRD.md` and `TASKS.md` for project requirements and implementation planning.

---

## 📚 Resources

- [Product Requirements Document](PRD.md)
- [Implementation Task List](TASKS.md)
- [Official Docs](docs/)
- [GitHub Actions CI](https://github.com/iamgp/dataflow/actions)
