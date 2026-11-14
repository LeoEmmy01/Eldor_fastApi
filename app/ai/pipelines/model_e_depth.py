
import asyncio
import io
import uuid
from pathlib import Path
from typing import Any, Dict

from huggingface_hub import AsyncInferenceClient
from PIL import Image

from app.core.config import settings


class DepthEstimationPipeline:
    """
    Model E: monocular depth estimation with Depth Anything V2.
    Produces a grayscale depth map at the original image size, saved to its own file.
    """

    def __init__(self):
        self.api_token = settings.HF_TOKEN_MODEL_E or settings.HF_TOKEN
        self.model_id = settings.HF_MODEL_E
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
    def _save_depth(depth_image: Image.Image, original_size, out_path: Path) -> None:
        """Blocking work: normalize, resize to the original size, save as PNG."""
        out_path.parent.mkdir(parents=True, exist_ok=True)
        depth = depth_image.convert("L").resize(original_size, Image.BICUBIC)
        depth.save(out_path)

    async def generate_depth_map(self, image_path: str, output_dir: str | None = None) -> Dict[str, Any]:
        if not self.api_token:
            return {"success": False, "error": "HF_TOKEN_MODEL_E is missing."}

        if not Path(image_path).is_file():
            return {"success": False, "error": f"Image file not found: {image_path}"}

        if not hasattr(self.client, "depth_estimation"):
            return {
                "success": False,
                "error": "Installed huggingface_hub has no depth_estimation. Run: pip install -U huggingface_hub",
            }

        try:
            image_bytes, original_size = await asyncio.to_thread(self._load_image_bytes, image_path)

            result = await self.client.depth_estimation(image_bytes)

            depth_image = getattr(result, "depth", result)
            if not isinstance(depth_image, Image.Image):
                return {"success": False, "error": "Depth model did not return an image."}

            base_dir = Path(output_dir) if output_dir else Path(settings.LOCAL_STORAGE_PATH) / "depth_maps"
            out_path = base_dir / f"{uuid.uuid4().hex}.png"

            await asyncio.to_thread(self._save_depth, depth_image, original_size, out_path)

            return {
                "success": True,
                "depth_map_url": str(out_path),  # a local path for now
                "model_used": self.model_id,
                "provider": "huggingface",
            }

        except Exception as e:
            return {"success": False, "error": f"Depth estimation failed: {e}"}