# DATAFLOW Troubleshooting Guide

This guide addresses common issues you might encounter when working with DATAFLOW and provides solutions to help you resolve them quickly.

## Docker Compose Issues

### Services Won't Start

**Problem**: One or more services fail to start when running `docker-compose up`.

**Solutions**:

1. **Check for port conflicts**:

   - If a service fails because the port is already in use, you can change the port mapping in `docker-compose.yml`
   - Example: Change `"8000:8000"` to `"8001:8000"` to use port 8001 on your host machine

2. **Verify Docker is running**:

   ```bash
   docker info
   ```

3. **Check for conflicting container names**:

   ```bash
   docker ps -a
   ```

   Remove conflicting containers if necessary:

   ```bash
   docker rm <container_name>
   ```

4. **Inspect service logs for specific errors**:

   ```bash
   docker-compose logs <service_name>
   ```

5. **Try rebuilding the images**:
   ```bash
   docker-compose build --no-cache
   docker-compose up
   ```

## Database Connectivity Issues

**Problem**: Services can't connect to the database.

**Solutions**:

1. **Check if the database service is running**:

   ```bash
   docker-compose ps db
   ```

2. **Verify database credentials in environment variables** match what's in `docker-compose.yml` or `.env` file.

3. **Try connecting to the database directly**:

   ```bash
   docker-compose exec db psql -U postgres -d dataflow
   ```

4. **Reset the database volume** if corruption is suspected:
   ```bash
   docker-compose down -v  # WARNING: This removes persistent data
   docker-compose up
   ```

## Minio (Object Storage) Issues

**Problem**: Can't access files stored in Minio, or services can't connect to Minio.

**Solutions**:

1. **Verify Minio is running**:

   ```bash
   docker-compose ps minio
   ```

2. **Check Minio credentials** in your environment variables match what's in `docker-compose.yml` or `.env` file.

3. **Access Minio console** to verify bucket creation and permissions:

   - Open http://localhost:9001
   - Login with credentials (default: minioadmin/minioadmin)

4. **Reset Minio volume** if necessary:
   ```bash
   docker-compose down -v  # WARNING: This removes persistent data
   docker-compose up
   ```

## Python Environment Issues

**Problem**: Python dependencies or virtual environment issues.

**Solutions**:

1. **Verify your Python environment is activated**:

   ```bash
   # For uv
   uv venv
   source .venv/bin/activate  # On Unix-like systems
   .venv\Scripts\activate     # On Windows

   # For hatch
   hatch shell
   ```

2. **Reinstall dependencies**:

   ```bash
   # Using uv
   uv pip install --upgrade -e .

   # Using pip
   pip install --upgrade -e .
   ```

3. **Check for dependency conflicts**:

   ```bash
   pip check
   ```

4. **Regenerate lock file** if using uv:
   ```bash
   uv pip compile pyproject.toml -o requirements.txt
   uv pip sync requirements.txt
   ```

## Dagster Issues

**Problem**: Dagster UI is not showing workflows or fails to start.

**Solutions**:

1. **Check Dagster logs**:

   ```bash
   docker-compose logs dagster
   ```

2. **Verify the workspace.yaml file** is correctly configured.

3. **Ensure workflows are properly registered** in the Dagster repository.

4. **Restart Dagster service**:
   ```bash
   docker-compose restart dagster
   ```

## Evidence Dashboard Issues

**Problem**: Evidence dashboards are not showing or data is not appearing.

**Solutions**:

1. **Check Evidence logs**:

   ```bash
   docker-compose logs evidence
   ```

2. **Verify database connection** in Evidence configuration.

3. **Check SQL queries** in Evidence markdown files for syntax errors.

4. **Restart Evidence service**:
   ```bash
   docker-compose restart evidence
   ```

## CLI Issues

**Problem**: The DATAFLOW CLI is not working correctly.

**Solutions**:

1. **Verify the CLI package is installed**:

   ```bash
   python -m dataflow.cli --help
   ```

2. **Check Python path** to ensure the DATAFLOW package is in your Python path:

   ```bash
   python -c "import sys; print(sys.path)"
   ```

3. **Check log file** for CLI errors:

   ```bash
   cat logs/cli.log
   ```

4. **Reinstall the package in development mode**:
   ```bash
   pip install -e .
   ```

## Logging and Monitoring Issues

**Problem**: Logs are not appearing in Grafana/Loki, or monitoring is not working.

**Solutions**:

1. **Verify Grafana, Loki, and Promtail are running**:

   ```bash
   docker-compose ps grafana loki promtail
   ```

2. **Check Promtail logs** for scraping errors:

   ```bash
   docker-compose logs promtail
   ```

3. **Verify Loki data source** is correctly configured in Grafana.

4. **Check log format** in services to ensure they're compatible with what Promtail expects.

## Getting More Help

If you continue to experience issues not covered in this guide:

1. Check the [GitHub Issues](https://github.com/iamgp/dataflow/issues) for similar problems
2. Review the documentation in the `docs/` directory
3. Contact the project maintainers via [contact information]
