from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    PROJECT_NAME: str = "EldorSketch"
    API_V1_STR: str = "/api/v1"
    DATABASE_URL: str = "sqlite:///./eldorsketch.db"
    STORAGE_TYPE: str = "local"
    LOCAL_STORAGE_PATH: str = "./storage_data"
    AI_PROVIDER: str = "huggingface"

    HF_TOKEN: str = ""
    HF_TOKEN_MODEL_A: str = ""
    HF_TOKEN_MODEL_B: str = ""
    HF_TOKEN_MODEL_E: str = ""
    HF_TOKEN_MODEL_D: str = ""
    HF_TOKEN_MODEL_G: str = ""
    HF_TOKEN_MODEL_F: str = ""

    HF_MODEL_A: str = "Qwen/Qwen2.5-VL-7B-Instruct"
    HF_MODEL_B: str = "nvidia/segformer-b0-finetuned-ade-512-512"
    HF_MODEL_E: str = "depth-anything/Depth-Anything-V2-Base-hf"
    HF_MODEL_D: str = "stabilityai/stable-diffusion-xl-base-1.0"
    HF_MODEL_F: str = "ai-forever/Real-ESRGAN"
    HF_MODEL_G: str = "openai/clip-vit-large-patch14"

    @field_validator("DATABASE_URL", mode="before")
    @classmethod
    def normalize_database_url(cls, value: str) -> str:
        if isinstance(value, str) and value.startswith("postgres://"):
            return value.replace("postgres://", "postgresql://", 1)
        return value

    @field_validator("AI_PROVIDER")
    @classmethod
    def validate_ai_provider(cls, value: str) -> str:
        provider = value.strip().lower()
        if provider not in {"huggingface", "mock"}:
            raise ValueError("AI_PROVIDER must be 'huggingface' or 'mock'.")
        return provider

    @field_validator("STORAGE_TYPE")
    @classmethod
    def validate_storage_type(cls, value: str) -> str:
        storage_type = value.strip().lower()
        if storage_type != "local":
            raise ValueError("Only STORAGE_TYPE=local is implemented.")
        return storage_type

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


settings = Settings()
