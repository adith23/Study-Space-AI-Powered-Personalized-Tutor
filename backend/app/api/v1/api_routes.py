from fastapi import APIRouter

from app.api.v1.endpoints import (
    auth_routes,
    chat_routes,
    flashcard_routes,
    materials_file_routes,
    quiz_routes,
    video_routes,
)

api_router = APIRouter()

api_router.include_router(auth_routes.router, prefix="/auth", tags=["Auth"])

api_router.include_router(
    materials_file_routes.router, prefix="/materials", tags=["materials"]
)

api_router.include_router(
    chat_routes.router, prefix="/materials", tags=["materials"]
)

api_router.include_router(
    quiz_routes.router, prefix="/materials", tags=["materials"]
)

api_router.include_router(
    flashcard_routes.router, prefix="/materials", tags=["materials"]
)

api_router.include_router(
    video_routes.router, prefix="/videos", tags=["videos"]
)
