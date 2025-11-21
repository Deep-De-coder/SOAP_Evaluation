"""Evaluation modules for SOAP note evaluation."""

from .deterministic import (
    has_soap_structure,
    compute_coverage_det,
    compute_hallucination_rate_det,
    compute_rouge_l,
    compute_bleu,
)
from .llm_judge import LLMJudge
from .pipeline import evaluate_example, run_evaluation, aggregate_metrics

__all__ = [
    "has_soap_structure",
    "compute_coverage_det",
    "compute_hallucination_rate_det",
    "compute_rouge_l",
    "compute_bleu",
    "LLMJudge",
    "evaluate_example",
    "run_evaluation",
    "aggregate_metrics",
]

