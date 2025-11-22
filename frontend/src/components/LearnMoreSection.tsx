import React from 'react';
import { Card } from './Card';
import { SectionHeader } from './SectionHeader';

export const LearnMoreSection: React.FC = () => {
  return (
    <section className="py-12">
      <SectionHeader
        title="Why this dashboard exists"
        subtitle="Understanding our approach to SOAP note quality evaluation"
      />
      <Card hover>
        <div className="space-y-4 text-[var(--color-text-primary)]">
          <p className="text-base leading-relaxed">
            This dashboard helps us monitor the quality of AI‑generated SOAP notes without reading every chart by hand.
            By combining deterministic checks with LLM‑based judging, we can quickly see when a new model or prompt hurts coverage, increases hallucinations, or introduces clinical risk.
          </p>
          <p className="text-base leading-relaxed">
            The visualizations highlight where notes are strong, where they fail, and which cases may need human review.
          </p>
          <div className="mt-6 pt-6 border-t border-[var(--color-border-subtle)]">
            <ul className="space-y-2 text-base">
              <li className="flex items-start">
                <span className="text-[var(--color-primary)] mr-2">•</span>
                <span>Track overall model quality over time</span>
              </li>
              <li className="flex items-start">
                <span className="text-[var(--color-primary)] mr-2">•</span>
                <span>Compare coverage vs faithfulness</span>
              </li>
              <li className="flex items-start">
                <span className="text-[var(--color-primary)] mr-2">•</span>
                <span>Identify high‑risk notes for clinician review</span>
              </li>
            </ul>
          </div>
        </div>
      </Card>
    </section>
  );
};

