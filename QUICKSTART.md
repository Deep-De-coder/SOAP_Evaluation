# Quick Start Guide

## Step 1: Install Dependencies

```bash
pip install -r requirements.txt
```

## Step 2: Set Up OpenAI API Key

You have two options:

### Option A: Environment Variable (Recommended)
```bash
# Windows PowerShell
$env:OPENAI_API_KEY="your-api-key-here"

# Windows CMD
set OPENAI_API_KEY=your-api-key-here

# Linux/Mac
export OPENAI_API_KEY=your-api-key-here
```

### Option B: Create .env File
Create a `.env` file in the project root:
```
OPENAI_API_KEY=your-api-key-here
```

## Step 3: Run the Evaluation

### Basic Usage (100 examples with LLM)
```bash
python -m src.run_eval
```

### Custom Number of Examples
```bash
python -m src.run_eval --n 50
```

### Test Without LLM (Uses Dummy Scores)
```bash
python -m src.run_eval --no-llm
```

### Full Options
```bash
python -m src.run_eval --split test --n 100 --output-dir results --use-llm
```

## Step 4: View Results

Results will be saved in the `results/` directory:
- `per_note.jsonl` - Individual evaluation results
- `summary.json` - Aggregated metrics
- `summary.csv` - Aggregated metrics in CSV format

## Step 5: Analyze Results (Optional)

Open the Jupyter notebook:
```bash
jupyter notebook notebooks/analysis.ipynb
```

Or if using VS Code, just open the notebook file directly.

## Troubleshooting

### If you get "ModuleNotFoundError"
Make sure you're running from the project root directory:
```bash
cd "C:\Users\esote\Downloads\Git Project\Evals-Suite"
python -m src.run_eval
```

### If you get "OPENAI_API_KEY not set"
Make sure you've set the environment variable or created a `.env` file.

### If you want to test without API calls
Use the `--no-llm` flag to generate dummy scores for testing.

