import { useState, useRef } from 'react';
import { SummaryMetrics } from './components/SummaryMetrics';
import { NotesList } from './components/NotesList';
import { NoteDetail } from './components/NoteDetail';
import { Hero } from './components/Hero';
import { ChartsSection } from './components/ChartsSection';
import { LearnMoreSection } from './components/LearnMoreSection';

function App() {
  const [selectedNoteId, setSelectedNoteId] = useState<string | null>(null);
  const learnMoreRef = useRef<HTMLDivElement>(null);

  const handleLearnMoreClick = () => {
    learnMoreRef.current?.scrollIntoView({ behavior: 'smooth', block: 'start' });
  };

  return (
    <div className="min-h-screen bg-[var(--color-surface-alt)]">
      {/* Hero Section */}
      <Hero onLearnMoreClick={handleLearnMoreClick} />

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-16 lg:py-20">
        {selectedNoteId ? (
          <NoteDetail
            exampleId={selectedNoteId}
            onClose={() => setSelectedNoteId(null)}
          />
        ) : (
          <>
            <ChartsSection />
            <SummaryMetrics />
            <div ref={learnMoreRef}>
              <LearnMoreSection />
            </div>
            <div className="mt-16">
              <NotesList onNoteSelect={setSelectedNoteId} />
            </div>
          </>
        )}
      </main>

      {/* Footer */}
      <footer className="bg-[var(--color-surface)] border-t border-[var(--color-border-subtle)] mt-20">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
          <p className="text-center text-sm text-[var(--color-text-secondary)]">
            SOAP Note Evaluation Framework
          </p>
        </div>
      </footer>
    </div>
  );
}

export default App;
