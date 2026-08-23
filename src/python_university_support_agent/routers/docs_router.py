from fastapi import APIRouter

router = APIRouter(prefix="/docs", tags=["Docs"])

@router.get("/")
def get_docs():
    return "Docs Page"