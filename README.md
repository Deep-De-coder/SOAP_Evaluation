# SOAP Note Evals Suite

A minimal but solid evaluation framework for clinical SOAP notes. This project automatically flags and scores generated SOAP notes against reference notes and transcripts, identifying missing critical findings, hallucinations, and clinical accuracy issues.

## Overview

This evaluation framework assesses the quality of generated SOAP notes by comparing them against:
- **Transcripts**: Original doctor-patient dialogues
- **Reference SOAP notes**: Ground truth SOAP notes from the dataset (optional, not available in production mode)
- **Generated SOAP notes**: Notes to be evaluated (synthetically corrupted for demonstration, or real generated notes in production)

**Two modes:**
- **Evaluation mode** (default): Uses transcript + generated note + reference note for comprehensive evaluation
- **Production mode** (`--production` flag): Uses only transcript + generated note (no reference available)

### Three Error Types Evaluated

1. **Missing Critical Findings** - Important facts present in the reference/transcript but omitted from the generated note
2. **Hallucinated / Unsupported Facts** - Statements in the generated note that are not grounded in the transcript/reference
3. **Clinical Accuracy Issues** - Clinically incorrect or misleading content

## Dataset

We use the Hugging Face dataset **`omi-health/medical-dialogue-to-soap-summary`** as our source of dialogues and SOAP notes. The framework samples the first ~100 examples from the **`test`** split for demonstration purposes.

- The dataset's `dialogue` column provides the doctor-patient transcript
- The dataset's `soap` column provides the reference SOAP note
- Generated notes are created by synthetically corrupting the reference notes (dropping sentences, truncating details) to simulate model output

## Approach

### Two-Layer Evaluation

1. **Deterministic Layer** - Fast, cheap metrics without LLM calls:
   - SOAP structure detection (presence of S:, O:, A:, P: sections)
   - Coverage detection (sentence-level matching between reference and generated notes)
   - Hallucination rate detection (sentences in generated note not found in source)
   - Always computed, regardless of LLM usage

2. **LLM-as-a-Judge Layer** - Nuanced clinical evaluation:
   - Uses OpenAI's GPT-4o-mini (configurable) to review notes
   - Identifies specific issues with categories, severity, and spans
   - Provides detailed scores for coverage, faithfulness, and accuracy

### Metrics

- **Coverage** (0.0-1.0): How well the note covers important facts from the transcript/reference
- **Faithfulness** (0.0-1.0): How closely the note sticks to the transcript/reference (absence of hallucinations)
- **Accuracy** (0.0-1.0): Clinical correctness and safety
- **Overall Quality** (0.0-1.0): Weighted combination (40% coverage + 30% faithfulness + 30% accuracy)

### Use Cases

- **Fast iteration on models**: Quickly identify which generated notes have issues and what types
- **Production quality monitoring**: Track critical error rates over time (e.g., hallucination rate, missing critical findings rate)

## Installation

