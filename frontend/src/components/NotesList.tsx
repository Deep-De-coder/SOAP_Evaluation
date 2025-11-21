import React, { useEffect, useState } from 'react';
import { fetchNotes, NoteListItem } from '../api';
import { Card } from './Card';
import { Badge } from './Badge';

interface NotesListProps {
  onNoteSelect: (exampleId: string) => void;
}

export const NotesList: React.FC<NotesListProps> = ({ onNoteSelect }) => {
  const [notes, setNotes] = useState<NoteListItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Filter state
  const [minQuality, setMinQuality] = useState<number>(0);
  const [maxQuality, setMaxQuality] = useState<number>(1);
  const [hallucinationOnly, setHallucinationOnly] = useState(false);
  const [missingCriticalOnly, setMissingCriticalOnly] = useState(false);
  const [majorIssuesOnly, setMajorIssuesOnly] = useState(false);

  const loadNotes = async () => {
    try {
      setLoading(true);
      const data = await fetchNotes({
        min_quality: minQuality,
        max_quality: maxQuality,
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
  }, [minQuality, maxQuality, hallucinationOnly, missingCriticalOnly, majorIssuesOnly]);

  return (
    <div>
      <div className="flex justify-between items-center mb-6">
        <h2 className="text-2xl font-bold text-gray-900">Notes Explorer</h2>
        <p className="text-sm text-gray-600">
          Showing {notes.length} note{notes.length !== 1 ? 's' : ''}
        </p>
      </div>

      {/* Filters */}
      <Card className="mb-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">Filters</h3>
        <div className="space-y-4">
          {/* Quality Range */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Overall Quality Range: {minQuality.toFixed(2)} - {maxQuality.toFixed(2)}
            </label>
            <div className="flex gap-2">
              <input
                type="range"
                min="0"
                max="1"
                step="0.01"
                value={minQuality}
                onChange={(e) => setMinQuality(parseFloat(e.target.value))}
                className="flex-1"
              />
              <input
                type="range"
                min="0"
                max="1"
                step="0.01"
                value={maxQuality}
                onChange={(e) => setMaxQuality(parseFloat(e.target.value))}
                className="flex-1"
              />
            </div>
            <div className="flex justify-between text-xs text-gray-500 mt-1">
              <span>0.0</span>
              <span>1.0</span>
            </div>
          </div>

          {/* Checkboxes */}
          <div className="flex flex-wrap gap-4">
            <label className="flex items-center">
              <input
                type="checkbox"
                checked={hallucinationOnly}
                onChange={(e) => setHallucinationOnly(e.target.checked)}
                className="rounded border-gray-300 text-primary-600 focus:ring-primary-500"
              />
              <span className="ml-2 text-sm text-gray-700">Only notes with hallucinations</span>
            </label>
            <label className="flex items-center">
              <input
                type="checkbox"
                checked={missingCriticalOnly}
                onChange={(e) => setMissingCriticalOnly(e.target.checked)}
                className="rounded border-gray-300 text-primary-600 focus:ring-primary-500"
              />
              <span className="ml-2 text-sm text-gray-700">Only notes with missing critical findings</span>
            </label>
            <label className="flex items-center">
              <input
                type="checkbox"
                checked={majorIssuesOnly}
                onChange={(e) => setMajorIssuesOnly(e.target.checked)}
                className="rounded border-gray-300 text-primary-600 focus:ring-primary-500"
              />
              <span className="ml-2 text-sm text-gray-700">Only notes with major/critical issues</span>
            </label>
          </div>
        </div>
      </Card>

      {/* Notes Table */}
      {loading ? (
        <div className="text-center py-12">
          <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-primary-600"></div>
          <p className="mt-2 text-gray-600">Loading notes...</p>
        </div>
      ) : error ? (
        <div className="bg-red-50 border border-red-200 rounded-lg p-4">
          <p className="text-red-800">{error}</p>
        </div>
      ) : notes.length === 0 ? (
        <Card>
          <p className="text-center text-gray-500">No notes match the current filters.</p>
        </Card>
      ) : (
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 overflow-hidden">
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    ID
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Overall Quality
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Coverage
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Faithfulness
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Accuracy
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Status
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Actions
                  </th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {notes.map((note) => (
                  <tr
                    key={note.example_id}
                    className="hover:bg-gray-50 cursor-pointer transition-colors"
                    onClick={() => onNoteSelect(note.example_id)}
                  >
                    <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                      {note.example_id}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                      {note.overall_quality.toFixed(3)}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                      {note.coverage.toFixed(3)}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                      {note.faithfulness.toFixed(3)}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                      {note.accuracy.toFixed(3)}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm">
                      <div className="flex flex-wrap gap-1">
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
                        className="text-primary-600 hover:text-primary-800 font-medium"
                      >
                        View
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
};

