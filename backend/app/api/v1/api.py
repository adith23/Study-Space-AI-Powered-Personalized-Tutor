from fastapi import APIRouter

from app.api.v1.endpoints import auth, health, materials

api_router = APIRouter()

api_router.include_router(auth.router, prefix="/auth", tags=["Auth"])
api_router.include_router(health.router, tags=["health"])
api_router.include_router(materials.router, prefix="/materials", tags=["materials"])
#api_router.include_router(study_space.router, tags=["Study Spaces"])