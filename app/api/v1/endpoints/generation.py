from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.models.project import Project
from app.models.generation_job import GenerationJob
from app.models.user import User
from app.core.security import get_current_user
from app.schemas.generation import GenerationRequest, GenerationResponse
from app.services.generation_service import process_generation_job

router = APIRouter()


@router.post("/generations", response_model=GenerationResponse, summary="Queue an AI generation job")
async def trigger_generation(
    payload: GenerationRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    project = (
        db.query(Project)
        .filter(Project.id == payload.project_id, Project.user_id == current_user.id)
        .first()
    )
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    job = GenerationJob(project_id=project.id, status="queued", stage="initialization")
    db.add(job)
    db.commit()
    db.refresh(job)

    background_tasks.add_task(
        process_generation_job,
        job.id,
        payload.prompt,
        payload.negative_prompt,
    )

    return {
        "job_id": job.id,
        "status": job.status,
        "message": "Generation job queued.",
    }


@router.get("/generations/{job_id}", summary="Check status of a queued generation job")
def check_job_status(
    job_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    job = (
        db.query(GenerationJob)
        .join(Project, Project.id == GenerationJob.project_id)
        .filter(GenerationJob.id == job_id, Project.user_id == current_user.id)
        .first()
    )
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    return {
        "job_id": job.id,
        "status": job.status,
        "stage": job.stage,
        "output_url": job.output_url,
        "error_message": job.error_message,
        "created_at": job.created_at,
        "updated_at": job.updated_at,
    }