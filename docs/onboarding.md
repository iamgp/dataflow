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

2. **Start all services:**

   ```bash
   docker-compose up -d
   ```

   This will start the following services:

   - FastAPI (API server) on port 8000
   - Dagster UI on port 3000
   - Evidence dashboards on port 9000
   - Grafana on port 3001
   - MinIO (object storage) on port 9000 (API) and 9001 (console)
   - PostgreSQL on port 5432
   - Loki, Promtail, and Prometheus for logging and monitoring

3. **Access the services:**

   - FastAPI docs: http://localhost:8000/docs
   - Dagster UI: http://localhost:3000
   - Evidence dashboards: http://localhost:9000
   - Grafana: http://localhost:3001
   - MinIO Console: http://localhost:9001

4. **Stop the services:**

   ```bash
   docker-compose down
   ```

5. **View logs for a specific service:**
   ```bash
   docker-compose logs -f <service-name>
   ```
   Replace `<service-name>` with one of: api, dagster, db, minio, evidence, grafana, loki, promtail, prometheus

### Option 2: Using Dev Containers in VS Code

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
open http://localhost:9000
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

## Troubleshooting

### Common Issues

1. **Port conflicts**

   - If a service fails to start due to a port conflict, you can change the port mapping in docker-compose.yml
   - Example: Change `"8000:8000"` to `"8001:8000"` to use port 8001 on your host machine

2. **Docker volume permissions**

   - If you encounter permission issues with Docker volumes, you may need to adjust the permissions or user/group IDs

3. **Python dependency issues**
   - Use `uv pip install --upgrade -e .` to reinstall dependencies
   - Check for conflicts in pyproject.toml

### Getting Help

For more detailed information on running and developing Dataflow, refer to:

- The full documentation in the `docs/` directory
- The PRD in the root of the repository
- The README.md file for quick reference

If you encounter any issues not covered here, please reach out to the team via [contact information].
