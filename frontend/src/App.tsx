import React, { useState } from 'react';
import { SummaryMetrics } from './components/SummaryMetrics';
import { NotesList } from './components/NotesList';
import { NoteDetail } from './components/NoteDetail';

function App() {
  const [selectedNoteId, setSelectedNoteId] = useState<string | null>(null);

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
          <h1 className="text-3xl font-bold text-gray-900">SOAP Note Evaluation Dashboard</h1>
          <p className="mt-1 text-sm text-gray-600">
            Explore and analyze evaluation results for generated SOAP notes
          </p>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {selectedNoteId ? (
          <NoteDetail
            exampleId={selectedNoteId}
            onClose={() => setSelectedNoteId(null)}
          />
        ) : (
          <>
            <SummaryMetrics />
            <div className="mt-12">
              <NotesList onNoteSelect={setSelectedNoteId} />
            </div>
          </>
        )}
      </main>

      {/* Footer */}
      <footer className="bg-white border-t border-gray-200 mt-12">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <p className="text-center text-sm text-gray-500">
            SOAP Note Evaluation Framework
          </p>
        </div>
      </footer>
    </div>
  );
}

export default App;

