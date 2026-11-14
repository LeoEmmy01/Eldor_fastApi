from abc import ABC, abstractmethod
from typing import Dict, Any, Optional

class BaseAIProvider(ABC):
    
    @abstractmethod
    async def generate_image(self, prompt: str, negative_prompt: Optional[str] = None, **kwargs) -> Dict[str, Any]:
        """Generates an interior design image from a text prompt and optional source image."""
        pass

    @abstractmethod
    async def edit_image(self, image_path: str, prompt: str, mask_path: Optional[str] = None, **kwargs) -> Dict[str, Any]:
        """Edits an existing room image based on instructions or masks."""
        pass

    @abstractmethod
    async def upscale_image(self, image_path: str, scale_factor: int = 2, **kwargs) -> Dict[str, Any]:
        """Enhances the resolution of a generated image."""
        pass

    @abstractmethod
    async def health_check(self) -> bool:
        """Verifies if the provider is available and healthy."""
        pass