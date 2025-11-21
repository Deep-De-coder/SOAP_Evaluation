"""Streamlit dashboard for SOAP note evaluation results."""

import json
import sys
from pathlib import Path
from typing import Dict, List, Any

import streamlit as st
import pandas as pd

try:
    import plotly.express as px
    PLOTLY_AVAILABLE = True
except ImportError:
    PLOTLY_AVAILABLE = False
    px = None

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

# Page config
st.set_page_config(
    page_title="SOAP Note Evaluation Dashboard",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Constants
RESULTS_DIR = Path(__file__).parent.parent / "results"
PER_NOTE_PATH = RESULTS_DIR / "per_note.jsonl"
SUMMARY_PATH = RESULTS_DIR / "summary.json"


@st.cache_data(ttl=1)  # Cache for 1 second to allow refresh
def load_results() -> tuple[List[Dict[str, Any]], Dict[str, Any] | None]:
    """
    Load evaluation results from JSONL and summary JSON files.

    Returns:
        Tuple of (list of per-note results, summary dict or None)
    """
    results = []
    summary = None

    if PER_NOTE_PATH.exists():
        with open(PER_NOTE_PATH, "r", encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    results.append(json.loads(line))
    else:
        return [], None

    if SUMMARY_PATH.exists():
        with open(SUMMARY_PATH, "r", encoding="utf-8") as f:
            summary = json.load(f)

    return results, summary


def has_issue_category(result: Dict[str, Any], category: str) -> bool:
    """Check if result has an issue of the given category."""
    return any(issue.get("category") == category for issue in result.get("issues", []))


def has_major_or_critical_issue(result: Dict[str, Any]) -> bool:
    """Check if result has a major or critical issue."""
    return any(
        issue.get("severity") in ["major", "critical"]
        for issue in result.get("issues", [])
    )


def main():
    """Main dashboard application."""
    st.title("📊 SOAP Note Evaluation Dashboard")
    st.markdown("Explore evaluation results for generated SOAP notes")

    # Load data
    results, summary = load_results()

    if not results or summary is None:
        st.warning(
            "⚠️ No results found. Please run the evaluation CLI first:\n\n"
            "```bash\npython -m src.run_eval --n 20 --split test --no-llm\n```"
        )
        return

    # ===== SIDEBAR FILTERS =====
    st.sidebar.header("Filters")

    # Overall quality range
    quality_scores = [r.get("scores", {}).get("overall_quality", 0.0) for r in results]
    if quality_scores:
        min_quality = float(min(quality_scores))
        max_quality = float(max(quality_scores))
        if min_quality == max_quality:
            # Handle case where all scores are the same
            min_quality = max(0.0, min_quality - 0.1)
            max_quality = min(1.0, max_quality + 0.1)
    else:
        min_quality = 0.0
        max_quality = 1.0
    
    quality_range = st.sidebar.slider(
        "Overall Quality Range",
        min_value=min_quality,
        max_value=max_quality,
        value=(min_quality, max_quality),
        step=0.01,
    )

    # Checkbox filters
    filter_hallucinations = st.sidebar.checkbox("Only notes with hallucinations", False)
    filter_missing_critical = st.sidebar.checkbox(
        "Only notes with missing critical findings", False
    )
    filter_major_issues = st.sidebar.checkbox(
        "Only notes with major/critical issues", False
    )
    filter_failed_structure = st.sidebar.checkbox(
        "Only notes failing SOAP structure", False
    )

    # Apply filters
    filtered_results = results
    if filter_hallucinations:
        filtered_results = [
            r for r in filtered_results if has_issue_category(r, "hallucination")
        ]
    if filter_missing_critical:
        filtered_results = [
            r for r in filtered_results if has_issue_category(r, "missing_critical")
        ]
    if filter_major_issues:
        filtered_results = [r for r in filtered_results if has_major_or_critical_issue(r)]
    if filter_failed_structure:
        filtered_results = [
            r for r in filtered_results if r["scores"].get("structure", 1.0) == 0.0
        ]

    # Quality range filter
    filtered_results = [
        r
        for r in filtered_results
        if quality_range[0] <= r.get("scores", {}).get("overall_quality", 0.0) <= quality_range[1]
    ]

    st.sidebar.markdown("---")
    st.sidebar.info(f"Showing {len(filtered_results)} of {len(results)} notes")

    # ===== SUMMARY CARDS =====
    st.header("📈 Summary Metrics")
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("Notes Evaluated", summary.get("n_examples", 0))

    with col2:
        overall_mean = summary.get("scores", {}).get("overall_quality", {}).get("mean", 0.0)
        st.metric("Mean Overall Quality", f"{overall_mean:.3f}")

    with col3:
        halluc_rate = summary.get("error_rates", {}).get("hallucination", {}).get("rate", 0.0)
        st.metric("Hallucination Rate", f"{halluc_rate:.1%}")

    with col4:
        clinical_error_rate = summary.get("error_rates", {}).get("clinical_error", {}).get("rate", 0.0)
        st.metric("Major/Critical Errors", f"{clinical_error_rate:.1%}")

    # ===== CHARTS =====
    st.header("📊 Charts")

    col1, col2 = st.columns(2)

    with col1:
        # Histogram of overall quality
        quality_scores_filtered = [r.get("scores", {}).get("overall_quality", 0.0) for r in filtered_results]
        if quality_scores_filtered and PLOTLY_AVAILABLE:
            fig_hist = px.histogram(
                x=quality_scores_filtered,
                nbins=20,
                title="Distribution of Overall Quality Scores",
                labels={"x": "Overall Quality", "y": "Frequency"},
            )
            fig_hist.update_layout(showlegend=False)
            st.plotly_chart(fig_hist, use_container_width=True)
        else:
            # Fallback to simple histogram
            st.bar_chart(pd.Series(quality_scores_filtered).value_counts().sort_index())

    with col2:
        # Bar chart of mean scores
        scores_dict = summary.get("scores", {})
        score_data = {
            "Metric": ["Coverage", "Faithfulness", "Accuracy"],
            "Mean Score": [
                scores_dict.get("coverage", {}).get("mean", 0.0),
                scores_dict.get("faithfulness", {}).get("mean", 0.0),
                scores_dict.get("accuracy", {}).get("mean", 0.0),
            ],
        }
        df_scores = pd.DataFrame(score_data)
        if PLOTLY_AVAILABLE:
            fig_bar = px.bar(
                df_scores,
                x="Metric",
                y="Mean Score",
                title="Mean Scores by Metric",
                range_y=[0, 1],
            )
            st.plotly_chart(fig_bar, use_container_width=True)
        else:
            st.bar_chart(df_scores.set_index("Metric"))

    # ===== PER-NOTE EXPLORER =====
    st.header("🔍 Per-Note Explorer")

    if not filtered_results:
        st.info("No notes match the current filters.")
    else:
        # Create DataFrame for table
        table_data = []
        for r in filtered_results:
            scores = r.get("scores", {})
            table_data.append(
                {
                    "ID": r.get("example_id", "N/A"),
                    "Overall Quality": f"{scores.get('overall_quality', 0.0):.3f}",
                    "Coverage": f"{scores.get('coverage', 0.0):.3f}",
                    "Faithfulness": f"{scores.get('faithfulness', 0.0):.3f}",
                    "Accuracy": f"{scores.get('accuracy', 0.0):.3f}",
                    "Structure": "✓" if scores.get("structure", 0) == 1.0 else "✗",
                    "Issues": len(r.get("issues", [])),
                    "Has Hallucination": "✓"
                    if has_issue_category(r, "hallucination")
                    else "",
                    "Has Missing": "✓" if has_issue_category(r, "missing_critical") else "",
                    "Major/Critical": "✓" if has_major_or_critical_issue(r) else "",
                }
            )

        df_table = pd.DataFrame(table_data)

        # Note selector
        note_ids = [r.get("example_id", f"note_{i}") for i, r in enumerate(filtered_results)]
        if not note_ids:
            st.info("No notes available to display.")
            return
        
        selected_id = st.selectbox("Select a note to view details:", note_ids)

        # Display selected note details
        selected_result = next((r for r in filtered_results if r.get("example_id") == selected_id), None)
        if not selected_result:
            st.error("Selected note not found.")
            return

        st.subheader(f"Note: {selected_id}")

        # Scores
        selected_scores = selected_result.get("scores", {})
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Overall Quality", f"{selected_scores.get('overall_quality', 0.0):.3f}")
        with col2:
            st.metric("Coverage", f"{selected_scores.get('coverage', 0.0):.3f}")
        with col3:
            st.metric("Faithfulness", f"{selected_scores.get('faithfulness', 0.0):.3f}")
        with col4:
            st.metric("Accuracy", f"{selected_scores.get('accuracy', 0.0):.3f}")

        # Deterministic metrics
        if "coverage_det" in selected_scores:
            st.markdown("**Deterministic Metrics:**")
            det_col1, det_col2, det_col3 = st.columns(3)
            with det_col1:
                st.metric(
                    "Coverage (Det)",
                    f"{selected_scores.get('coverage_det', 0.0):.3f}",
                )
            with det_col2:
                st.metric(
                    "Hallucination Rate (Det)",
                    f"{selected_scores.get('hallucination_rate_det', 0.0):.3f}",
                )
            with det_col3:
                st.metric(
                    "Structure",
                    "✓" if selected_scores.get("structure", 0) == 1.0 else "✗",
                )

        # Issues
        issues = selected_result.get("issues", [])
        if issues:
            st.subheader("Issues")
            for i, issue in enumerate(issues, 1):
                severity_color = {
                    "minor": "🟡",
                    "major": "🟠",
                    "critical": "🔴",
                }
                with st.expander(
                    f"{severity_color.get(issue['severity'], '⚪')} [{issue['severity'].upper()}] {issue['category']}"
                ):
                    st.write(f"**Description:** {issue['description']}")
                    if issue.get("span_model"):
                        st.code(f"Model span: {issue['span_model']}")
                    if issue.get("span_source"):
                        st.code(f"Source span: {issue['span_source']}")
        else:
            st.success("✅ No issues found for this note.")

        # Full text content (if available in results)
        if "transcript" in selected_result or "reference_note" in selected_result:
            st.subheader("Content")
            if "transcript" in selected_result:
                with st.expander("📝 Transcript"):
                    st.text_area("", selected_result.get("transcript", "N/A"), height=150, disabled=True, key=f"transcript_{selected_id}")

            if "reference_note" in selected_result:
                with st.expander("📋 Reference Note"):
                    st.text_area("", selected_result.get("reference_note", "N/A"), height=200, disabled=True, key=f"ref_{selected_id}")

            if "generated_note" in selected_result:
                with st.expander("✏️ Generated Note"):
                    st.text_area("", selected_result.get("generated_note", "N/A"), height=200, disabled=True, key=f"gen_{selected_id}")

        # Table view
        st.subheader("All Filtered Notes")
        st.dataframe(df_table, use_container_width=True, hide_index=True)


if __name__ == "__main__":
    main()

