import { useState, type FC } from 'react';
import Header from './components/Layout/Header';
import Sidebar, { type SidebarTab } from './components/Layout/Sidebar';
import ChatPanel from './components/Chat/ChatPanel';
import TravelStatePanel from './components/trip/TravelStatePanel';
import ItineraryPanel from './components/trip/ItineraryPanel';
import BudgetPanel from './components/trip/BudgetPanel';
import FlightResults from './components/flights/FlightResults';
import HotelResults from './components/hotels/HotelResults';
import ActivityResults from './components/activities/ActivityResults';
import WeatherWidget from './components/weather/WeatherWidget';
import MapPanel from './components/Map/MapPanel';
import { useChat } from './hooks/useChat';
import {
  Sparkles,
  Compass,
  ArrowRight,
  ShieldCheck,
  Zap,
  Globe,
  Map as MapIcon,
  Columns,
  Maximize2,
} from 'lucide-react';
import './App.css';

const App: FC = () => {
  const {
    messages,
    tripData,
    isLoading,
    sessionId,
    sendUserMessage,
    retryLast,
    clearSession,
  } = useChat();

  const [activeTab, setActiveTab] = useState<SidebarTab>('itinerary');
  const [showLanding, setShowLanding] = useState<boolean>(true);
  const [layoutMode, setLayoutMode] = useState<'standard' | 'split-map'>('standard');

  const hasStartedConversation = messages.length > 0;
  const isLandingVisible = showLanding && !hasStartedConversation;
  const markerCount = tripData.map_data?.markers?.length || 0;

  const handleStartPlanning = (initialPrompt?: string) => {
    setShowLanding(false);
    if (initialPrompt) {
      sendUserMessage(initialPrompt);
    }
  };

  const handleNewTrip = () => {
    clearSession();
    setShowLanding(true);
    setActiveTab('itinerary');
    setLayoutMode('standard');
  };

  const handleUserSend = async (text: string) => {
    setShowLanding(false);
    await sendUserMessage(text);
  };

  return (
    <div className="travelos-app">
      <Header onNewTrip={handleNewTrip} sessionId={sessionId} />

      {isLandingVisible ? (
        <main className="landing-view animate-fade-in">
          <section className="landing-hero">
            <div className="hero-badge">
              <Sparkles size={14} className="hero-badge-icon" />
              <span>Next-Generation Travel Intelligence</span>
            </div>
            <h1 className="hero-title">
              Plan your next journey with <span className="gradient-text">AI</span>.
            </h1>
            <p className="hero-description">
              Tell TravelOS where you want to go, what you love, and how you want to travel.
              Every destination, flight, stay, and sight is dynamically mapped and planned in real time.
            </p>

            <div className="hero-actions">
              <button
                id="hero-plan-btn"
                className="btn-primary-hero"
                onClick={() => handleStartPlanning()}
              >
                Plan a Trip
                <ArrowRight size={16} />
              </button>
              <button
                id="hero-explore-btn"
                className="btn-secondary-hero"
                onClick={() => handleStartPlanning('Explore top trending destinations in Asia and Europe')}
              >
                <Compass size={16} />
                Explore Destinations
              </button>
            </div>

            {/* Quick Inspiration Cards */}
            <div className="inspiration-section">
              <h2 className="inspiration-heading">Popular Journeys</h2>
              <div className="inspiration-cards">
                <div
                  className="inspire-card card"
                  onClick={() => handleStartPlanning('Plan a 7-day cultural and culinary trip to Tokyo and Kyoto for 2 people')}
                >
                  <div className="inspire-tag">Japan</div>
                  <h3>Tokyo & Kyoto Journey</h3>
                  <p>7 days · Culture, Michelin Ramen & Historic Temples</p>
                </div>
                <div
                  className="inspire-card card"
                  onClick={() => handleStartPlanning('Plan a 5-day romantic getaway to Paris and French countryside')}
                >
                  <div className="inspire-tag">France</div>
                  <h3>Parisian Romance</h3>
                  <p>5 days · Art, Wine Tasting & Iconic Landmarks</p>
                </div>
                <div
                  className="inspire-card card"
                  onClick={() => handleStartPlanning('Plan a 6-day budget adventure trip in Bali with surfing and nature')}
                >
                  <div className="inspire-tag">Indonesia</div>
                  <h3>Bali Nature & Surf</h3>
                  <p>6 days · Beaches, Waterfalls & Ubud Culture</p>
                </div>
              </div>
            </div>

            {/* Features Bar */}
            <div className="features-strip">
              <div className="feature-item">
                <Globe size={16} /> Live Geographical Mapping
              </div>
              <div className="feature-item">
                <Zap size={16} /> Instant Route & Hotel Plotting
              </div>
              <div className="feature-item">
                <ShieldCheck size={16} /> Multi-Agent Intelligence
              </div>
            </div>
          </section>
        </main>
      ) : (
        <div className={`workspace-layout layout-${layoutMode} animate-fade-in`}>
          {/* Left / Main Chat Panel */}
          <div className="workspace-chat-container">
            <TravelStatePanel state={tripData.travel_state} />
            <ChatPanel
              messages={messages}
              isLoading={isLoading}
              latestStatuses={tripData.agent_statuses}
              onSend={handleUserSend}
              onRetry={retryLast}
            />
          </div>

          {/* Right Panels with Sidebar Navigation */}
          <div className="workspace-results-container">
            {/* Top Workspace Bar with Map Reflection Status & Layout Switcher */}
            <div className="results-top-strip glass">
              <div className="map-reflection-indicator">
                <span className="reflection-pulse-dot" />
                <span className="reflection-text">
                  {markerCount > 0
                    ? `🗺️ ${markerCount} location${markerCount > 1 ? 's' : ''} mapped`
                    : '🗺️ Map synced with AI'}
                </span>
              </div>

              <div className="layout-toggle-group">
                <button
                  className={`layout-btn ${layoutMode === 'standard' ? 'active' : ''}`}
                  onClick={() => setLayoutMode('standard')}
                  title="Tabbed workspace view"
                >
                  <Columns size={13} />
                  <span>Panels</span>
                </button>
                <button
                  className={`layout-btn ${layoutMode === 'split-map' ? 'active' : ''}`}
                  onClick={() => setLayoutMode('split-map')}
                  title="Split view with permanent map"
                >
                  <MapIcon size={13} />
                  <span>Split Map</span>
                </button>
              </div>
            </div>

            {layoutMode === 'split-map' ? (
              /* Split Layout: Map is permanently visible on top, tabbed panels below */
              <div className="split-map-view">
                <div className="split-map-upper">
                  <MapPanel
                    mapData={tripData.map_data}
                    onPromptSend={handleUserSend}
                  />
                </div>
                <div className="split-panels-lower">
                  <Sidebar
                    activeTab={activeTab}
                    onTabChange={setActiveTab}
                    tripData={tripData}
                  />
                  <div className="split-panel-content">
                    {activeTab === 'map' && (
                      <div className="mini-map-tab-hint">
                        <Maximize2 size={16} />
                        <p>Map is live in the upper viewport above.</p>
                      </div>
                    )}
                    {activeTab === 'itinerary' && <ItineraryPanel itinerary={tripData.itinerary} />}
                    {activeTab === 'hotels' && <HotelResults hotels={tripData.hotels} onPromptSend={handleUserSend} />}
                    {activeTab === 'flights' && <FlightResults flights={tripData.flights} onPromptSend={handleUserSend} />}
                    {activeTab === 'activities' && (
                      <ActivityResults
                        activities={tripData.activities}
                        onPromptSend={handleUserSend}
                      />
                    )}
                    {activeTab === 'budget' && (
                      <BudgetPanel
                        budget={tripData.budget}
                        onPromptSend={handleUserSend}
                      />
                    )}
                    {activeTab === 'weather' && <WeatherWidget weather={tripData.weather} />}
                  </div>
                </div>
              </div>
            ) : (
              /* Standard Full Tab View */
              <div className="standard-results-view">
                <Sidebar
                  activeTab={activeTab}
                  onTabChange={setActiveTab}
                  tripData={tripData}
                />
                <div className="workspace-active-panel">
                  {activeTab === 'map' && (
                    <MapPanel
                      mapData={tripData.map_data}
                      onPromptSend={handleUserSend}
                    />
                  )}
                  {activeTab === 'itinerary' && <ItineraryPanel itinerary={tripData.itinerary} />}
                  {activeTab === 'hotels' && <HotelResults hotels={tripData.hotels} onPromptSend={handleUserSend} />}
                  {activeTab === 'flights' && <FlightResults flights={tripData.flights} onPromptSend={handleUserSend} />}
                  {activeTab === 'activities' && (
                    <ActivityResults
                      activities={tripData.activities}
                      onPromptSend={handleUserSend}
                    />
                  )}
                  {activeTab === 'budget' && (
                    <BudgetPanel
                      budget={tripData.budget}
                      onPromptSend={handleUserSend}
                    />
                  )}
                  {activeTab === 'weather' && <WeatherWidget weather={tripData.weather} />}
                </div>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
};

export default App;
