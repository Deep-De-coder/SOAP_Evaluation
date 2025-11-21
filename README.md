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

## Quick Start (Docker - Recommended)

The easiest way to run the entire system is using Docker Compose:

1. **Clone the repository:**
```bash
git clone <repository-url>
cd SOAP_Evaluation
```

2. **Set up environment variables:**
```bash
cp .env.example .env
# Edit .env and set your OPENAI_API_KEY and other configuration
```

3. **Run everything with Docker:**
```bash
docker-compose up --build
```

This will:
- Build the backend and frontend containers
- Run the evaluation using settings from `.env`
- Start the FastAPI backend on `http://localhost:8000`
- Start the React frontend on `http://localhost:5173`

4. **Access the dashboard:**
Open your browser to `http://localhost:5173`

### Configuration

All configuration is done via environment variables in the `.env` file. See `.env.example` for all available options:

- `USE_LLM`: Enable/disable LLM judge (true/false)
- `NUM_EXAMPLES`: Number of examples to evaluate
- `PRODUCTION_MODE`: Production mode - no reference notes (true/false)
- `DATASET_SPLIT`: Dataset split to use (default: "test")
- `OPENAI_API_KEY`: Your OpenAI API key
- `BACKEND_PORT`: Backend API port (default: 8000)
- `FRONTEND_PORT`: Frontend port (default: 5173)

## Manual Installation (Without Docker)

If you prefer to run without Docker:

1. **Install Python dependencies:**
```bash
pip install -r requirements.txt
```

2. **Install frontend dependencies:**
```bash
cd frontend
npm install
```

3. **Set up environment variables:**
```bash
cp .env.example .env
# Edit .env with your configuration
```

4. **Run evaluation:**
```bash
python -m src.run_eval_env
```

5. **Start backend:**
```bash
uvicorn src.api.app:app --reload
```

6. **Start frontend (in another terminal):**
```bash
cd frontend
npm run dev
```

## Usage

### Environment-Based Configuration

All configuration is now done via environment variables in `.env`, not CLI flags:

- `USE_LLM=true/false` - Enable/disable LLM judge
- `NUM_EXAMPLES=50` - Number of examples to evaluate
- `PRODUCTION_MODE=true/false` - Production mode (no reference notes)
- `DATASET_SPLIT=test` - Dataset split to use
- `OUTPUT_DIR=results` - Output directory for results

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

A modern React + FastAPI dashboard provides an interactive way to explore evaluation results.

### Architecture

- **Backend**: FastAPI REST API (`src/api/app.py`) that serves evaluation results
- **Frontend**: React + TypeScript + Vite application with Tailwind CSS

### Running the Dashboard

**With Docker (Recommended):**
```bash
docker-compose up --build
```

**Manually:**

1. Run evaluation (if not already done):
```bash
python -m src.run_eval_env
```

2. Start the backend:
```bash
uvicorn src.api.app:app --host 0.0.0.0 --port 8000
```

3. Start the frontend:
```bash
cd frontend
npm install
npm run dev
```

The dashboard will be available at `http://localhost:5173` and will connect to the backend API.

### Dashboard Features

1. **Summary Metrics View**: 
   - Overview cards showing key statistics (notes evaluated, mean scores, error rates)
   - Clean, responsive grid layout

2. **Notes List with Filters**:
   - Filter by overall quality range (slider)
   - Filter by issue types (checkboxes for hallucinations, missing critical findings, major issues)
   - Sortable table with key metrics
   - Status badges for quick identification of issues

3. **Note Detail View**:
   - Complete scores breakdown
   - Issues grouped by category with severity indicators
   - Expandable sections for transcript, reference note, and generated note
   - Clean, readable layout with proper typography

### API Endpoints

The FastAPI backend exposes the following endpoints:

- `GET /api/summary` - Get aggregated evaluation summary
- `GET /api/notes` - Get list of notes with optional filtering (query parameters: `min_quality`, `max_quality`, `hallucination_only`, `missing_critical_only`, `major_issues_only`)
- `GET /api/notes/{example_id}` - Get detailed information for a specific note

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
SOAP_Evaluation/
├── src/
│   ├── __init__.py
│   ├── config.py          # Central configuration (Pydantic BaseSettings)
│   ├── models.py          # Pydantic models for examples and eval results
│   ├── data_loader.py     # Load and prepare OMI Health dataset
│   ├── corrupt_note.py    # Utilities to generate "generated" notes by corrupting reference
│   ├── run_eval_env.py    # Environment-driven evaluation entrypoint
│   ├── eval/              # Evaluation modules
│   │   ├── __init__.py
│   │   ├── deterministic.py  # Deterministic metrics (structure, coverage, ROUGE, BLEU)
│   │   ├── llm_judge.py      # LLM-as-a-judge wrapper
│   │   └── pipeline.py       # Main evaluation pipeline
│   └── api/               # API module
│       ├── __init__.py
│       └── app.py         # FastAPI backend for serving results
├── frontend/
│   ├── src/
│   │   ├── components/    # React components
│   │   ├── api.ts         # API client functions
│   │   ├── App.tsx        # Main application component
│   │   └── main.tsx       # Entry point
│   ├── Dockerfile         # Frontend Docker image
│   ├── package.json
│   └── vite.config.ts
├── notebooks/
│   └── analysis.ipynb     # Analysis and visualization
├── results/               # Created at runtime; holds output files
├── Dockerfile.backend     # Backend Docker image
├── docker-compose.yml     # Docker Compose configuration
├── .env.example           # Example environment variables
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
