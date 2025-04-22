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


# Helper to validate service names
def validate_services(service_names, all_flag, action_desc):
    """
    Validate service names and handle the --all flag.

    Args:
        service_names: Tuple of service names provided by the user
        all_flag: Boolean indicating if --all flag was used
        action_desc: Description of the action (for logging)

    Returns:
        tuple: (list of target services, boolean indicating validity)
    """
    target_services = []
    if all_flag:
        log.info(f"Will {action_desc} all services...")
        return target_services, True
    elif service_names:
        target_services = list(service_names)
        log.info(f"Will {action_desc} services: {', '.join(target_services)}...")
        return target_services, True
    else:
        click.echo("Error: No services specified. Use service names or --all.")
        log.error(f"No services specified for '{action_desc}' action.")
        return [], False


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

    target_services, valid = validate_services(service_names, all, "start")
    if not valid:
        return

    if not all and target_services:
        args.extend(target_services)

    run_docker_compose(args)


@service_group.command("stop")
@click.argument("service_names", nargs=-1)
@click.option("--all", is_flag=True, help="Stop all services.")
def stop_services(service_names, all):
    """Stop specified services or all services."""
    args = ["stop"]

    target_services, valid = validate_services(service_names, all, "stop")
    if not valid:
        return

    if not all and target_services:
        args.extend(target_services)

    run_docker_compose(args)


@service_group.command("status")
def service_status():
    """Show the status of running services."""
    log.info("Checking service status...")
    run_docker_compose(["ps"])


@service_group.command("restart")
@click.argument("service_names", nargs=-1)
@click.option("--all", is_flag=True, help="Restart all services.")
def restart_services(service_names, all):
    """Restart specified services or all services."""
    args = ["restart"]

    target_services, valid = validate_services(service_names, all, "restart")
    if not valid:
        return

    if not all and target_services:
        args.extend(target_services)

    run_docker_compose(args)


@service_group.command("logs")
@click.argument("service_names", nargs=-1)
@click.option("--all", is_flag=True, help="Show logs for all services.")
@click.option("-f", "--follow", is_flag=True, help="Follow log output.")
@click.option(
    "-t", "--tail", default="100", help="Number of lines to show from the end of the logs."
)
def service_logs(service_names, all, follow, tail):
    """View logs for specified services."""
    args = ["logs"]

    if follow:
        args.append("--follow")

    args.extend(["--tail", tail])

    target_services, valid = validate_services(service_names, all, "view logs for")
    if not valid:
        return

    if not all and target_services:
        args.extend(target_services)

    run_docker_compose(args)
