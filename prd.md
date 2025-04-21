# Product Requirements Document (PRD)

## Project Name: DATAFLOW

> Data Architecture for Transformation, Analytics, File storage, Layered Orchestration, and Warehousing

---

## 1. Overview

**DATAFLOW** is a modern, modular data warehouse platform designed to streamline the extraction, transformation, orchestration, storage, semantic enrichment, and visualization of data. The system leverages best-in-class open-source tools to provide a scalable, maintainable, and extensible data infrastructure for analytics, reporting, and advanced data applications.

---

## 2. Quickstart & Onboarding

### 2.1 Local Setup

1. **Clone the repository:**
   `git clone <repo-url> && cd dataflow`
2. **Set up your environment:**
   - Install uv or hatch for dependency management.
   - Run `uv venv` or `hatch shell` to create a virtual environment.
   - Install dependencies: `uv pip install -r requirements.txt` or `hatch run pip install .`
3. **Start all services:**
   - `docker-compose up` (brings up DB, Minio, Dagster, API, Evidence, Loki, Promtail, Grafana, etc.)
4. **Access the platform:**
   - Dagster UI: http://localhost:3000
   - FastAPI docs: http://localhost:8000/docs
   - Evidence dashboards: http://localhost:9000
   - Grafana: http://localhost:3001

### 2.2 Documentation

- MkDocs site: `docs/` directory, served locally with `mkdocs serve`
- API docs: `/docs` and `/redoc` endpoints from FastAPI
- Workflow authoring guide: See Section 15

---

## 3. Goals & Objectives

- **Unified Data Pipeline:** Seamlessly ingest, transform, and store data from diverse sources.
- **Data Quality & Governance:** Ensure data integrity, traceability, and discoverability.
- **Semantic Enrichment:** Enable advanced analytics and interoperability through semantic layers and ontologies.
- **User Empowerment:** Provide accessible APIs, CLI tools, and visualization interfaces for technical and non-technical users.
- **Scalability & Maintainability:** Use containerization and orchestration for easy deployment and scaling.

---

## 4. Core Components & Tools

| Function               | Tool/Technology        | Description                                                 |
| ---------------------- | ---------------------- | ----------------------------------------------------------- |
| Extraction/Ingestion   | DLT                    | Extracts and ingests data from various sources.             |
| Transformation         | DBT                    | Transforms raw data into analytics-ready models.            |
| Orchestration          | Dagster                | Manages and schedules data workflows and dependencies.      |
| Table Storage          | DuckDB or Postgres     | Stores structured, queryable data tables.                   |
| File/Object Storage    | Minio                  | S3-compatible storage for files and unstructured data.      |
| Visualization          | Evidence               | Generates dashboards and reports from warehouse data.       |
| Semantic Layer         | Embeddings             | Provides vector-based semantic search and analytics.        |
| Ontology               | OWL                    | Defines data relationships and enhances interoperability.   |
| REST API               | FastAPI                | Exposes data and metadata via a performant, documented API. |
| Command Line Interface | Click                  | CLI for managing workflows, data, and system operations.    |
| Containerization       | Docker + Dev Container | Ensures consistent development and deployment environments. |
| CI/CD                  | GitHub Actions         | Automates testing, linting, builds, and deployment.         |

---

## 5. Stretch Goals

- **Data Quality:** Integrate Deequ for automated data validation and quality checks.
- **Data Catalog:** Add Amundsen for metadata management and data discovery.
- **Monitoring:** Use Prometheus (and optionally Grafana) for system and pipeline monitoring.

---

## 6. User Stories

- _As a data engineer_, I want to ingest and transform data with minimal manual intervention.
- _As a data analyst_, I want to explore and visualize data through dashboards and semantic search.
- _As a developer_, I want to access data and metadata via a REST API and CLI.
- _As a data steward_, I want to ensure data quality, trace lineage, and manage metadata.

---

## 7. Success Metrics

