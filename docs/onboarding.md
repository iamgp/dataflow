# Dataflow Onboarding Guide

Welcome to Dataflow, a modern, modular data warehouse platform. This guide will help you get started with the project using Docker Compose and Dev Containers.

## Prerequisites

- [Docker](https://docs.docker.com/get-docker/) and [Docker Compose](https://docs.docker.com/compose/install/)
- [VS Code](https://code.visualstudio.com/) (recommended for Dev Containers)
- [Remote - Containers](https://marketplace.visualstudio.com/items?itemName=ms-vscode-remote.remote-containers) VS Code extension (for Dev Containers)

## Getting Started

### Option 1: Using Docker Compose

Docker Compose allows you to run all the services required for Dataflow with a single command.

1. **Clone the repository:**

   ```bash
   git clone <repo-url> && cd dataflow
   ```

2. **Set up environment variables (optional):**

   Create a `.env` file in the project root to override default configuration:

   ```bash
   # Example .env file
   POSTGRES_PASSWORD=mysecurepassword
   LOG_LEVEL=DEBUG
   ```

   See [Environment Variables Documentation](environment_variables.md) for a complete list of available variables.

3. **Start all services:**

   ```bash
   # Start all services in the foreground
   docker-compose up

   # Or start in detached (background) mode
   docker-compose up -d
   ```

   This will start the following services:

   - FastAPI (API server) on port 8000
   - Dagster UI on port 3000
   - Evidence dashboards on port 9002
   - Grafana on port 3001
   - MinIO (object storage) on port 9000 (API) and 9001 (console)
   - PostgreSQL on port 5432
   - Loki, Promtail, and Prometheus for logging and monitoring

4. **Access the services:**

   - FastAPI docs: http://localhost:8000/docs
   - Dagster UI: http://localhost:3000
   - Evidence dashboards: http://localhost:9002
   - Grafana: http://localhost:3001 (login with admin/admin)
   - MinIO Console: http://localhost:9001 (login with minioadmin/minioadmin)

5. **Stop the services:**

   ```bash
   # Stop all services but keep volumes
   docker-compose down

   # Stop services and remove volumes (will delete all data)
   docker-compose down -v
   ```

6. **View logs for a specific service:**
   ```bash
   docker-compose logs -f <service-name>
   ```
   Replace `<service-name>` with one of: api, dagster, db, minio, evidence, grafana, loki, promtail, prometheus

### Option 2: Using the CLI

DATAFLOW provides a CLI for managing services, workflows, and more.

1. **Set up your Python environment:**

   ```bash
   # Using uv
   uv venv
   source .venv/bin/activate  # On Unix-like systems
   .venv\Scripts\activate     # On Windows
   uv pip install -e .

   # Or using hatch
   hatch shell
   ```

2. **Start services using the CLI:**

   ```bash
   # Start all services in the background
   python -m dataflow.cli service start --all -d

   # Start specific services
   python -m dataflow.cli service start api dagster

   # Check status of services
   python -m dataflow.cli service status

   # View logs for a service
   python -m dataflow.cli service logs dagster
   ```

See the [CLI Usage Documentation](cli_usage.md) for more details on using the CLI.

### Option 3: Using Dev Containers in VS Code

Dev Containers provide a consistent development environment with all necessary tools and dependencies pre-installed.

1. **Clone the repository:**

   ```bash
   git clone <repo-url> && cd dataflow
   ```

2. **Open the project in VS Code:**

   ```bash
   code .
   ```

3. **Start the Dev Container:**

   - Click on the green button in the bottom-left corner of VS Code
   - Select "Reopen in Container"
   - VS Code will build and start the Dev Container (this may take a few minutes the first time)

4. **Working in the Dev Container:**

   - All necessary extensions are pre-installed
   - Python 3.11 with uv is available
   - Docker CLI is available inside the container
   - The project is mounted at `/workspace`

5. **Start the services:**
   Inside the Dev Container terminal:

   ```bash
   docker-compose up -d
   ```

6. **Access the services:**
   The necessary ports are forwarded to your local machine, so you can access the services at the same URLs as in Option 1.

## Working With Dataflow

### Running the CLI

```bash
# Using Docker
docker-compose run --rm cli <command>

# In Dev Container or local environment
python -m dataflow.cli <command>
```

### Working with the API

The API is built with FastAPI and provides RESTful endpoints for accessing data and metadata.

```bash
# Start the API server
docker-compose up api

# Access the API docs
open http://localhost:8000/docs
```

### Working with Dagster

Dagster is used for workflow orchestration and scheduling.

```bash
# Start the Dagster UI
docker-compose up dagster

# Access the Dagster UI
open http://localhost:3000
```

### Working with Evidence

Evidence is used for data visualization and dashboards. In the Dataflow project structure, each workflow has its own Evidence dashboard in the workflow-specific directory.

```bash
# Start Evidence
docker-compose up evidence

# Access Evidence dashboards
open http://localhost:9002
```

The Evidence service uses the `evidencedev/devenv` Docker image with the source directory mounted to allow access to all workflow-specific Evidence dashboards.

#### Structure of Evidence Dashboards

Evidence dashboards are organized by workflow:

```
src/
  dataflow/
    workflows/
      <workflow_name>/
        evidence/  <-- Evidence dashboard files for this workflow
```

To initialize a new Evidence project for a specific workflow:

```bash
# Create a workflow directory structure if it doesn't exist
mkdir -p src/dataflow/workflows/my_workflow/evidence

# Initialize a new Evidence project for a workflow
docker run -v=$(pwd)/src/dataflow/workflows/my_workflow/evidence:/evidence-workspace -it --rm evidencedev/devenv:latest --init
```

After initialization, you can modify the Evidence dashboard files in the workflow's directory, and they'll be accessible through the Evidence service.

## Multi-Stage Docker Builds

The project uses a multi-stage Docker build to optimize image size and build times:

- `base`: Contains common dependencies and environment setup
- `dependencies`: Installs Python dependencies from pyproject.toml
- `development`: Includes dev dependencies for local development
- `api`: Configures the FastAPI server
- `dagster`: Configures the Dagster server
- `cli`: Sets up the CLI entrypoint

To build a specific stage:

```bash
docker build --target <stage-name> -t dataflow:<stage-name> .
```

## Best Practices

- Use the Dev Container for consistent development environments
- Run `docker-compose up -d` to start all services in the background
- Use `docker-compose logs -f <service-name>` to view logs
- Add new Python dependencies to pyproject.toml, not directly in Dockerfile
- Use `uv pip install -e .` for development installations
- Create a `.env` file for local configuration rather than modifying docker-compose.yml

## Troubleshooting

If you encounter issues while setting up or running DATAFLOW, please refer to our comprehensive [Troubleshooting Guide](troubleshooting.md). The guide covers common issues with:

- Docker Compose services
- Database connectivity
- MinIO (object storage)
- Python environment
- Dagster workflows
- Evidence dashboards
- CLI functionality
- Logging and monitoring

## Additional Documentation

- [Environment Variables](environment_variables.md) - List of all environment variables and how to configure them
- [CLI Usage](cli_usage.md) - Detailed guide to using the DATAFLOW CLI
- [Troubleshooting](troubleshooting.md) - Solutions to common issues
- [Workflow Authoring](workflows.md) - How to create and manage workflows

## Getting Help

For more detailed information on running and developing Dataflow, refer to:

- The full documentation in the `docs/` directory
- The PRD in the root of the repository
- The README.md file for quick reference

If you encounter any issues not covered in the documentation, please reach out to the team via [contact information].
