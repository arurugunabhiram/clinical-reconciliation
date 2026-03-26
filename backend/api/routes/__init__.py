from fastapi import APIRouter

from .reconcile import router as reconcile_router
from .validate import router as validate_router

api_router = APIRouter(prefix="/api")
api_router.include_router(reconcile_router)
api_router.include_router(validate_router)
