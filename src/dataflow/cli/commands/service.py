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


# List of services that are not part of docker-compose but can be managed by the CLI
NON_DOCKER_SERVICES = ["docs"]


# Helper to run the mkdocs server
def run_mkdocs_server(background=False):
    """Start the MkDocs documentation server"""
    log.info("Starting documentation server...")
    cmd = ["mkdocs", "serve"]

    if background:
        cmd = ["nohup"] + cmd + ["&"]
        log.info("Starting documentation server in background at http://127.0.0.1:8000")
        try:
            process = subprocess.Popen(
                " ".join(cmd), shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
            )
            click.echo("Documentation server started in background at http://127.0.0.1:8000")
        except Exception as e:
            log.error(f"Failed to start documentation server: {e}")
            click.echo(f"Error starting documentation server: {e}")
    else:
        log.info("Starting documentation server at http://127.0.0.1:8000")
        try:
            subprocess.run(cmd)
        except subprocess.CalledProcessError as e:
            log.error(f"Failed to start documentation server: {e}")
            click.echo(f"Error starting documentation server: {e}")
        except KeyboardInterrupt:
            log.info("Documentation server stopped by user")
            click.echo("Documentation server stopped by user")


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
    target_services, valid = validate_services(service_names, all, "start")
    if not valid:
        return

    # Filter out non-docker services
    docker_services = [svc for svc in target_services if svc not in NON_DOCKER_SERVICES]
    non_docker_services = [svc for svc in target_services if svc in NON_DOCKER_SERVICES]

    # Start Docker Compose services if any
    if all or docker_services:
        args = ["up"]
        if detach:
            args.append("-d")

        if not all and docker_services:
            args.extend(docker_services)

        run_docker_compose(args)

    # Start documentation server if requested
    if all or "docs" in non_docker_services:
        # Always run docs in background mode if detach is True or if other services are started
        background_mode = detach or all or (len(target_services) > 1)
        run_mkdocs_server(background=background_mode)


@service_group.command("stop")
@click.argument("service_names", nargs=-1)
@click.option("--all", is_flag=True, help="Stop all services.")
def stop_services(service_names, all):
    """Stop specified services or all services."""
    target_services, valid = validate_services(service_names, all, "stop")
    if not valid:
        return

    # Filter out non-docker services
    docker_services = [svc for svc in target_services if svc not in NON_DOCKER_SERVICES]
    non_docker_services = [svc for svc in target_services if svc in NON_DOCKER_SERVICES]

    # Stop Docker Compose services if any
    if all or docker_services:
        args = ["stop"]
        if not all and docker_services:
            args.extend(docker_services)
        run_docker_compose(args)

    # Stop documentation server if requested
    if all or "docs" in non_docker_services:
        log.info("Stopping documentation server...")
        click.echo("Stopping documentation server...")
        # Find and stop the documentation server process
        try:
            # On Unix-like systems, find and kill the mkdocs process
            subprocess.run(["pkill", "-f", "mkdocs serve"], check=False)
            click.echo("Documentation server stopped.")
        except Exception as e:
            log.error(f"Failed to stop documentation server: {e}")
            click.echo(f"Error stopping documentation server: {e}")


@service_group.command("status")
def service_status():
    """Show the status of running services."""
    log.info("Checking service status...")
    run_docker_compose(["ps"])

    # Check documentation server status
    try:
        # On Unix-like systems, check if mkdocs is running
        result = subprocess.run(
            ["pgrep", "-f", "mkdocs serve"], capture_output=True, text=True, check=False
        )
        if result.returncode == 0:
            click.echo("Documentation server: Running (http://127.0.0.1:8000)")
        else:
            click.echo("Documentation server: Stopped")
    except Exception as e:
        log.error(f"Failed to check documentation server status: {e}")


@service_group.command("restart")
@click.argument("service_names", nargs=-1)
@click.option("--all", is_flag=True, help="Restart all services.")
def restart_services(service_names, all):
    """Restart specified services or all services."""
    target_services, valid = validate_services(service_names, all, "restart")
    if not valid:
        return

    # Filter out non-docker services
    docker_services = [svc for svc in target_services if svc not in NON_DOCKER_SERVICES]
    non_docker_services = [svc for svc in target_services if svc in NON_DOCKER_SERVICES]

    # Restart Docker Compose services if any
    if all or docker_services:
        args = ["restart"]
        if not all and docker_services:
            args.extend(docker_services)
        run_docker_compose(args)

    # Restart documentation server if requested
    if all or "docs" in non_docker_services:
        log.info("Restarting documentation server...")
        click.echo("Restarting documentation server...")

        # Stop the documentation server if it's running
        try:
            subprocess.run(["pkill", "-f", "mkdocs serve"], check=False)
        except Exception:
            pass

        # Start the documentation server again
        run_mkdocs_server(background=True)


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

    # Filter out non-docker services
    docker_services = [svc for svc in target_services if svc not in NON_DOCKER_SERVICES]
    non_docker_services = [svc for svc in target_services if svc in NON_DOCKER_SERVICES]

    # Display warning for non-Docker services
    if non_docker_services:
        click.echo(
            f"Note: Logs for non-Docker services ({', '.join(non_docker_services)}) are not available through this command."
        )

    if all or docker_services:
        if not all and docker_services:
            args.extend(docker_services)
        run_docker_compose(args)
