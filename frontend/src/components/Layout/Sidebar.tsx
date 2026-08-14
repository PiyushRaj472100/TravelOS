import type { FC } from 'react';
import {
  Map,
  CalendarDays,
  Hotel,
  Plane,
  Activity,
  PiggyBank,
  CloudSun,
} from 'lucide-react';
import type { TripData } from '../../types';
import './Sidebar.css';

export type SidebarTab = 'map' | 'itinerary' | 'hotels' | 'flights' | 'activities' | 'budget' | 'weather';

interface SidebarProps {
  activeTab: SidebarTab;
  onTabChange: (tab: SidebarTab) => void;
  tripData: TripData;
}

interface TabConfig {
  id: SidebarTab;
  icon: React.ReactNode;
  label: string;
  badge?: number;
}

const Sidebar: FC<SidebarProps> = ({ activeTab, onTabChange, tripData }) => {
  const tabs: TabConfig[] = [
    { id: 'map', icon: <Map size={18} />, label: 'Map' },
    { id: 'itinerary', icon: <CalendarDays size={18} />, label: 'Itinerary', badge: tripData.itinerary.length },
    { id: 'hotels', icon: <Hotel size={18} />, label: 'Hotels', badge: tripData.hotels.length },
    { id: 'flights', icon: <Plane size={18} />, label: 'Flights', badge: tripData.flights.length },
    { id: 'activities', icon: <Activity size={18} />, label: 'Activities', badge: tripData.activities.length },
    { id: 'budget', icon: <PiggyBank size={18} />, label: 'Budget' },
    { id: 'weather', icon: <CloudSun size={18} />, label: 'Weather', badge: tripData.weather ? 1 : 0 },
  ];

  return (
    <nav className="sidebar glass-strong" aria-label="Panel navigation">
      {tabs.map(tab => (
        <button
          key={tab.id}
          id={`tab-${tab.id}`}
          className={`sidebar-tab ${activeTab === tab.id ? 'active' : ''}`}
          onClick={() => onTabChange(tab.id)}
          title={tab.label}
          aria-selected={activeTab === tab.id}
        >
          <span className="sidebar-icon">{tab.icon}</span>
          <span className="sidebar-label">{tab.label}</span>
          {tab.badge !== undefined && tab.badge > 0 && (
            <span className="sidebar-badge">{tab.badge}</span>
          )}
        </button>
      ))}
    </nav>
  );
};

export default Sidebar;
