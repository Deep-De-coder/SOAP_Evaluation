"""Data loading utilities for the OMI Health dataset."""

import logging
from pathlib import Path
from datasets import load_dataset
from typing import List

from .models import SoapExample

logger = logging.getLogger(__name__)


def load_omi_examples(
    split: str = "test", n: int = 100, dataset_name: str = "omi-health/medical-dialogue-to-soap-summary"
) -> List[SoapExample]:
    """
    Load the first n examples from the specified split and build SoapExample objects.

    The dataset will be automatically downloaded and cached by Hugging Face datasets
    under ~/.cache/huggingface/datasets.

    Args:
        split: Dataset split to load (default: "test")
        n: Number of examples to load (default: 100)
        dataset_name: Hugging Face dataset name (default: "omi-health/medical-dialogue-to-soap-summary")

    Returns:
        List of SoapExample objects. The generated_note will initially be a copy
        of reference_note; it should be overwritten by the corruption step.
    """
    logger.info(f"Loading {n} examples from {split} split of {dataset_name}...")
    ds = load_dataset(dataset_name, split=split)
    ds = ds.select(range(min(n, len(ds))))

    examples: List[SoapExample] = []
    for i, row in enumerate(ds):
        examples.append(
            SoapExample(
                id=f"{split}_{i}",
                transcript=row["dialogue"],
                reference_note=row["soap"],
                generated_note=row["soap"],  # will be corrupted later
            )
        )

    logger.info(f"Loaded {len(examples)} examples")
    return examples


def save_subset(split: str = "test", n: int = 100, out_path: str = "data/omi_soap_100.jsonl") -> None:
    """
    Save a sampled subset of the dataset to a JSONL file.

    Args:
        split: Dataset split to use (default: "test")
        n: Number of examples to save (default: 100)
        out_path: Output file path (default: "data/omi_soap_100.jsonl")
    """
    logger.info(f"Saving {n} examples from {split} split to {out_path}...")
    ds = load_dataset("omi-health/medical-dialogue-to-soap-summary", split=split)
    ds = ds.select(range(min(n, len(ds))))
    Path(out_path).parent.mkdir(parents=True, exist_ok=True)
    ds.to_json(out_path)
    logger.info(f"Saved {len(ds)} examples to {out_path}")

