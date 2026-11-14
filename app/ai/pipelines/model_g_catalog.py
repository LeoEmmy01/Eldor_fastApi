import asyncio
import os
from typing import Any, Dict

from huggingface_hub import InferenceClient
from PIL import Image

from app.core.config import settings


class FurnitureCatalogPipeline:
    """Extract furniture image features; product matching requires a real catalog."""

    def __init__(self) -> None:
        self.api_token = settings.HF_TOKEN_MODEL_G or settings.HF_TOKEN
        self.model_id = settings.HF_MODEL_G
        self.client = InferenceClient(
            model=self.model_id,
            token=self.api_token or None,
            timeout=120,
        )

    async def match_furniture(self, cropped_furniture_image_path: str) -> Dict[str, Any]:
        if not os.path.isfile(cropped_furniture_image_path):
            return {"success": False, "error": "Cropped furniture image path not found."}
        if not self.api_token:
            return {"success": False, "error": "HF_TOKEN_MODEL_G or HF_TOKEN is required."}

        try:
            embedding = await asyncio.to_thread(self._extract_features, cropped_furniture_image_path)
            dimension = len(embedding) if hasattr(embedding, "__len__") else None
            return {
                "success": False,
                "error": "Feature extraction succeeded, but no product catalog is configured for matching.",
                "embedding_dimension": dimension,
                "matched_products": [],
                "model_used": self.model_id,
                "provider": "huggingface",
            }
        except Exception as exc:
            return {"success": False, "error": f"Catalog feature extraction failed: {exc}"}

    def _extract_features(self, image_path: str) -> Any:
        with Image.open(image_path) as image:
            return self.client.feature_extraction(image=image)
