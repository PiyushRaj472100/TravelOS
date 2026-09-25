// TravelOS — centralised API layer
// All backend communication goes through here — no raw fetch in components

import type { AgentStatus, ChatRequest, ChatResponse } from '../types';

const API_BASE =
  (import.meta.env.VITE_API_URL as string) ||
  'https://travelos-ncn1.onrender.com';

// ----------------------------------------------------------------
// Generic request helper
// ----------------------------------------------------------------
async function request<T>(
  path: string,
  options: RequestInit = {},
): Promise<T> {
  const url = `${API_BASE}${path}`;
  const res = await fetch(url, {
    headers: { 'Content-Type': 'application/json', ...options.headers },
    ...options,
  });

  if (!res.ok) {
    let detail = `HTTP ${res.status}`;
    try {
      const body = await res.json() as { detail?: string };
      detail = body.detail ?? detail;
    } catch {
      // ignore
    }
    throw new Error(detail);
  }

  return res.json() as Promise<T>;
}

// ----------------------------------------------------------------
// Chat — the single primary endpoint
// ----------------------------------------------------------------
export async function sendMessage(payload: ChatRequest): Promise<ChatResponse> {
  return request<ChatResponse>('/api/chat', {
    method: 'POST',
    body: JSON.stringify(payload),
  });
}

// ----------------------------------------------------------------
// Chat Stream — SSE endpoint for real-time agent updates
// ----------------------------------------------------------------
export async function sendMessageStream(
  payload: ChatRequest,
  onStatus?: (statuses: AgentStatus[]) => void,
): Promise<ChatResponse> {
  const url = `${API_BASE}/api/chat/stream`;
  try {
    const res = await fetch(url, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    });

    if (!res.ok || !res.body) {
      return sendMessage(payload);
    }

    const reader = res.body.getReader();
    const decoder = new TextDecoder();
    let buffer = '';
    let finalResponse: ChatResponse | null = null;

    while (true) {
      const { done, value } = await reader.read();
      if (done) break;

      buffer += decoder.decode(value, { stream: true });
      const lines = buffer.split('\n\n');
      buffer = lines.pop() ?? '';

      for (const line of lines) {
        const trimmed = line.trim();
        if (trimmed.startsWith('data: ')) {
          try {
            const data = JSON.parse(trimmed.slice(6));
            if (data.type === 'status' && Array.isArray(data.statuses)) {
              onStatus?.(data.statuses);
            } else if (data.type === 'complete' && data.response) {
              finalResponse = data.response as ChatResponse;
            }
          } catch {
            // ignore JSON parse errors in individual chunks
          }
        }
      }
    }

    if (finalResponse) {
      return finalResponse;
    }
  } catch (err) {
    console.warn('[TravelOS] Streaming failed, falling back to standard endpoint:', err);
  }

  return sendMessage(payload);
}

// ----------------------------------------------------------------
// Health check (for connection status indicator)
// ----------------------------------------------------------------
export async function healthCheck(): Promise<boolean> {
  try {
    await request<{ status: string }>('/healthz');
    return true;
  } catch {
    return false;
  }
}

// ----------------------------------------------------------------
// Extension point — add future endpoints here as they are created
// e.g.:
//   export async function getTrips(): Promise<Trip[]> { ... }
//   export async function saveTrip(trip: Trip): Promise<void> { ... }
// ----------------------------------------------------------------
