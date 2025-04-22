import os
import subprocess

import click

from dataflow.shared.logging import get_logger

logger = get_logger(__name__)


@click.group("docs")
def docs_group():
    """Documentation commands."""
    pass


@docs_group.command("build")
@click.option("--clean", is_flag=True, help="Clean the site directory before building")
def build(clean):
    """Build the documentation."""
    logger.info("Building documentation")

    cmd = ["mkdocs", "build"]
    if clean:
        cmd.append("--clean")

    try:
        subprocess.run(cmd, check=True)
        logger.info("Documentation built successfully")
    except subprocess.CalledProcessError as e:
        logger.error(f"Failed to build documentation: {e}")
        raise click.ClickException(f"Documentation build failed: {e}")


@docs_group.command("serve")
@click.option("--dev-addr", default="127.0.0.1:8000", help="Development server address")
@click.option("--livereload", is_flag=True, default=True, help="Enable live reloading")
@click.option("--dbt", is_flag=True, help="Serve DBT documentation")
@click.option("-d", "--background", is_flag=True, help="Run in background (detached) mode")
def serve(dev_addr, livereload, dbt, background):
    """Serve the documentation for local viewing."""
    if dbt:
        logger.info("Serving DBT documentation")
        # Assuming DBT docs are in the target directory
        dbt_docs_path = "target/index.html"
        if not os.path.exists(dbt_docs_path):
            logger.error("DBT documentation not found. Run 'dataflow dbt docs generate' first.")
            raise click.ClickException("DBT documentation not found")

        # Use Python's built-in HTTP server to serve DBT docs
        cmd = ["python", "-m", "http.server", "-d", "target", dev_addr.split(":")[1]]

        if background:
            # For background mode, redirect output to /dev/null
            cmd = ["nohup"] + cmd + ["&"]
            logger.info(f"Starting DBT documentation server in background at http://{dev_addr}")
            process = subprocess.Popen(
                " ".join(cmd), shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
            )
            click.echo(f"DBT documentation server started in background at http://{dev_addr}")
            return
        else:
            try:
                logger.info(f"Serving DBT documentation at http://{dev_addr}")
                subprocess.run(cmd)
            except subprocess.CalledProcessError as e:
                logger.error(f"Failed to serve DBT documentation: {e}")
                raise click.ClickException(f"Failed to serve DBT documentation: {e}")
    else:
        logger.info("Serving MkDocs documentation")
        cmd = ["mkdocs", "serve"]

        if dev_addr:
            cmd.extend(["--dev-addr", dev_addr])

        if not livereload:
            cmd.append("--no-livereload")

        if background:
            # For background mode, redirect output to /dev/null
            cmd = ["nohup"] + cmd + ["&"]
            logger.info(f"Starting documentation server in background at http://{dev_addr}")
            process = subprocess.Popen(
                " ".join(cmd), shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
            )
            click.echo(f"Documentation server started in background at http://{dev_addr}")
            return
        else:
            try:
                logger.info(f"Serving documentation at http://{dev_addr}")
                subprocess.run(cmd)
            except subprocess.CalledProcessError as e:
                logger.error(f"Failed to serve documentation: {e}")
                raise click.ClickException(f"Documentation server failed: {e}")


@docs_group.command("new")
@click.argument("title")
@click.option("--filename", help="Filename to use (defaults to title with lowercase and hyphens)")
@click.option("--template", help="Template file to use")
def new(title, filename, template):
    """Create a new documentation page with the given title."""
    if not filename:
        # Convert title to filename: "My Page" -> "my-page.md"
        filename = title.lower().replace(" ", "-").replace("/", "-")
        if not filename.endswith(".md"):
            filename += ".md"

    docs_dir = "docs"
    filepath = os.path.join(docs_dir, filename)

    if os.path.exists(filepath):
        logger.warning(f"File already exists: {filepath}")
        if not click.confirm(f"File {filepath} already exists. Overwrite?"):
            return

    logger.info(f"Creating new documentation page: {filepath}")

    if template and os.path.exists(template):
        with open(template) as f:
            content = f.read()
        # Replace template placeholders
        content = content.replace("{{title}}", title)
    else:
        # Create a basic markdown file with the title
        content = f"# {title}\n\nWrite your documentation here.\n"

    with open(filepath, "w") as f:
        f.write(content)

    logger.info(f"Created documentation page: {filepath}")
    click.echo(f"Created documentation page: {filepath}")
