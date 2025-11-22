"""Utilities to corrupt SOAP notes for synthetic evaluation."""

import random
import re
import logging
from typing import List

from .models import SoapExample

logger = logging.getLogger(__name__)


def corrupt_soap_note(soap: str, drop_prob: float = 0.35) -> str:
    """
    Split SOAP note into sentences and randomly drop some to simulate missing content.

    Args:
        soap: The original SOAP note text
        drop_prob: Probability of dropping each sentence (default: 0.35)

    Returns:
        Corrupted SOAP note with some sentences removed
    """
    if not soap.strip():
        return soap

    # Split into sentences using a simple regex
    # This handles common sentence endings and SOAP section headers
    sentences = re.split(r"(?<=[.!?])\s+(?=[A-Z])|(?<=\n)(?=[SOAP]:)", soap)
    sentences = [s.strip() for s in sentences if s.strip()]

    # Randomly drop sentences based on drop_prob
    kept_sentences = [
        s for s in sentences if random.random() > drop_prob
    ]

    # If we dropped everything, keep at least one sentence
    if not kept_sentences and sentences:
        kept_sentences = [random.choice(sentences)]

    # Optionally truncate some sentences to simulate missing details
    result_sentences = []
    for sent in kept_sentences:
        # 10% chance to truncate a sentence (remove last 20-40% of words)
        if random.random() < 0.1 and len(sent.split()) > 5:
            words = sent.split()
            truncate_at = max(3, int(len(words) * random.uniform(0.6, 0.8)))
            sent = " ".join(words[:truncate_at]) + "..."

        result_sentences.append(sent)

    corrupted = " ".join(result_sentences)
    return corrupted


def corrupt_examples(examples: List[SoapExample], drop_prob: float = 0.35) -> None:
    """
    Apply corruption to a list of SoapExample objects in-place.

    Args:
        examples: List of SoapExample objects to corrupt
        drop_prob: Probability of dropping each sentence (default: 0.35)
    """
    logger.info(f"Corrupting {len(examples)} examples with drop_prob={drop_prob}")
    for example in examples:
        example.generated_note = corrupt_soap_note(example.reference_note, drop_prob)

