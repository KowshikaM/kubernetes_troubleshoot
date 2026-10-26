"""API route aggregation."""

from fastapi import APIRouter

from app.api.health import router as health_router
from app.api.history import router as history_router
from app.api.investigate import router as investigate_router
from app.api.progress_stream import router as progress_router
from app.api.clusters import router as clusters_router

api_router = APIRouter()
api_router.include_router(health_router)
api_router.include_router(investigate_router)
api_router.include_router(history_router)
api_router.include_router(progress_router)
api_router.include_router(clusters_router)
