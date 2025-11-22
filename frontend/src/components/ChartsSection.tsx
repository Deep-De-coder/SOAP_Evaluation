import React, { useEffect, useState } from 'react';
import { fetchSummary, fetchNotes, Summary, NoteListItem } from '../api';
import { SectionHeader } from './SectionHeader';
import {
  QualityDistributionChart,
  MetricBarChart,
  IssueBreakdownChart,
  CoverageFaithfulnessScatter,
} from './charts';

export const ChartsSection: React.FC = () => {
  const [summary, setSummary] = useState<Summary | null>(null);
  const [notes, setNotes] = useState<NoteListItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const loadData = async () => {
      try {
        setLoading(true);
        const [summaryData, notesData] = await Promise.all([
          fetchSummary(),
          fetchNotes(),
        ]);
        setSummary(summaryData);
        setNotes(notesData);
        setError(null);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to load chart data');
      } finally {
        setLoading(false);
      }
    };

    loadData();
  }, []);

  if (loading) {
    return (
      <section className="py-12">
        <SectionHeader
          title="Quality at a glance"
          subtitle="Visual breakdown of note scores and failure modes."
        />
        <div className="text-center py-16">
          <div className="inline-block animate-spin rounded-full h-10 w-10 border-b-2 border-[var(--color-primary)]"></div>
          <p className="mt-4 text-[var(--color-text-secondary)]">Loading charts...</p>
        </div>
      </section>
    );
  }

  if (error || !summary || notes.length === 0) {
    return (
      <section className="py-12">
        <SectionHeader
          title="Quality at a glance"
          subtitle="Visual breakdown of note scores and failure modes."
        />
        <div className="text-center py-8 text-[var(--color-text-secondary)]">
          {error || 'No data available for charts'}
        </div>
      </section>
    );
  }

  return (
    <section className="py-12">
      <SectionHeader
        title="Quality at a glance"
        subtitle="Visual breakdown of note scores and failure modes."
      />
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Row 1 */}
        <QualityDistributionChart notes={notes} />
        <MetricBarChart summary={summary} />
        {/* Row 2 */}
        <IssueBreakdownChart summary={summary} />
        <CoverageFaithfulnessScatter notes={notes} />
      </div>
    </section>
  );
};

