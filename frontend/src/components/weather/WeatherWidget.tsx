import type { FC } from 'react';
import { Thermometer, Wind, Droplets, CloudSun } from 'lucide-react';
import type { WeatherData } from '../../types';
import EmptyState from '../common/EmptyState';
import './WeatherWidget.css';

const WEATHER_ICONS: Record<number, string> = {
  0: '☀️', 1: '🌤️', 2: '⛅', 3: '☁️',
  45: '🌫️', 48: '🌫️',
  51: '🌦️', 53: '🌦️', 55: '🌧️',
  61: '🌧️', 63: '🌧️', 65: '🌧️',
  71: '🌨️', 73: '🌨️', 75: '❄️',
  80: '🌦️', 81: '🌧️', 82: '⛈️',
  95: '⛈️', 96: '⛈️', 99: '⛈️',
};

function getWeatherIcon(code?: number): string {
  if (!code) return '🌤️';
  return WEATHER_ICONS[code] ?? '🌤️';
}

interface WeatherWidgetProps {
  weather?: WeatherData;
}

const WeatherWidget: FC<WeatherWidgetProps> = ({ weather }) => {
  if (!weather) {
    return (
      <EmptyState
        icon={<CloudSun size={28} />}
        title="No weather data yet"
        description='Ask about the weather. Example: "What is the weather like in Tokyo?"'
      />
    );
  }

  const icon = getWeatherIcon(weather.weather_code);

  return (
    <div className="weather-panel">
      <div className="weather-card card">
        {/* Hero */}
        <div className="weather-hero">
          <div className="weather-location">
            {weather.city && <h2 className="weather-city">{weather.city}</h2>}
            {weather.country && <span className="weather-country">{weather.country}</span>}
          </div>
          <div className="weather-icon-large">{icon}</div>
        </div>

        {/* Temperature */}
        {weather.temperature !== undefined && (
          <div className="weather-temp-block">
            <span className="weather-temp">{weather.temperature}°C</span>
            {weather.apparent_temperature !== undefined && (
              <span className="weather-feels">
                Feels like {weather.apparent_temperature}°C
              </span>
            )}
          </div>
        )}

        {/* Stats grid */}
        <div className="weather-stats">
          {weather.humidity !== undefined && (
            <div className="weather-stat">
              <Droplets size={16} className="stat-icon" />
              <div>
                <span className="stat-value">{weather.humidity}%</span>
                <span className="stat-label">Humidity</span>
              </div>
            </div>
          )}
          {weather.wind_speed !== undefined && (
            <div className="weather-stat">
              <Wind size={16} className="stat-icon" />
              <div>
                <span className="stat-value">{weather.wind_speed} km/h</span>
                <span className="stat-label">Wind</span>
              </div>
            </div>
          )}
          {weather.temperature !== undefined && (
            <div className="weather-stat">
              <Thermometer size={16} className="stat-icon" />
              <div>
                <span className="stat-value">{weather.temperature}°C</span>
                <span className="stat-label">Temperature</span>
              </div>
            </div>
          )}
        </div>

        {weather.time && (
          <p className="weather-updated">
            Updated: {new Date(weather.time).toLocaleString()}
          </p>
        )}
      </div>
    </div>
  );
};

export default WeatherWidget;
