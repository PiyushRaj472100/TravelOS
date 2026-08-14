import { Plane, Map, Globe, Sparkles } from 'lucide-react';
import type { FC } from 'react';
import './Header.css';

interface HeaderProps {
  onNewTrip: () => void;
  sessionId: string | null;
}

const Header: FC<HeaderProps> = ({ onNewTrip, sessionId }) => {
  return (
    <header className="header glass-strong">
      <div className="header-brand">
        <div className="header-logo">
          <div className="logo-orbit">
            <Globe size={20} />
          </div>
          <Plane size={14} className="logo-plane" />
        </div>
        <div className="header-title">
          <span className="header-name gradient-text">TravelOS</span>
          <span className="header-tagline">AI Travel Planning</span>
        </div>
      </div>

      <div className="header-center">
        <div className="header-badge">
          <Sparkles size={12} />
          <span>Multi-Agent AI</span>
        </div>
        <div className="header-status-dots">
          <span className="dot dot-green" title="Research Agent" />
          <span className="dot dot-blue" title="Hotel Agent" />
          <span className="dot dot-purple" title="Itinerary Agent" />
          <span className="dot dot-gold" title="Budget Agent" />
        </div>
      </div>

      <div className="header-actions">
        {sessionId && (
          <span className="session-chip">
            <span className="session-indicator" />
            Active session
          </span>
        )}
        <button
          id="new-trip-btn"
          className="btn-new-trip"
          onClick={onNewTrip}
          title="Start a new trip"
        >
          <Map size={14} />
          New Trip
        </button>
      </div>
    </header>
  );
};

export default Header;
