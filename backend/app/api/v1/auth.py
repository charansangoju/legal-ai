from fastapi import APIRouter
router=APIRouter(prefix="/auth",tags=["auth"])
@router.get("/status")
def status(): return {"status":"auth_adapter_ready"}
