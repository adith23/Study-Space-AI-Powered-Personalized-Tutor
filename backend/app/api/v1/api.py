from fastapi import APIRouter

from app.api.v1.endpoints import auth, materials

api_router = APIRouter()

api_router.include_router(auth.router, prefix="/auth", tags=["Auth"])
api_router.include_router(materials.router, prefix="/materials", tags=["materials"])
