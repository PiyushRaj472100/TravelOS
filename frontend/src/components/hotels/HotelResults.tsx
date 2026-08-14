import type { FC } from 'react';
import { Hotel } from 'lucide-react';
import type { HotelResult } from '../../types';
import HotelCard from './HotelCard';
import EmptyState from '../common/EmptyState';
import './HotelResults.css';

interface HotelResultsProps {
  hotels: HotelResult[];
  onPromptSend?: (prompt: string) => void;
}

const HotelResults: FC<HotelResultsProps> = ({ hotels, onPromptSend }) => {
  if (!hotels.length) {
    return (
      <EmptyState
        icon={<Hotel size={28} />}
        title="No hotels yet"
        description='Ask TravelOS to find hotels. Example: "Show me hotels in Tokyo for 3 nights"'
      />
    );
  }

  return (
    <div className="hotel-results">
      <p className="hotel-results-count">
        {hotels.length} hotel{hotels.length !== 1 ? 's' : ''} found
      </p>
      <div className="hotel-grid">
        {hotels.map((h, i) => (
          <HotelCard key={h.id ?? i} hotel={h} index={i} onPromptSend={onPromptSend} />
        ))}
      </div>
    </div>
  );
};

export default HotelResults;
