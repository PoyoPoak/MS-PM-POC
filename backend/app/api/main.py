from fastapi import APIRouter

from app.api.routes import (
    dashboard,
    items,
    login,
    model_artifacts,
    patients,
    private,
    telemetry,
    training,
    users,
    utils,
)
from app.core.config import settings

api_router = APIRouter()
api_router.include_router(login.router)
api_router.include_router(users.router)
api_router.include_router(utils.router)
api_router.include_router(items.router)
api_router.include_router(telemetry.router)
api_router.include_router(model_artifacts.router)
api_router.include_router(training.router)
api_router.include_router(patients.router)
api_router.include_router(dashboard.router)


if settings.ENVIRONMENT == "local":
    api_router.include_router(private.router)
