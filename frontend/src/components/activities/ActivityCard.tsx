import type { FC } from 'react';
import { Clock, MapPin, DollarSign, Compass, RefreshCw, Trash2 } from 'lucide-react';
import type { Activity } from '../../types';
import './ActivityCard.css';

const TYPE_ICONS: Record<string, string> = {
  cultural: '🏛️',
  food: '🍜',
  nature: '🌿',
  shopping: '🛍️',
  entertainment: '🎭',
  sightseeing: '📷',
  adventure: '🧗',
  wellness: '🧘',
};

const TYPE_COLORS: Record<string, string> = {
  cultural: 'var(--brand-gold)',
  food: 'var(--brand-rose)',
  nature: 'var(--brand-emerald)',
  sightseeing: 'var(--brand-accent)',
  adventure: '#f97316',
};

interface ActivityCardProps {
  activity: Activity;
  index: number;
  onPromptSend?: (prompt: string) => void;
}

const ActivityCard: FC<ActivityCardProps> = ({ activity, index, onPromptSend }) => {
  const typeKey = (activity.type ?? '').toLowerCase();
  const icon = TYPE_ICONS[typeKey] ?? '✨';
  const color = TYPE_COLORS[typeKey] ?? 'var(--brand-primary)';
  const cost = activity.estimated_cost_per_person ?? 0;
  const currency = activity.cost_currency ?? 'USD';
  const isFree = cost === 0;
  const tier = activity.cost_tier ?? (isFree || cost < 1000 ? 'budget' : (cost > 5000 ? 'premium' : 'moderate'));

  return (
    <article
      className={`activity-card card animate-slide-up tier-${tier}`}
      style={{ animationDelay: `${index * 40}ms`, '--activity-color': color } as React.CSSProperties}
      aria-label={`Activity: ${activity.name}`}
    >
      <div className="activity-type-bar" />

      <div className="activity-header">
        <span className="activity-type-icon">{icon}</span>
        <div className="activity-meta">
          {activity.type && (
            <span className="activity-type-label">{activity.type}</span>
          )}
          {activity.area && (
            <span className="activity-area">
              <MapPin size={9} />
              {activity.area}
            </span>
          )}
        </div>
        <div className="activity-badges-right">
          <span className={`tier-badge tier-${tier}`}>
            {tier === 'budget' ? (isFree ? 'Free' : 'In Budget') : (tier === 'premium' ? 'Premium' : 'Moderate')}
          </span>
          {activity.day_suggestion && (
            <span className="activity-day-badge">Day {activity.day_suggestion}</span>
          )}
        </div>
      </div>

      <h3 className="activity-name">{activity.name}</h3>

      {activity.description && (
        <p className="activity-description">{activity.description}</p>
      )}

      {activity.highlights && activity.highlights.length > 0 && (
        <div className="activity-highlights">
          {activity.highlights.slice(0, 3).map(h => (
            <span key={h} className="highlight-tag">{h}</span>
          ))}
        </div>
      )}

      <div className="activity-footer">
        {activity.duration_hours && (
          <span className="activity-stat">
            <Clock size={11} />
            {activity.duration_hours}h
          </span>
        )}
        {activity.best_time && (
          <span className="activity-stat">
            <Compass size={11} />
            {activity.best_time}
          </span>
        )}
        <span className={`activity-stat activity-cost ${isFree ? 'cost-free' : ''}`}>
          <DollarSign size={11} />
          {isFree ? 'Free Admission' : `${currency} ${cost.toLocaleString()}`}
          {activity.cost_note && !isFree ? ` (${activity.cost_note})` : ''}
        </span>
      </div>

      {/* Interactive AI Actions Bar */}
      {onPromptSend && (
        <div className="activity-action-bar">
          <button
            className="act-btn btn-replace"
            onClick={() => onPromptSend(`Give another option for ${activity.name}`)}
            title="Ask AI for a budget-friendly alternative"
          >
            <RefreshCw size={11} />
            <span>Give another option</span>
          </button>
          <button
            className="act-btn btn-leave"
            onClick={() => onPromptSend(`Leave ${activity.name}`)}
            title="Remove from trip and save budget"
          >
            <Trash2 size={11} />
            <span>Leave it</span>
          </button>
        </div>
      )}
    </article>
  );
};

export default ActivityCard;