- **Pipeline Reliability:** >99% successful runs of scheduled workflows.
- **Data Quality:** <1% data quality errors detected post-validation.
- **User Adoption:** At least 3 teams actively using Evidence dashboards and the API.
- **Performance:** Sub-second query response times for key analytics queries.
- **Documentation:** 100% coverage for API and CLI usage.

---

## 8. Timeline

| Phase             | Milestone                                  | Target Date |
| ----------------- | ------------------------------------------ | ----------- |
| Phase 1           | Core pipeline (DLT, DBT, Dagster, Storage) | YYYY-MM-DD  |
| Phase 2           | API, CLI, and Visualization (Evidence)     | YYYY-MM-DD  |
| Phase 3           | Semantic Layer, Ontology, Containerization | YYYY-MM-DD  |
| Phase 4 (Stretch) | Data Quality, Catalog, Monitoring          | YYYY-MM-DD  |
| Phase 5           | Testing, Documentation, Deployment         | YYYY-MM-DD  |

---

## 9. Risks & Mitigations

- **Integration Complexity:** Use containerization and clear interface contracts.
- **Data Quality Issues:** Implement automated validation (Deequ) and monitoring.
- **User Onboarding:** Provide comprehensive documentation and training sessions.

---

## 10. Open Questions & Decisions

| Area                | Question/Decision                                       | Status/Notes |
| ------------------- | ------------------------------------------------------- | ------------ |
| Storage Backend     | DuckDB or Postgres as primary?                          | TBD          |
| Data Sources        | What are initial data sources and expected volumes?     | TBD          |
| API Auth            | What authentication/authorization for FastAPI?          | TBD          |
| Data Lineage        | Will we use Dagster, Amundsen, or custom metadata?      | TBD          |
| Metadata Standards  | How will we document datasets, fields, transformations? | TBD          |
| Workflow Versioning | How will we handle breaking changes to workflows?       | TBD          |

---

## 11. Architecture Diagrams

### 11.1 System Architecture

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

### 11.2 Sequence Diagram: Typical ETL Workflow

`mermaid
sequenceDiagram
participant User
participant DLT
participant Dagster
participant DBT
participant DuckDB
participant Evidence

    User->>DLT: Trigger ETL
    DLT->>Dagster: Send data extraction job
    Dagster->>DBT: Run transformation
    DBT->>DuckDB: Store transformed data
    DuckDB->>Evidence: Data available for visualization
    User->>Evidence: View dashboard

`

---

## 12. Python Underpinnings & Developer Tooling

### 12.1 Core Tooling

| Tool           | Purpose                      | Why Use It?                                    |
| -------------- | ---------------------------- | ---------------------------------------------- |
| uv             | Dependency management, venvs | Ultra-fast, modern, reproducible environments  |
| ruff           | Linting & formatting         | Fast, all-in-one, easy to configure            |
| hatch          | Project management           | Modern, flexible, PEP 621 support              |
| basedpyright   | Static type checking         | Fast, strict, modern Python support            |
| pytest         | Testing                      | Powerful, extensible, industry standard        |
| mkdocs         | Documentation                | Simple, Markdown-based, easy to deploy         |
| pre-commit     | Pre-commit hooks             | Enforce code quality automatically             |
| github actions | CI/CD                        | Automates testing, linting, builds, deployment |

### 12.2 Type Checking

- **basedpyright** is used for static type checking, providing fast and strict type analysis.
- It supports the latest Python features and integrates well with editors (e.g., VS Code).
- Example configuration (`pyrightconfig.json`):

  `{
  "typeCheckingMode": "strict",
  "reportMissingTypeStubs": false,
  "exclude": ["**/build", "**/dist", "**/.venv"]
}`

### 12.3 Linting & Formatting

- **ruff** is used for both linting and code formatting, ensuring code consistency and catching common errors.
- Configuration is managed in `pyproject.toml`.

### 12.4 Dependency & Project Management

- **uv** is used for fast dependency installation and environment management.
- **hatch** manages project structure, builds, and environment isolation.

