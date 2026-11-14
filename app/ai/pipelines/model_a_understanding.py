
import asyncio
import base64
import io
import json
import re
from pathlib import Path
from typing import Any, Dict

from huggingface_hub import AsyncInferenceClient
from PIL import Image

from app.core.config import settings


class RoomUnderstandingPipeline:
    """
    Model A: room understanding with a vision-language model.
    Extracts room type, visible furniture, lighting and layout as structured JSON.
    """

    PROMPT = (
        "Analyze this interior room photo. Respond with JSON only, no extra text, "
        'using exactly these keys: "room_type" (string), "furniture" (list of strings), '
        '"lighting" (string), "layout_notes" (string), "dominant_colors" (list of strings).'
    )

    def __init__(self):
        self.api_token = settings.HF_TOKEN_MODEL_A or settings.HF_TOKEN
        self.model_id = settings.HF_MODEL_A
        self.client = AsyncInferenceClient(model=self.model_id, token=self.api_token or None)

    @staticmethod
    def _to_data_url(image_path: str, max_side: int = 1024) -> str:
        """Blocking work: load, downscale, and encode the image as a data URL."""
        with Image.open(image_path) as img:
            img = img.convert("RGB")
            img.thumbnail((max_side, max_side))
            buf = io.BytesIO()
            img.save(buf, format="JPEG", quality=90)
        encoded = base64.b64encode(buf.getvalue()).decode("utf-8")
        return f"data:image/jpeg;base64,{encoded}"

    @staticmethod
    def _parse_json(text: str):
        cleaned = re.sub(r"^```(?:json)?|```$", "", text.strip(), flags=re.MULTILINE).strip()
        try:
            return json.loads(cleaned)
        except json.JSONDecodeError:
            return None

    async def analyze_room(self, image_path: str) -> Dict[str, Any]:
        if not self.api_token:
            return {"success": False, "error": "HF_TOKEN_MODEL_A is missing."}

        if not Path(image_path).is_file():
            return {"success": False, "error": f"Image file not found: {image_path}"}

        try:
            data_url = await asyncio.to_thread(self._to_data_url, image_path)

            response = await self.client.chat_completion(
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {"type": "image_url", "image_url": {"url": data_url}},
                            {"type": "text", "text": self.PROMPT},
                        ],
                    }
                ],
                max_tokens=500,
            )

            raw_text = response.choices[0].message.content or ""
            parsed = self._parse_json(raw_text)
            if not isinstance(parsed, dict):
                return {"success": False, "error": "Room understanding returned invalid JSON."}

            expected_keys = {"room_type", "furniture", "lighting", "layout_notes", "dominant_colors"}
            if not expected_keys.issubset(parsed):
                return {"success": False, "error": "Room understanding response is missing required fields."}
            if (
                not isinstance(parsed["room_type"], str)
                or not isinstance(parsed["furniture"], list)
                or not all(isinstance(item, str) for item in parsed["furniture"])
                or not isinstance(parsed["lighting"], str)
                or not isinstance(parsed["layout_notes"], str)
                or not isinstance(parsed["dominant_colors"], list)
                or not all(isinstance(item, str) for item in parsed["dominant_colors"])
            ):
                return {"success": False, "error": "Room understanding response has invalid field types."}

            return {
                "success": True,
                "model_used": self.model_id,
                "analysis_output": parsed,
                "raw_text": raw_text,
                "provider": "huggingface",
            }

        except Exception as e:
            return {"success": False, "error": f"Room understanding failed: {e}"}