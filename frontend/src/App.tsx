import { useEffect, useState } from 'react';
import { Layers, Activity, History } from 'lucide-react';
import RequirementsForm from './components/RequirementsForm';
import RequirementsConfirmationView from './components/RequirementsConfirmationView';
import ResultsView from './components/ResultsView';
import ChatPanel from './components/ChatPanel';
import LoadingState from './components/LoadingState';
import ErrorBanner from './components/ErrorBanner';
import HistoryDrawer from './components/HistoryDrawer';
import { useAnalysis } from './hooks/useAnalysis';
import { checkHealth } from './api/client';
import type { AnalyzeRequest, HealthStatus, ValidatedRequirementsContext } from './types';

export default function App() {
  const {
    loading,
    error,
    discovered,
    result,
    progress,
    discover,
    confirmAndAnalyze,
    loadSavedAnalysis,
    resume,
    reset,
  } = useAnalysis();
  const [health, setHealth] = useState<HealthStatus | null>(null);
  const [historyOpen, setHistoryOpen] = useState(false);

  useEffect(() => {
    checkHealth()
      .then(setHealth)
      .catch(() => setHealth(null));
  }, [result]);

  const handleInitialSubmit = async (request: AnalyzeRequest, files: File[]) => {
    await discover(request, files);
  };

  const handleConfirmRequirements = async (validatedContext: ValidatedRequirementsContext) => {
    await confirmAndAnalyze(validatedContext);
  };

  const showResults = result && !loading;
  const showConfirmation = discovered && !loading && !showResults;

  return (
    <div className="h-screen max-h-screen flex flex-col bg-gray-50/50 overflow-hidden">
      {/* Header */}
      <header className="bg-white border-b border-gray-200 px-6 py-4 shrink-0 z-40">
        <div className="max-w-7xl mx-auto flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="p-2 bg-brand-600 rounded-lg">
              <Layers className="w-6 h-6 text-white" />
            </div>
            <div>
              <h1 className="text-xl font-bold text-gray-900">ASAC</h1>
              <p className="text-xs text-gray-500">AI Solution Architect Copilot</p>
            </div>
          </div>

          <div className="flex items-center gap-4">
            <button
              onClick={() => setHistoryOpen(true)}
              className="flex items-center gap-1.5 px-3 py-1.5 border border-gray-300 rounded-lg text-xs font-semibold text-gray-700 hover:bg-gray-50 transition-colors"
            >
              <History className="w-4 h-4 text-brand-600" />
              History & Saved Reports
            </button>

            {health && (
              <div className="flex items-center gap-2 text-xs text-gray-500 bg-gray-100/80 px-2.5 py-1 rounded-full">
                <Activity
                  className={`w-3.5 h-3.5 ${
                    health.status === 'healthy' ? 'text-green-500' : 'text-amber-500'
                  }`}
                />
                <span>
                  AI Provider:{' '}
                  {health.ai_providers.azure_openai === 'available'
                    ? 'Azure OpenAI'
                    : health.ai_providers.openai === 'available'
                      ? 'OpenAI'
                      : health.ai_providers.ollama === 'available'
                        ? 'Ollama'
                        : 'Template (Demo Mode)'}
                </span>
              </div>
            )}
          </div>
        </div>
      </header>

      {/* History Drawer */}
      <HistoryDrawer
        isOpen={historyOpen}
        onClose={() => setHistoryOpen(false)}
        onSelectAnalysis={(sessionId) => loadSavedAnalysis(sessionId)}
      />

      {/* Main content */}
      <div className="flex-1 flex min-h-0 w-full overflow-hidden">
        <main className={`flex-1 p-6 overflow-y-auto min-w-0 ${showResults ? '' : 'max-w-7xl mx-auto'}`}>
          {error && (
            <div className="mb-4">
              <ErrorBanner message={error} onDismiss={reset} />
            </div>
          )}

          {loading && <LoadingState progress={progress} />}

          {!loading && !showResults && !showConfirmation && (
            <div className="max-w-3xl mx-auto">
              <RequirementsForm onSubmit={handleInitialSubmit} loading={loading} />
            </div>
          )}

          {!loading && showConfirmation && discovered && (
            <RequirementsConfirmationView
              discovered={discovered}
              onConfirm={handleConfirmRequirements}
              onCancel={reset}
              loading={loading}
            />
          )}

          {showResults && (
            <div>
              <div className="flex items-center justify-between mb-6">
                <div>
                  <h2 className="text-2xl font-bold text-gray-900">{result.project_name}</h2>
                  <p className="text-sm text-gray-500">Analysis complete · Session {result.session_id.slice(0, 8)}</p>
                </div>
                <button
                  onClick={reset}
                  className="text-sm text-brand-600 hover:text-brand-700 font-medium px-4 py-2 border border-brand-200 rounded-lg bg-brand-50/50"
                >
                  + New Analysis
                </button>
              </div>
              <ResultsView result={result} onResume={resume} isResuming={loading} />
            </div>
          )}
        </main>

        {/* Chat sidebar */}
        {showResults && (
          <aside className="w-96 lg:w-[440px] shrink-0 border-l border-gray-200 bg-white h-full flex flex-col min-h-0 overflow-hidden">
            <ChatPanel sessionId={result.session_id} />
          </aside>
        )}
      </div>
    </div>
  );
}
