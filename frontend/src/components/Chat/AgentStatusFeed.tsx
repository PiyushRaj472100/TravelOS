import type { FC } from 'react';
import type { AgentStatus } from '../../types';
import './AgentStatusFeed.css';

const AGENT_ICONS: Record<string, string> = {
  research: '🔍',
  hotel: '🏨',
  activities: '🗺️',
  itinerary: '📅',
  budget: '💰',
  flights: '✈️',
  weather: '🌤️',
};

const AGENT_LABELS: Record<string, string> = {
  research: 'Research',
  hotel: 'Hotels',
  activities: 'Activities',
  itinerary: 'Itinerary',
  budget: 'Budget',
  flights: 'Flights',
  weather: 'Weather',
};

interface AgentStatusFeedProps {
  statuses: AgentStatus[];
  isLoading: boolean;
}

const AgentStatusFeed: FC<AgentStatusFeedProps> = ({ statuses, isLoading }) => {
  if (!isLoading && statuses.length === 0) return null;

  return (
    <div className="agent-feed" role="status" aria-live="polite">
      <div className="agent-feed-header">
        {isLoading && (
          <div className="thinking-dots">
            <span />
            <span />
            <span />
          </div>
        )}
        <span className="agent-feed-title">
          {isLoading ? 'AI agents working…' : 'Agents completed'}
        </span>
      </div>
      <div className="agent-chips">
        {statuses.map((s, i) => (
          <div
            key={`${s.agent}-${i}`}
            className={`agent-chip status-${s.status}`}
          >
            <span className="agent-chip-icon">
              {AGENT_ICONS[s.agent] ?? '🤖'}
            </span>
            <span className="agent-chip-name">
              {AGENT_LABELS[s.agent] ?? s.agent}
            </span>
            <span className={`agent-chip-dot status-dot-${s.status}`} />
          </div>
        ))}
      </div>
    </div>
  );
};

export default AgentStatusFeed;
