import {
  AgentEvent,
  EvaluationData,
  Paper,
  ResearchConfigInput,
  ResearchIteration,
  ResearchResultData,
  ResearchRun,
  Theme,
} from '../types';

const API_BASE = '/api';

export async function createResearch(
  research_question: string,
  config?: ResearchConfigInput
): Promise<ResearchRun> {
  const res = await fetch(`${API_BASE}/research`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ research_question, config }),
  });
  if (!res.ok) {
    const errorData = await res.json().catch(() => ({ detail: 'Network error' }));
    let message = 'Failed to start research run';
    if (typeof errorData.detail === 'string') {
      message = errorData.detail;
    } else if (Array.isArray(errorData.detail) && errorData.detail.length > 0) {
      message = errorData.detail.map((d: any) => d.msg || JSON.stringify(d)).join('; ');
    }
    throw new Error(message);
  }
  return res.json();
}

export async function listResearchRuns(limit = 50): Promise<ResearchRun[]> {
  const res = await fetch(`${API_BASE}/research?limit=${limit}`);
  if (!res.ok) throw new Error('Failed to fetch research history');
  return res.json();
}

export async function getResearchRun(runId: string): Promise<ResearchRun> {
  const res = await fetch(`${API_BASE}/research/${runId}`);
  if (!res.ok) throw new Error(`Run ${runId} not found`);
  return res.json();
}

export async function getIterations(runId: string): Promise<ResearchIteration[]> {
  const res = await fetch(`${API_BASE}/research/${runId}/iterations`);
  if (!res.ok) throw new Error('Failed to fetch iterations');
  return res.json();
}

export async function getPapers(
  runId: string,
  params?: {
    is_relevant?: boolean;
    source?: string;
    min_relevance?: number;
    search?: string;
    sort_by?: string;
  }
): Promise<Paper[]> {
  const query = new URLSearchParams();
  if (params?.is_relevant !== undefined) query.set('is_relevant', String(params.is_relevant));
  if (params?.source) query.set('source', params.source);
  if (params?.min_relevance !== undefined) query.set('min_relevance', String(params.min_relevance));
  if (params?.search) query.set('search', params.search);
  if (params?.sort_by) query.set('sort_by', params.sort_by);

  const res = await fetch(`${API_BASE}/research/${runId}/papers?${query.toString()}`);
  if (!res.ok) throw new Error('Failed to fetch papers');
  return res.json();
}

export async function getThemes(runId: string): Promise<Theme[]> {
  const res = await fetch(`${API_BASE}/research/${runId}/themes`);
  if (!res.ok) throw new Error('Failed to fetch themes');
  return res.json();
}

export async function getEvents(runId: string, afterId?: string): Promise<AgentEvent[]> {
  const query = afterId ? `?after_id=${encodeURIComponent(afterId)}` : '';
  const res = await fetch(`${API_BASE}/research/${runId}/events${query}`);
  if (!res.ok) throw new Error('Failed to fetch events');
  return res.json();
}

export async function getResult(runId: string): Promise<ResearchResultData> {
  const res = await fetch(`${API_BASE}/research/${runId}/result`);
  if (!res.ok) throw new Error('Failed to fetch research result');
  return res.json();
}

export async function getEvaluation(runId: string): Promise<EvaluationData> {
  const res = await fetch(`${API_BASE}/research/${runId}/evaluation`);
  if (!res.ok) throw new Error('Failed to fetch evaluation');
  return res.json();
}

export async function cancelRun(runId: string): Promise<{ cancelled: boolean }> {
  const res = await fetch(`${API_BASE}/research/${runId}/cancel`, { method: 'POST' });
  if (!res.ok) throw new Error('Failed to cancel run');
  return res.json();
}

export async function getHealth(): Promise<{ status: string; mode: string; is_mock_mode: boolean }> {
  const res = await fetch(`${API_BASE}/health`);
  if (!res.ok) throw new Error('Failed to query health');
  return res.json();
}

export function subscribeEvents(
  runId: string,
  onEvent: (event: any) => void,
  onError?: (err: any) => void
): () => void {
  const es = new EventSource(`${API_BASE}/research/${runId}/events/stream`);

  es.onmessage = (e) => {
    try {
      const data = JSON.parse(e.data);
      onEvent(data);
    } catch (err) {
      // ping or keepalive
    }
  };

  const eventTypes = [
    'connected',
    'research.started',
    'planner.started',
    'planner.completed',
    'retrieval.started',
    'retrieval.completed',
    'retrieval.failed',
    'filter.completed',
    'synthesis.started',
    'synthesis.completed',
    'reflection.started',
    'reflection.completed',
    'replanning.started',
    'replanning.completed',
    'research.completed',
    'research.failed',
    'research.cancelled',
  ];

  for (const t of eventTypes) {
    es.addEventListener(t, (e: MessageEvent) => {
      try {
        const data = JSON.parse(e.data);
        onEvent({ ...data, event_type: t });
      } catch (err) {
        onEvent({ event_type: t });
      }
    });
  }

  es.onerror = (err) => {
    if (onError) onError(err);
  };

  return () => {
    es.close();
  };
}
