# app/ai/pipelines/model_b_segmentation.py
import asyncio
import base64
import io
import uuid
from pathlib import Path
from typing import Any, Dict, List

from huggingface_hub import AsyncInferenceClient
from PIL import Image

from app.core.config import settings


class RoomSegmentationPipeline:
    """
    Model B: semantic segmentation of a room photo.
    Produces one binary mask (PNG) per detected region, at the original image size.
    """

    def __init__(self):
        self.api_token = settings.HF_TOKEN_MODEL_B or settings.HF_TOKEN
        self.model_id = settings.HF_MODEL_B
        self.client = AsyncInferenceClient(
            model=self.model_id, token=self.api_token or None, timeout=120
        )

    @staticmethod
    def _load_image_bytes(image_path: str, max_side: int = 1024):
        """Blocking work: load, downscale, JPEG-encode. Returns (bytes, original_size)."""
        with Image.open(image_path) as img:
            original_size = img.size
            img = img.convert("RGB")
            img.thumbnail((max_side, max_side))
            buf = io.BytesIO()
            img.save(buf, format="JPEG", quality=90)
        return buf.getvalue(), original_size

    @staticmethod
    def _mask_to_image(mask) -> Image.Image:
        """Newer huggingface_hub returns a PIL image; older versions return base64."""
        if isinstance(mask, Image.Image):
            return mask
        return Image.open(io.BytesIO(base64.b64decode(mask)))

    @staticmethod
    def _save_masks(items, original_size, out_dir: Path) -> List[Dict[str, Any]]:
        """Blocking work: resize masks to the original size and save as PNGs."""
        out_dir.mkdir(parents=True, exist_ok=True)
        regions: List[Dict[str, Any]] = []
        for i, item in enumerate(items):
            mask = RoomSegmentationPipeline._mask_to_image(item.mask).convert("L")
            mask = mask.resize(original_size, Image.NEAREST)
            safe_label = "".join(c if c.isalnum() else "_" for c in item.label.lower())
            mask_path = out_dir / f"{i:02d}_{safe_label}.png"
            mask.save(mask_path)
            regions.append(
                {
                    "label": item.label,
                    "mask_path": str(mask_path),
                    "confidence": item.score,  # may be None for some models
                }
            )
        return regions

    async def generate_masks(self, image_path: str, output_dir: str | None = None) -> Dict[str, Any]:
        if not self.api_token:
            return {"success": False, "error": "HF_TOKEN_MODEL_B is missing."}

        if not Path(image_path).is_file():
            return {"success": False, "error": f"Image file not found: {image_path}"}

        try:
            image_bytes, original_size = await asyncio.to_thread(self._load_image_bytes, image_path)

            items = await self.client.image_segmentation(image_bytes)
            if not items:
                return {"success": False, "error": "Segmentation returned no regions."}

            out_dir = Path(output_dir) if output_dir else (
                Path(settings.LOCAL_STORAGE_PATH) / "masks" / uuid.uuid4().hex
            )
            regions = await asyncio.to_thread(self._save_masks, items, original_size, out_dir)

            return {
                "success": True,
                "segmented_regions": regions,
                "model_used": self.model_id,
                "provider": "huggingface",
            }

        except Exception as e:
            return {"success": False, "error": f"Room segmentation failed: {e}"}