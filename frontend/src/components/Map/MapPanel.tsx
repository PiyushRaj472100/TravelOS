import { useEffect, useRef, useState, type FC } from 'react';
import * as maplibregl from 'maplibre-gl';
import 'maplibre-gl/dist/maplibre-gl.css';
import {
  Layers,
  Compass,
  Navigation,
  Sparkles,
} from 'lucide-react';
import type { MapData, MapMarker } from '../../types';
import EmptyState from '../common/EmptyState';
import './MapPanel.css';

interface MapPanelProps {
  mapData?: MapData;
  onMarkerSelect?: (marker: MapMarker) => void;
  onPromptSend?: (prompt: string) => void;
}

type MapStyleKey = 'dark' | 'streets' | 'satellite';

const MAP_STYLES: Record<MapStyleKey, { name: string; url: string }> = {
  dark: {
    name: 'Dark Matter',
    url: 'https://a.basemaps.cartocdn.com/rastertiles/dark_all/{z}/{x}/{y}.png',
  },
  streets: {
    name: 'Voyager',
    url: 'https://a.basemaps.cartocdn.com/rastertiles/voyager/{z}/{x}/{y}.png',
  },
  satellite: {
    name: 'Positron',
    url: 'https://a.basemaps.cartocdn.com/rastertiles/light_all/{z}/{x}/{y}.png',
  },
};

