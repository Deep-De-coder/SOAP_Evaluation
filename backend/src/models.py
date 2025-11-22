"""Data models for SOAP note evaluation."""

from typing import Literal, Optional
from pydantic import BaseModel, Field


class SoapExample(BaseModel):
    """A single example containing transcript and SOAP notes."""

    id: str
    transcript: str = Field(..., description="Doctor-patient dialogue")
    reference_note: Optional[str] = Field(
        None, description="Reference SOAP note from dataset (optional, None in production mode)"
    )
    generated_note: str = Field(..., description="Generated/corrupted SOAP note to evaluate")


class Issue(BaseModel):
    """An identified issue in the generated SOAP note."""

    category: Literal["missing_critical", "hallucination", "clinical_inaccuracy"]
    severity: Literal["minor", "major", "critical"]
    description: str = Field(..., description="Human-readable description of the issue")
    span_model: str | None = Field(
        None, description="Snippet from generated note related to the issue"
    )
    span_source: str | None = Field(
        None, description="Related snippet from transcript or reference note"
    )


class EvalResult(BaseModel):
    """Evaluation result for a single SOAP note example."""

    example_id: str
    issues: list[Issue] = Field(default_factory=list)
    scores: dict[str, float | None] = Field(
        ...,
        description="Scores including coverage, faithfulness, accuracy, overall_quality. Reference-based metrics (rouge_l_f, bleu) may be None in production mode.",
    )

