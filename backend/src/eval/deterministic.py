"""Deterministic metrics for SOAP note evaluation (no LLM required)."""

import logging
import re
from typing import Optional

try:
    from rouge_score import rouge_scorer
    ROUGE_AVAILABLE = True
except ImportError:
    ROUGE_AVAILABLE = False
    rouge_scorer = None

try:
    import sacrebleu
    SACREBLEU_AVAILABLE = True
except ImportError:
    SACREBLEU_AVAILABLE = False
    sacrebleu = None

logger = logging.getLogger(__name__)


def compute_rouge_l(reference: str, generated: str) -> float:
    """
    Compute ROUGE-L F1 between reference and generated text.
    
    Args:
        reference: Reference text
        generated: Generated text
        
    Returns:
        ROUGE-L F1 score in [0, 1]
    """
    if not ROUGE_AVAILABLE:
        logger.warning("rouge-score not available, skipping ROUGE-L computation")
        return 0.0
    
    try:
        scorer = rouge_scorer.RougeScorer(["rougeL"], use_stemmer=True)
        scores = scorer.score(reference, generated)
        return scores["rougeL"].fmeasure
    except Exception as e:
        logger.warning(f"Error computing ROUGE-L: {e}")
        return 0.0


def compute_bleu(reference: str, generated: str) -> float:
    """
    Compute BLEU score between reference and generated text.
    
    Args:
        reference: Reference text
        generated: Generated text
        
    Returns:
        BLEU score in [0, 1] (normalized from percentage)
    """
    if not SACREBLEU_AVAILABLE:
        logger.warning("sacrebleu not available, skipping BLEU computation")
        return 0.0
    
    try:
        bleu = sacrebleu.corpus_bleu([generated], [[reference]])
        # sacrebleu returns percentage * 100; normalize to [0, 1]
        return bleu.score / 100.0
    except Exception as e:
        logger.warning(f"Error computing BLEU: {e}")
        return 0.0


def has_soap_structure(text: str) -> bool:
    """
    Check if text appears to contain SOAP sections (S:, O:, A:, P:).

    Args:
        text: Text to check

    Returns:
        True if SOAP structure is detected
    """
    text_upper = text.upper()
    # Check for at least 2 of the 4 SOAP sections
    sections_found = sum(
        1
        for section in ["S:", "O:", "A:", "P:"]
        if section in text_upper or f"SUBJECTIVE:" in text_upper
    )
    return sections_found >= 2


def _split_into_sentences(text: str) -> list[str]:
    """
    Split text into sentences using simple heuristics.

    Args:
        text: Text to split

    Returns:
        List of sentences (non-empty, stripped)
    """
    if not text.strip():
        return []
    # Simple sentence splitting: split on . ! ? followed by space or newline
    sentences = re.split(r"[.!?]+\s+", text)
    # Filter out empty sentences and very short fragments
    sentences = [s.strip() for s in sentences if s.strip() and len(s.strip()) > 3]
    return sentences


def compute_coverage_det(reference_note: str | None, generated_note: str) -> float | None:
    """
    Compute deterministic coverage: proportion of reference sentences found in generated note.

    Args:
        reference_note: Reference SOAP note (None in production mode)
        generated_note: Generated SOAP note

    Returns:
        Coverage score between 0.0 and 1.0, or None if reference_note is None
    """
    if reference_note is None:
        return None  # Cannot compute coverage without reference in production mode

    if not reference_note.strip():
        return 1.0 if not generated_note.strip() else 0.0

    ref_sentences = _split_into_sentences(reference_note)
    if not ref_sentences:
        return 1.0

    gen_lower = generated_note.lower()
    matched = sum(1 for sent in ref_sentences if sent.lower() in gen_lower)

    return matched / len(ref_sentences)


def compute_hallucination_rate_det(
    generated_note: str, transcript: str, reference_note: str | None = None
) -> float:
    """
    Compute deterministic hallucination rate: proportion of generated sentences
    not found in transcript (and optionally reference).

    Args:
        generated_note: Generated SOAP note
        transcript: Doctor-patient dialogue
        reference_note: Reference SOAP note (optional, None in production mode)

    Returns:
        Hallucination rate between 0.0 and 1.0 (higher = more hallucinations)
    """
    if not generated_note.strip():
        return 0.0

    gen_sentences = _split_into_sentences(generated_note)
    if not gen_sentences:
        return 0.0

    # Combine transcript and reference (if available) for checking
    source_text = transcript.lower()
    if reference_note:
        source_text = (transcript + " " + reference_note).lower()

    hallucinated = sum(
        1 for sent in gen_sentences if sent.lower() not in source_text
    )

    return hallucinated / len(gen_sentences)

