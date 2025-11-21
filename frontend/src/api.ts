import { API_BASE_URL } from './config';

export interface Summary {
  n_examples: number;
  scores: {
    overall_quality: { mean: number; std: number };
    coverage: { mean: number; std: number };
    faithfulness: { mean: number; std: number };
    accuracy: { mean: number; std: number };
    rouge_l_f?: { mean: number; std: number } | null;
    bleu?: { mean: number; std: number } | null;
  };
  error_rates: {
    hallucination: { rate: number; count: number };
    missing_critical: { rate: number; count: number };
    clinical_error: { rate: number; count: number };
  };
}

export interface NoteListItem {
  example_id: string;
  overall_quality: number;
  coverage: number;
  faithfulness: number;
  accuracy: number;
  structure_score: number;
  has_hallucination: boolean;
  has_missing_critical: boolean;
  has_major_issue: boolean;
  rouge_l_f?: number | null;
  bleu?: number | null;
}

export interface Issue {
  category: string;
  severity: string;
  description: string;
  span_model?: string;
  span_source?: string;
}

export interface NoteDetail {
  example_id: string;
  transcript?: string;
  reference_note?: string;
  generated_note?: string;
  scores: Record<string, number | null>;
  issues: Issue[];
}

export async function fetchSummary(): Promise<Summary> {
  const response = await fetch(`${API_BASE_URL}/api/summary`);
  if (!response.ok) {
    throw new Error(`Failed to fetch summary: ${response.statusText}`);
  }
  return response.json();
}

export async function fetchNotes(params?: {
  min_quality?: number;
  max_quality?: number;
  hallucination_only?: boolean;
  missing_critical_only?: boolean;
  major_issues_only?: boolean;
}): Promise<NoteListItem[]> {
  const searchParams = new URLSearchParams();
  if (params?.min_quality !== undefined) {
    searchParams.append('min_quality', params.min_quality.toString());
  }
  if (params?.max_quality !== undefined) {
    searchParams.append('max_quality', params.max_quality.toString());
  }
  if (params?.hallucination_only) {
    searchParams.append('hallucination_only', 'true');
  }
  if (params?.missing_critical_only) {
    searchParams.append('missing_critical_only', 'true');
  }
  if (params?.major_issues_only) {
    searchParams.append('major_issues_only', 'true');
  }

  const url = `${API_BASE_URL}/api/notes${searchParams.toString() ? `?${searchParams.toString()}` : ''}`;
  const response = await fetch(url);
  if (!response.ok) {
    throw new Error(`Failed to fetch notes: ${response.statusText}`);
  }
  return response.json();
}

export async function fetchNoteDetail(exampleId: string): Promise<NoteDetail> {
  const response = await fetch(`${API_BASE_URL}/api/notes/${exampleId}`);
  if (!response.ok) {
    throw new Error(`Failed to fetch note detail: ${response.statusText}`);
  }
  return response.json();
}

