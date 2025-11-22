"""Environment-driven evaluation entrypoint (no CLI flags)."""

import logging

from .config import settings
from .eval.pipeline import run_evaluation

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)

if __name__ == "__main__":
    run_evaluation()

