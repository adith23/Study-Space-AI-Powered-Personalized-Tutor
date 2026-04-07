from fastapi import APIRouter

from app.api.v1.endpoints import (
    auth_routes,
    materials_chat_routes,
    materials_file_routes,
)

api_router = APIRouter()

api_router.include_router(auth_routes.router, prefix="/auth", tags=["Auth"])
api_router.include_router(
    materials_file_routes.router, prefix="/materials", tags=["materials"]
)
api_router.include_router(
    materials_chat_routes.router, prefix="/materials", tags=["materials"]
)