### 12.5 Testing

- **pytest** is the standard for unit, integration, and end-to-end tests.
- Test environments are managed via `hatch`.

### 12.6 Documentation

- **mkdocs** is used for project documentation, enabling easy authoring and deployment of Markdown-based docs.
- Documentation will be maintained in the `/docs` directory and published as a static site.

### 12.7 Pre-commit Hooks

- **pre-commit** is used to automate code quality checks (linting, type checking, formatting) before every commit.

### 12.8 CI/CD with GitHub Actions

- **GitHub Actions** is used for continuous integration and deployment.
- **CI pipeline** runs on every PR and push:
  - Linting (`ruff`)
  - Type checking (`basedpyright`)
  - Testing (`pytest`)
  - Docs build (`mkdocs`)
  - (Optional) Build and push Docker images
  - (Optional) Deploy to staging/production
- **Sample workflow file** is provided in `.github/workflows/ci.yml`.
- **Secrets** and credentials are managed via GitHub Secrets.

---

## 13. Command Line Interface (CLI)

### 13.1 Overview

DATAFLOW will provide a comprehensive CLI, built with **Click**, to allow users and developers to manage, inspect, and operate the platform and its workflows directly from the command line. The CLI will complement the orchestrator (Dagster) and provide additional control for local development, automation, and debugging.

---

### 13.2 CLI Capabilities

- **Workflow Management**

  - List available workflows
  - Trigger (run) a workflow manually
  - Show workflow status/history
  - Validate workflow configuration

- **Service Management**

  - Start/stop/restart core services (API, Dagster, Evidence, Minio, DB, Loki, Promtail, Grafana, etc.)
  - Start services in the background (detached mode)
  - Start/stop/restart services individually or as a group (e.g., `dataflow service start dagster`, `dataflow service start all`)
  - Check service status
  - Tail logs for a specific service

- **Data Operations**

  - Ingest data from a source
  - Export data to a file or external system
  - Run data quality checks

- **Developer Utilities**

  - Run tests for a workflow or the whole project
  - Lint and type-check code
  - Generate or update documentation

- **Admin/Setup**
  - Initialize a new workflow (scaffold folder structure)
  - Manage environment variables and secrets
  - Show platform version and health

---

### 13.3 Example CLI Commands

- `dataflow workflow list`
- `dataflow workflow run nightscout`
- `dataflow workflow status nightscout`
- `dataflow service start all --background`
- `dataflow service start dagster --background`
- `dataflow service stop evidence`
- `dataflow service restart minio`
- `dataflow service status`
- `dataflow logs tail dagster`
- `dataflow ingest --source nightscout`
- `dataflow test --workflow nightscout`
- `dataflow lint`
- `dataflow docs build`
- `dataflow workflow init my_new_workflow`

---

### 13.4 Implementation Notes

- **Click** will be used for its composability, help text, and subcommand support.
- The CLI will interact with Docker Compose, systemd, or direct process management for service control.
- Services can be started in the foreground or background (detached mode), individually or as a group.
- For workflow operations, the CLI will interface with the workflow registry and orchestrator APIs.
- Logs can be tailed by reading from files or querying Loki.
- The CLI will be documented in the main docs and provide `--help` for all commands.

---

### 13.5 Benefits

- **Unified control:** Manage all aspects of DATAFLOW from one tool.
- **Developer productivity:** Simplifies local dev, testing, and debugging.
- **Automation:** Enables scripting and CI/CD integration.
- **Consistency:** Reduces manual errors and ensures repeatable operations.
- **Flexibility:** Start/stop/restart services as needed, in the foreground or background, individually or as a group.

---

## 14. Workflow Organization & Registry Pattern

### 14.1 Overview

DATAFLOW adopts a **workflow-centric, colocated project structure**. Each workflow (e.g., a specific ETL and visualization pipeline) is self-contained, with all its logic, configuration, orchestration, and assets grouped together. This approach improves maintainability, discoverability, and scalability as the number of workflows grows.

