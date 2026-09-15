import axios from 'axios';
import type {
  AnalysisResponse,
  AnalyzeRequest,
  ChatMessage,
  ChatResponse,
  ConfirmRequirementsRequest,
  DiscoveredRequirements,
  HealthStatus,
  HistoryItem,
} from '../types';

const API_BASE = import.meta.env.VITE_API_URL || '/api/v1';

const client = axios.create({
  baseURL: API_BASE,
  timeout: 300000,
});

export async function discoverRequirements(
  request: AnalyzeRequest,
  files?: File[]
): Promise<DiscoveredRequirements> {
  const formData = new FormData();
  formData.append('request', JSON.stringify(request));
  if (files && files.length > 0) {
    files.forEach((file) => formData.append('files', file));
  }
  const { data } = await client.post<DiscoveredRequirements>(
    '/analyze/requirements-discovery',
    formData,
    { headers: { 'Content-Type': 'multipart/form-data' } }
  );
  return data;
}

export async function confirmRequirements(
  payload: ConfirmRequirementsRequest
): Promise<AnalysisResponse> {
  const { data } = await client.post<AnalysisResponse>(
    '/analyze/confirm',
    payload,
    { headers: { 'Content-Type': 'application/json' } }
  );
  return data;
}

export async function analyzeRequirements(
  request: AnalyzeRequest,
  files?: File[]
): Promise<AnalysisResponse> {
  const formData = new FormData();
  formData.append('request', JSON.stringify(request));
  
  if (files && files.length > 0) {
    files.forEach((file) => {
      formData.append('files', file);
    });
  }

  const { data } = await client.post<AnalysisResponse>('/analyze', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  });
  return data;
}

export async function sendChatMessage(
  sessionId: string,
  message: string
): Promise<ChatResponse> {
  const { data } = await client.post<ChatResponse>('/chat', {
    session_id: sessionId,
    message,
  }, {
    headers: { 'Content-Type': 'application/json' },
  });
  return data;
}

export async function fetchChatHistory(sessionId: string): Promise<ChatMessage[]> {
  const { data } = await client.get<ChatMessage[]>(`/chat/${sessionId}`);
  return data;
}

export async function fetchHistory(): Promise<HistoryItem[]> {

  const { data } = await client.get<HistoryItem[]>('/history');
  return data;
}

export async function fetchHistoryItem(sessionId: string): Promise<AnalysisResponse> {
  const { data } = await client.get<AnalysisResponse>(`/history/${sessionId}`);
  return data;
}

export async function resumeAnalysis(sessionId: string): Promise<AnalysisResponse> {
  const { data } = await client.post<AnalysisResponse>(`/analyze/resume/${sessionId}`);
  return data;
}

export function getExportMarkdownUrl(sessionId: string): string {
  return `${API_BASE}/history/${sessionId}/export/markdown`;
}

export async function checkHealth(): Promise<HealthStatus> {
  const { data } = await client.get<HealthStatus>('/health');
  return data;
}

export default client;
