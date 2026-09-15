import { useCallback, useState } from 'react';
import { analyzeRequirements, discoverRequirements, confirmRequirements, fetchHistoryItem, resumeAnalysis } from '../api/client';
import type { AnalysisResponse, AnalyzeRequest, DiscoveredRequirements, ValidatedRequirementsContext } from '../types';

export function useAnalysis() {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [discovered, setDiscovered] = useState<DiscoveredRequirements | null>(null);
  const [intake, setIntake] = useState<AnalyzeRequest | null>(null);
  const [result, setResult] = useState<AnalysisResponse | null>(null);
  const [progress, setProgress] = useState(0);

  const discover = useCallback(async (request: AnalyzeRequest, files?: File[]) => {
    setLoading(true);
    setError(null);
    setDiscovered(null);
    setResult(null);
    setIntake(request);
    try {
      const response = await discoverRequirements(request, files);
      setDiscovered(response);
      return response;
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Requirements discovery failed.';
      setError(message);
      throw err;
    } finally {
      setLoading(false);
    }
  }, []);

  const confirmAndAnalyze = useCallback(async (validatedContext: ValidatedRequirementsContext) => {
    if (!discovered || !intake) {
      setError('Missing discovery session context.');
      return;
    }

    setLoading(true);
    setError(null);
    setProgress(0);

    const progressInterval = setInterval(() => {
      setProgress((p) => Math.min(p + 3, 90));
    }, 1200);

    try {
      const response = await confirmRequirements({
        session_id: discovered.session_id,
        intake,
        validated_context: validatedContext,
      });
      setResult(response);
      setDiscovered(null);
      setProgress(100);
      return response;
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Architecture analysis failed.';
      setError(message);
      throw err;
    } finally {
      clearInterval(progressInterval);
      setLoading(false);
    }
  }, [discovered, intake]);

  const analyze = useCallback(async (request: AnalyzeRequest, files?: File[]) => {
    setLoading(true);
    setError(null);
    setResult(null);
    setProgress(0);

    const progressInterval = setInterval(() => {
      setProgress((p) => Math.min(p + 2, 90));
    }, 1500);

    try {
      const response = await analyzeRequirements(request, files);
      setResult(response);
      setProgress(100);
      return response;
    } catch (err) {
      const message =
        err instanceof Error ? err.message : 'Analysis failed. Please try again.';
      setError(message);
      throw err;
    } finally {
      clearInterval(progressInterval);
      setLoading(false);
    }
  }, []);

  const loadSavedAnalysis = useCallback(async (sessionId: string) => {
    setLoading(true);
    setError(null);
    setResult(null);
    setDiscovered(null);
    try {
      const response = await fetchHistoryItem(sessionId);
      setResult(response);
      return response;
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Failed to load saved analysis.';
      setError(message);
    } finally {
      setLoading(false);
    }
  }, []);

  const resume = useCallback(async (sessionId: string) => {
    setLoading(true);
    setError(null);
    setProgress(0);

    const progressInterval = setInterval(() => {
      setProgress((p) => Math.min(p + 3, 90));
    }, 1200);

    try {
      const response = await resumeAnalysis(sessionId);
      setResult(response);
      setProgress(100);
      return response;
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Resuming analysis failed.';
      setError(message);
      throw err;
    } finally {
      clearInterval(progressInterval);
      setLoading(false);
    }
  }, []);

  const reset = useCallback(() => {
    setResult(null);
    setDiscovered(null);
    setIntake(null);
    setError(null);
    setProgress(0);
  }, []);

  return {
    loading,
    error,
    discovered,
    result,
    progress,
    discover,
    confirmAndAnalyze,
    analyze,
    loadSavedAnalysis,
    resume,
    reset,
  };
}
