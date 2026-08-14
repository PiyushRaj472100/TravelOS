import { useState, useMemo, type FC } from 'react';
import { Activity as ActivityIcon, ArrowUpDown, Sparkles } from 'lucide-react';
import type { Activity as ActivityType } from '../../types';
import ActivityCard from './ActivityCard';
import EmptyState from '../common/EmptyState';
import './ActivityResults.css';

interface ActivityResultsProps {
  activities: ActivityType[];
  onPromptSend?: (prompt: string) => void;
}

type FilterTier = 'all' | 'budget' | 'moderate' | 'premium';
type SortOption = 'default' | 'price-asc' | 'price-desc' | 'duration';

const ActivityResults: FC<ActivityResultsProps> = ({ activities, onPromptSend }) => {
  const [selectedTier, setSelectedTier] = useState<FilterTier>('all');
  const [sortOption, setSortOption] = useState<SortOption>('default');

  if (!activities.length) {
    return (
      <EmptyState
        icon={<ActivityIcon size={28} />}
        title="No activities yet"
        description='Ask TravelOS what to do. Example: "What should I do in Tokyo?"'
      />
    );
  }

  // Filter activities
  const filtered = useMemo(() => {
    let list = [...activities];

    if (selectedTier !== 'all') {
      list = list.filter(a => {
        const cost = a.estimated_cost_per_person ?? 0;
        const tier = a.cost_tier ?? (cost === 0 || cost < 1000 ? 'budget' : (cost > 5000 ? 'premium' : 'moderate'));
        return tier === selectedTier;
      });
    }

    if (sortOption === 'price-asc') {
      list.sort((a, b) => (a.estimated_cost_per_person ?? 0) - (b.estimated_cost_per_person ?? 0));
    } else if (sortOption === 'price-desc') {
      list.sort((a, b) => (b.estimated_cost_per_person ?? 0) - (a.estimated_cost_per_person ?? 0));
    } else if (sortOption === 'duration') {
      list.sort((a, b) => (b.duration_hours ?? 0) - (a.duration_hours ?? 0));
    }

    return list;
  }, [activities, selectedTier, sortOption]);

  const budgetCount = activities.filter(a => {
    const cost = a.estimated_cost_per_person ?? 0;
    const tier = a.cost_tier ?? (cost === 0 || cost < 1000 ? 'budget' : 'other');
    return tier === 'budget';
  }).length;

  return (
    <div className="activity-results">
      {/* Controls Bar: Filters & Sorting */}
      <div className="activity-controls card">
        <div className="filter-tabs">
          <button
            className={`filter-btn ${selectedTier === 'all' ? 'active' : ''}`}
            onClick={() => setSelectedTier('all')}
          >
            All ({activities.length})
          </button>
          <button
            className={`filter-btn filter-in-budget ${selectedTier === 'budget' ? 'active' : ''}`}
            onClick={() => setSelectedTier('budget')}
          >
            ✨ In Budget ({budgetCount})
          </button>
          <button
            className={`filter-btn ${selectedTier === 'moderate' ? 'active' : ''}`}
            onClick={() => setSelectedTier('moderate')}
          >
            Moderate
          </button>
          <button
            className={`filter-btn ${selectedTier === 'premium' ? 'active' : ''}`}
            onClick={() => setSelectedTier('premium')}
          >
            Premium
          </button>
        </div>

        <div className="sort-wrapper">
          <ArrowUpDown size={12} className="sort-icon" />
          <select
            className="sort-select"
            value={sortOption}
            onChange={(e) => setSortOption(e.target.value as SortOption)}
            aria-label="Sort activities"
          >
            <option value="default">Itinerary Order</option>
            <option value="price-asc">Price: Low to High</option>
            <option value="price-desc">Price: High to Low</option>
            <option value="duration">Longest Duration</option>
          </select>
        </div>
      </div>

      <div className="activity-results-header">
        <p className="activity-results-count">
          Showing {filtered.length} of {activities.length} suggested experiences
        </p>
        {onPromptSend && (
          <button
            className="btn-quick-expensive-check"
            onClick={() => onPromptSend("What are the most expensive activities?")}
          >
            <Sparkles size={12} />
            <span>Check Expensive Activities</span>
          </button>
        )}
      </div>

      <div className="activity-grid">
        {filtered.map((a, i) => (
          <ActivityCard
            key={a.id ?? i}
            activity={a}
            index={i}
            onPromptSend={onPromptSend}
          />
        ))}
      </div>
    </div>
  );
};

export default ActivityResults;

