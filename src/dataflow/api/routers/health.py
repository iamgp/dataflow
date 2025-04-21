from fastapi import APIRouter

router = APIRouter(
    prefix="/health",
    tags=["Health"],
)


@router.get("/")
def health_check():
    """Check the health of the API."""
    # In the future, this could check database connections, etc.
    return {"status": "ok"}
