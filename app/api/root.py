from fastapi import APIRouter

router = APIRouter()


@router.get("/", tags=["Root"])
def root():
    return {
        "status": "running",
        "message": "Enterprise Knowledge Copilot API",
        "version": "1.0.0",
    }