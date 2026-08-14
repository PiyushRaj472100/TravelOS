import type { FC } from 'react';
import { MapPin, Calendar, Users, DollarSign, Heart, Zap } from 'lucide-react';
import './TravelStatePanel.css';

interface TravelStatePanelProps {
  state?: Record<string, unknown>;
}

function getStr(v: unknown): string | null {
  if (typeof v === 'string' && v) return v;
  if (Array.isArray(v) && v.length > 0) return v.join(', ');
  return null;
}
function getArr(v: unknown): string[] {
  if (Array.isArray(v)) return v.filter(x => typeof x === 'string') as string[];
  return [];
}

const TravelStatePanel: FC<TravelStatePanelProps> = ({ state }) => {
  if (!state) return null;

  const destination = getStr(state.destinations) || getStr(state.cities);
  const dates = [state.start_date, state.end_date].filter(Boolean).join(' → ');
  const duration = state.duration_days as number | undefined;
  const travelers = state.travelers as number | undefined;
  const budget = state.budget as number | undefined;
  const currency = state.currency as string | undefined;
  const interests = getArr(state.interests);
  const travelStyle = state.travel_style as string | undefined;

  const hasAnyInfo = destination || dates || travelers || budget || interests.length;
  if (!hasAnyInfo) return null;

  return (
    <div className="travel-state-panel">
      <div className="state-panel-header">
        <Zap size={12} />
        <span>Trip understood so far</span>
      </div>
      <div className="state-chips">
        {destination && (
          <div className="state-chip">
            <MapPin size={11} />
            <span>{destination}</span>
          </div>
        )}
        {(dates || duration) && (
          <div className="state-chip">
            <Calendar size={11} />
            <span>
              {dates || (duration ? `${duration} days` : '')}
            </span>
          </div>
        )}
        {travelers && (
          <div className="state-chip">
            <Users size={11} />
            <span>{travelers} traveler{travelers !== 1 ? 's' : ''}</span>
          </div>
        )}
        {budget && (
          <div className="state-chip state-chip-budget">
            <DollarSign size={11} />
            <span>{currency ?? ''} {budget.toLocaleString()}</span>
          </div>
        )}
        {travelStyle && (
          <div className="state-chip state-chip-style">
            <span>{travelStyle}</span>
          </div>
        )}
        {interests.map(interest => (
          <div key={interest} className="state-chip state-chip-interest">
            <Heart size={9} />
            <span>{interest}</span>
          </div>
        ))}
      </div>
    </div>
  );
};

export default TravelStatePanel;
