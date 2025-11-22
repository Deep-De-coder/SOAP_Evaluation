# SOAP Note Evaluation Framework

A monorepo containing a hybrid deterministic + LLM evaluation framework for clinical SOAP notes, with a React dashboard for visualization.

## Monorepo Structure

```
SOAP_Evaluation/
├── backend/          # Python/FastAPI backend (deploy to Render)
│   ├── src/          # Python source code
│   ├── requirements.txt
│   ├── Dockerfile    # For Render deployment
│   └── .env.example  # Backend environment variables
├── frontend/         # React dashboard (deploy to Vercel)
│   ├── src/          # React source code
│   ├── package.json
│   └── .env.local.example  # Frontend environment variables
└── README.md
```

## Overview

This evaluation framework assesses the quality of generated SOAP notes by comparing them against:
- **Transcripts**: Original doctor-patient dialogues
- **Reference SOAP notes**: Ground truth SOAP notes from the dataset (optional, not available in production mode)
- **Generated SOAP notes**: Notes to be evaluated

**Two modes:**
- **Evaluation mode** (default): Uses transcript + generated note + reference note for comprehensive evaluation
- **Production mode**: Uses only transcript + generated note (no reference available)

### Three Error Types Evaluated

1. **Missing Critical Findings** - Important facts present in the reference/transcript but omitted from the generated note
2. **Hallucinated / Unsupported Facts** - Statements in the generated note that are not grounded in the transcript/reference
3. **Clinical Accuracy Issues** - Clinically incorrect or misleading content

## Dataset

We use the Hugging Face dataset **`omi-health/medical-dialogue-to-soap-summary`** as our source of dialogues and SOAP notes.

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

## Local Development

### Prerequisites

- Python 3.11+
- Node.js 18+
- OpenAI API key (for LLM evaluation)

### Backend Setup

1. **Navigate to backend directory:**
```bash
cd backend
```

2. **Set up environment variables:**
```bash
cp .env.example .env
# Edit .env and set your OPENAI_API_KEY and other configuration
```

3. **Install dependencies:**
```bash
pip install -r requirements.txt
```

4. **Run evaluation:**
```bash
python -m src.run_eval_env
```

5. **Start the API server:**
```bash
uvicorn src.api.app:app --reload --host 0.0.0.0 --port 8000
```

The backend API will be available at `http://localhost:8000`

### Frontend Setup

1. **Navigate to frontend directory:**
```bash
cd frontend
```

2. **Set up environment variables:**
```bash
cp .env.local.example .env.local
# Edit .env.local if needed (defaults to http://localhost:8000)
```

3. **Install dependencies:**
```bash
npm install
```

4. **Start the development server:**
```bash
npm run dev
```

The frontend will be available at `http://localhost:5173`

## Deployment

### Backend Deployment (Render)

1. **Create a new Web Service on Render:**
   - Connect your GitHub repository
   - Set **Root Directory** to `backend`
   - Choose **Docker** as the build method (or use the Dockerfile)

2. **Set environment variables in Render dashboard:**
   Copy from `backend/.env.example`:
   - `USE_LLM=true`
   - `NUM_EXAMPLES=50`
   - `PRODUCTION_MODE=false`
   - `DATASET_NAME=omi-health/medical-dialogue-to-soap-summary`
   - `DATASET_SPLIT=test`
   - `BACKEND_PORT=8000`
   - `FRONTEND_ORIGIN=https://your-frontend.vercel.app` (set after deploying frontend)
   - `OPENAI_API_KEY=your_key_here`
   - `OPENAI_MODEL=gpt-4o-mini`
   - `OPENAI_TEMPERATURE=0.0`
   - `OUTPUT_DIR=results`

3. **Deploy:**
   - Render will build the Docker image
   - On container start, it runs evaluation then starts the API server
   - Note the HTTPS URL (e.g., `https://your-backend.onrender.com`)

### Frontend Deployment (Vercel)

1. **Create a new Vercel project:**
   - Connect your GitHub repository
   - Set **Root Directory** to `frontend`
   - Framework Preset: Vite

2. **Set environment variables in Vercel dashboard:**
   - `VITE_API_BASE_URL=https://your-backend.onrender.com` (use your Render backend URL)

3. **Build settings (should auto-detect):**
   - Build Command: `npm run build`
   - Output Directory: `dist`
   - Install Command: `npm install`

4. **Deploy:**
   - Vercel will build and deploy the React app
   - Note the Vercel URL (e.g., `https://your-app.vercel.app`)

5. **Update backend CORS:**
   - Go back to Render dashboard
   - Update `FRONTEND_ORIGIN` to your Vercel URL (e.g., `https://your-app.vercel.app`)
   - Redeploy the backend if needed

## Configuration

### Backend Environment Variables

All backend configuration is in `backend/.env` (or set via Render dashboard):

- `USE_LLM`: Enable/disable LLM judge (true/false)
- `NUM_EXAMPLES`: Number of examples to evaluate
- `PRODUCTION_MODE`: Production mode - no reference notes (true/false)
- `DATASET_NAME`: Hugging Face dataset name
- `DATASET_SPLIT`: Dataset split to use (default: "test")
- `OPENAI_API_KEY`: Your OpenAI API key
- `OPENAI_MODEL`: OpenAI model to use (default: "gpt-4o-mini")
- `OPENAI_TEMPERATURE`: Temperature for LLM (default: 0.0)
- `BACKEND_PORT`: Backend API port (default: 8000)
- `FRONTEND_ORIGIN`: Frontend origin for CORS (comma-separated for multiple origins)
- `OUTPUT_DIR`: Output directory for results (default: "results")

### Frontend Environment Variables

Frontend configuration in `frontend/.env.local` (or set via Vercel dashboard):

- `VITE_API_BASE_URL`: Backend API base URL (default: "http://localhost:8000")

## API Endpoints

The backend provides the following endpoints:

- `GET /api/summary` - Get evaluation summary statistics
- `GET /api/notes` - Get list of notes with optional filtering
  - Query params: `min_quality`, `max_quality`, `hallucination_only`, `missing_critical_only`, `major_issues_only`
- `GET /api/notes/{example_id}` - Get detailed information for a specific note

## Output Files

After running evaluation, results are written to `backend/results/`:

- `per_note.jsonl` - One JSON object per line with detailed results for each note
- `summary.json` - Aggregated metrics and statistics
- `summary.csv` - Same aggregated metrics in CSV format

## CORS Configuration

The backend uses CORS middleware to allow requests from the frontend. The `FRONTEND_ORIGIN` environment variable controls which origins are allowed. For production:

- Set `FRONTEND_ORIGIN` to your Vercel app URL (e.g., `https://your-app.vercel.app`)
- Multiple origins can be comma-separated: `https://app1.vercel.app,https://app2.vercel.app`