To enable automatic discovery and orchestration of workflows, DATAFLOW uses a **Python registry decorator pattern**. Each workflow registers itself with a global registry, allowing the orchestrator (e.g., Dagster) and CLI to dynamically discover and manage all available workflows without manual updates to a central list.

---

### 14.2 Project Structure

`src/
dataflow/
workflows/
<workflow_name>/
**init**.py
ingestion.py # Data extraction logic
transform.py # Data transformation logic
assets.py # Dagster assets/resources (optional)
dagster_job.py # Dagster job/op definitions, registry decorator
config.yaml # Workflow-specific config
dbt/
evidence/
tests/
shared/
**init**.py
... (shared connectors, DB helpers, etc.)
workflows/
registry.py # Global workflow registry and decorator
integrations/

# (Optional: for external or shared DBT/Evidence projects)

docs/

# MkDocs documentation

`

---

### 14.3 Structure Description

- **`src/dataflow/workflows/<workflow_name>/`**:
  Contains all logic and assets for a workflow, split by responsibility:

  - `ingestion.py`: Data extraction logic (e.g., API calls, file reads).
  - `transform.py`: Data transformation logic (e.g., cleaning, enrichment, mapping).
  - `assets.py`: Dagster assets, resources, or reusable asset definitions (optional).
  - `dagster_job.py`: Dagster job/op definitions, registry decorator, and workflow wiring.
  - `config.yaml`: Workflow-specific configuration (e.g., API URLs, secrets).
  - `dbt/`: DBT models for this workflow.
  - `evidence/`: Evidence dashboards for this workflow.
  - `tests/`: Unit and integration tests for this workflow.

- **`src/dataflow/shared/`**:
  Shared utilities, connectors, and interfaces used by multiple workflows (e.g., API clients, DB helpers).

- **`src/dataflow/workflows/registry.py`**:
  Defines the global workflow registry and the `@register_workflow` decorator. This enables automatic registration and discovery of all workflows.

- **`integrations/`**:
  (Optional) For external or shared DBT/Evidence projects.

- **`docs/`**:
  Project documentation (MkDocs).

---

### 14.4 Workflow Registry Pattern

- **Global Registry:**
  A list or dictionary that holds references to all registered workflows.

- **Decorator:**
  A `@register_workflow` decorator is applied to each workflow’s main job (e.g., Dagster job). When the job is defined, it is automatically added to the registry.

- **Discovery:**
  The orchestrator (e.g., Dagster repository) and CLI can iterate over the registry to discover and manage all workflows, without manual updates.

---

### 14.5 Example: Nightscout Workflow

- `src/dataflow/workflows/nightscout/ingestion.py`
  Contains data extraction logic, e.g., `fetch_nightscout_data()`.
- `src/dataflow/workflows/nightscout/transform.py`
  Contains transformation logic, e.g., `transform_entries()`.
- `src/dataflow/workflows/nightscout/assets.py`
  (Optional) Defines Dagster assets/resources.
- `src/dataflow/workflows/nightscout/dagster_job.py`
  Wires together the workflow, registers with the registry, and defines Dagster jobs/ops.
- `src/dataflow/workflows/nightscout/config.yaml`
  Workflow-specific configuration.
- `src/dataflow/workflows/nightscout/dbt/`
  DBT models for this workflow.
- `src/dataflow/workflows/nightscout/evidence/`
  Evidence dashboards for this workflow.
- `src/dataflow/workflows/nightscout/tests/`
  Unit and integration tests for this workflow.

---

### 14.6 How It Works

