import React, { useMemo } from 'react';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';
import { Card } from '../Card';
import { NoteListItem } from '../../api';

interface QualityDistributionChartProps {
  notes: NoteListItem[];
}

export const QualityDistributionChart: React.FC<QualityDistributionChartProps> = ({ notes }) => {
  const binnedData = useMemo(() => {
    const bins = Array.from({ length: 10 }, (_, i) => ({
      range: `${(i * 0.1).toFixed(1)}-${((i + 1) * 0.1).toFixed(1)}`,
      min: i * 0.1,
      max: (i + 1) * 0.1,
      count: 0,
    }));

    notes.forEach((note) => {
      const quality = note.overall_quality;
      const binIndex = Math.min(Math.floor(quality * 10), 9);
      bins[binIndex].count += 1;
    });

    return bins;
  }, [notes]);

  return (
    <Card hover>
      <h3 className="text-lg font-semibold text-[var(--color-text-primary)] mb-4">
        Quality Distribution
      </h3>
      <ResponsiveContainer width="100%" height={300}>
        <BarChart data={binnedData} margin={{ top: 5, right: 20, left: 0, bottom: 5 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="var(--color-border-subtle)" />
          <XAxis
            dataKey="range"
            tick={{ fill: 'var(--color-text-secondary)', fontSize: 12 }}
            angle={-45}
            textAnchor="end"
            height={60}
          />
          <YAxis tick={{ fill: 'var(--color-text-secondary)', fontSize: 12 }} />
          <Tooltip
            contentStyle={{
              backgroundColor: 'var(--color-surface)',
              border: '1px solid var(--color-border-subtle)',
              borderRadius: '8px',
            }}
            labelStyle={{ color: 'var(--color-text-primary)' }}
          />
          <Bar dataKey="count" fill="var(--color-primary)" radius={[8, 8, 0, 0]} />
        </BarChart>
      </ResponsiveContainer>
      <p className="text-xs text-[var(--color-text-secondary)] mt-4 text-center">
        Distribution of overall note quality scores.
      </p>
    </Card>
  );
};

