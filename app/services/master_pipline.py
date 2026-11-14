from pathlib import Path
from tempfile import TemporaryDirectory

from sqlalchemy.orm import Session

from app.ai.orchestrator import ai_orchestrator
from app.ai.pipelines.model_a_understanding import RoomUnderstandingPipeline
from app.ai.pipelines.model_b_segmentation import RoomSegmentationPipeline
from app.ai.pipelines.model_e_depth import DepthEstimationPipeline
from app.core.config import settings
from app.database.session import SessionLocal
from app.models.generation_job import GenerationJob
from app.models.project import Project
from app.services.prompt_service import PromptService
from app.storage.local_storage import LocalStorage


async def run_full_ai_pipeline(
    job_id: str,
    prompt: str,
    negative_prompt: str | None = None,
) -> None:
    db: Session = SessionLocal()
    try:
        job = db.query(GenerationJob).filter(GenerationJob.id == job_id).first()
        if not job:
            return

        project = db.query(Project).filter(Project.id == job.project_id).first()
        if not project:
            job.status = "failed"
            job.stage = "failed"
            job.error_message = "Associated project not found."
            db.commit()
            return

        image_path = await LocalStorage().get_file(project.original_image_url)
        if not Path(image_path).is_file():
            raise FileNotFoundError("The project's uploaded source image was not found.")

        storage_root = LocalStorage().base_dir

        job.status = "processing"
        job.stage = "understanding_room"
        db.commit()
        analysis_result = await RoomUnderstandingPipeline().analyze_room(image_path)
        if not analysis_result.get("success"):
            raise RuntimeError(f"Room understanding failed: {analysis_result.get('error')}")

        job.stage = "estimating_depth"
        db.commit()
        with TemporaryDirectory(dir=storage_root) as depth_output_dir:
            depth_result = await DepthEstimationPipeline().generate_depth_map(
                image_path,
                output_dir=depth_output_dir,
            )
        if not depth_result.get("success"):
            raise RuntimeError(f"Depth estimation failed: {depth_result.get('error')}")

        job.stage = "segmenting_objects"
        db.commit()
        with TemporaryDirectory(dir=storage_root) as masks_output_dir:
            segmentation_result = await RoomSegmentationPipeline().generate_masks(
                image_path,
                output_dir=masks_output_dir,
            )
        if not segmentation_result.get("success"):
            raise RuntimeError(f"Room segmentation failed: {segmentation_result.get('error')}")

        job.stage = "generating_image"
        db.commit()
        enhanced_prompt = PromptService.enhance_prompt(
            user_prompt=prompt,
            room_type=project.room_type,
            style=project.style,
            primary_color=project.primary_color,
            secondary_color=project.secondary_color,
            accent_color=project.accent_color,
            room_analysis=analysis_result.get("analysis_output"),
        )

        generation_result = await ai_orchestrator.run_generation(
            prompt=enhanced_prompt,
            negative_prompt=negative_prompt,
            user_id=project.user_id,
            image_path=image_path,
        )
        if not generation_result.get("success"):
            raise RuntimeError(generation_result.get("error", "Image generation failed."))

        job.status = "completed"
        job.stage = "finished"
        job.output_url = generation_result.get("output_url")
        job.error_message = None
        db.commit()
    except Exception as exc:
        db.rollback()
        job = db.query(GenerationJob).filter(GenerationJob.id == job_id).first()
        if job:
            job.status = "failed"
            job.stage = "failed"
            job.error_message = str(exc)
            db.commit()
    finally:
        db.close()
