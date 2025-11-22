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

    # CORS config
    FRONTEND_ORIGIN: str = Field(
        default="http://localhost:5173",
        description="Frontend origin for CORS (e.g. http://localhost:5173 locally, https://your-app.vercel.app in prod)",
    )

    # Output config
    OUTPUT_DIR: str = Field(
        default="results", description="Output directory for evaluation results (relative to backend/)"
    )

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True

    def get_output_dir(self) -> Path:
        """Get absolute path to output directory."""
        # If OUTPUT_DIR is absolute, use it; otherwise make it relative to backend/
        output_path = Path(self.OUTPUT_DIR)
        if output_path.is_absolute():
            return output_path
        # Get backend directory (parent of src/)
        backend_dir = Path(__file__).parent.parent
        return backend_dir / output_path


# Global settings instance
settings = Settings()

