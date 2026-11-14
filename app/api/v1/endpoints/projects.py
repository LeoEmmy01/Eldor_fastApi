from fastapi import APIRouter, Depends, HTTPException
from pathlib import Path
from sqlalchemy.orm import Session
from typing import List

from app.database.session import get_db
from app.models.project import Project
from app.models.user import User
from app.core.security import get_current_user
from app.schemas.projects import ProjectCreate, ProjectResponse
from app.storage.local_storage import LocalStorage


router = APIRouter()
storage = LocalStorage()


@router.post("/projects", response_model=ProjectResponse, summary="Create a new design project")
async def create_project(
    project: ProjectCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    image_reference = f"uploads/{current_user.id}/{project.image_filename}"
    image_path = Path(await storage.get_file(image_reference))
    if not image_path.is_file():
        raise HTTPException(status_code=404, detail="Uploaded image not found")

    db_project = Project(
        user_id=current_user.id,
        title=project.title,
        original_image_url=image_reference,
        room_type=project.room_type,
        style=project.style,
        primary_color=project.primary_color,
        secondary_color=project.secondary_color,
        accent_color=project.accent_color,
    )
    db.add(db_project)
    db.commit()
    db.refresh(db_project)
    return db_project


@router.get("/projects", response_model=List[ProjectResponse], summary="List all user projects")
def get_user_projects(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return db.query(Project).filter(Project.user_id == current_user.id).all()


@router.get("/projects/{project_id}", response_model=ProjectResponse, summary="Get project details by ID")
def get_project(
    project_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    project = (
        db.query(Project)
        .filter(
            Project.id == project_id,
            Project.user_id == current_user.id,
        )
        .first()
    )

    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return project