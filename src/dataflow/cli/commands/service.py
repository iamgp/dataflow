import subprocess  # Needed for docker-compose calls

import click

from dataflow.shared.logging import log


# Helper to run docker-compose commands
def run_docker_compose(args: list[str]):
    command = ["docker-compose"] + args
    log.debug(f"Running command: {' '.join(command)}")
    try:
        # Use run instead of call to capture output/errors if needed later
        result = subprocess.run(command, check=True, capture_output=True, text=True)
        log.info(f"Command succeeded: {' '.join(command)}")
        if result.stdout:
            click.echo(result.stdout)
        if result.stderr:
            # Log stderr even on success, as compose sometimes outputs info there
            log.debug(f"Command stderr: {result.stderr.strip()}")
        return True
    except FileNotFoundError:
        log.error(
            "Error: 'docker-compose' command not found. Is Docker Compose installed and in PATH?"
        )
        return False
    except subprocess.CalledProcessError as e:
        log.error(f"Command failed: {' '.join(command)}")
        log.error(f"Return code: {e.returncode}")
        if e.stdout:
            click.echo(f"stdout:\n{e.stdout}")
        if e.stderr:
            click.echo(f"stderr:\n{e.stderr}")
        return False
    except Exception as e:
        log.error(f"An unexpected error occurred: {e}")
        return False


@click.group("service")
def service_group():
    """Manage DATAFLOW services (via Docker Compose)."""
    log.debug("Service command group invoked.")
    pass


@service_group.command("start")
@click.argument("service_names", nargs=-1)  # 0 or more service names
@click.option("--all", is_flag=True, help="Start all services.")
@click.option("-d", "--detach", is_flag=True, help="Run in detached mode.")
def start_services(service_names, all, detach):
    """Start specified services or all services."""
    args = ["up"]
    if detach:
        args.append("-d")

    target_services = []
    if all:
        target_services = ["all"]
        log.info("Starting all services...")
    elif service_names:
        target_services = list(service_names)
        args.extend(target_services)
        log.info(f"Starting services: {', '.join(target_services)}...")
    else:
        click.echo("Error: No services specified. Use service names or --all.")
        log.error("No services specified for 'start' command.")
        return

    run_docker_compose(args)


@service_group.command("stop")
@click.argument("service_names", nargs=-1)
@click.option("--all", is_flag=True, help="Stop all services.")
def stop_services(service_names, all):
    """Stop specified services or all services."""
    args = ["stop"]
    target_services = []
    if all:
        target_services = ["all"]
        log.info("Stopping all services...")
        # No need to add service names if stopping all
    elif service_names:
        target_services = list(service_names)
        args.extend(target_services)
        log.info(f"Stopping services: {', '.join(target_services)}...")
    else:
        click.echo("Error: No services specified. Use service names or --all.")
        log.error("No services specified for 'stop' command.")
        return

    run_docker_compose(args)


@service_group.command("status")
def service_status():
    """Show the status of running services."""
    log.info("Checking service status...")
    run_docker_compose(["ps"])


# TODO: Add commands for logs, restart, etc.
