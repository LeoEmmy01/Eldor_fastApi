from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.models.project import Project
from app.models.user import User
from app.core.security import get_current_user
from app.schemas.palette import PaletteUpdate, PaletteResponse

router = APIRouter()

@router.get("/projects/{project_id}/palette", response_model=PaletteResponse, summary="Get project color palette")
def get_project_palette(
    project_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    project = db.query(Project).filter(Project.id == project_id, Project.user_id == current_user.id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
        
    return PaletteResponse(
        primary_color=project.primary_color,
        secondary_color=project.secondary_color,
        accent_color=project.accent_color
    )

@router.patch("/projects/{project_id}/palette", response_model=PaletteResponse, summary="Update 3-color palette")
def update_project_palette(
    project_id: str,
    palette_in: PaletteUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    project = db.query(Project).filter(Project.id == project_id, Project.user_id == current_user.id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    if palette_in.primary_color is not None:
        project.primary_color = palette_in.primary_color
    if palette_in.secondary_color is not None:
        project.secondary_color = palette_in.secondary_color
    if palette_in.accent_color is not None:
        project.accent_color = palette_in.accent_color

    db.commit()
    db.refresh(project)
    
    return PaletteResponse(
        primary_color=project.primary_color,
        secondary_color=project.secondary_color,
        accent_color=project.accent_color
    )