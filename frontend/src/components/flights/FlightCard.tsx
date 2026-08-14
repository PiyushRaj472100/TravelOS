import type { FC } from 'react';
import { Plane, Clock, ArrowRight } from 'lucide-react';
import type { FlightResult } from '../../types';
import './FlightCard.css';

function formatDuration(minutes?: number): string {
  if (!minutes) return '';
  const h = Math.floor(minutes / 60);
  const m = minutes % 60;
  return `${h}h ${m}m`;
}

function formatTime(isoString?: string): string {
  if (!isoString) return '';
  try {
    return new Date(isoString).toLocaleTimeString([], {
      hour: '2-digit',
      minute: '2-digit',
    });
  } catch {
    return isoString;
  }
}

interface FlightCardProps {
  flight: FlightResult;
  index: number;
  onPromptSend?: (prompt: string) => void;
}

const FlightCard: FC<FlightCardProps> = ({ flight, index, onPromptSend }) => {
  const stopsLabel =
    flight.stops === 0
      ? 'Nonstop'
      : flight.stops === 1
      ? '1 stop'
      : `${flight.stops} stops`;

  return (
    <article
      className="flight-card animate-slide-up card"
      style={{ animationDelay: `${index * 60}ms` }}
      aria-label={`Flight from ${flight.origin} to ${flight.destination}`}
    >
      {/* Header */}
      <div className="flight-card-header">
        <div className="flight-airline">
          <div className="airline-icon">
            <Plane size={14} />
          </div>
          <span className="airline-name">{flight.provider ?? 'Airline'}</span>
        </div>
        {index === 0 && (
          <span className="flight-badge">Best option</span>
        )}
      </div>

      {/* Route */}
      <div className="flight-route">
        <div className="flight-endpoint">
          <span className="flight-code">{flight.origin}</span>
          {flight.departure && (
            <span className="flight-time">{formatTime(flight.departure)}</span>
          )}
        </div>

        <div className="flight-middle">
          {formatDuration(flight.duration_minutes) && (
            <span className="flight-duration">
              <Clock size={10} />
              {formatDuration(flight.duration_minutes)}
            </span>
          )}
          <div className="flight-line">
            <span className="flight-dot" />
            <span className="flight-track" />
            <ArrowRight size={10} className="flight-arrow" />
          </div>
          <span className={`flight-stops ${flight.stops === 0 ? 'nonstop' : ''}`}>
            {stopsLabel}
          </span>
        </div>

        <div className="flight-endpoint flight-endpoint-right">
          <span className="flight-code">{flight.destination}</span>
          {flight.arrival && (
            <span className="flight-time">{formatTime(flight.arrival)}</span>
          )}
        </div>
      </div>

      {/* Footer */}
      <div className="flight-footer">
        <div className="flight-price">
          {flight.price ? (
            <>
              <span className="price-amount">
                {flight.currency && <span className="price-currency">{flight.currency} </span>}
                {flight.price.toLocaleString()}
              </span>
              <span className="price-label">per person (exact rate)</span>
            </>
          ) : (
            <span className="price-label">Price unavailable</span>
          )}
        </div>
        <div style={{ display: 'flex', gap: '8px' }}>
          {onPromptSend && flight.price && (
            <button
              type="button"
              className="flight-action-btn"
              onClick={() => onPromptSend(`Can flight from ${flight.origin} to ${flight.destination} at ${flight.price} ${flight.currency} fit in my budget?`)}
            >
              ✈️ Check Budget
            </button>
          )}
        </div>
      </div>
    </article>
  );
};

export default FlightCard;
