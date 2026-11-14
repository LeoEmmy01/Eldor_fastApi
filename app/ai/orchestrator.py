from app.ai.providers.huggingface_provider import HuggingFaceAIProvider
from app.ai.providers.mock_providers import MockAIProvider
from app.ai.providers.base import BaseAIProvider
from app.core.config import settings

class AIOrchestrator:
    def __init__(self, provider_name: str | None = None):
        self.provider_name = (provider_name or settings.AI_PROVIDER).lower()
        self.provider = self._load_provider()
        
    def _load_provider(self) -> BaseAIProvider:
        if self.provider_name == "huggingface":
            return HuggingFaceAIProvider()
        if self.provider_name == "mock":
            return MockAIProvider()
        raise ValueError(f"Unsupported AI provider: {self.provider_name}")
    
    
    async def run_generation(self, prompt: str, **kwargs):
        return await self.provider.generate_image(prompt, **kwargs)

ai_orchestrator = AIOrchestrator()