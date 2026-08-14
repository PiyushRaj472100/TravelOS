import { useState, type FC } from 'react';
import { CalendarDays, Sun, Coffee, Moon, Utensils, Lightbulb, ChevronDown, ChevronUp } from 'lucide-react';
import type { DayPlan, TimeSlot } from '../../types';
import EmptyState from '../common/EmptyState';
import './ItineraryPanel.css';

// ----------------------------------------------------------------
// Time slot renderers
// ----------------------------------------------------------------
interface SlotProps {
  slot?: TimeSlot;
  period: 'morning' | 'afternoon' | 'evening';
}

const PERIOD_ICONS = {
  morning: <Sun size={14} />,
  afternoon: <Coffee size={14} />,
  evening: <Moon size={14} />,
};

const Slot: FC<SlotProps> = ({ slot, period }) => {
  if (!slot) return null;
  return (
    <div className={`itin-slot itin-slot-${period}`}>
      <div className="slot-period-icon">{PERIOD_ICONS[period]}</div>
      <div className="slot-content">
        <div className="slot-header">
          {slot.time && <span className="slot-time">{slot.time}</span>}
          <span className="slot-activity">{slot.activity}</span>
        </div>
        {slot.description && (
          <p className="slot-description">{slot.description}</p>
        )}
        <div className="slot-meta">
          {slot.duration_hours && (
            <span className="slot-tag">{slot.duration_hours}h</span>
          )}
          {slot.type && (
            <span className="slot-tag slot-tag-type">{slot.type}</span>
          )}
          {slot.area && (
            <span className="slot-tag slot-tag-area">📍 {slot.area}</span>
          )}
        </div>
      </div>
    </div>
  );
};

// ----------------------------------------------------------------
// Day Card
// ----------------------------------------------------------------
interface DayCardProps {
  day: DayPlan;
  isOpen: boolean;
  onToggle: () => void;
}

const DayCard: FC<DayCardProps> = ({ day, isOpen, onToggle }) => (
  <article className={`day-card card ${isOpen ? 'day-card-open' : ''}`}>
    <button className="day-card-header" onClick={onToggle} aria-expanded={isOpen}>
      <div className="day-number-badge">
        <span className="day-number">Day {day.day}</span>
        {day.date && <span className="day-date">{day.date}</span>}
      </div>
      <div className="day-theme">
        {day.theme && <h3>{day.theme}</h3>}
        {day.estimated_daily_cost && (
          <span className="day-cost">
            ~{day.cost_currency ?? ''} {day.estimated_daily_cost}/day
          </span>
        )}
      </div>
      <span className="day-toggle-icon">
        {isOpen ? <ChevronUp size={16} /> : <ChevronDown size={16} />}
      </span>
    </button>

    {isOpen && (
      <div className="day-body animate-slide-up">
        <Slot slot={day.morning} period="morning" />
        <Slot slot={day.afternoon} period="afternoon" />
        <Slot slot={day.evening} period="evening" />

        {/* Meals */}
        {day.meals && (
          <div className="day-meals">
            <div className="meals-header">
              <Utensils size={12} />
              <span>Meals</span>
            </div>
            <div className="meals-grid">
              {day.meals.breakfast && (
                <div className="meal-item">
                  <span className="meal-label">Breakfast</span>
                  <span className="meal-name">{day.meals.breakfast}</span>
                </div>
              )}
              {day.meals.lunch && (
                <div className="meal-item">
                  <span className="meal-label">Lunch</span>
                  <span className="meal-name">{day.meals.lunch}</span>
                </div>
              )}
              {day.meals.dinner && (
                <div className="meal-item">
                  <span className="meal-label">Dinner</span>
                  <span className="meal-name">{day.meals.dinner}</span>
                </div>
              )}
            </div>
          </div>
        )}

        {/* Tips */}
        {day.tips && day.tips.length > 0 && (
          <div className="day-tips">
            <div className="tips-header">
              <Lightbulb size={12} />
              <span>Tips</span>
            </div>
            <ul className="tips-list">
              {day.tips.map((tip, i) => (
                <li key={i} className="tip-item">{tip}</li>
              ))}
            </ul>
          </div>
        )}
      </div>
    )}
  </article>
);

// ----------------------------------------------------------------
// ItineraryPanel
// ----------------------------------------------------------------
interface ItineraryPanelProps {
  itinerary: DayPlan[];
}

const ItineraryPanel: FC<ItineraryPanelProps> = ({ itinerary }) => {
  const [openDays, setOpenDays] = useState<Set<number>>(new Set([1]));

  if (!itinerary.length) {
    return (
      <EmptyState
        icon={<CalendarDays size={28} />}
        title="No itinerary yet"
        description='Ask TravelOS to build your trip plan. Example: "Plan my trip to Tokyo" or "Create the itinerary"'
      />
    );
  }

  const toggleDay = (day: number) =>
    setOpenDays(prev => {
      const next = new Set(prev);
      if (next.has(day)) next.delete(day);
      else next.add(day);
      return next;
    });

  return (
    <div className="itinerary-panel">
      <div className="itinerary-header">
        <CalendarDays size={16} />
        <span>{itinerary.length}-Day Itinerary</span>
      </div>

      <div className="itinerary-days">
        {itinerary.map(day => (
          <DayCard
            key={day.day}
            day={day}
            isOpen={openDays.has(day.day)}
            onToggle={() => toggleDay(day.day)}
          />
        ))}
      </div>
    </div>
  );
};

export default ItineraryPanel;
