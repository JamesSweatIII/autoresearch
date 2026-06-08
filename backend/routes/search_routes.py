from fastapi import APIRouter
from services.web_search_service import list_backends, get_active_backend, set_active_backend

router = APIRouter(prefix="/api/search", tags=["search"])


@router.get("/backends")
def get_backends():
    return {"active": get_active_backend(), "backends": list_backends()}


@router.post("/backends/{name}")
def switch_backend(name: str):
    set_active_backend(name)
    return {"active": get_active_backend(), "backends": list_backends()}
