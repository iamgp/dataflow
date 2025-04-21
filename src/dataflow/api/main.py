from fastapi import FastAPI

from dataflow.api.routers import data, health, logs, workflows

app = FastAPI(
    title="DATAFLOW API",
    description="API for managing DATAFLOW workflows, data, and operations.",
    version="0.1.0",
)

# Include routers
app.include_router(health.router)
app.include_router(workflows.router)
app.include_router(data.router)
app.include_router(logs.router)


# Root endpoint (optional)
@app.get("/")
def read_root():
    return {"message": "Welcome to the DATAFLOW API"}
