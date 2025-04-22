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
  ```
- **(TODO)** `run`: Trigger a specific workflow run.
- **(TODO)** `status`: Check the status of workflow runs.

_(More details will be added as commands are implemented)_

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

### Managing Workflows (when implemented)

```bash
# List available workflows
dataflow workflow list

# Run a specific workflow
dataflow workflow run <workflow_name>

# Check status of workflow runs
dataflow workflow status <workflow_name>
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

---

_(This document will be updated as more CLI commands and features are added.)_
