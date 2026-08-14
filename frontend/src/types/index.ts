// TravelOS — TypeScript type definitions
// Derived from the actual backend Pydantic models

// ================================================================
// Geo / Location
// ================================================================

export interface GeoLocation {
  name: string;
  country?: string;
  region?: string;
  city?: string;
  latitude?: number;
  longitude?: number;
  location_type?: string;
}

export interface TravelLeg {
  from_location: GeoLocation;
  to_location: GeoLocation;
  order: number;
  distance_km?: number;
  estimated_duration_minutes?: number;
  transportation?: string;
}

// ================================================================
// Travel State (mirrors backend TravelState model exactly)
// ================================================================

export interface TravelState {
  origin?: string;
  destinations: string[];
  countries: string[];
  regions: string[];
  cities: string[];
  start_date?: string;
  end_date?: string;
  duration_days?: number;
  travelers?: number;
  traveler_type?: string;
  budget?: number;
  currency?: string;
  interests: string[];
  travel_style?: string;
  pace?: string;
  accommodation_preference?: string;
  transportation_preference?: string;
  food_preferences: string[];
  itinerary: DayPlan[];
  hotels: HotelResult[];
  activities: Activity[];
  weather: Record<string, unknown>;
  locations: GeoLocation[];
  travel_legs: TravelLeg[];
  packing_list?: string[];
}

// ================================================================
// Agent Status — generic, not tied to specific agent names
// ================================================================

export interface AgentStatus {
  agent: string;        // any string — new agents can be added freely
  status: 'working' | 'done' | 'failed' | 'skipped';
  message?: string;
}

// ================================================================
// Budget
// ================================================================

export interface BudgetItem {
  label: string;
  amount?: number;
  currency?: string;
  is_live: boolean;
}

export interface BudgetBreakdown {
  total_budget?: number;
  currency?: string;
  flights?: number;
  hotels?: number;
  food?: number;
  activities?: number;
  transport?: number;
  remaining?: number;
  cost_per_day?: number;
  cost_per_person?: number;
  duration_days?: number;
  travelers?: number;
  items: BudgetItem[];
  note?: string;
}

// ================================================================
// Map Data
// ================================================================

export interface MapMarker {
  id: string;
  name: string;
  latitude: number;
  longitude: number;
  marker_type: 'destination' | 'hotel' | 'activity' | 'restaurant' | 'airport' | string;
  day?: number;
  description?: string;
}

export interface MapRoute {
  from_name: string;
  to_name: string;
  from_lat: number;
  from_lng: number;
  to_lat: number;
  to_lng: number;
  transport_type: 'flight' | 'train' | 'drive' | 'walk' | string;
  order: number;
}

export interface MapData {
  markers: MapMarker[];
  routes: MapRoute[];
  center_lat?: number;
  center_lng?: number;
  zoom?: number;
}

// ================================================================
// Sources (RAG / Research)
// ================================================================

export interface ChatSource {
  title?: string;
  source?: string;
  source_url?: string;
  fallback_search_url?: string;
  country?: string;
  region?: string;
  city?: string;
  category?: string;
  score?: number;
}

// ================================================================
// Flight
// ================================================================

export interface FlightResult {
  provider?: string;
  origin: string;
  destination: string;
  departure?: string;
  arrival?: string;
  duration_minutes?: number;
  stops: number;
  price?: number;
  currency?: string;
  option_id?: string;
  cabin_class?: string;
  booking_url?: string;
}

// ================================================================
// Hotel
// ================================================================

export interface HotelResult {
  id?: string;
  name: string;
  provider?: string;
  stars?: number;
  price?: number;
  currency?: string;
  published_rate?: number;
  savings?: number;
  distance?: number;
  image?: string;
  chain?: string;
  refundable?: boolean;
  breakfast_included?: boolean;
  facilities?: string[];
  address?: string;
  latitude?: number;
  longitude?: number;
}

// ================================================================
// Activity
// ================================================================

export interface Activity {
  id?: string;
  name: string;
  type?: string;
  description?: string;
  duration_hours?: number;
  estimated_cost_per_person?: number;
  cost_currency?: string;
  cost_tier?: 'budget' | 'moderate' | 'premium' | string;
  cost_note?: string;
  day_suggestion?: number;
  area?: string;
  highlights?: string[];
  best_time?: string;
  image?: string;
}

// ================================================================
// Itinerary
// ================================================================

export interface TimeSlot {
  time?: string;
  activity: string;
  description?: string;
  duration_hours?: number;
  type?: string;
  area?: string;
}

export interface DayPlan {
  day: number;
  date?: string;
  theme?: string;
  morning?: TimeSlot;
  afternoon?: TimeSlot;
  evening?: TimeSlot;
  meals?: { breakfast?: string; lunch?: string; dinner?: string };
  tips?: string[];
  estimated_daily_cost?: number;
  cost_currency?: string;
}

// ================================================================
// Weather
// ================================================================

export interface WeatherData {
  city?: string;
  country?: string;
  temperature?: number;
  apparent_temperature?: number;
  humidity?: number;
  wind_speed?: number;
  weather_code?: number;
  time?: string;
}

// ================================================================
// Chat Message (frontend-only, enriched)
// ================================================================

export interface ChatMessage {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp: number;
  // Enriched data from backend response
  flights?: FlightResult[];
  hotels?: HotelResult[];
  activities?: Activity[];
  itinerary?: DayPlan[];
  budget?: BudgetBreakdown;
  weather?: WeatherData;
  currency?: Record<string, unknown>;
  sources?: ChatSource[];
  agent_statuses?: AgentStatus[];
  /** CTA action signal: 'generate_itinerary' etc. */
  cta_action?: string | null;
  // Extension point: future capabilities can add new fields here
  [key: string]: unknown;
}

// ================================================================
// API Request / Response (mirrors backend exactly)
// ================================================================

export interface ChatRequest {
  message: string;
  session_id?: string | null;
}

export interface ChatResponse {
  session_id: string;
  message: string;
  missing_information: string[];
  travel_state: Record<string, unknown>;
  sources: ChatSource[];
  agent_statuses: AgentStatus[];
  flights: FlightResult[];
  hotels: HotelResult[];
  weather?: WeatherData;
  currency?: Record<string, unknown>;
  activities: Activity[];
  itinerary: DayPlan[];
  budget?: BudgetBreakdown;
  map_data?: MapData;
  /** CTA action signal from backend, e.g. 'generate_itinerary' */
  cta_action?: string | null;
}

// ================================================================
// Trip Data — aggregated from conversation responses
// ================================================================

export interface TripData {
  flights: FlightResult[];
  hotels: HotelResult[];
  activities: Activity[];
  itinerary: DayPlan[];
  budget?: BudgetBreakdown;
  weather?: WeatherData;
  currency?: Record<string, unknown>;
  map_data?: MapData;
  agent_statuses: AgentStatus[];
  sources: ChatSource[];
  travel_state?: Record<string, unknown>;
}
