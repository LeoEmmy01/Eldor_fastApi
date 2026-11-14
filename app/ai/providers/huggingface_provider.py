import asyncio
import uuid
from pathlib import Path
from typing import Any, Dict, Optional

from huggingface_hub import AsyncInferenceClient
from PIL import Image

from app.ai.providers.base import BaseAIProvider
from app.core.config import settings


class HuggingFaceAIProvider(BaseAIProvider):
    def __init__(self) -> None:
        self.api_token = settings.HF_TOKEN_MODEL_D or settings.HF_TOKEN
        self.model_id = settings.HF_MODEL_D
        self.client = AsyncInferenceClient(
            model=self.model_id,
            token=self.api_token or None,
        )

    async def generate_image(
        self,
        prompt: str,
        negative_prompt: Optional[str] = None,
        **kwargs: Any,
    ) -> Dict[str, Any]:
        if not self.api_token:
            return {"success": False, "error": "HF_TOKEN_MODEL_D or HF_TOKEN is required."}

        user_id = kwargs.get("user_id")
        if not user_id:
            return {"success": False, "error": "A project owner is required to save the generated image."}

        try:
            source_path = kwargs.get("image_path")
            if source_path:
                source_image = await asyncio.to_thread(self._load_image, Path(source_path))
                image = await self.client.image_to_image(
                    image=source_image,
                    prompt=prompt,
                    negative_prompt=negative_prompt,
                )
            else:
                image = await self.client.text_to_image(
                    prompt,
                    negative_prompt=negative_prompt,
                )
            if not isinstance(image, Image.Image):
                return {"success": False, "error": "The image provider returned no image."}

            filename = f"{uuid.uuid4().hex}.png"
            output_dir = Path(settings.LOCAL_STORAGE_PATH) / "generations" / str(user_id)
            output_path = output_dir / filename
            await asyncio.to_thread(self._save_image, image, output_path)

            return {
                "success": True,
                "output_url": f"{settings.API_V1_STR}/files/{filename}?kind=generations",
                "model_used": self.model_id,
                "provider": "huggingface",
            }
        except Exception as exc:
            return {"success": False, "error": f"Image generation failed: {exc}"}

    async def edit_image(
        self,
        image_path: str,
        prompt: str,
        mask_path: Optional[str] = None,
        **kwargs: Any,
    ) -> Dict[str, Any]:
        return {
            "success": False,
            "error": "Image editing is not implemented by the configured Hugging Face provider.",
        }

    async def upscale_image(
        self,
        image_path: str,
        scale_factor: int = 2,
        **kwargs: Any,
    ) -> Dict[str, Any]:
        return {
            "success": False,
            "error": "Image upscaling is not implemented by the configured Hugging Face provider.",
        }

    async def health_check(self) -> bool:
        return bool(self.api_token)

    @staticmethod
    def _save_image(image: Image.Image, output_path: Path) -> None:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        image.save(output_path, format="PNG")

    @staticmethod
    def _load_image(image_path: Path) -> Image.Image:
        with Image.open(image_path) as image:
            return image.convert("RGB")
