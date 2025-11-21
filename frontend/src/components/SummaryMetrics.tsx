import React, { useEffect, useState } from 'react';
import { fetchSummary, Summary } from '../api';
import { Card } from './Card';

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
      <div className="text-center py-12">
        <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-primary-600"></div>
        <p className="mt-2 text-gray-600">Loading summary...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-red-50 border border-red-200 rounded-lg p-4">
        <p className="text-red-800">{error}</p>
      </div>
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
      description: 'Total number of notes',
    },
    {
      label: 'Mean Overall Quality',
      value: overallQuality.toFixed(3),
      description: 'Average quality score',
    },
    {
      label: 'Mean Coverage',
      value: coverage.toFixed(3),
      description: 'Average coverage score',
    },
    {
      label: 'Mean Faithfulness',
      value: faithfulness.toFixed(3),
      description: 'Average faithfulness score',
    },
    {
      label: 'Mean Accuracy',
      value: accuracy.toFixed(3),
      description: 'Average accuracy score',
    },
    {
      label: 'Mean ROUGE-L F1',
      value: rougeLf ? rougeLf.mean.toFixed(3) : 'N/A',
      description: rougeLf ? 'Average ROUGE-L F1 score' : 'N/A (no reference)',
    },
    {
      label: 'Mean BLEU',
      value: bleu ? bleu.mean.toFixed(3) : 'N/A',
      description: bleu ? 'Average BLEU score' : 'N/A (no reference)',
    },
    {
      label: 'Hallucination Rate',
      value: `${(hallucinationRate * 100).toFixed(1)}%`,
      description: 'Percentage with hallucinations',
    },
    {
      label: 'Major/Critical Errors',
      value: `${(clinicalErrorRate * 100).toFixed(1)}%`,
      description: 'Percentage with major issues',
    },
  ];

  return (
    <div>
      <h2 className="text-2xl font-bold text-gray-900 mb-6">Summary Metrics</h2>
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
        {metrics.map((metric, index) => (
          <Card key={index}>
            <div>
              <p className="text-sm font-medium text-gray-500 mb-1">{metric.label}</p>
              <p className="text-2xl font-bold text-gray-900">{metric.value}</p>
              <p className="text-xs text-gray-400 mt-1">{metric.description}</p>
            </div>
          </Card>
        ))}
      </div>
    </div>
  );
};