const MapPanel: FC<MapPanelProps> = ({ mapData, onMarkerSelect, onPromptSend }) => {
  const mapContainerRef = useRef<HTMLDivElement>(null);
  const mapInstanceRef = useRef<maplibregl.Map | null>(null);
  const markersRef = useRef<maplibregl.Marker[]>([]);

  const [filterType, setFilterType] = useState<string>('all');
  const [selectedMarker, setSelectedMarker] = useState<MapMarker | null>(null);
  const [is3D, setIs3D] = useState(false);
  const [currentStyle, setCurrentStyle] = useState<MapStyleKey>('streets');
  const [showStyleMenu, setShowStyleMenu] = useState(false);

  const markers = mapData?.markers || [];
  const routes = mapData?.routes || [];
  const hasMarkers = markers.length > 0;

  // Initialize Map
  useEffect(() => {
    if (!mapContainerRef.current) return;

    const centerLng = mapData?.center_lng ?? 139.6917;
    const centerLat = mapData?.center_lat ?? 35.6895;
    const zoom = mapData?.zoom ?? 4;

    const map = new maplibregl.Map({
      container: mapContainerRef.current,
      style: {
        version: 8,
        sources: {
          'base-tiles': {
            type: 'raster',
            tiles: [MAP_STYLES[currentStyle].url],
            tileSize: 256,
            attribution: '&copy; CARTO &copy; OpenStreetMap',
          },
        },
        layers: [
          {
            id: 'base-tiles-layer',
            type: 'raster',
            source: 'base-tiles',
            minzoom: 0,
            maxzoom: 19,
          },
        ],
      },
      center: [centerLng, centerLat],
      zoom: zoom,
      pitch: 0,
      bearing: 0,
      attributionControl: false,
    });

    map.addControl(new maplibregl.NavigationControl({ showCompass: true }), 'top-right');

    mapInstanceRef.current = map;

    return () => {
      markersRef.current.forEach(m => m.remove());
      markersRef.current = [];
      map.remove();
    };
  }, []);

  // Update base tiles if style changed
  useEffect(() => {
    const map = mapInstanceRef.current;
    if (!map) return;

    const source = map.getSource('base-tiles') as maplibregl.RasterTileSource | undefined;
    if (source && source.setTiles) {
      source.setTiles([MAP_STYLES[currentStyle].url]);
    }
  }, [currentStyle]);

  // Toggle 3D Tilt
  const toggle3D = () => {
    const map = mapInstanceRef.current;
    if (!map) return;
    const next3D = !is3D;
    setIs3D(next3D);
    map.easeTo({
      pitch: next3D ? 50 : 0,
      bearing: next3D ? 25 : 0,
      duration: 1000,
    });
  };

  // Reset Camera
  const resetCamera = () => {
    const map = mapInstanceRef.current;
    if (!map || !markers.length) return;

    const bounds = new maplibregl.LngLatBounds();
    markers.forEach(m => {
      if (m.longitude != null && m.latitude != null) {
        bounds.extend([m.longitude, m.latitude]);
      }
    });

    if (!bounds.isEmpty()) {
      map.fitBounds(bounds, { padding: 80, maxZoom: 13, duration: 1200 });
    }
  };

  // Update Markers & Routes whenever mapData or filterType changes
  useEffect(() => {
    const map = mapInstanceRef.current;
    if (!map) return;

    // Clear old markers
    markersRef.current.forEach(m => m.remove());
    markersRef.current = [];

    const visibleMarkers = filterType === 'all'
      ? markers
      : markers.filter(m => m.marker_type === filterType);

    if (visibleMarkers.length === 0) return;

    const bounds = new maplibregl.LngLatBounds();

    visibleMarkers.forEach((marker) => {
      if (marker.longitude == null || marker.latitude == null) return;

      bounds.extend([marker.longitude, marker.latitude]);

      // Custom marker container
      const el = document.createElement('div');
      el.className = `premium-map-marker marker-type-${marker.marker_type || 'destination'}`;
      
      const icon = 
        marker.marker_type === 'hotel' ? '🏨' :
        marker.marker_type === 'activity' ? '📍' :
        marker.marker_type === 'airport' ? '✈️' :
        marker.marker_type === 'restaurant' ? '🍽️' : '🌍';

      el.innerHTML = `
        <div class="marker-pulse-ring"></div>
        <div class="marker-badge">
          <span class="marker-icon">${icon}</span>
        </div>
        <div class="marker-pill">${marker.name}</div>
      `;

      el.addEventListener('click', (e) => {
        e.stopPropagation();
        setSelectedMarker(marker);
        if (onMarkerSelect) onMarkerSelect(marker);

        map.flyTo({
          center: [marker.longitude, marker.latitude],
          zoom: Math.max(map.getZoom(), 12),
          duration: 1000,
          essential: true,
        });
      });

      const m = new maplibregl.Marker({ element: el })
        .setLngLat([marker.longitude, marker.latitude])
        .addTo(map);

      markersRef.current.push(m);
    });

    // Draw route lines if available
    if (routes.length > 0 && map.isStyleLoaded()) {
      const routeGeoJSON = {
        type: 'FeatureCollection' as const,
        features: routes.map((r, i) => ({
          type: 'Feature' as const,
          properties: { id: i, name: `${r.from_name} → ${r.to_name}` },
          geometry: {
            type: 'LineString' as const,
            coordinates: [
              [r.from_lng, r.from_lat],
              [r.to_lng, r.to_lat],
            ],
          },
        })),
      };

      if (map.getSource('flight-routes')) {
        (map.getSource('flight-routes') as maplibregl.GeoJSONSource).setData(routeGeoJSON);
      } else {
        map.addSource('flight-routes', {
          type: 'geojson',
          data: routeGeoJSON,
        });

        map.addLayer({
          id: 'flight-routes-glow',
          type: 'line',
          source: 'flight-routes',
          layout: { 'line-join': 'round', 'line-cap': 'round' },
          paint: {
            'line-color': '#6366f1',
            'line-width': 4,
            'line-opacity': 0.4,
            'line-blur': 3,
          },
        });

        map.addLayer({
          id: 'flight-routes-core',
          type: 'line',
          source: 'flight-routes',
          layout: { 'line-join': 'round', 'line-cap': 'round' },
          paint: {
            'line-color': '#06b6d4',
            'line-width': 2,
            'line-dasharray': [2, 2],
          },
        });
      }
    }

    if (!bounds.isEmpty()) {
      map.fitBounds(bounds, { padding: 80, maxZoom: 13, duration: 1200 });
    }
  }, [mapData, filterType]);

  // Counts by category
  const countByType = {
    all: markers.length,
    destination: markers.filter(m => m.marker_type === 'destination').length,
    hotel: markers.filter(m => m.marker_type === 'hotel').length,
    activity: markers.filter(m => m.marker_type === 'activity').length,
    restaurant: markers.filter(m => m.marker_type === 'restaurant').length,
    airport: markers.filter(m => m.marker_type === 'airport').length,
  };

  return (
    <div className="premium-map-container">
      {/* Top Floating Bar / Filter Chips */}
      <div className="map-top-bar glass-strong">
        <div className="map-filter-group">
          <button
            className={`map-chip ${filterType === 'all' ? 'active' : ''}`}
            onClick={() => setFilterType('all')}
          >
            All <span className="chip-count">{countByType.all}</span>
          </button>
          {countByType.destination > 0 && (
            <button
              className={`map-chip ${filterType === 'destination' ? 'active' : ''}`}
              onClick={() => setFilterType('destination')}
            >
              🌍 Destinations <span className="chip-count">{countByType.destination}</span>
            </button>
          )}
          {countByType.hotel > 0 && (
            <button
              className={`map-chip ${filterType === 'hotel' ? 'active' : ''}`}
              onClick={() => setFilterType('hotel')}
            >
              🏨 Hotels <span className="chip-count">{countByType.hotel}</span>
            </button>
          )}
          {countByType.activity > 0 && (
            <button
              className={`map-chip ${filterType === 'activity' ? 'active' : ''}`}
              onClick={() => setFilterType('activity')}
            >
              📍 Attractions <span className="chip-count">{countByType.activity}</span>
            </button>
          )}
          {countByType.airport > 0 && (
            <button
              className={`map-chip ${filterType === 'airport' ? 'active' : ''}`}
              onClick={() => setFilterType('airport')}
            >
              ✈️ Routes <span className="chip-count">{countByType.airport}</span>
            </button>
          )}
        </div>


        {/* Map Control Tools */}
        <div className="map-tools">
          <button
            className={`tool-btn ${is3D ? 'active' : ''}`}
            onClick={toggle3D}
            title="Toggle 3D perspective"
          >
            <Compass size={14} />
            <span>3D</span>
          </button>

          <button
            className="tool-btn"
            onClick={resetCamera}
            title="Fit all markers"
          >
            <Navigation size={14} />
            <span>Fit</span>
          </button>

          <div className="map-style-dropdown-container">
            <button
              className="tool-btn"
              onClick={() => setShowStyleMenu(prev => !prev)}
              title="Change Map Style"
            >
              <Layers size={14} />
              <span>Theme</span>
            </button>
            {showStyleMenu && (
              <div className="style-dropdown glass-strong animate-slide-up">
                {(['dark', 'streets', 'satellite'] as MapStyleKey[]).map(style => (
                  <button
                    key={style}
                    className={`style-option ${currentStyle === style ? 'active' : ''}`}
                    onClick={() => {
                      setCurrentStyle(style);
                      setShowStyleMenu(false);
                    }}
                  >
                    {MAP_STYLES[style].name}
                  </button>
                ))}
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Map Canvas */}
      <div ref={mapContainerRef} className="map-canvas" />

      {/* Empty Overlay */}
      {!hasMarkers && (
        <div className="map-empty-overlay">
          <EmptyState
            icon={<Sparkles size={28} />}
            title="Live Geographical Intelligence"
            description="Mention any city, flights, hotels or experiences in chat, and TravelOS will immediately plot locations, coordinates, and routes."
          />
        </div>
      )}

      {/* Active Marker Detail Drawer / Floating Card */}
      {selectedMarker && (
        <div className="marker-detail-card card glass-strong animate-slide-up">
          <div className="detail-card-header">
            <div className="detail-icon-wrap">
              {selectedMarker.marker_type === 'hotel' ? '🏨' :
               selectedMarker.marker_type === 'activity' ? '📍' :
               selectedMarker.marker_type === 'airport' ? '✈️' : '🌍'}
            </div>
            <div className="detail-text">
              <h4>{selectedMarker.name}</h4>
              <p>{selectedMarker.description || selectedMarker.marker_type}</p>
            </div>
            <button
              className="detail-close-btn"
              onClick={() => setSelectedMarker(null)}
            >
              ✕
            </button>
          </div>

          <div className="detail-actions">
            {onPromptSend && (
              <button
                className="btn-ask-ai"
                onClick={() => {
                  onPromptSend(`Tell me more about ${selectedMarker.name} and what makes it special`);
                  setSelectedMarker(null);
                }}
              >
                <Sparkles size={12} />
                Ask TravelOS about this
              </button>
            )}
          </div>
        </div>
      )}
    </div>
  );
};

export default MapPanel;
