"""Core metrics computation for SOAP note evaluation."""

from __future__ import annotations

import logging
import re
from typing import List, Dict, Any, Optional
import statistics

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

from .models import SoapExample, EvalResult, Issue

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


def compute_case_metrics(
    example: SoapExample, llm_judge: Any = None, use_llm: bool = True
) -> EvalResult:
    """
    Compute evaluation metrics for a single SOAP note example.

    This function implements a hybrid approach:
    - Deterministic layer (always runs): structure, coverage_det, hallucination_rate_det
    - LLM layer (optional, default ON): coverage, faithfulness, accuracy, issues

    Args:
        example: SoapExample to evaluate
        llm_judge: LLMJudge instance (required if use_llm=True)
        use_llm: Whether to use LLM judge (default: True)

    Returns:
        EvalResult with issues and scores (includes both deterministic and LLM scores)
    """
    issues: List[Issue] = []
    scores: Dict[str, float] = {}

    # ===== DETERMINISTIC LAYER (always runs) =====
    structure_score = 1.0 if has_soap_structure(example.generated_note) else 0.0
    
    # Coverage detection (only if reference_note is available)
    coverage_det = compute_coverage_det(example.reference_note, example.generated_note)
    
    # Hallucination rate (works with or without reference_note)
    hallucination_rate_det = compute_hallucination_rate_det(
        example.generated_note, example.transcript, example.reference_note
    )
    # Convert hallucination rate to faithfulness (1.0 - rate)
    faithfulness_det = 1.0 - hallucination_rate_det

    # Simple length checks (production mode)
    note_length = len(example.generated_note.strip())
    transcript_length = len(example.transcript.strip())
    is_very_short = note_length < 50  # Flag for very short notes
    is_too_short_relative = transcript_length > 0 and (note_length / transcript_length) < 0.1  # Less than 10% of transcript length

    scores["structure"] = structure_score
    if coverage_det is not None:
        scores["coverage_det"] = coverage_det
    scores["hallucination_rate_det"] = hallucination_rate_det
    scores["faithfulness_det"] = faithfulness_det
    scores["note_length"] = float(note_length)
    scores["is_very_short"] = 1.0 if is_very_short else 0.0
    scores["is_too_short_relative"] = 1.0 if is_too_short_relative else 0.0

    # ===== REFERENCE-BASED TEXT SIMILARITY METRICS =====
    # Only compute when reference_note is available
    if example.reference_note is not None and example.reference_note.strip():
        rouge_l_f = compute_rouge_l(example.reference_note, example.generated_note)
        bleu_score = compute_bleu(example.reference_note, example.generated_note)
        scores["rouge_l_f"] = rouge_l_f
        scores["bleu"] = bleu_score
    else:
        # Production mode: set to None to indicate not available
        scores["rouge_l_f"] = None
        scores["bleu"] = None

    # ===== LLM LAYER (optional, default ON) =====
    llm_scores: Dict[str, float] = {}
    if use_llm and llm_judge:
        try:
            llm_result = llm_judge.review(
                example.transcript, example.generated_note, example.reference_note
            )
            issues = llm_result.get("issues", [])
            llm_scores = llm_result.get("scores", {})
            # Check if LLM returned default/error scores (all 0.5) - if so, treat as failure
            if llm_scores.get("coverage") == 0.5 and llm_scores.get("faithfulness") == 0.5 and llm_scores.get("accuracy") == 0.5:
                logger.warning(f"LLM returned default scores for {example.id}, using deterministic metrics instead")
                llm_scores = {}  # Use deterministic scores instead
            else:
                scores.update(llm_scores)  # Add LLM scores with their original keys
        except Exception as e:
            logger.error(f"Error in LLM evaluation for {example.id}: {e}")
            # Fall back: use deterministic scores as base
            llm_scores = {}
    else:
        # No LLM: use deterministic scores as proxies
        llm_scores = {}

    # ===== COMBINE DETERMINISTIC + LLM SCORES =====
    # Final scores: prefer LLM if available, otherwise use deterministic
    # In production mode (coverage_det is None), only use LLM for coverage
    if coverage_det is not None:
        coverage_final = llm_scores.get("coverage", coverage_det)
    else:
        # Production mode: only LLM can provide coverage
        coverage_final = llm_scores.get("coverage", 0.5)  # Default if no LLM in production
    
    faithfulness_final = llm_scores.get("faithfulness", faithfulness_det)
    # For accuracy, we only have LLM (no deterministic proxy)
    accuracy_final = llm_scores.get("accuracy", 0.75)  # Default if no LLM

    scores["coverage_final"] = coverage_final
    scores["faithfulness_final"] = faithfulness_final
    scores["accuracy_final"] = accuracy_final

    # Also keep the original keys for backward compatibility
    scores["coverage"] = coverage_final
    scores["faithfulness"] = faithfulness_final
    scores["accuracy"] = accuracy_final

    # Compute overall quality as weighted sum
    overall_quality = (
        0.4 * coverage_final + 0.3 * faithfulness_final + 0.3 * accuracy_final
    )
    scores["overall_quality"] = overall_quality

    return EvalResult(example_id=example.id, issues=issues, scores=scores)


