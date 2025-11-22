import React, { useMemo } from 'react';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, LabelList } from 'recharts';
import { Card } from '../Card';
import { Summary } from '../../api';

interface MetricBarChartProps {
  summary: Summary;
}

export const MetricBarChart: React.FC<MetricBarChartProps> = ({ summary }) => {
  const data = useMemo(() => {
    const metrics = [
      { name: 'Coverage', value: summary.scores.coverage.mean, formatted: summary.scores.coverage.mean.toFixed(2) },
      { name: 'Faithfulness', value: summary.scores.faithfulness.mean, formatted: summary.scores.faithfulness.mean.toFixed(2) },
      { name: 'Accuracy', value: summary.scores.accuracy.mean, formatted: summary.scores.accuracy.mean.toFixed(2) },
    ];

    // Add reference-based metrics if available
    if (summary.scores.rouge_l_f) {
      metrics.push({ name: 'ROUGE-L F1', value: summary.scores.rouge_l_f.mean, formatted: summary.scores.rouge_l_f.mean.toFixed(2) });
    }
    if (summary.scores.bleu) {
      metrics.push({ name: 'BLEU', value: summary.scores.bleu.mean, formatted: summary.scores.bleu.mean.toFixed(2) });
    }

    return metrics;
  }, [summary]);

  return (
    <Card hover>
      <h3 className="text-lg font-semibold text-[var(--color-text-primary)] mb-4">
        Average Metrics
      </h3>
      <ResponsiveContainer width="100%" height={300}>
        <BarChart data={data} margin={{ top: 20, right: 20, left: 0, bottom: 5 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="var(--color-border-subtle)" />
          <XAxis
            dataKey="name"
            tick={{ fill: 'var(--color-text-secondary)', fontSize: 12 }}
            angle={-45}
            textAnchor="end"
            height={60}
          />
          <YAxis
            domain={[0, 1]}
            tick={{ fill: 'var(--color-text-secondary)', fontSize: 12 }}
          />
          <Tooltip
            contentStyle={{
              backgroundColor: 'var(--color-surface)',
              border: '1px solid var(--color-border-subtle)',
              borderRadius: '8px',
            }}
            labelStyle={{ color: 'var(--color-text-primary)' }}
            formatter={(value: number) => value.toFixed(3)}
          />
          <Bar dataKey="value" fill="var(--color-primary)" radius={[8, 8, 0, 0]}>
            <LabelList
              dataKey="formatted"
              position="top"
              fill="var(--color-text-secondary)"
              fontSize={11}
            />
          </Bar>
        </BarChart>
      </ResponsiveContainer>
    </Card>
  );
};

