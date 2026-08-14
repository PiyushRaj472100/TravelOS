import type { FC } from 'react';
import { PiggyBank, TrendingUp, Zap, Sparkles, Calendar, Users, DollarSign, ArrowRightLeft } from 'lucide-react';
import type { BudgetBreakdown } from '../../types';
import EmptyState from '../common/EmptyState';
import './BudgetPanel.css';

interface BudgetPanelProps {
  budget?: BudgetBreakdown;
  onPromptSend?: (prompt: string) => void;
}

const ITEM_ICONS: Record<string, string> = {
  Flights: '✈️',
  Hotels: '🏨',
  'Food & Dining': '🍽️',
  'Activities & Attractions': '🗺️',
  'Local Transport': '🚇',
};

const POPULAR_CURRENCIES = [
  { code: 'INR', label: 'INR (₹)', name: 'Indian Rupee' },
  { code: 'USD', label: 'USD ($)', name: 'US Dollar' },
  { code: 'EUR', label: 'EUR (€)', name: 'Euro' },
  { code: 'GBP', label: 'GBP (£)', name: 'British Pound' },
  { code: 'JPY', label: 'JPY (¥)', name: 'Japanese Yen' },
  { code: 'AUD', label: 'AUD ($)', name: 'Australian Dollar' },
  { code: 'CAD', label: 'CAD ($)', name: 'Canadian Dollar' },
  { code: 'SGD', label: 'SGD ($)', name: 'Singapore Dollar' },
  { code: 'AED', label: 'AED (د.إ)', name: 'UAE Dirham' },
  { code: 'THB', label: 'THB (฿)', name: 'Thai Baht' },
];

const BudgetPanel: FC<BudgetPanelProps> = ({ budget, onPromptSend }) => {
  if (!budget) {
    return (
      <EmptyState
        icon={<PiggyBank size={28} />}
        title="No budget estimate yet"
        description='Ask TravelOS for a budget estimate. Example: "What will my trip to Tokyo cost?"'
      />
    );
  }

  const totalEstimated = budget.items.reduce((sum, item) => sum + (item.amount ?? 0), 0);
  const currency = budget.currency ?? 'USD';
  const duration = budget.duration_days ?? 7;
  const travelers = budget.travelers ?? 2;
  const costPerDay = budget.cost_per_day ?? (duration > 0 ? totalEstimated / duration : totalEstimated);
  const costPerPerson = budget.cost_per_person ?? (travelers > 0 ? totalEstimated / travelers : totalEstimated);

  const handleCurrencyChange = (newCurr: string) => {
    if (newCurr !== currency && onPromptSend) {
      onPromptSend(`Switch currency to ${newCurr}`);
    }
  };

  return (
    <div className="budget-panel">

      {/* Top Currency Switcher & Quick Actions Bar */}
      <div className="budget-currency-bar card">
        <div className="currency-bar-left">
          <ArrowRightLeft size={14} className="curr-icon" />
          <span className="curr-label">Currency:</span>
          <select
            className="currency-select"
            value={currency}
            onChange={(e) => handleCurrencyChange(e.target.value)}
            aria-label="Select Currency"
          >
            {POPULAR_CURRENCIES.map(c => (
              <option key={c.code} value={c.code}>
                {c.label} - {c.name}
              </option>
            ))}
          </select>
        </div>

        {onPromptSend && (
          <button
            className="btn-ask-expensive"
            onClick={() => onPromptSend("What are the most expensive activities in my trip?")}
            title="Ask AI to identify expensive activities and suggest budget replacements"
          >
            <Sparkles size={13} />
            <span>Ask AI: Expensive Activities</span>
          </button>
        )}
      </div>

      {/* Summary card */}
      <div className="budget-summary card">
        <div className="budget-summary-header">
          <div>
            <p className="budget-summary-label">Estimated Total Spend</p>
            <p className="budget-total">
              {currency} {totalEstimated.toLocaleString(undefined, { maximumFractionDigits: 0 })}
            </p>
          </div>
          {budget.total_budget && (
            <div className="budget-user-budget">
              <p className="budget-summary-label">Your Budget Target</p>
              <p className="budget-user-amount">
                {currency} {budget.total_budget.toLocaleString()}
              </p>
            </div>
          )}
        </div>

        {budget.remaining !== undefined && (
          <div className={`budget-remaining ${budget.remaining >= 0 ? 'remaining-ok' : 'remaining-over'}`}>
            <TrendingUp size={13} />
            {budget.remaining >= 0
              ? `${currency} ${budget.remaining.toLocaleString()} remaining under budget`
              : `${currency} ${Math.abs(budget.remaining).toLocaleString()} over budget`}
          </div>
        )}

        {/* Duration & Traveler Summary Chips */}
        <div className="budget-meta-grid">
          <div className="budget-meta-box">
            <Calendar size={13} className="meta-icon" />
            <div>
              <span className="meta-sublabel">Duration</span>
              <span className="meta-val">{duration} Days</span>
            </div>
          </div>
          <div className="budget-meta-box">
            <Users size={13} className="meta-icon" />
            <div>
              <span className="meta-sublabel">Travelers</span>
              <span className="meta-val">{travelers} People</span>
            </div>
          </div>
          <div className="budget-meta-box">
            <DollarSign size={13} className="meta-icon" />
            <div>
              <span className="meta-sublabel">Avg / Day</span>
              <span className="meta-val">{currency} {Math.round(costPerDay).toLocaleString()}</span>
            </div>
          </div>
          <div className="budget-meta-box">
            <DollarSign size={13} className="meta-icon" />
            <div>
              <span className="meta-sublabel">Avg / Person</span>
              <span className="meta-val">{currency} {Math.round(costPerPerson).toLocaleString()}</span>
            </div>
          </div>
        </div>
      </div>

      {/* Items breakdown */}
      <div className="budget-breakdown">
        <h3 className="breakdown-title">Expense Allocation</h3>
        <div className="breakdown-list">
          {budget.items.map((item, i) => {
            const pct = totalEstimated > 0 ? ((item.amount ?? 0) / totalEstimated) * 100 : 0;
            return (
              <div key={i} className="breakdown-item">
                <div className="breakdown-item-header">
                  <span className="breakdown-icon">
                    {ITEM_ICONS[item.label] ?? '💼'}
                  </span>
                  <span className="breakdown-label">{item.label}</span>
                  <div className="breakdown-right">
                    {item.is_live && (
                      <span className="live-badge" title="Live price">
                        <Zap size={9} /> Live
                      </span>
                    )}
                    <span className="breakdown-amount">
                      {item.currency ?? currency} {(item.amount ?? 0).toLocaleString(undefined, { maximumFractionDigits: 0 })}
                    </span>
                  </div>
                </div>
                <div className="breakdown-bar-track">
                  <div
                    className="breakdown-bar-fill"
                    style={{ width: `${pct.toFixed(1)}%` }}
                  />
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {/* Note */}
      {budget.note && (
        <div className="budget-note">
          <p>{budget.note}</p>
        </div>
      )}
    </div>
  );
};

export default BudgetPanel;