1. Clone this repository:
```bash
git clone <repository-url>
cd Evals-Suite
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Set up your OpenAI API key:
```bash
export OPENAI_API_KEY=your_api_key_here
```

Or create a `.env` file:
```
OPENAI_API_KEY=your_api_key_here
```

## Usage

### Running the Evaluation

Basic usage (evaluates 100 examples from test split):
```bash
python -m src.run_eval
```

With custom parameters:
```bash
python -m src.run_eval --n 50 --split test --output-dir results
```

Without LLM (uses dummy scores for offline testing):
```bash
python -m src.run_eval --no-llm
```

Production mode (evaluate without reference notes - transcript + generated only):
```bash
python -m src.run_eval --production --n 50
```

### Command-Line Arguments

- `--split`: Dataset split to use (default: "test")
- `--n`: Number of examples to evaluate (default: 100)
- `--output-dir`: Output directory for results (default: "results")
- `--use-llm`: Use LLM judge (default: True)
- `--no-llm`: Disable LLM judge (use dummy scores)
- `--production`: Production mode - evaluate without reference notes (transcript + generated only)

### Output Files

The evaluation generates three output files in the `results/` directory:

1. **`per_note.jsonl`**: One JSON object per evaluated note, containing:
   - Example ID
   - List of identified issues (category, severity, description, spans)
   - Scores (coverage, faithfulness, accuracy, overall_quality)

2. **`summary.json`**: Aggregated dataset-level metrics:
   - Error rates (missing_critical, hallucination, clinical_error) with 95% confidence intervals
   - Mean scores and standard deviations for all metrics

3. **`summary.csv`**: Same aggregated metrics in CSV format for easy analysis

### Example Output

```json
{
  "n_examples": 100,
  "error_rates": {
    "missing_critical": {
      "rate": 0.45,
      "count": 45,
      "ci_95": {"lower": 0.35, "upper": 0.55}
    },
    "hallucination": {
      "rate": 0.12,
      "count": 12,
      "ci_95": {"lower": 0.07, "upper": 0.20}
    },
    "clinical_error": {
      "rate": 0.08,
      "count": 8,
      "ci_95": {"lower": 0.04, "upper": 0.15}
    }
  },
  "scores": {
    "coverage": {"mean": 0.72, "std": 0.15},
    "faithfulness": {"mean": 0.88, "std": 0.12},
    "accuracy": {"mean": 0.85, "std": 0.10},
    "overall_quality": {"mean": 0.80, "std": 0.11}
  }
}
```

## Interpreting the Metrics

### Example Evaluation Result

```json
{
  "example_id": "42",
  "issues": [
    {
      "category": "missing_critical",
      "severity": "major",
      "description": "Missing mention of patient's allergy to penicillin",
      "span_model": null,
      "span_source": "Patient reports allergy to penicillin"
    },
    {
      "category": "hallucination",
      "severity": "minor",
      "description": "Generated note mentions 'blood pressure 120/80' but this is not in transcript",
      "span_model": "Blood pressure: 120/80",
      "span_source": null
    }
  ],
  "scores": {
    "coverage": 0.65,
    "faithfulness": 0.90,
    "accuracy": 0.85,
    "overall_quality": 0.78
  }
}
```

**Interpretation:**
- **Coverage (0.65)**: The note misses some important information (e.g., penicillin allergy)
- **Faithfulness (0.90)**: Mostly faithful to source, but has one hallucination
- **Accuracy (0.85)**: Generally clinically accurate
- **Overall Quality (0.78)**: Weighted average indicating decent but improvable quality

## Dashboard

A Streamlit dashboard provides an interactive way to explore evaluation results:

### Running the Dashboard

```bash
streamlit run dashboard/app.py
```

The dashboard will automatically open in your browser. It provides:

- **Summary Metrics**: Key statistics at a glance
- **Interactive Charts**: Distribution of scores and metrics
- **Per-Note Explorer**: Filter and drill down into individual notes
- **Sidebar Filters**: Filter by quality range, issue types, and more

### Dashboard Features

1. **Summary Cards**: Overview of evaluation metrics
2. **Charts**: 
   - Histogram of overall quality scores
   - Bar chart of mean coverage/faithfulness/accuracy
3. **Per-Note Details**: 
   - View transcript, reference note, and generated note
   - See all issues with severity indicators
   - Compare deterministic vs LLM scores

## Analysis Notebook

The `notebooks/analysis.ipynb` notebook provides:
- Histogram of overall quality scores
- Scatter plot of coverage vs faithfulness
- Examples of the worst 5 notes by overall quality with their issues
- Issue category distribution

To run:
```bash
jupyter notebook notebooks/analysis.ipynb
```

## Project Structure

```
Evals-Suite/
├── src/
│   ├── __init__.py
│   ├── models.py          # Pydantic models for examples and eval results
│   ├── data_loader.py     # Load and prepare OMI Health dataset
│   ├── corrupt_note.py    # Utilities to generate "generated" notes by corrupting reference
│   ├── llm_judges.py      # Wrapper around OpenAI Chat Completions API
│   ├── metrics.py         # Core metric computation
│   └── run_eval.py        # CLI script to run evaluation
├── notebooks/
│   └── analysis.ipynb     # Analysis and visualization
├── results/               # Created at runtime; holds output files
├── README.md
└── requirements.txt
```

## Limitations & Future Work

### Current Limitations

- **Synthetic Data**: Generated notes are created by corrupting reference notes, not from actual model outputs
- **LLM Judge Bias**: The LLM-as-a-judge approach may have biases and inconsistencies
- **Not for Clinical Decision-Making**: This is a research/demonstration tool, not validated for real clinical use
- **Limited Dataset**: Only uses 100 examples from test split for demonstration
- **Single LLM Provider**: Currently only supports OpenAI (though architecture allows extension)

### Future Improvements

- Support for actual model-generated notes (not just corrupted references)
- Multiple LLM judge providers (Anthropic, local models, etc.)
- More sophisticated deterministic metrics (entity extraction, semantic similarity)
- Human-in-the-loop validation of LLM judge outputs
- Support for custom evaluation criteria and prompts
- Integration with production monitoring systems
- Expanded dataset coverage and cross-validation

## Requirements

- Python 3.11+
- See `requirements.txt` for package dependencies

## License

[Add your license here]

## Contributing

[Add contribution guidelines if applicable]
