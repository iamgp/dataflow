# DATAFLOW Environment Variables

This document describes the environment variables used in DATAFLOW and how to configure them. These variables control the behavior of the various services and components.

## Core Environment Variables

Below is a list of the core environment variables used across the DATAFLOW services. These are defined in the `docker-compose.yml` file and can be overridden by creating a `.env` file in the project root.

### Database Configuration

| Variable            | Description              | Default    |
| ------------------- | ------------------------ | ---------- |
| `POSTGRES_HOST`     | PostgreSQL host          | `db`       |
| `POSTGRES_PORT`     | PostgreSQL port          | `5432`     |
| `POSTGRES_USER`     | PostgreSQL username      | `postgres` |
| `POSTGRES_PASSWORD` | PostgreSQL password      | `postgres` |
| `POSTGRES_DB`       | PostgreSQL database name | `dataflow` |

### MinIO Configuration

| Variable           | Description      | Default      |
| ------------------ | ---------------- | ------------ |
| `MINIO_HOST`       | MinIO host       | `minio`      |
| `MINIO_PORT`       | MinIO port       | `9000`       |
| `MINIO_ACCESS_KEY` | MinIO access key | `minioadmin` |
| `MINIO_SECRET_KEY` | MinIO secret key | `minioadmin` |

### Dagster Configuration

| Variable       | Description            | Default                     |
| -------------- | ---------------------- | --------------------------- |
| `DAGSTER_HOME` | Dagster home directory | `/opt/dagster/dagster_home` |
| `DAGSTER_HOST` | Dagster host           | `dagster`                   |
| `DAGSTER_PORT` | Dagster port           | `3000`                      |

### API Configuration

| Variable           | Description                    | Default   |
| ------------------ | ------------------------------ | --------- |
| `API_HOST`         | API server host                | `0.0.0.0` |
| `API_PORT`         | API server port                | `8000`    |
| `API_ENABLE_CORS`  | Enable CORS for API            | `false`   |
| `API_REQUIRE_AUTH` | Require authentication for API | `false`   |

### Logging Configuration

| Variable          | Description                 | Default             |
| ----------------- | --------------------------- | ------------------- |
| `LOG_LEVEL`       | Logging level               | `INFO`              |
| `LOG_JSON_FORMAT` | Enable JSON format for logs | `true`              |
| `LOG_FILE`        | Log file path               | `logs/dataflow.log` |

### Evidence Configuration

| Variable                | Description               | Default                                         |
| ----------------------- | ------------------------- | ----------------------------------------------- |
| `EVIDENCE_PORT`         | Evidence dashboard port   | `9002`                                          |
| `EVIDENCE_DATABASE_URL` | Database URL for Evidence | `postgres://postgres:postgres@db:5432/dataflow` |

### Grafana Configuration

| Variable                 | Description            | Default |
| ------------------------ | ---------------------- | ------- |
| `GRAFANA_ADMIN_USER`     | Grafana admin username | `admin` |
| `GRAFANA_ADMIN_PASSWORD` | Grafana admin password | `admin` |

## Workflow-Specific Environment Variables

Each workflow may require its own set of environment variables. These should be defined in the workflow's documentation or configuration files. Here are some examples:

### Nightscout Workflow

| Variable             | Description        | Default         |
| -------------------- | ------------------ | --------------- |
| `NIGHTSCOUT_API_URL` | Nightscout API URL | None (Required) |
| `NIGHTSCOUT_API_KEY` | Nightscout API key | None (Required) |

## Creating a .env File

To override the default environment variables, create a `.env` file in the project root directory. For example:

```bash
# Database Configuration
POSTGRES_PASSWORD=securepassword

# MinIO Configuration
MINIO_ACCESS_KEY=secure_access_key
MINIO_SECRET_KEY=secure_secret_key

# Logging Configuration
LOG_LEVEL=DEBUG
```

This `.env` file will override the default values in `docker-compose.yml`.

## Environment Variables in Development vs. Production

For development, you can use the provided defaults or create a `.env` file with development-specific values. For production, you should create a separate `.env` file with production-specific values, including secure passwords and keys.

### Development Settings

| Variable        | Description                        | Default |
| --------------- | ---------------------------------- | ------- |
| `DEV_MODE`      | Enable development mode            | `true`  |
| `DEV_SKIP_AUTH` | Skip authentication in development | `true`  |

### Production Settings

In production, make sure to:

1. Set secure passwords for all services
2. Disable development settings
3. Enable authentication and CORS as needed
4. Consider using a secret management tool instead of a `.env` file

## Environment Variables in CI/CD

For CI/CD pipelines, you can use GitHub Secrets or similar mechanisms to securely pass environment variables to the build and deployment process.

In GitHub Actions workflows, you can use secrets like this:

```yaml
env:
  POSTGRES_PASSWORD: ${{ secrets.POSTGRES_PASSWORD }}
  MINIO_ACCESS_KEY: ${{ secrets.MINIO_ACCESS_KEY }}
  MINIO_SECRET_KEY: ${{ secrets.MINIO_SECRET_KEY }}
```

## Accessing Environment Variables in Code

Environment variables can be accessed in Python code using the `os.environ` dictionary:

```python
import os

db_host = os.environ.get("POSTGRES_HOST", "db")
db_port = int(os.environ.get("POSTGRES_PORT", "5432"))
```

Using `os.environ.get()` with a default value is recommended to prevent errors if the variable is not set.
