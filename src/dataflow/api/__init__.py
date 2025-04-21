from fastapi import FastAPI
from pydantic import BaseModel

# Create FastAPI application
app = FastAPI(
    title="Dataflow API",
    description="API for the Dataflow data warehouse platform",
    version="0.1.0",
)


class HealthResponse(BaseModel):
    status: str
    version: str


@app.get("/", response_model=HealthResponse)
async def health_check():
    """Health check endpoint."""
    return HealthResponse(status="ok", version="0.1.0")


def main():
    """Run the API server using uvicorn."""
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)


if __name__ == "__main__":
    main()
