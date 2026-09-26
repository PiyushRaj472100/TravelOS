import { useState, useCallback, useRef, useEffect } from 'react';
import { sendMessageStream } from '../api/chat';
import type {
  ChatMessage,
  ChatResponse,
  TripData,
} from '../types';

// ----------------------------------------------------------------
// Empty state helpers
// ----------------------------------------------------------------

const EMPTY_TRIP: TripData = {
  flights: [],
  hotels: [],
  activities: [],
  itinerary: [],
  budget: undefined,
  weather: undefined,
  currency: undefined,
  map_data: undefined,
  agent_statuses: [],
  sources: [],
  travel_state: undefined,
};

function msgFromResponse(
  role: 'user' | 'assistant',
  content: string,
  resp?: ChatResponse,
): ChatMessage {
  return {
    id: crypto.randomUUID(),
    role,
    content,
    timestamp: Date.now(),
    flights: resp?.flights,
    hotels: resp?.hotels,
    activities: resp?.activities,
    itinerary: resp?.itinerary,
    budget: resp?.budget,
    weather: resp?.weather,
    currency: resp?.currency,
    sources: resp?.sources,
    agent_statuses: resp?.agent_statuses,
    cta_action: resp?.cta_action ?? null,
  };
}

// ----------------------------------------------------------------
// Merge trip data: prefer new non-empty values over previous
// ----------------------------------------------------------------

function mergeMapData(prevMap?: TripData['map_data'], newMap?: TripData['map_data']) {
  if (!newMap || !newMap.markers || newMap.markers.length === 0) return prevMap;
  if (!prevMap || !prevMap.markers || prevMap.markers.length === 0) return newMap;

  const markerMap = new Map();
  (prevMap.markers || []).forEach(m => {
    const key = m.id || `${m.name}_${m.latitude}_${m.longitude}`;
    markerMap.set(key, m);
  });

  (newMap.markers || []).forEach(m => {
    const key = m.id || `${m.name}_${m.latitude}_${m.longitude}`;
    markerMap.set(key, m);
  });

  const mergedMarkers = Array.from(markerMap.values());
  const mergedRoutes = [...(newMap.routes || []), ...(prevMap.routes || [])].filter(
    (r, idx, self) => self.findIndex(x => x.from_name === r.from_name && x.to_name === r.to_name) === idx
  );

  return {
    markers: mergedMarkers,
    routes: mergedRoutes,
    center_lat: newMap.center_lat ?? prevMap.center_lat,
    center_lng: newMap.center_lng ?? prevMap.center_lng,
    zoom: newMap.zoom ?? prevMap.zoom,
  };
}

function mergeTripData(prev: TripData, resp: ChatResponse): TripData {
  return {
    flights: resp.flights?.length ? resp.flights : prev.flights,
    hotels: resp.hotels?.length ? resp.hotels : prev.hotels,
    activities: resp.activities?.length ? resp.activities : prev.activities,
    itinerary: resp.itinerary?.length ? resp.itinerary : prev.itinerary,
    budget: resp.budget ?? prev.budget,
    weather: resp.weather ?? prev.weather,
    currency: resp.currency ?? prev.currency,
    map_data: mergeMapData(prev.map_data, resp.map_data),
    agent_statuses: resp.agent_statuses ?? [],
    sources: resp.sources ?? [],
    travel_state: resp.travel_state ?? prev.travel_state,
  };
}


// Storage Keys for state persistence across reloads
const STORAGE_KEYS = {
  MESSAGES: 'travelos_chat_messages',
  TRIP_DATA: 'travelos_trip_data',
  SESSION_ID: 'travelos_session_id',
};

function loadStored<T>(key: string, fallback: T): T {
  try {
    const raw = localStorage.getItem(key);
    return raw ? JSON.parse(raw) : fallback;
  } catch {
    return fallback;
  }
}

function saveStored<T>(key: string, val: T): void {
  try {
    localStorage.setItem(key, JSON.stringify(val));
  } catch (err) {
    console.warn(`[TravelOS] Error saving ${key} to localStorage:`, err);
  }
}

// Hook
// ----------------------------------------------------------------

export interface UseChatResult {
  messages: ChatMessage[];
  tripData: TripData;
  isLoading: boolean;
  error: string | null;
  sessionId: string | null;
  sendUserMessage: (text: string) => Promise<void>;
  retryLast: () => Promise<void>;
  clearSession: () => void;
}

export function useChat(): UseChatResult {
  const [messages, setMessages] = useState<ChatMessage[]>(() =>
    loadStored<ChatMessage[]>(STORAGE_KEYS.MESSAGES, [])
  );
  const [tripData, setTripData] = useState<TripData>(() =>
    loadStored<TripData>(STORAGE_KEYS.TRIP_DATA, EMPTY_TRIP)
  );
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const sessionIdRef = useRef<string | null>(
    (() => {
      try {
        return localStorage.getItem(STORAGE_KEYS.SESSION_ID) || null;
      } catch {
        return null;
      }
    })()
  );
  const lastUserMessageRef = useRef<string>('');

  // Persist messages whenever updated
  useEffect(() => {
    saveStored(STORAGE_KEYS.MESSAGES, messages);
  }, [messages]);

  // Persist tripData whenever updated
  useEffect(() => {
    saveStored(STORAGE_KEYS.TRIP_DATA, tripData);
  }, [tripData]);

  const doSend = useCallback(async (text: string) => {
    if (!text.trim() || isLoading) return;

    lastUserMessageRef.current = text;
    setMessages(prev => [...prev, msgFromResponse('user', text)]);
    setIsLoading(true);
    setError(null);

    try {
      const resp = await sendMessageStream(
        {
          message: text,
          session_id: sessionIdRef.current,
        },
        (liveStatuses) => {
          setTripData(prev => ({
            ...prev,
            agent_statuses: liveStatuses,
          }));
        },
      );

      sessionIdRef.current = resp.session_id;
      try {
        if (resp.session_id) {
          localStorage.setItem(STORAGE_KEYS.SESSION_ID, resp.session_id);
        }
      } catch {}

      setMessages(prev => [
        ...prev,
        msgFromResponse('assistant', resp.message, resp),
      ]);
      setTripData(prev => mergeTripData(prev, resp));
    } catch (err) {
      const msg = err instanceof Error ? err.message : 'Unknown error';
      setError(msg);
      setMessages(prev => [
        ...prev,
        msgFromResponse(
          'assistant',
          "⚠️ I couldn't reach the TravelOS server. Please ensure the backend is running and try again.",
        ),
      ]);
      console.error('[TravelOS] API error:', err);
    } finally {
      setIsLoading(false);
    }
  }, [isLoading]);

  const sendUserMessage = useCallback((text: string) => doSend(text), [doSend]);
  const retryLast = useCallback(() => doSend(lastUserMessageRef.current), [doSend]);

  const clearSession = useCallback(() => {
    sessionIdRef.current = null;
    lastUserMessageRef.current = '';
    setMessages([]);
    setTripData(EMPTY_TRIP);
    setError(null);
    try {
      localStorage.removeItem(STORAGE_KEYS.MESSAGES);
      localStorage.removeItem(STORAGE_KEYS.TRIP_DATA);
      localStorage.removeItem(STORAGE_KEYS.SESSION_ID);
      localStorage.removeItem('travelos_active_tab');
      localStorage.removeItem('travelos_show_landing');
    } catch {}
  }, []);

  return {
    messages,
    tripData,
    isLoading,
    error,
    sessionId: sessionIdRef.current,
    sendUserMessage,
    retryLast,
    clearSession,
  };
}

