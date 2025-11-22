import React, { useEffect, useState } from 'react';
import { fetchNotes, NoteListItem } from '../api';
import { Card, CardHeader } from './Card';
import { Badge } from './Badge';
import { SectionHeader } from './SectionHeader';

interface NotesListProps {
  onNoteSelect: (exampleId: string) => void;
}

export const NotesList: React.FC<NotesListProps> = ({ onNoteSelect }) => {
  const [notes, setNotes] = useState<NoteListItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Filter state
  const [minQuality, setMinQuality] = useState<number>(0);
  const [hallucinationOnly, setHallucinationOnly] = useState(false);
  const [missingCriticalOnly, setMissingCriticalOnly] = useState(false);
  const [majorIssuesOnly, setMajorIssuesOnly] = useState(false);

  const loadNotes = async () => {
    try {
      setLoading(true);
      const data = await fetchNotes({
        min_quality: minQuality,
        max_quality: 1,
        hallucination_only: hallucinationOnly,
        missing_critical_only: missingCriticalOnly,
        major_issues_only: majorIssuesOnly,
      });
      setNotes(data);
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load notes');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadNotes();
  }, [minQuality, hallucinationOnly, missingCriticalOnly, majorIssuesOnly]);

  return (
    <div>
      <div className="flex flex-col sm:flex-row sm:justify-between sm:items-center mb-8 gap-4">
        <SectionHeader
          title="Notes Overview"
          subtitle={`Showing ${notes.length} note${notes.length !== 1 ? 's' : ''}`}
        />
      </div>

      {/* Filters */}
      <Card className="mb-8" hover>
        <CardHeader
          title="Filters"
          subtitle="Refine your search criteria"
        />
        <div className="space-y-6">
          {/* Quality Range */}
          <div>
            <label className="block text-sm font-medium text-[var(--color-text-primary)] mb-3">
              Minimum Quality: {minQuality.toFixed(2)}
            </label>
            <div className="flex-1">
              <input
                type="range"
                min="0"
                max="1"
                step="0.01"
                value={minQuality}
                onChange={(e) => setMinQuality(parseFloat(e.target.value))}
                className="w-full h-2 bg-[var(--color-border-subtle)] rounded-lg appearance-none cursor-pointer accent-[var(--color-primary)]"
              />
              <div className="flex justify-between text-xs text-[var(--color-text-secondary)] mt-1">
                <span>0.0</span>
                <span>1.0</span>
              </div>
            </div>
          </div>

          {/* Checkboxes */}
          <div className="flex flex-wrap gap-6">
            <label className="flex items-center cursor-pointer">
              <input
                type="checkbox"
                checked={hallucinationOnly}
                onChange={(e) => setHallucinationOnly(e.target.checked)}
                className="w-4 h-4 rounded border-[var(--color-border-subtle)] text-[var(--color-primary)] focus:ring-[var(--color-primary)] focus:ring-2"
              />
              <span className="ml-3 text-base text-[var(--color-text-primary)]">Only notes with hallucinations</span>
            </label>
            <label className="flex items-center cursor-pointer">
              <input
                type="checkbox"
                checked={missingCriticalOnly}
                onChange={(e) => setMissingCriticalOnly(e.target.checked)}
                className="w-4 h-4 rounded border-[var(--color-border-subtle)] text-[var(--color-primary)] focus:ring-[var(--color-primary)] focus:ring-2"
              />
              <span className="ml-3 text-base text-[var(--color-text-primary)]">Only notes with missing critical findings</span>
            </label>
            <label className="flex items-center cursor-pointer">
              <input
                type="checkbox"
                checked={majorIssuesOnly}
                onChange={(e) => setMajorIssuesOnly(e.target.checked)}
                className="w-4 h-4 rounded border-[var(--color-border-subtle)] text-[var(--color-primary)] focus:ring-[var(--color-primary)] focus:ring-2"
              />
              <span className="ml-3 text-base text-[var(--color-text-primary)]">Only notes with major/critical issues</span>
            </label>
          </div>
        </div>
      </Card>

      {/* Notes Table */}
      {loading ? (
        <div className="text-center py-16">
          <div className="inline-block animate-spin rounded-full h-10 w-10 border-b-2 border-primary"></div>
          <p className="mt-4 text-[var(--color-text-secondary)]">Loading notes...</p>
        </div>
      ) : error ? (
        <Card className="border-red-200 bg-red-50">
          <p className="text-red-800">{error}</p>
        </Card>
      ) : notes.length === 0 ? (
        <Card>
          <p className="text-center text-[var(--color-text-secondary)] py-8">No notes match the current filters.</p>
        </Card>
      ) : (
        <Card className="p-0 overflow-hidden">
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-border-subtle">
              <thead className="bg-[var(--color-surface-alt)]">
                <tr>
                  <th className="px-6 py-4 text-left text-xs font-semibold text-[var(--color-text-secondary)] uppercase tracking-wider">
                    ID
                  </th>
                  <th className="px-6 py-4 text-left text-xs font-semibold text-[var(--color-text-secondary)] uppercase tracking-wider">
                    Overall Quality
                  </th>
                  <th className="px-6 py-4 text-left text-xs font-semibold text-[var(--color-text-secondary)] uppercase tracking-wider">
                    Coverage
                  </th>
                  <th className="px-6 py-4 text-left text-xs font-semibold text-[var(--color-text-secondary)] uppercase tracking-wider">
                    Faithfulness
                  </th>
                  <th className="px-6 py-4 text-left text-xs font-semibold text-[var(--color-text-secondary)] uppercase tracking-wider">
                    Accuracy
                  </th>
                  <th className="px-6 py-4 text-left text-xs font-semibold text-[var(--color-text-secondary)] uppercase tracking-wider">
                    Status
                  </th>
                  <th className="px-6 py-4 text-left text-xs font-semibold text-[var(--color-text-secondary)] uppercase tracking-wider">
                    Actions
                  </th>
                </tr>
              </thead>
              <tbody className="bg-[var(--color-surface)] divide-y divide-border-subtle">
                {notes.map((note) => (
                  <tr
                    key={note.example_id}
                    className="hover:bg-[var(--color-surface-alt)]/50 cursor-pointer transition-colors duration-150"
                    onClick={() => onNoteSelect(note.example_id)}
                  >
                    <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-[var(--color-text-primary)]">
                      {note.example_id}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-[var(--color-text-primary)]">
                      {note.overall_quality.toFixed(3)}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-[var(--color-text-primary)]">
                      {note.coverage.toFixed(3)}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-[var(--color-text-primary)]">
                      {note.faithfulness.toFixed(3)}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-[var(--color-text-primary)]">
                      {note.accuracy.toFixed(3)}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm">
                      <div className="flex flex-wrap gap-2">
                        {note.has_hallucination && (
                          <Badge variant="error">Hallucination</Badge>
                        )}
                        {note.has_missing_critical && (
                          <Badge variant="warning">Missing Critical</Badge>
                        )}
                        {note.has_major_issue && (
                          <Badge variant="error">Major Issue</Badge>
                        )}
                        {!note.has_hallucination && !note.has_missing_critical && !note.has_major_issue && (
                          <Badge variant="success">OK</Badge>
                        )}
                      </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm">
                      <button
                        onClick={(e) => {
                          e.stopPropagation();
                          onNoteSelect(note.example_id);
                        }}
                        className="text-primary hover:text-primary-dark font-semibold transition-colors"
                      >
                        View
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </Card>
      )}
    </div>
  );
};

