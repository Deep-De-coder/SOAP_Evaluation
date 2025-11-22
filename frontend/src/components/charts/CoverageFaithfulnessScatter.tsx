import React, { useMemo } from 'react';
import { ScatterChart, Scatter, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Cell } from 'recharts';
import { Card } from '../Card';
import { NoteListItem } from '../../api';

interface CoverageFaithfulnessScatterProps {
  notes: NoteListItem[];
}

export const CoverageFaithfulnessScatter: React.FC<CoverageFaithfulnessScatterProps> = ({ notes }) => {
  const data = useMemo(() => {
    return notes.map((note) => {
      // Use 1 - overall_quality as risk score (higher quality = lower risk)
      const risk = 1 - note.overall_quality;
      return {
        x: note.coverage,
        y: note.faithfulness,
        risk,
        example_id: note.example_id,
        overall_quality: note.overall_quality,
      };
    });
  }, [notes]);

  // Color mapping: higher risk = redder, lower risk = bluer
  const getColor = (risk: number) => {
    if (risk > 0.5) return 'var(--color-badge-danger)';
    if (risk > 0.3) return 'var(--color-badge-warning)';
    return 'var(--color-primary)';
  };

  return (
    <Card hover>
      <h3 className="text-lg font-semibold text-[var(--color-text-primary)] mb-4">
        Coverage vs Faithfulness
      </h3>
      <ResponsiveContainer width="100%" height={300}>
        <ScatterChart margin={{ top: 20, right: 20, bottom: 20, left: 0 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="var(--color-border-subtle)" />
          <XAxis
            type="number"
            dataKey="x"
            name="Coverage"
            domain={[0, 1]}
            tick={{ fill: 'var(--color-text-secondary)', fontSize: 12 }}
            label={{ value: 'Coverage', position: 'insideBottom', offset: -5, fill: 'var(--color-text-secondary)' }}
          />
          <YAxis
            type="number"
            dataKey="y"
            name="Faithfulness"
            domain={[0, 1]}
            tick={{ fill: 'var(--color-text-secondary)', fontSize: 12 }}
            label={{ value: 'Faithfulness', angle: -90, position: 'insideLeft', fill: 'var(--color-text-secondary)' }}
          />
          <Tooltip
            cursor={{ strokeDasharray: '3 3' }}
            contentStyle={{
              backgroundColor: 'var(--color-surface)',
              border: '1px solid var(--color-border-subtle)',
              borderRadius: '8px',
            }}
            labelStyle={{ color: 'var(--color-text-primary)' }}
            formatter={(value: number, name: string) => {
              if (name === 'Coverage' || name === 'Faithfulness') {
                return [value.toFixed(3), name];
              }
              return null;
            }}
            labelFormatter={(payload) => {
              if (payload && payload[0]) {
                return `Note: ${payload[0].payload.example_id}`;
              }
              return '';
            }}
          />
          <Scatter name="Notes" data={data} fill="var(--color-primary)">
            {data.map((entry, index) => (
              <Cell key={`cell-${index}`} fill={getColor(entry.risk)} />
            ))}
          </Scatter>
        </ScatterChart>
      </ResponsiveContainer>
      <p className="text-xs text-[var(--color-text-secondary)] mt-4 text-center">
        Point color indicates risk (red = higher risk, blue = lower risk).
      </p>
    </Card>
  );
};

