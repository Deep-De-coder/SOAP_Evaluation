"""LLM-as-a-judge wrapper for evaluating SOAP notes."""

import json
import logging
from typing import Dict, Any

try:
    from openai import OpenAI
except ImportError:
    OpenAI = None

from ..config import settings
from ..models import Issue

logger = logging.getLogger(__name__)


class LLMJudge:
    """Wrapper around OpenAI Chat Completions API for SOAP note evaluation."""

    def __init__(
        self,
        model: str | None = None,
        temperature: float | None = None,
        api_key: str | None = None,
    ):
        """
        Initialize the LLM judge.

        Args:
            model: OpenAI model name (defaults to settings.OPENAI_MODEL)
            temperature: Sampling temperature (defaults to settings.OPENAI_TEMPERATURE)
            api_key: OpenAI API key (defaults to settings.OPENAI_API_KEY)
        """
        if OpenAI is None:
            raise ImportError(
                "openai package is required. Install with: pip install openai"
            )

        api_key = api_key or settings.OPENAI_API_KEY
        if not api_key:
            raise ValueError(
                "OPENAI_API_KEY not set. Please set it in .env or pass as argument."
            )

        self.client = OpenAI(api_key=api_key)
        self.model = model or settings.OPENAI_MODEL
        self.temperature = temperature if temperature is not None else settings.OPENAI_TEMPERATURE

    def _parse_llm_json(self, response_text: str) -> Dict[str, Any]:
        """
        Parse JSON from LLM response, handling code fences and retrying on errors.

        Args:
            response_text: Raw text response from LLM

        Returns:
            Parsed JSON dictionary
        """
        # Strip code fences if present
        text = response_text.strip()
        if text.startswith("```"):
            # Remove opening and closing code fences
            lines = text.split("\n")
            if lines[0].startswith("```"):
                lines = lines[1:]
            if lines and lines[-1].strip() == "```":
                lines = lines[:-1]
            text = "\n".join(lines)

        try:
            return json.loads(text)
        except json.JSONDecodeError as e:
            logger.warning(f"Failed to parse JSON: {e}. Response: {text[:200]}")
            raise ValueError(f"Invalid JSON response from LLM: {e}")

    def review(
        self, transcript: str, generated_note: str, reference_note: str | None = None
    ) -> Dict[str, Any]:
        """
        Call the LLM to review a generated SOAP note against transcript and optionally reference.

        Args:
            transcript: Doctor-patient dialogue
            generated_note: Generated SOAP note to evaluate
            reference_note: Reference SOAP note for comparison (optional, None in production mode)

        Returns:
            Dictionary with "issues" (list) and "scores" (dict) keys
        """
        if reference_note is not None:
            # Evaluation mode: with reference note
            prompt = f"""You are evaluating a clinical SOAP note generated from a doctor-patient dialogue.

TRANSCRIPT (doctor-patient dialogue):
{transcript}

REFERENCE SOAP NOTE (ground truth):
{reference_note}

GENERATED SOAP NOTE (to evaluate):
{generated_note}

Please evaluate the generated SOAP note and provide:

1. A list of issues found, where each issue has:
   - category: one of "missing_critical", "hallucination", or "clinical_inaccuracy"
     * "missing_critical": Important facts from transcript/reference that are missing
     * "hallucination": Statements in generated note not supported by transcript/reference
     * "clinical_inaccuracy": Clinically incorrect or misleading content
   - severity: one of "minor", "major", or "critical"
   - description: Clear description of the issue
   - span_model: Relevant snippet from generated note (or null)
   - span_source: Related snippet from transcript/reference (or null)

2. Scores (0.0 to 1.0) for:
   - coverage: How well the note covers important facts from transcript/reference
   - faithfulness: How closely it sticks to the transcript/reference (no hallucinations)
   - accuracy: Clinical correctness and safety

Return ONLY valid JSON in this exact format:
{{
  "issues": [
    {{
      "category": "missing_critical",
      "severity": "major",
      "description": "...",
      "span_model": "...",
      "span_source": "..."
    }}
  ],
  "scores": {{
    "coverage": 0.75,
    "faithfulness": 0.90,
    "accuracy": 0.85
  }}
}}

Return valid JSON only, no additional text."""
        else:
            # Production mode: no reference note, evaluate only against transcript
            prompt = f"""You are evaluating a clinical SOAP note generated from a doctor-patient dialogue in production mode (no reference note available).

TRANSCRIPT (doctor-patient dialogue):
{transcript}

GENERATED SOAP NOTE (to evaluate):
{generated_note}

Please evaluate the generated SOAP note against ONLY the transcript and provide:

1. A list of issues found, where each issue has:
   - category: one of "missing_critical", "hallucination", or "clinical_inaccuracy"
     * "missing_critical": Important facts from transcript that are missing in the generated note
     * "hallucination": Statements in generated note not supported by the transcript
     * "clinical_inaccuracy": Clinically incorrect or misleading content
   - severity: one of "minor", "major", or "critical"
   - description: Clear description of the issue
   - span_model: Relevant snippet from generated note (or null)
   - span_source: Related snippet from transcript (or null)

2. Scores (0.0 to 1.0) for:
   - coverage: How well the note covers important facts from the transcript
   - faithfulness: How closely it sticks to the transcript (no hallucinations)
   - accuracy: Clinical correctness and safety

Return ONLY valid JSON in this exact format:
{{
  "issues": [
    {{
      "category": "missing_critical",
      "severity": "major",
      "description": "...",
      "span_model": "...",
      "span_source": "..."
    }}
  ],
  "scores": {{
    "coverage": 0.75,
    "faithfulness": 0.90,
    "accuracy": 0.85
  }}
}}

Return valid JSON only, no additional text."""

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are a clinical evaluation expert. Always return valid JSON.",
                    },
                    {"role": "user", "content": prompt},
                ],
                temperature=self.temperature,
            )

            response_text = response.choices[0].message.content
            result = self._parse_llm_json(response_text)

            # Validate structure
            if "issues" not in result or "scores" not in result:
                raise ValueError("LLM response missing 'issues' or 'scores' keys")

            # Convert issues to Issue objects for validation
            issues = []
            for issue_dict in result.get("issues", []):
                try:
                    issue = Issue(**issue_dict)
                    issues.append(issue)
                except Exception as e:
                    logger.warning(f"Invalid issue format: {issue_dict}, error: {e}")

            result["issues"] = issues
            return result

        except Exception as e:
            logger.error(f"Error calling LLM: {e}")
            # Return empty result to indicate LLM failure - pipeline will use deterministic scores
            return {
                "issues": [],
                "scores": {},  # Empty scores - pipeline will use deterministic fallback
            }

