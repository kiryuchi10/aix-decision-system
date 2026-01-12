from fastapi import APIRouter

router = APIRouter()

@router.get("/health")
def kpi_health():
    return {"status": "kpi router ready"}
