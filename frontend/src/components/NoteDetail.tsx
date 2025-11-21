import React, { useEffect, useState } from 'react';
import { fetchNoteDetail, NoteDetail as NoteDetailType } from '../api';
import { Card, CardHeader } from './Card';
import { Badge } from './Badge';

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
      <div className="text-center py-12">
        <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-primary-600"></div>
        <p className="mt-2 text-gray-600">Loading note details...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-red-50 border border-red-200 rounded-lg p-4">
        <p className="text-red-800">{error}</p>
        <button
          onClick={onClose}
          className="mt-4 text-sm text-red-600 hover:text-red-800"
        >
          ← Back to list
        </button>
      </div>
    );
  }

  if (!note) {
    return null;
  }

  const severityColors: Record<string, 'default' | 'warning' | 'error'> = {
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
      <div className="flex justify-between items-center mb-6">
        <h2 className="text-2xl font-bold text-gray-900">Note Details: {note.example_id}</h2>
        <button
          onClick={onClose}
          className="text-sm text-gray-600 hover:text-gray-900 font-medium"
        >
          ← Back to list
        </button>
      </div>

      {/* Scores */}
      <Card className="mb-6">
        <CardHeader title="Scores" />
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          {Object.entries(note.scores).map(([key, value]) => {
            // Skip None/null values for reference-based metrics
            if (value === null || value === undefined) {
              return null;
            }
            // Format ROUGE and BLEU with special handling
            const isReferenceMetric = key === 'rouge_l_f' || key === 'bleu';
            return (
              <div key={key}>
                <p className="text-sm font-medium text-gray-500 mb-1">
                  {key.replace(/_/g, ' ').replace(/\b\w/g, (l) => l.toUpperCase())}
                  {isReferenceMetric && (
                    <span className="ml-1 text-xs text-gray-400">(ref-based)</span>
                  )}
                </p>
                <p className="text-xl font-bold text-gray-900">
                  {typeof value === 'number' ? value.toFixed(3) : String(value)}
                </p>
              </div>
            );
          })}
        </div>
        {/* Show message if reference-based metrics are missing */}
        {(note.scores.rouge_l_f === null || note.scores.rouge_l_f === undefined ||
          note.scores.bleu === null || note.scores.bleu === undefined) && (
          <div className="mt-4 text-sm text-gray-500 italic">
            Note: ROUGE-L and BLEU metrics are only available when reference notes are present (not in production mode).
          </div>
        )}
      </Card>

      {/* Issues */}
      {note.issues.length > 0 ? (
        <Card className="mb-6">
          <CardHeader title="Issues" subtitle={`${note.issues.length} issue(s) found`} />
          <div className="space-y-4">
            {Object.entries(issuesByCategory).map(([category, issues]) => (
              <div key={category} className="border-l-4 border-gray-200 pl-4">
                <h4 className="font-semibold text-gray-900 mb-2">
                  {category.replace(/_/g, ' ').replace(/\b\w/g, (l) => l.toUpperCase())}
                </h4>
                <div className="space-y-3">
                  {issues.map((issue, index) => (
                    <div key={index} className="bg-gray-50 rounded p-3">
                      <div className="flex items-center gap-2 mb-2">
                        <Badge variant={severityColors[issue.severity] || 'default'}>
                          {issue.severity.toUpperCase()}
                        </Badge>
                      </div>
                      <p className="text-sm text-gray-700 mb-2">{issue.description}</p>
                      {issue.span_model && (
                        <div className="mt-2">
                          <p className="text-xs font-medium text-gray-500 mb-1">Model span:</p>
                          <code className="text-xs bg-white border border-gray-200 rounded px-2 py-1 block">
                            {issue.span_model}
                          </code>
                        </div>
                      )}
                      {issue.span_source && (
                        <div className="mt-2">
                          <p className="text-xs font-medium text-gray-500 mb-1">Source span:</p>
                          <code className="text-xs bg-white border border-gray-200 rounded px-2 py-1 block">
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
        <Card className="mb-6">
          <div className="text-center py-4">
            <Badge variant="success">No issues found</Badge>
          </div>
        </Card>
      )}

      {/* Content Sections */}
      <div className="space-y-4">
        {note.transcript && (
          <Card>
            <button
              onClick={() => toggleSection('transcript')}
              className="w-full text-left flex justify-between items-center"
            >
              <CardHeader title="Transcript" />
              <span className="text-gray-400">
                {expandedSections.transcript ? '▼' : '▶'}
              </span>
            </button>
            {expandedSections.transcript && (
              <div className="mt-4">
                <pre className="whitespace-pre-wrap text-sm text-gray-700 bg-gray-50 p-4 rounded border border-gray-200 max-h-96 overflow-y-auto">
                  {note.transcript}
                </pre>
              </div>
            )}
          </Card>
        )}

        {note.reference_note && (
          <Card>
            <button
              onClick={() => toggleSection('reference_note')}
              className="w-full text-left flex justify-between items-center"
            >
              <CardHeader title="Reference Note" />
              <span className="text-gray-400">
                {expandedSections.reference_note ? '▼' : '▶'}
              </span>
            </button>
            {expandedSections.reference_note && (
              <div className="mt-4">
                <pre className="whitespace-pre-wrap text-sm text-gray-700 bg-gray-50 p-4 rounded border border-gray-200 max-h-96 overflow-y-auto">
                  {note.reference_note}
                </pre>
              </div>
            )}
          </Card>
        )}

        {note.generated_note && (
          <Card>
            <button
              onClick={() => toggleSection('generated_note')}
              className="w-full text-left flex justify-between items-center"
            >
              <CardHeader title="Generated Note" />
              <span className="text-gray-400">
                {expandedSections.generated_note ? '▼' : '▶'}
              </span>
            </button>
            {expandedSections.generated_note && (
              <div className="mt-4">
                <pre className="whitespace-pre-wrap text-sm text-gray-700 bg-gray-50 p-4 rounded border border-gray-200 max-h-96 overflow-y-auto">
                  {note.generated_note}
                </pre>
              </div>
            )}
          </Card>
        )}
      </div>
    </div>
  );
};

