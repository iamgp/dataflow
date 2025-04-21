from fastapi import APIRouter

router = APIRouter(
    prefix="/data",
    tags=["Data"],
)


# TODO: Add endpoints for querying/exporting data
@router.get("/")
def query_data():
    return {"message": "Data query endpoint placeholder"}
