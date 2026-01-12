from fastapi import APIRouter

router = APIRouter()

@router.get("/health")
def workflow_health():
    return {"status": "workflow router ready"}
