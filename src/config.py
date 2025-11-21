"""Central configuration management using environment variables."""

from pathlib import Path
from typing import Optional

try:
    from pydantic_settings import BaseSettings
except ImportError:
    # Fallback for pydantic < 2.0
    from pydantic import BaseSettings

from pydantic import Field


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Evaluation config
    USE_LLM: bool = Field(default=True, description="Use LLM judge for evaluation")
    NUM_EXAMPLES: int = Field(default=50, description="Number of examples to evaluate")
    PRODUCTION_MODE: bool = Field(
        default=False, description="Production mode: no reference notes available"
    )

    # Dataset config
    DATASET_NAME: str = Field(
        default="omi-health/medical-dialogue-to-soap-summary",
        description="Hugging Face dataset name",
    )
    DATASET_SPLIT: str = Field(default="test", description="Dataset split to use")

    # OpenAI config
    OPENAI_API_KEY: Optional[str] = Field(
        default=None, description="OpenAI API key for LLM judge"
    )
    OPENAI_MODEL: str = Field(
        default="gpt-4o-mini", description="OpenAI model to use for LLM judge"
    )
    OPENAI_TEMPERATURE: float = Field(
        default=0.0, description="Temperature for LLM judge (0.0 for deterministic)"
    )

    # Backend config
    BACKEND_PORT: int = Field(default=8000, description="Backend API port")
    BACKEND_HOST: str = Field(
        default="0.0.0.0", description="Backend API host (0.0.0.0 for Docker)"
    )

    # Frontend config
    FRONTEND_PORT: int = Field(default=5173, description="Frontend dev server port")
    API_BASE_URL: str = Field(
        default="http://localhost:8000", description="Backend API base URL for frontend"
    )

    # Output config
    OUTPUT_DIR: str = Field(
        default="results", description="Output directory for evaluation results"
    )

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True


# Global settings instance
settings = Settings()

