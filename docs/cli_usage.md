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

- **`stop`**: Stops specified services or all services.

  ```bash
  # Stop all services
  dataflow service stop --all

  # Stop a specific service
  dataflow service stop minio
  ```

- **`status`**: Shows the status of running Docker Compose services.
  ```bash
  dataflow service status
  ```
- **(TODO)** `logs`: Tail logs for specific services.
- **(TODO)** `restart`: Restart services.

_(More details will be added as commands are implemented)_

---

_(This document will be updated as more CLI commands and features are added.)_
