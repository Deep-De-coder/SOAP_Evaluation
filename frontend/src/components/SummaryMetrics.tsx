import React, { useEffect, useState } from 'react';
import { fetchSummary, Summary } from '../api';
import { MetricCard } from './MetricCard';
import { SectionHeader } from './SectionHeader';

export const SummaryMetrics: React.FC = () => {
  const [summary, setSummary] = useState<Summary | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const loadSummary = async () => {
      try {
        setLoading(true);
        const data = await fetchSummary();
        setSummary(data);
        setError(null);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to load summary');
      } finally {
        setLoading(false);
      }
    };

    loadSummary();
  }, []);

  if (loading) {
    return (
      <div className="text-center py-16">
        <div className="inline-block animate-spin rounded-full h-10 w-10 border-b-2 border-primary"></div>
        <p className="mt-4 text-[var(--color-text-secondary)]">Loading summary...</p>
      </div>
    );
  }

  if (error) {
    return (
      <Card className="border-red-200 bg-red-50">
        <p className="text-red-800">{error}</p>
      </Card>
    );
  }

  if (!summary) {
    return null;
  }

  const overallQuality = summary.scores.overall_quality.mean;
  const coverage = summary.scores.coverage.mean;
  const faithfulness = summary.scores.faithfulness.mean;
  const accuracy = summary.scores.accuracy.mean;
  const hallucinationRate = summary.error_rates.hallucination.rate;
  const clinicalErrorRate = summary.error_rates.clinical_error.rate;
  const rougeLf = summary.scores.rouge_l_f;
  const bleu = summary.scores.bleu;

  const metrics = [
    {
      label: 'Notes Evaluated',
      value: summary.n_examples.toLocaleString(),
      caption: 'Total number of notes',
    },
    {
      label: 'Overall Quality',
      value: overallQuality.toFixed(3),
      caption: 'Average quality score',
    },
    {
      label: 'Coverage',
      value: coverage.toFixed(3),
      caption: 'Average coverage score',
    },
    {
      label: 'Faithfulness',
      value: faithfulness.toFixed(3),
      caption: 'Average faithfulness score',
    },
    {
      label: 'Accuracy',
      value: accuracy.toFixed(3),
      caption: 'Average accuracy score',
    },
    {
      label: 'ROUGE-L F1',
      value: rougeLf ? rougeLf.mean.toFixed(3) : 'N/A',
      caption: rougeLf ? 'Average ROUGE-L F1' : 'N/A (no reference)',
    },
    {
      label: 'BLEU Score',
      value: bleu ? bleu.mean.toFixed(3) : 'N/A',
      caption: bleu ? 'Average BLEU score' : 'N/A (no reference)',
    },
    {
      label: 'Hallucination Rate',
      value: `${(hallucinationRate * 100).toFixed(1)}%`,
      caption: 'Notes with hallucinations',
    },
    {
      label: 'Clinical Risk',
      value: `${(clinicalErrorRate * 100).toFixed(1)}%`,
      caption: 'Major/critical errors',
    },
  ];

  return (
    <div>
      <SectionHeader
        title="Evaluation Summary"
        subtitle="Comprehensive metrics for SOAP note quality assessment"
      />
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
        {metrics.map((metric, index) => (
          <MetricCard
            key={index}
            title={metric.label}
            value={metric.value}
            caption={metric.caption}
          />
        ))}
      </div>
    </div>
  );
};

import { Card } from './Card';

