# DATAFLOW Command Line Interface (CLI) Usage

This document describes how to use the DATAFLOW Command Line Interface (CLI) to manage workflows, services, and other aspects of the platform.

## Installation & Setup

Assuming you have followed the project setup instructions (see `README.md`), the CLI is installed as part of the project dependencies.

You can typically invoke the CLI using the `dataflow` command if the project's virtual environment is active or if the package is installed globally.

Alternatively, you can run it directly using:

```bash
python -m dataflow.cli [COMMANDS]
```

or via Hatch (if using it):

```bash
hatch run dataflow [COMMANDS]
```

## Getting Help

To see the list of available commands and top-level options, use:

```bash
dataflow --help
```

To get help for a specific command group (e.g., `workflow`), use:

```bash
dataflow workflow --help
```

To get help for a specific command within a group (e.g., `list` within `workflow`), use:

```bash
dataflow workflow list --help
```

## Command Groups

The CLI is organized into logical command groups.

### `workflow`

Commands for managing data workflows.

- **`list`**: Lists all available and registered workflows.

  ```bash
  dataflow workflow list

  # Example output:
  # ID              | Name             | Description                           | Status
  # ---------------|------------------|---------------------------------------|--------
  # example_workflow | Example Workflow | An example workflow for demonstration | active
  ```

- **`run`**: Trigger a specific workflow run.

  ```bash
  # Run workflow with default parameters
  dataflow workflow run example_workflow

  # Run workflow with specific parameters
  dataflow workflow run example_workflow --param date=2023-07-01

  # Run workflow with parameters from a JSON file
  dataflow workflow run example_workflow --param-file params.json
  ```

- **`status`**: Check the status of workflow runs.

  ```bash
  # Check status of all runs for a workflow
  dataflow workflow status example_workflow

  # Check status of a specific run
  dataflow workflow status example_workflow --run-id run_12345

  # Example output:
  # Run ID   | Workflow        | Status   | Start Time          | End Time
  # ---------|----------------|----------|---------------------|-------------------
  # run_12345 | example_workflow | success  | 2023-07-01 12:00:00 | 2023-07-01 12:05:30
  ```

- **`logs`**: View logs for a specific workflow run.

  ```bash
  # View logs for the latest run of a workflow
  dataflow workflow logs example_workflow

  # View logs for a specific run
  dataflow workflow logs example_workflow --run-id run_12345

  # Follow logs in real-time for an active run
  dataflow workflow logs example_workflow --follow
  ```

- **`init`**: Initialize a new workflow from a template.

  ```bash
  # Create a new workflow with default template
  dataflow workflow init my_new_workflow

  # Create a new workflow with a specific template
  dataflow workflow init my_new_workflow --template api_ingestion

  # This will create:
  # - src/dataflow/workflows/my_new_workflow/
  # - All necessary files based on the template
  ```

### `service`

Commands for managing the Docker Compose services (Database, Minio, Dagster, API, etc.).

- **`start`**: Starts specified services or all services.

  ```bash
  # Start all services in the background
  dataflow service start --all -d

  # Start specific services (e.g., api and dagster) in the foreground
  dataflow service start api dagster
  ```

  Options:

  - `--all`: Start all services
  - `-d, --detach`: Run in detached (background) mode

- **`stop`**: Stops specified services or all services.

  ```bash
  # Stop all services
  dataflow service stop --all

  # Stop a specific service
  dataflow service stop minio
  ```

  Options:

  - `--all`: Stop all services

- **`restart`**: Restarts specified services or all services.

  ```bash
  # Restart all services
  dataflow service restart --all

  # Restart a specific service
  dataflow service restart dagster
  ```

  Options:

  - `--all`: Restart all services

- **`status`**: Shows the status of running Docker Compose services.

  ```bash
  dataflow service status

  # Example output:
  # Service  | Status   | Ports
  # ---------|----------|----------------------------------------
  # api      | Running  | 0.0.0.0:8000->8000/tcp
  # dagster  | Running  | 0.0.0.0:3000->3000/tcp
  # duckdb   | Running  |
  # minio    | Running  | 0.0.0.0:9001->9001/tcp, 9000/tcp
  # evidence | Running  | 0.0.0.0:9000->3000/tcp
  # grafana  | Running  | 0.0.0.0:3001->3000/tcp
  # loki     | Running  | 0.0.0.0:3100->3100/tcp
  ```

- **`logs`**: View logs for specified services.

  ```bash
  # View logs for a specific service
  dataflow service logs api

  # Follow logs for multiple services
  dataflow service logs -f api dagster

  # View last 50 lines of logs for all services
  dataflow service logs --all -t 50
  ```

  Options:

  - `--all`: Show logs for all services
  - `-f, --follow`: Follow log output (real-time)
  - `-t, --tail <n>`: Show last n lines (default: 100)

### `db`

