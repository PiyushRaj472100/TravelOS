import { useState, type FC } from 'react';
import { Plane, ArrowUpDown } from 'lucide-react';
import type { FlightResult } from '../../types';
import FlightCard from './FlightCard';
import EmptyState from '../common/EmptyState';
import './FlightResults.css';

type SortKey = 'default' | 'price' | 'duration' | 'stops';

function sortFlights(flights: FlightResult[], key: SortKey): FlightResult[] {
  if (key === 'default') return flights;
  return [...flights].sort((a, b) => {
    if (key === 'price') return (a.price ?? Infinity) - (b.price ?? Infinity);
    if (key === 'duration') return (a.duration_minutes ?? Infinity) - (b.duration_minutes ?? Infinity);
    if (key === 'stops') return (a.stops ?? Infinity) - (b.stops ?? Infinity);
    return 0;
  });
}

interface FlightResultsProps {
  flights: FlightResult[];
  onPromptSend?: (prompt: string) => void;
}

const FlightResults: FC<FlightResultsProps> = ({ flights, onPromptSend }) => {
  const [sort, setSort] = useState<SortKey>('default');

  if (!flights.length) {
    return (
      <EmptyState
        icon={<Plane size={28} />}
        title="No flights yet"
        description='Ask TravelOS to find flights. Example: "Find flights from Delhi to Tokyo in October"'
      />
    );
  }

  const sorted = sortFlights(flights, sort);

  return (
    <div className="flight-results">
      {/* Sort bar */}
      <div className="flight-sort-bar">
        <ArrowUpDown size={13} />
        <span className="sort-label">Sort by:</span>
        {(['default', 'price', 'duration', 'stops'] as SortKey[]).map(k => (
          <button
            key={k}
            className={`sort-btn ${sort === k ? 'active' : ''}`}
            onClick={() => setSort(k)}
          >
            {k === 'default' ? 'Recommended' : k.charAt(0).toUpperCase() + k.slice(1)}
          </button>
        ))}
      </div>

      <p className="flight-count">{flights.length} flight{flights.length !== 1 ? 's' : ''} found</p>

      <div className="flight-list">
        {sorted.map((f, i) => (
          <FlightCard key={f.option_id ?? i} flight={f} index={i} onPromptSend={onPromptSend} />
        ))}
      </div>
    </div>
  );
};

export default FlightResults;
