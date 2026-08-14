// TravelOS — centralised API layer
// All backend communication goes through here — no raw fetch in components

import type { ChatRequest, ChatResponse } from '../types';

const API_BASE = (import.meta.env.VITE_API_URL as string) || '';

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