Commands for managing the database.

- **`init`**: Initialize the database schema.

  ```bash
  dataflow db init
  ```

- **`migrate`**: Apply database migrations.

  ```bash
  dataflow db migrate
  ```

- **`backup`**: Create a backup of the database.

  ```bash
  dataflow db backup --output ~/backups/dataflow_$(date +%Y%m%d).sql
  ```

- **`restore`**: Restore the database from a backup.
  ```bash
  dataflow db restore --input ~/backups/dataflow_20230701.sql
  ```

### `dbt`

Commands for running dbt operations.

- **`run`**: Run dbt models.

  ```bash
  # Run all dbt models
  dataflow dbt run

  # Run models for a specific workflow
  dataflow dbt run --workflow example_workflow

  # Run specific models
  dataflow dbt run --select model_name
  ```

- **`test`**: Run dbt tests.

  ```bash
  # Run all dbt tests
  dataflow dbt test

  # Run tests for specific models
  dataflow dbt test --select model_name
  ```

- **`generate`**: Generate dbt artifacts.

  ```bash
  # Generate dbt documentation
  dataflow dbt generate docs

  # Generate sources
  dataflow dbt generate sources
  ```

### `dev`

Commands for developers.

- **`lint`**: Run code linting.

  ```bash
  dataflow dev lint
  ```

- **`test`**: Run tests.

  ```bash
  # Run all tests
  dataflow dev test

  # Run specific test types
  dataflow dev test --type unit

  # Run tests with coverage
  dataflow dev test --coverage
  ```

- **`docs`**: Build and serve documentation.

  ```bash
  # Build docs
  dataflow dev docs build

  # Serve docs
  dataflow dev docs serve
  ```

## Global CLI Options

These options can be used with any command:

- `--log-level`: Set logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
- `--log-json`: Output logs in JSON format (default: true)
- `--log-file`: Path to log file (default: logs/cli.log)

Example:

```bash
dataflow --log-level DEBUG service start --all
```

## Examples

Here are some common usage examples:

### Starting the Platform for Development

```bash
# Start all services in background mode
dataflow service start --all -d

# Check status of services
dataflow service status

# View logs for specific services
dataflow service logs -f api dagster
```

### Stopping/Restarting Services

```bash
# Restart a specific service (e.g., after code changes)
dataflow service restart api

# Stop all services when finished
dataflow service stop --all
```

### Running a Complete Workflow

```bash
# List available workflows
dataflow workflow list

# Start all required services
dataflow service start --all -d

# Run a specific workflow
dataflow workflow run example_workflow

# Check status of the workflow
dataflow workflow status example_workflow

# View logs of the workflow run
dataflow workflow logs example_workflow
```

### Creating and Testing a New Workflow

```bash
# Create a new workflow from template
dataflow workflow init my_new_workflow

# Edit the files in src/dataflow/workflows/my_new_workflow/

# Run tests for the new workflow
dataflow dev test --select workflows/my_new_workflow

# Run the workflow
dataflow workflow run my_new_workflow
```

### Working with dbt Models

```bash
# Run dbt models for a specific workflow
dataflow dbt run --workflow my_workflow

# Test dbt models
dataflow dbt test --workflow my_workflow

# Generate dbt documentation
dataflow dbt generate docs

# View dbt documentation
dataflow dev docs serve --dbt
```

## Extending the CLI

The CLI is built using Click and is designed to be extensible. New command groups and commands can be added by:

1. Creating a new Python module in `src/dataflow/cli/commands/`
2. Implementing commands using Click decorators
3. Registering the command group in `src/dataflow/cli/main.py`

Example of a new command group:

```python
import click

@click.group("new_command_group")
def new_command_group():
    """Description of the new command group."""
    pass

@new_command_group.command("new_command")
@click.argument("argument")
def new_command(argument):
    """Description of the new command."""
    # Command implementation
    pass
```

Then register it in `main.py`:

```python
from dataflow.cli.commands import new_command_group

# Add command groups
cli.add_command(new_command_group.new_command_group)
```

## Command Cheat Sheet

| Task                  | Command                                  |
| --------------------- | ---------------------------------------- |
| Start all services    | `dataflow service start --all -d`        |
| Stop all services     | `dataflow service stop --all`            |
| View service status   | `dataflow service status`                |
| List workflows        | `dataflow workflow list`                 |
| Run a workflow        | `dataflow workflow run <workflow_id>`    |
| Check workflow status | `dataflow workflow status <workflow_id>` |
| View workflow logs    | `dataflow workflow logs <workflow_id>`   |
| Create a new workflow | `dataflow workflow init <workflow_id>`   |
| Run tests             | `dataflow dev test`                      |
| Build documentation   | `dataflow dev docs build`                |
| Run dbt models        | `dataflow dbt run`                       |

---

_(This document will be updated as more CLI commands and features are added.)_
