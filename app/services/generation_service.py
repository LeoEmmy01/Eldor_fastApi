from app.services.master_pipline import run_full_ai_pipeline


async def process_generation_job(
    job_id: str,
    prompt: str,
    negative_prompt: str | None = None,
) -> None:
    """Run the configured image-generation workflow for a queued job."""
    await run_full_ai_pipeline(job_id, prompt, negative_prompt=negative_prompt)