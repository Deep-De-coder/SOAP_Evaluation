import React, { useMemo } from 'react';
import { PieChart, Pie, Cell, ResponsiveContainer, Tooltip } from 'recharts';
import { Card } from '../Card';
import { Summary } from '../../api';

interface IssueBreakdownChartProps {
  summary: Summary;
}

export const IssueBreakdownChart: React.FC<IssueBreakdownChartProps> = ({ summary }) => {
  const data = useMemo(() => {
    const total = summary.n_examples;
    const hallucinationCount = summary.error_rates.hallucination.count;
    const missingCriticalCount = summary.error_rates.missing_critical.count;
    const clinicalErrorCount = summary.error_rates.clinical_error.count;
    const noIssues = total - hallucinationCount - missingCriticalCount - clinicalErrorCount;

    return [
      {
        name: 'Missing Critical',
        value: missingCriticalCount,
        percentage: ((missingCriticalCount / total) * 100).toFixed(1),
        color: 'var(--color-badge-warning)',
      },
      {
        name: 'Hallucination',
        value: hallucinationCount,
        percentage: ((hallucinationCount / total) * 100).toFixed(1),
        color: 'var(--color-badge-danger)',
      },
      {
        name: 'Clinical Error',
        value: clinicalErrorCount,
        percentage: ((clinicalErrorCount / total) * 100).toFixed(1),
        color: 'var(--color-badge-danger)',
      },
      {
        name: 'No Issues',
        value: noIssues,
        percentage: ((noIssues / total) * 100).toFixed(1),
        color: 'var(--color-badge-info)',
      },
    ].filter((item) => item.value > 0); // Only show slices with values > 0
  }, [summary]);

  const COLORS = data.map((item) => item.color);

  return (
    <Card hover>
      <h3 className="text-lg font-semibold text-[var(--color-text-primary)] mb-4">
        Issue Breakdown
      </h3>
      <ResponsiveContainer width="100%" height={300}>
        <PieChart>
          <Pie
            data={data}
            cx="50%"
            cy="50%"
            labelLine={false}
            label={(entry: any) => {
              if (entry && entry.percentage) {
                return `${entry.name}: ${entry.percentage}%`;
              }
              return entry?.name || '';
            }}
            outerRadius={100}
            fill="#8884d8"
            dataKey="value"
          >
            {data.map((_, index) => (
              <Cell key={`cell-${index}`} fill={COLORS[index]} />
            ))}
          </Pie>
          <Tooltip
            contentStyle={{
              backgroundColor: 'var(--color-surface)',
              border: '1px solid var(--color-border-subtle)',
              borderRadius: '8px',
            }}
            labelStyle={{ color: 'var(--color-text-primary)' }}
            formatter={(value: number, name: string, props: any) => [
              `${value} notes (${props.payload.percentage}%)`,
              name,
            ]}
          />
        </PieChart>
      </ResponsiveContainer>
    </Card>
  );
};

