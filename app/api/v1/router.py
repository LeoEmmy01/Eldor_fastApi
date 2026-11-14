from fastapi import APIRouter
from app.api.v1.endpoints import uploads, projects, generation, health, auth, palette, editing

api_router = APIRouter()
api_router.include_router(auth.router, prefix="/auth", tags=["Authentication"])
api_router.include_router(uploads.router, tags=["Uploads"])
api_router.include_router(projects.router, tags=["Project"])
api_router.include_router(palette.router, tags=["Palette"])
api_router.include_router(editing.router, tags=["Scene Objects"])
api_router.include_router(generation.router, tags={"Generation"})
api_router.include_router(health.router, tags=["Health"])