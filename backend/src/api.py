"""FastAPI backend for SOAP note evaluation results."""

import json
from pathlib import Path
from typing import List, Optional, Dict, Any

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# Constants
RESULTS_DIR = Path(__file__).parent.parent / "results"
PER_NOTE_PATH = RESULTS_DIR / "per_note.jsonl"
SUMMARY_PATH = RESULTS_DIR / "summary.json"

# FastAPI app
app = FastAPI(
    title="SOAP Note Evaluation API",
    description="API for accessing SOAP note evaluation results",
    version="1.0.0",
)

# CORS middleware for React frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],  # Vite default, CRA default
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Pydantic models for API responses
class IssueResponse(BaseModel):
    category: str
    severity: str
    description: str
    span_model: Optional[str] = None
    span_source: Optional[str] = None


class NoteListItem(BaseModel):
    example_id: str
    overall_quality: float
    coverage: float
    faithfulness: float
    accuracy: float
    structure_score: float
    has_hallucination: bool
    has_missing_critical: bool
    has_major_issue: bool
    rouge_l_f: Optional[float] = None
    bleu: Optional[float] = None


class NoteDetail(BaseModel):
    example_id: str
    transcript: Optional[str] = None
    reference_note: Optional[str] = None
    generated_note: Optional[str] = None
    scores: Dict[str, float]
    issues: List[IssueResponse]


def load_summary() -> Dict[str, Any]:
    """Load summary.json file."""
    if not SUMMARY_PATH.exists():
        raise HTTPException(
            status_code=404,
            detail=f"Summary file not found at {SUMMARY_PATH}. Please run the evaluation CLI first.",
        )
    with open(SUMMARY_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def load_all_notes() -> List[Dict[str, Any]]:
    """Load all notes from per_note.jsonl file."""
    if not PER_NOTE_PATH.exists():
        raise HTTPException(
            status_code=404,
            detail=f"Per-note results file not found at {PER_NOTE_PATH}. Please run the evaluation CLI first.",
        )
    notes = []
    with open(PER_NOTE_PATH, "r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                notes.append(json.loads(line))
    return notes


def has_issue_category(result: Dict[str, Any], category: str) -> bool:
    """Check if result has an issue of the given category."""
    return any(issue.get("category") == category for issue in result.get("issues", []))


def has_major_or_critical_issue(result: Dict[str, Any]) -> bool:
    """Check if result has a major or critical issue."""
    return any(
        issue.get("severity") in ["major", "critical"]
        for issue in result.get("issues", [])
    )


@app.get("/api/summary")
def get_summary() -> Dict[str, Any]:
    """Get evaluation summary statistics."""
    return load_summary()


@app.get("/api/notes", response_model=List[NoteListItem])
def get_notes(
    min_quality: Optional[float] = None,
    max_quality: Optional[float] = None,
    hallucination_only: bool = False,
    missing_critical_only: bool = False,
    major_issues_only: bool = False,
) -> List[NoteListItem]:
    """
    Get list of notes with optional filtering.
    
    Query parameters:
    - min_quality: Minimum overall quality score (0.0-1.0)
    - max_quality: Maximum overall quality score (0.0-1.0)
    - hallucination_only: Only return notes with hallucinations
    - missing_critical_only: Only return notes with missing critical findings
    - major_issues_only: Only return notes with major/critical issues
    """
    all_notes = load_all_notes()
    
    # Apply filters
    filtered = all_notes
    
    if min_quality is not None:
        filtered = [
            n for n in filtered
            if n.get("scores", {}).get("overall_quality", 0.0) >= min_quality
        ]
    
    if max_quality is not None:
        filtered = [
            n for n in filtered
            if n.get("scores", {}).get("overall_quality", 0.0) <= max_quality
        ]
    
    if hallucination_only:
        filtered = [n for n in filtered if has_issue_category(n, "hallucination")]
    
    if missing_critical_only:
        filtered = [n for n in filtered if has_issue_category(n, "missing_critical")]
    
    if major_issues_only:
        filtered = [n for n in filtered if has_major_or_critical_issue(n)]
    
    # Convert to response model
    result = []
    for note in filtered:
        scores = note.get("scores", {})
        result.append(
            NoteListItem(
                example_id=note.get("example_id", ""),
                overall_quality=scores.get("overall_quality", 0.0),
                coverage=scores.get("coverage", 0.0),
                faithfulness=scores.get("faithfulness", 0.0),
                accuracy=scores.get("accuracy", 0.0),
                structure_score=scores.get("structure", 0.0),
                has_hallucination=has_issue_category(note, "hallucination"),
                has_missing_critical=has_issue_category(note, "missing_critical"),
                has_major_issue=has_major_or_critical_issue(note),
                rouge_l_f=scores.get("rouge_l_f"),
                bleu=scores.get("bleu"),
            )
        )
    
    return result


@app.get("/api/notes/{example_id}", response_model=NoteDetail)
def get_note_detail(example_id: str) -> NoteDetail:
    """Get detailed information for a specific note."""
    all_notes = load_all_notes()
    
    # Find the note
    note = next((n for n in all_notes if n.get("example_id") == example_id), None)
    
    if note is None:
        raise HTTPException(status_code=404, detail=f"Note with ID '{example_id}' not found")
    
    # Convert issues
    issues = [
        IssueResponse(
            category=issue.get("category", ""),
            severity=issue.get("severity", ""),
            description=issue.get("description", ""),
            span_model=issue.get("span_model"),
            span_source=issue.get("span_source"),
        )
        for issue in note.get("issues", [])
    ]
    
    return NoteDetail(
        example_id=note.get("example_id", ""),
        transcript=note.get("transcript"),
        reference_note=note.get("reference_note"),
        generated_note=note.get("generated_note"),
        scores=note.get("scores", {}),
        issues=issues,
    )


@app.get("/")
def root():
    """Root endpoint with API information."""
    return {
        "message": "SOAP Note Evaluation API",
        "version": "1.0.0",
        "endpoints": {
            "summary": "/api/summary",
            "notes": "/api/notes",
            "note_detail": "/api/notes/{example_id}",
        },
    }

