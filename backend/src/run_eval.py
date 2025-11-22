"""CLI script to run SOAP note evaluation."""

import argparse
import json
import logging
import os
from pathlib import Path
from typing import List

try:
    from tqdm import tqdm
except ImportError:
    tqdm = None

try:
    from dotenv import load_dotenv
    # Load .env file from project root
    env_path = Path(__file__).parent.parent / ".env"
    if env_path.exists():
        load_dotenv(dotenv_path=str(env_path), override=True)
    else:
        load_dotenv(override=True)
except ImportError:
    pass

from .data_loader import load_omi_examples
from .corrupt_note import corrupt_examples
from .llm_judges import LLMJudge
from .metrics import compute_case_metrics, aggregate_metrics
from .models import EvalResult, SoapExample

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


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
    import csv

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
            writer.writerow([f"{score_type}_mean", data["mean"]])
            writer.writerow([f"{score_type}_std", data["std"]])


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Evaluate SOAP notes using LLM-as-a-judge"
    )
    parser.add_argument(
        "--split",
        type=str,
        default="test",
        help="Dataset split to use (default: test)",
    )
    parser.add_argument(
        "--n",
        type=int,
        default=100,
        help="Number of examples to evaluate (default: 100)",
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default="results",
        help="Output directory for results (default: results)",
    )
    parser.add_argument(
        "--use-llm",
        action="store_true",
        default=True,
        help="Use LLM judge (default: True)",
    )
    parser.add_argument(
        "--no-llm",
        dest="use_llm",
        action="store_false",
        help="Disable LLM judge (use dummy scores)",
    )
    parser.add_argument(
        "--production",
        action="store_true",
        help="Production mode: evaluate without reference notes (transcript + generated only)",
    )

    args = parser.parse_args()

    # Create output directory
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    # Load examples
    logger.info("Loading examples...")
    examples = load_omi_examples(split=args.split, n=args.n)

    # Production mode: set reference_note to None
    if args.production:
        logger.info("Production mode: Setting reference_note to None for all examples")
        for example in examples:
            example.reference_note = None
    else:
        # Corrupt notes to simulate generated output (only in non-production mode)
        logger.info("Corrupting reference notes...")
        corrupt_examples(examples, drop_prob=0.35)

    # Initialize LLM judge if requested
    llm_judge = None
    if args.use_llm:
        try:
            llm_judge = LLMJudge()
            logger.info("LLM judge initialized")
        except Exception as e:
            logger.warning(f"Failed to initialize LLM judge: {e}. Using dummy scores.")
            args.use_llm = False

    # Evaluate each example
    logger.info("Evaluating examples...")
    results: List[EvalResult] = []

    iterator = examples
    if tqdm:
        iterator = tqdm(examples, desc="Evaluating")

    for example in iterator:
        result = compute_case_metrics(example, llm_judge, use_llm=args.use_llm)
        results.append(result)

    # Write per-note results
    per_note_path = output_dir / "per_note.jsonl"
    write_jsonl(results, examples, per_note_path)
    logger.info(f"Wrote per-note results to {per_note_path}")

    # Aggregate metrics
    logger.info("Aggregating metrics...")
    aggregated = aggregate_metrics(results, production_mode=args.production)

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
        logger.info(f"  {score_type}: {data['mean']:.3f} ± {data['std']:.3f}")
    logger.info("=" * 60)


if __name__ == "__main__":
    main()

