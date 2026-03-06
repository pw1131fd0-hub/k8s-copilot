from fastapi import APIRouter
from backend.controllers import pod_controller, diagnose_controller, yaml_controller

router = APIRouter()

router.include_router(pod_controller.router, prefix="/cluster", tags=["cluster"])
router.include_router(diagnose_controller.router, prefix="/diagnose", tags=["diagnose"])
router.include_router(yaml_controller.router, prefix="/yaml", tags=["yaml"])
