import asyncio
import uuid
from pathlib import Path
from typing import Any, Dict

from huggingface_hub import InferenceClient
from PIL import Image

from app.core.config import settings


class ImageUpscalePipeline:
    """Image enhancement using the configured Hugging Face upscaling model."""

    def __init__(self) -> None:
        self.api_token = settings.HF_TOKEN_MODEL_F or settings.HF_TOKEN
        self.model_id = settings.HF_MODEL_F
        self.client = InferenceClient(
            model=self.model_id,
            token=self.api_token or None,
            timeout=120,
        )

    async def upscale_image(self, image_path: str, scale_factor: int = 4) -> Dict[str, Any]:
        source = Path(image_path)
        if not source.is_file():
            return {"success": False, "error": "Image path not found."}
        if not self.api_token:
            return {"success": False, "error": "HF_TOKEN_MODEL_F or HF_TOKEN is required."}
        if scale_factor < 2:
            return {"success": False, "error": "scale_factor must be at least 2."}
        if not hasattr(self.client, "image_to_image"):
            return {"success": False, "error": "The installed Hugging Face client does not support image-to-image inference."}

        output_path = source.parent / f"{source.stem}_{uuid.uuid4().hex}_upscaled.png"
        try:
            result = await asyncio.to_thread(self._upscale_sync, source, output_path)
            if not isinstance(result, Image.Image):
                return {"success": False, "error": "The upscaling model did not return an image."}
            await asyncio.to_thread(result.save, output_path, format="PNG")
            return {
                "success": True,
                "upscaled_url": str(output_path),
                "scale_factor": scale_factor,
                "model_used": self.model_id,
                "provider": "huggingface",
            }
        except Exception as exc:
            output_path.unlink(missing_ok=True)
            return {"success": False, "error": f"Image upscaling failed: {exc}"}

    def _upscale_sync(self, source: Path, output_path: Path) -> Any:
        with Image.open(source) as image:
            return self.client.image_to_image(image=image)
