from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List


from app.database.session import get_db
from app.models.project import Project
from app.models.scene_object import SceneObject
from app.models.user import User
from app.core.security import get_current_user
from app.schemas.scene import SceneObjectCreate, SceneObjectResponse

router = APIRouter()


@router.get("/projects/{project_id}/objects", response_model=list[SceneObjectResponse], summary="List scene objects")
def get_scene_objects(
    project_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    
    project = db.query(Project).filter(Project.id == project_id, Project.user_id == current_user.id).first()
    if not project: 
        raise HTTPException(status_code=404, detail="Project not found")
    return db.query(SceneObject).filter(SceneObject.project_id == project_id).all()

@router.post("/projects/{project_id}/objects", response_model=SceneObjectResponse, summary="Add editable object")
def add_scene_object(
    project_id: str,
    obj_in: SceneObjectCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    
    project = db.query(Project).filter(Project.id == project_id, Project.user_id == current_user.id).first()
    if not project:
        raise HTTPException(status_code= 404, detail="Project not found")
    
    scene_obj = SceneObject(
        project_id=project.id,
        object_type=obj_in.object_type,
        display_name=obj_in.display_name,
        color=obj_in.color,
        material=obj_in.material
    )
    db.add(scene_obj)
    db.commit()
    db.refresh(scene_obj)
    return scene_obj