1. **Ingestion logic** in `ingestion.py` extracts data from sources.
2. **Transformation logic** in `transform.py` cleans and enriches data.
3. **Assets/resources** in `assets.py` (optional) define reusable Dagster assets.
4. **Dagster job** in `dagster_job.py` wires together the workflow and registers it.
5. **When the project starts**, all workflows are automatically registered in the global registry.
6. **The orchestrator (e.g., Dagster repository)** imports the registry and exposes all registered workflows for scheduling, execution, and monitoring.
7. **DBT and Evidence assets** are colocated for easy workflow-specific analytics and visualization.
8. **Tests** are colocated for easy maintenance and workflow-specific validation.

---

## 15. Workflow Authoring Checklist

To add a new workflow, follow this template:

1. **Create a new folder** in `src/dataflow/workflows/<workflow_name>/`
2. **Add ingestion logic** in `ingestion.py`
   - Implement functions/classes to extract data from sources.
3. **Add transformation logic** in `transform.py`
   - Implement functions/classes to clean, enrich, and map data.
4. **Define assets/resources** in `assets.py` (optional)
   - Define Dagster assets, resources, or reusable asset definitions.
5. **Define a Dagster job** in `dagster_job.py`
   - Wire together ingestion, transformation, and assets.
   - Use the `@register_workflow` decorator to register the job.
6. **Add workflow-specific configuration** in `config.yaml`
7. **(Optional) Add DBT models** in `dbt/`
8. **(Optional) Add Evidence dashboards** in `evidence/`
9. **Add tests** in `tests/`
10. **Document the workflow** (README or docstring)
11. **(Optional) Add metadata** (e.g., `metadata.yaml`) for lineage, ownership, and description.

---

## 16. Logging and Log Aggregation

### 16.1 Overview

DATAFLOW uses structured logging for observability and debugging. All logs are output in JSON format using **Loguru** and **structlog**. Logs are aggregated and visualized using **Grafana Loki** and **Grafana**.

### 16.2 Logging Workflow

- **Loguru + structlog:** All logs are structured and include context (workflow, job, user, etc.).
- **Promtail:** Collects logs from files or stdout and ships them to Loki.
- **Loki:** Aggregates and indexes logs for efficient querying.
- **Grafana:** Provides a UI for searching, filtering, and visualizing logs.

### 16.3 Example Log Entry

`{
  "event": "Workflow started",
  "workflow": "nightscout",
  "user": "gareth",
  "level": "info",
  "timestamp": "2024-04-21T15:00:00.000Z"
}`

### 16.4 Benefits

- Structured, queryable logs
- Unified UI for logs and metrics
- Scalable, OSS, and cloud-native ready

---

## 17. Glossary

- **DLT:** Data Loading Tool for extracting and ingesting data.
- **DBT:** Data Build Tool for transforming raw data into analytics-ready models.
- **Dagster:** Orchestration tool for managing and scheduling data workflows.
- **DuckDB:** In-process analytical database for structured data storage.
- **Postgres:** Relational database for structured data storage.
- **Minio:** S3-compatible object storage for files and unstructured data.
- **Evidence:** Open-source BI tool for data visualization and reporting.
- **OWL Ontology:** Web Ontology Language for defining semantic relationships in data.
- **Semantic Layer (Embeddings):** Layer for semantic search and advanced analytics using vector representations.
- **FastAPI:** High-performance web framework for building RESTful APIs.
- **Click:** Python package for creating command-line interfaces.
- **Docker + Dev Container:** Containerization tools for consistent development and deployment environments.
- **Deequ:** Library for automated data quality validation (stretch goal).
- **Amundsen:** Data catalog for metadata management and discovery (stretch goal).
- **Prometheus:** Monitoring and alerting toolkit (stretch goal).
- **Loki:** Log aggregation system for storing and querying logs.
- **Grafana:** Visualization and dashboard tool for logs and metrics.
- **GitHub Actions:** CI/CD platform for automating testing, builds, and deployment.

---

## 18. Contact & Ownership

- **Product Owner:** [Name], [email/Slack]
- **Technical Lead:** [Name], [email/Slack]
- **DevOps/Platform Contact:** [Name], [email/Slack]
- **Support/Questions:** [Channel or contact info]

---

**End of PRD**
