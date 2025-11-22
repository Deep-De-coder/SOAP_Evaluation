import React, { useEffect, useState } from 'react';
import { fetchNoteDetail, NoteDetail as NoteDetailType } from '../api';
import { Card, CardHeader } from './Card';
import { Badge } from './Badge';
import { SectionHeader } from './SectionHeader';

interface NoteDetailProps {
  exampleId: string;
  onClose: () => void;
}

export const NoteDetail: React.FC<NoteDetailProps> = ({ exampleId, onClose }) => {
  const [note, setNote] = useState<NoteDetailType | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [expandedSections, setExpandedSections] = useState<Record<string, boolean>>({
    transcript: false,
    reference_note: false,
    generated_note: false,
  });

  useEffect(() => {
    const loadNote = async () => {
      try {
        setLoading(true);
        const data = await fetchNoteDetail(exampleId);
        setNote(data);
        setError(null);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to load note detail');
      } finally {
        setLoading(false);
      }
    };

    loadNote();
  }, [exampleId]);

  const toggleSection = (section: string) => {
    setExpandedSections((prev) => ({
      ...prev,
      [section]: !prev[section],
    }));
  };

  if (loading) {
    return (
      <div className="text-center py-16">
        <div className="inline-block animate-spin rounded-full h-10 w-10 border-b-2 border-primary"></div>
        <p className="mt-4 text-[var(--color-text-secondary)]">Loading note details...</p>
      </div>
    );
  }

  if (error) {
    return (
      <Card className="border-red-200 bg-red-50">
        <p className="text-red-800 mb-4">{error}</p>
        <button
          onClick={onClose}
          className="text-sm text-primary hover:text-primary-dark font-semibold"
        >
          ← Back to list
        </button>
      </Card>
    );
  }

  if (!note) {
    return null;
  }

  const severityColors: Record<string, 'default' | 'warning' | 'error' | 'info'> = {
    minor: 'default',
    major: 'warning',
    critical: 'error',
  };

  const issuesByCategory = note.issues.reduce((acc, issue) => {
    if (!acc[issue.category]) {
      acc[issue.category] = [];
    }
    acc[issue.category].push(issue);
    return acc;
  }, {} as Record<string, typeof note.issues>);

  return (
    <div>
      <div className="flex flex-col sm:flex-row sm:justify-between sm:items-center mb-8 gap-4">
        <SectionHeader
          title={`Note Details: ${note.example_id}`}
          subtitle="Comprehensive evaluation results"
        />
        <button
          onClick={onClose}
          className="text-sm text-[var(--color-text-secondary)] hover:text-[var(--color-text-primary)] font-semibold transition-colors"
        >
          ← Back to list
        </button>
      </div>

      {/* Two Column Layout */}
      <div className="grid lg:grid-cols-2 gap-8">
        {/* Left Column: Scores & Issues */}
        <div className="space-y-6">
          {/* Scores */}
          <Card hover>
            <CardHeader title="Scores" subtitle="Evaluation metrics" />
            <div className="grid grid-cols-2 gap-4">
              {Object.entries(note.scores).map(([key, value]) => {
                // Skip None/null values for reference-based metrics
                if (value === null || value === undefined) {
                  return null;
                }
                // Format ROUGE and BLEU with special handling
                const isReferenceMetric = key === 'rouge_l_f' || key === 'bleu';
                return (
                  <div key={key} className="text-center p-3 bg-[var(--color-surface-alt)] rounded-lg">
                    <p className="text-xs font-semibold uppercase tracking-wider text-[var(--color-text-secondary)] mb-1">
                      {key.replace(/_/g, ' ').replace(/\b\w/g, (l) => l.toUpperCase())}
                      {isReferenceMetric && (
                        <span className="ml-1 text-xs">(ref)</span>
                      )}
                    </p>
                    <p className="text-xl font-bold text-[var(--color-text-primary)]">
                      {typeof value === 'number' ? value.toFixed(3) : String(value)}
                    </p>
                  </div>
                );
              })}
            </div>
            {/* Show message if reference-based metrics are missing */}
            {(note.scores.rouge_l_f === null || note.scores.rouge_l_f === undefined ||
              note.scores.bleu === null || note.scores.bleu === undefined) && (
              <div className="mt-4 pt-4 border-t border-[var(--color-border-subtle)] text-xs text-[var(--color-text-secondary)] italic">
                Note: ROUGE-L and BLEU metrics are only available when reference notes are present.
              </div>
            )}
          </Card>

          {/* Issues */}
          {note.issues.length > 0 ? (
            <Card hover>
              <CardHeader 
                title="Issues" 
                subtitle={`${note.issues.length} issue${note.issues.length !== 1 ? 's' : ''} found`} 
              />
              <div className="space-y-4">
                {Object.entries(issuesByCategory).map(([category, issues]) => (
                  <div key={category} className="border-l-4 border-primary pl-4">
                    <h4 className="text-sm font-semibold text-[var(--color-text-primary)] mb-2">
                      {category.replace(/_/g, ' ').replace(/\b\w/g, (l) => l.toUpperCase())}
                    </h4>
                    <div className="space-y-3">
                      {issues.map((issue, index) => (
                        <div key={index} className="bg-[var(--color-surface-alt)] rounded-lg p-3">
                          <div className="flex items-center gap-2 mb-2">
                            <Badge variant={severityColors[issue.severity] || 'default'}>
                              {issue.severity.toUpperCase()}
                            </Badge>
                          </div>
                          <p className="text-sm text-[var(--color-text-primary)] mb-2">{issue.description}</p>
                          {issue.span_model && (
                            <div className="mt-2">
                              <p className="text-xs font-semibold text-[var(--color-text-secondary)] mb-1">Model:</p>
                              <code className="text-xs bg-[var(--color-surface)] border border-[var(--color-border-subtle)] rounded px-2 py-1 block text-[var(--color-text-primary)]">
                                {issue.span_model}
                              </code>
                            </div>
                          )}
                          {issue.span_source && (
                            <div className="mt-2">
                              <p className="text-xs font-semibold text-[var(--color-text-secondary)] mb-1">Source:</p>
                              <code className="text-xs bg-[var(--color-surface)] border border-[var(--color-border-subtle)] rounded px-2 py-1 block text-[var(--color-text-primary)]">
                                {issue.span_source}
                              </code>
                            </div>
                          )}
                        </div>
                      ))}
                    </div>
                  </div>
                ))}
              </div>
            </Card>
          ) : (
            <Card>
              <div className="text-center py-6">
                <Badge variant="success">No issues found</Badge>
              </div>
            </Card>
          )}
        </div>

        {/* Right Column: Text Content */}
        <div className="space-y-6">
          {note.transcript && (
            <Card hover>
              <button
                onClick={() => toggleSection('transcript')}
                className="w-full text-left flex justify-between items-center"
              >
                <CardHeader title="Transcript" subtitle="Doctor-patient dialogue" />
                <span className="text-[var(--color-text-secondary)] text-xl">
                  {expandedSections.transcript ? '▼' : '▶'}
                </span>
              </button>
              {expandedSections.transcript && (
                <div className="mt-4">
                  <pre className="whitespace-pre-wrap text-sm text-[var(--color-text-primary)] bg-[var(--color-surface-alt)] p-4 rounded-lg border border-[var(--color-border-subtle)] max-h-96 overflow-y-auto">
                    {note.transcript}
                  </pre>
                </div>
              )}
            </Card>
          )}

          {note.reference_note && (
            <Card hover>
              <button
                onClick={() => toggleSection('reference_note')}
                className="w-full text-left flex justify-between items-center"
              >
                <CardHeader title="Reference Note" subtitle="Ground truth SOAP note" />
                <span className="text-[var(--color-text-secondary)] text-xl">
                  {expandedSections.reference_note ? '▼' : '▶'}
                </span>
              </button>
              {expandedSections.reference_note && (
                <div className="mt-4">
                  <pre className="whitespace-pre-wrap text-sm text-[var(--color-text-primary)] bg-[var(--color-surface-alt)] p-4 rounded-lg border border-[var(--color-border-subtle)] max-h-96 overflow-y-auto">
                    {note.reference_note}
                  </pre>
                </div>
              )}
            </Card>
          )}

          {note.generated_note && (
            <Card hover>
              <button
                onClick={() => toggleSection('generated_note')}
                className="w-full text-left flex justify-between items-center"
              >
                <CardHeader title="Generated Note" subtitle="Evaluated SOAP note" />
                <span className="text-[var(--color-text-secondary)] text-xl">
                  {expandedSections.generated_note ? '▼' : '▶'}
                </span>
              </button>
              {expandedSections.generated_note && (
                <div className="mt-4">
                  <pre className="whitespace-pre-wrap text-sm text-[var(--color-text-primary)] bg-[var(--color-surface-alt)] p-4 rounded-lg border border-[var(--color-border-subtle)] max-h-96 overflow-y-auto">
                    {note.generated_note}
                  </pre>
                </div>
              )}
            </Card>
          )}
        </div>
      </div>
    </div>
  );
};
