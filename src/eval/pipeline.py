"""Main evaluation pipeline combining deterministic and LLM metrics."""

import csv
import json
import logging
import statistics
from pathlib import Path
from typing import List, Dict, Any

try:
    from tqdm import tqdm
except ImportError:
    tqdm = None

from ..config import settings
from ..models import SoapExample, EvalResult, Issue
from .deterministic import (
    has_soap_structure,
    compute_coverage_det,
    compute_hallucination_rate_det,
    compute_rouge_l,
    compute_bleu,
)
from .llm_judge import LLMJudge

logger = logging.getLogger(__name__)


def evaluate_example(
    example: SoapExample, llm_judge: LLMJudge | None = None, use_llm: bool = True
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


def write_jsonl(results: List[EvalResult], examples: List[SoapExample], filepath: Path) -> None:
    """
    Write results to JSONL file, optionally including example data for dashboard.

    Args:
        results: List of EvalResult objects
        examples: List of SoapExample objects (for including full data)
        filepath: Output file path
    """
    with open(filepath, "w", encoding="utf-8") as f:
        # Create a mapping of example_id to example for quick lookup
        example_map = {ex.id: ex for ex in examples}
        
        for result in results:
            result_dict = result.model_dump()
            # Optionally include example data for dashboard viewing
            if result.example_id in example_map:
                ex = example_map[result.example_id]
                result_dict["transcript"] = ex.transcript
                result_dict["reference_note"] = ex.reference_note
                result_dict["generated_note"] = ex.generated_note
            f.write(json.dumps(result_dict) + "\n")


def write_summary_json(aggregated: dict, filepath: Path) -> None:
    """Write aggregated metrics to JSON file."""
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(aggregated, f, indent=2)


def write_summary_csv(aggregated: dict, filepath: Path) -> None:
    """Write aggregated metrics to CSV file."""
    with open(filepath, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["Metric", "Value"])

        # Error rates
        for error_type, data in aggregated.get("error_rates", {}).items():
            writer.writerow([f"{error_type}_rate", data["rate"]])
            writer.writerow([f"{error_type}_count", data["count"]])
            writer.writerow([f"{error_type}_ci_lower", data["ci_95"]["lower"]])
            writer.writerow([f"{error_type}_ci_upper", data["ci_95"]["upper"]])

        # Scores
        for score_type, data in aggregated.get("scores", {}).items():
            if data is not None and isinstance(data, dict):
                writer.writerow([f"{score_type}_mean", data["mean"]])
                writer.writerow([f"{score_type}_std", data["std"]])


def run_evaluation() -> None:
    """
    Run the evaluation pipeline using settings from config.
    
    This function:
    1. Loads examples from the dataset
    2. Optionally corrupts reference notes (if not in production mode)
    3. Evaluates each example
    4. Writes results to output directory
    """
    from ..data_loader import load_omi_examples
    from ..corrupt_note import corrupt_examples

    # Create output directory
    output_dir = Path(settings.OUTPUT_DIR)
    output_dir.mkdir(parents=True, exist_ok=True)

    # Load examples
    logger.info("Loading examples...")
    examples = load_omi_examples(
        split=settings.DATASET_SPLIT,
        n=settings.NUM_EXAMPLES,
        dataset_name=settings.DATASET_NAME,
    )

    # Production mode: set reference_note to None
    if settings.PRODUCTION_MODE:
        logger.info("Production mode: Setting reference_note to None for all examples")
        for example in examples:
            example.reference_note = None
    else:
        # Corrupt notes to simulate generated output (only in non-production mode)
        logger.info("Corrupting reference notes...")
        corrupt_examples(examples, drop_prob=0.35)

    # Initialize LLM judge if requested
    llm_judge = None
    if settings.USE_LLM:
        try:
            llm_judge = LLMJudge()
            logger.info("LLM judge initialized")
        except Exception as e:
            logger.warning(f"Failed to initialize LLM judge: {e}. Using deterministic scores only.")
            # Continue without LLM

    # Evaluate each example
    logger.info("Evaluating examples...")
    results: List[EvalResult] = []

    iterator = examples
    if tqdm:
        iterator = tqdm(examples, desc="Evaluating")

    for example in iterator:
        result = evaluate_example(example, llm_judge, use_llm=settings.USE_LLM)
        results.append(result)

    # Write per-note results
    per_note_path = output_dir / "per_note.jsonl"
    write_jsonl(results, examples, per_note_path)
    logger.info(f"Wrote per-note results to {per_note_path}")

    # Aggregate metrics
    logger.info("Aggregating metrics...")
    aggregated = aggregate_metrics(results, production_mode=settings.PRODUCTION_MODE)

    # Write summary files
    summary_json_path = output_dir / "summary.json"
    write_summary_json(aggregated, summary_json_path)
    logger.info(f"Wrote summary JSON to {summary_json_path}")

    summary_csv_path = output_dir / "summary.csv"
    write_summary_csv(aggregated, summary_csv_path)
    logger.info(f"Wrote summary CSV to {summary_csv_path}")

    # Print summary
    logger.info("\n" + "=" * 60)
    logger.info("EVALUATION SUMMARY")
    logger.info("=" * 60)
    if aggregated.get("production_mode", False):
        logger.info("MODE: PRODUCTION (no reference notes - transcript + generated only)")
    else:
        logger.info("MODE: EVALUATION (with reference notes)")
    logger.info(f"Examples evaluated: {aggregated['n_examples']}")
    logger.info("\nError Rates:")
    for error_type, data in aggregated["error_rates"].items():
        logger.info(
            f"  {error_type}: {data['rate']:.2%} "
            f"(95% CI: {data['ci_95']['lower']:.2%} - {data['ci_95']['upper']:.2%})"
        )
    logger.info("\nAverage Scores:")
    for score_type, data in aggregated["scores"].items():
        if data is not None and isinstance(data, dict):
            logger.info(f"  {score_type}: {data['mean']:.3f} ± {data['std']:.3f}")
    logger.info("=" * 60)

