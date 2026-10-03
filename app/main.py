from fastapi import FastAPI

from app.api.routes.auth import (
    router as auth_router,
)

from app.api.routes.health import (
    router as health_router,
)

from app.api.routes.materials import (
    router as materials_router,
)

from app.api.routes.subjects import (
    router as subjects_router,
)

from app.core.config import settings


app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description=(
        "Backend API for the "
        "LearnLoop AI mobile "
        "study application."
    ),
)


app.include_router(
    health_router
)

app.include_router(
    auth_router
)

app.include_router(
    subjects_router
)

app.include_router(
    materials_router
)


@app.get("/")
async def root():
    return {
        "application": (
            settings.app_name
        ),
        "version": (
            settings.app_version
        ),
        "message": (
            "Welcome to "
            "LearnLoop AI API"
        ),
    }