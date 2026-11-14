from typing import Dict, Any, Optional
from app.ai.providers.base import BaseAIProvider

class MockAIProvider(BaseAIProvider):
    async def generate_image(self, prompt: str, negative_prompt: Optional[str] = None, **kwargs) -> Dict[str, Any]:
        return {
            "success": False,
            "error": "The mock provider does not generate image files. Configure AI_PROVIDER=huggingface.",
            "provider": "mock"
        }

    async def edit_image(self, image_path: str, prompt: str, mask_path: Optional[str] = None, **kwargs) -> Dict[str, Any]:
        return {
            "success": True,
            "output_url": image_path, # Return original or simulated edited path
            "model_used": "mock-editor-v1",
            "provider": "mock"
        }

    async def upscale_image(self, image_path: str, scale_factor: int = 2, **kwargs) -> Dict[str, Any]:
        return {
            "success": True,
            "output_url": image_path,
            "model_used": "mock-upscaler-v1",
            "provider": "mock"
        }

    async def health_check(self) -> bool:
        return True