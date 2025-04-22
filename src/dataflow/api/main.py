import time
import uuid
from contextvars import ContextVar

import structlog
from fastapi import FastAPI, Request

from dataflow.api.routers import configs, data, health, logs, workflows
from dataflow.shared.logging import log, setup_logging

# Call setup_logging early, before defining the app or routes
setup_logging()

# Context variable for request ID (optional but good practice)
request_id_var: ContextVar[str | None] = ContextVar("request_id", default=None)

app = FastAPI(
    title="DATAFLOW API",
    description="API for managing DATAFLOW workflows, data, and operations.",
    version="0.1.0",
)


# --- Middleware for Logging --- #
@app.middleware("http")
async def log_requests(request: Request, call_next):
    request_id = str(uuid.uuid4())
    request_id_var.set(request_id)

    client_host = request.client.host if request.client else "unknown"
    client_port = request.client.port if request.client else "unknown"

    # Bind essential request info
    structlog.contextvars.bind_contextvars(
        request_id=request_id,
        path=request.url.path,
        method=request.method,
        client_host=client_host,
        client_port=client_port,
    )

    log.info("Request started")
    start_time = time.time()

    response = await call_next(request)

    process_time = (time.time() - start_time) * 1000
    formatted_process_time = f"{process_time:.2f}"

    log.info(
        "Request finished",
        status_code=response.status_code,
        process_time_ms=formatted_process_time,
    )

    structlog.contextvars.clear_contextvars()
    request_id_var.set(None)
    return response


# --- End Middleware --- #


# Include routers
app.include_router(health.router)
app.include_router(workflows.router)
app.include_router(configs.router)
app.include_router(data.router)
app.include_router(logs.router)


# Root endpoint (optional)
@app.get("/")
def read_root():
    log.debug("Accessed root endpoint")  # Example endpoint log
    return {"message": "Welcome to the DATAFLOW API"}
