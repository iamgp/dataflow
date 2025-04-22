from fastapi import APIRouter
from pydantic import BaseModel


class HealthResponse(BaseModel):
    status: str
    version: str = "0.1.0"


router = APIRouter(
    prefix="/health",
    tags=["Health"],
)


from dataflow.api import health_check as base_health_check


@router.get("/", response_model=HealthResponse)
def health_check():
    """Check the health of the API."""
    # In the future, this could check database connections, etc.
    return base_health_check()
