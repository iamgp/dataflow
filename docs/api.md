# API Reference

DATAFLOW provides a RESTful API built with FastAPI for interacting with workflows, data, and system components.

## API Documentation

The interactive API documentation is available at:

- **Swagger UI**: [http://localhost:8000/docs](http://localhost:8000/docs)
- **ReDoc**: [http://localhost:8000/redoc](http://localhost:8000/redoc)

These interfaces provide detailed information about all endpoints, request/response schemas, and allow testing the API directly.

## Authentication

Currently, the API does not require authentication for local development. In production environments, authentication should be implemented based on your organization's requirements.

## Base URL

```
http://localhost:8000
```

## API Endpoints

### Workflows

| Method | Endpoint                                  | Description                           |
| ------ | ----------------------------------------- | ------------------------------------- |
| GET    | `/api/v1/workflows`                       | List all available workflows          |
| GET    | `/api/v1/workflows/{workflow_id}`         | Get details about a specific workflow |
| POST   | `/api/v1/workflows/{workflow_id}/run`     | Run a specific workflow               |
| GET    | `/api/v1/workflows/{workflow_id}/status`  | Get status of a workflow              |
| GET    | `/api/v1/workflows/{workflow_id}/history` | Get execution history of a workflow   |

### Health

| Method | Endpoint           | Description                            |
| ------ | ------------------ | -------------------------------------- |
| GET    | `/health`          | Check if the API is running            |
| GET    | `/health/services` | Check status of all dependent services |

### Logs

| Method | Endpoint                     | Description                       |
| ------ | ---------------------------- | --------------------------------- |
| GET    | `/api/v1/logs`               | Query logs with filtering options |
| GET    | `/api/v1/logs/{workflow_id}` | Get logs for a specific workflow  |

## Example Requests

### List Workflows

```bash
curl -X GET http://localhost:8000/api/v1/workflows
```

Response:

```json
{
  "workflows": [
    {
      "id": "example_workflow",
      "name": "Example Workflow",
      "description": "An example workflow for demonstration purposes",
      "status": "active"
    }
  ]
}
```

### Run a Workflow

```bash
curl -X POST http://localhost:8000/api/v1/workflows/example_workflow/run \
  -H "Content-Type: application/json" \
  -d '{"parameters": {"date": "2023-01-01"}}'
```

Response:

```json
{
  "run_id": "12345",
  "workflow_id": "example_workflow",
  "status": "started",
  "start_time": "2023-01-01T12:00:00"
}
```

## Error Handling

The API uses standard HTTP status codes to indicate success or failure:

- `200 OK`: The request was successful
- `400 Bad Request`: The request was invalid
- `404 Not Found`: The requested resource was not found
- `500 Internal Server Error`: An error occurred on the server

Error responses include a JSON body with details:

```json
{
  "detail": "Detailed error message",
  "status_code": 400,
  "error_type": "ValidationError"
}
```