def wilson_confidence_interval(successes: int, n: int, z: float = 1.96) -> tuple[float, float]:
    """
    Compute Wilson score confidence interval for a proportion.

    Args:
        successes: Number of successes
        n: Total number of trials
        z: Z-score for confidence level (1.96 for 95%)

    Returns:
        Tuple of (lower_bound, upper_bound)
    """
    if n == 0:
        return (0.0, 0.0)

    p = successes / n
    denominator = 1 + (z**2 / n)
    center = (p + (z**2 / (2 * n))) / denominator
    margin = (z / denominator) * ((p * (1 - p) / n) + (z**2 / (4 * n**2))) ** 0.5

    lower = max(0.0, center - margin)
    upper = min(1.0, center + margin)
    return (lower, upper)


def aggregate_metrics(results: List[EvalResult], production_mode: bool = False) -> Dict[str, Any]:
    """
    Aggregate evaluation results into dataset-level metrics with confidence intervals.

    Args:
        results: List of EvalResult objects
        production_mode: Whether evaluation was run in production mode (no reference notes)

    Returns:
        Dictionary with aggregated metrics including confidence intervals
    """
    n = len(results)
    if n == 0:
        return {}
    
    # Check if we're in production mode by checking if any result has coverage_det
    # If all results lack coverage_det, we're likely in production mode
    has_coverage_det = any(
        r.scores.get("coverage_det") is not None for r in results
    )
    if not has_coverage_det:
        production_mode = True

    # Count issues by category
    missing_critical_count = sum(
        1 for r in results if any(i.category == "missing_critical" for i in r.issues)
    )
    hallucination_count = sum(
        1 for r in results if any(i.category == "hallucination" for i in r.issues)
    )
    clinical_error_count = sum(
        1
        for r in results
        if any(
            i.category == "clinical_inaccuracy"
            and i.severity in ["major", "critical"]
            for i in r.issues
        )
    )

    # Compute rates
    missing_rate = missing_critical_count / n
    hallucination_rate = hallucination_count / n
    clinical_error_rate = clinical_error_count / n

    # Compute confidence intervals
    missing_ci = wilson_confidence_interval(missing_critical_count, n)
    hallucination_ci = wilson_confidence_interval(hallucination_count, n)
    clinical_error_ci = wilson_confidence_interval(clinical_error_count, n)

    # Aggregate scores (both deterministic and final/LLM)
    coverage_scores = [r.scores.get("coverage", 0.0) for r in results]
    faithfulness_scores = [r.scores.get("faithfulness", 0.0) for r in results]
    accuracy_scores = [r.scores.get("accuracy", 0.0) for r in results]
    overall_scores = [r.scores.get("overall_quality", 0.0) for r in results]

    # Deterministic metrics (coverage_det may be None in production mode)
    coverage_det_scores = [
        r.scores.get("coverage_det") for r in results if r.scores.get("coverage_det") is not None
    ]
    hallucination_rate_det_scores = [
        r.scores.get("hallucination_rate_det", 0.0) for r in results
    ]
    structure_scores = [r.scores.get("structure", 0.0) for r in results]
    is_very_short_scores = [r.scores.get("is_very_short", 0.0) for r in results]
    is_too_short_relative_scores = [r.scores.get("is_too_short_relative", 0.0) for r in results]

    # Reference-based text similarity metrics (only available when reference_note exists)
    rouge_l_f_scores = [
        r.scores.get("rouge_l_f") for r in results 
        if r.scores.get("rouge_l_f") is not None
    ]
    bleu_scores = [
        r.scores.get("bleu") for r in results 
        if r.scores.get("bleu") is not None
    ]

    def mean_std(values: List[float]) -> Dict[str, float]:
        if not values:
            return {"mean": 0.0, "std": 0.0}
        return {
            "mean": statistics.mean(values),
            "std": statistics.stdev(values) if len(values) > 1 else 0.0,
        }

    aggregated = {
        "n_examples": n,
        "production_mode": production_mode,
        "error_rates": {
            "missing_critical": {
                "rate": missing_rate,
                "count": missing_critical_count,
                "ci_95": {"lower": missing_ci[0], "upper": missing_ci[1]},
            },
            "hallucination": {
                "rate": hallucination_rate,
                "count": hallucination_count,
                "ci_95": {"lower": hallucination_ci[0], "upper": hallucination_ci[1]},
            },
            "clinical_error": {
                "rate": clinical_error_rate,
                "count": clinical_error_count,
                "ci_95": {"lower": clinical_error_ci[0], "upper": clinical_error_ci[1]},
            },
        },
        "scores": {
            "coverage": mean_std(coverage_scores),
            "faithfulness": mean_std(faithfulness_scores),
            "accuracy": mean_std(accuracy_scores),
            "overall_quality": mean_std(overall_scores),
        },
        "deterministic_metrics": {
            "hallucination_rate_det": mean_std(hallucination_rate_det_scores),
            "structure": mean_std(structure_scores),
            "is_very_short_rate": mean_std(is_very_short_scores),
            "is_too_short_relative_rate": mean_std(is_too_short_relative_scores),
        },
    }
    
    # Only include coverage_det if we have scores (not in production mode)
    if coverage_det_scores:
        aggregated["deterministic_metrics"]["coverage_det"] = mean_std(coverage_det_scores)
    
    # Include reference-based metrics if available (not in production mode)
    if rouge_l_f_scores:
        aggregated["scores"]["rouge_l_f"] = mean_std(rouge_l_f_scores)
    else:
        aggregated["scores"]["rouge_l_f"] = None
    
    if bleu_scores:
        aggregated["scores"]["bleu"] = mean_std(bleu_scores)
    else:
        aggregated["scores"]["bleu"] = None
    
    return aggregated

