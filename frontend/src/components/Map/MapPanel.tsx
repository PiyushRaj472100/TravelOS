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

type MapStyleKey = 'streets' | 'dark' | 'satellite' | 'outdoor';

const MAPTILER_KEY = import.meta.env.VITE_MAPTILER_API_KEY || '';
const GEOAPIFY_KEY = import.meta.env.VITE_GEOAPIFY_API_KEY || '8089437eb40b4a00a78111daa732d395';

const getMapStyleUrl = (style: MapStyleKey): string | maplibregl.StyleSpecification => {
  if (MAPTILER_KEY) {
    const styleIds: Record<MapStyleKey, string> = {
      streets: 'streets-v2',
      dark: 'dataviz-dark',
      satellite: 'hybrid',
      outdoor: 'outdoor-v2',
    };
    return `https://api.maptiler.com/maps/${styleIds[style]}/style.json?key=${MAPTILER_KEY}`;
  }

  // Graceful fallback raster tiles when MapTiler API Key is not yet set
  const geoapifyStyles: Record<MapStyleKey, string> = {
    streets: 'osm-carto',
    dark: 'dark-matter',
    satellite: 'positron',
    outdoor: 'osm-carto',
  };
  const tileUrl = GEOAPIFY_KEY
    ? `https://maps.geoapify.com/v1/tile/${geoapifyStyles[style]}/{z}/{x}/{y}.png?apiKey=${GEOAPIFY_KEY}`
    : 'https://tile.openstreetmap.org/{z}/{x}/{y}.png';

  return {
    version: 8,
    sources: {
      'base-tiles': {
        type: 'raster',
        tiles: [tileUrl],
        tileSize: 256,
        attribution: '&copy; MapLibre &copy; OpenStreetMap contributors',
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
  };
};

const MAP_STYLE_NAMES: Record<MapStyleKey, string> = {
  streets: 'Streets (MapTiler)',
  dark: 'Dark Matter (MapTiler)',
  satellite: 'Satellite (MapTiler)',
  outdoor: 'Outdoor & Topo (MapTiler)',
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

  // Draw or update route lines on current map style
  const drawRoutes = (map: maplibregl.Map, currentRoutes: typeof routes) => {
    if (!map || currentRoutes.length === 0) return;
    if (!map.isStyleLoaded()) {
      map.once('style.load', () => drawRoutes(map, currentRoutes));
      return;
    }

    const routeGeoJSON = {
      type: 'FeatureCollection' as const,
      features: currentRoutes.map((r, i) => ({
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

    const existingSource = map.getSource('flight-routes') as maplibregl.GeoJSONSource | undefined;
    if (existingSource) {
      existingSource.setData(routeGeoJSON);
    } else {
      map.addSource('flight-routes', {
        type: 'geojson',
        data: routeGeoJSON,
      });

      if (!map.getLayer('flight-routes-glow')) {
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
      }

      if (!map.getLayer('flight-routes-core')) {
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
  };

  // Switch Map Style
  const handleStyleChange = (style: MapStyleKey) => {
    setCurrentStyle(style);
    setShowStyleMenu(false);
    const map = mapInstanceRef.current;
    if (!map) return;

    map.setStyle(getMapStyleUrl(style));
    map.once('style.load', () => {
      drawRoutes(map, routes);
    });
  };

  // Initialize Map
  useEffect(() => {
    if (!mapContainerRef.current) return;

    const centerLng = mapData?.center_lng ?? 139.6917;
    const centerLat = mapData?.center_lat ?? 35.6895;
    const zoom = mapData?.zoom ?? 4;

    const map = new maplibregl.Map({
      container: mapContainerRef.current,
      style: getMapStyleUrl(currentStyle),
      center: [centerLng, centerLat],
      zoom: zoom,
      pitch: 0,
      bearing: 0,
      attributionControl: false,
    });

    map.addControl(new maplibregl.NavigationControl({ showCompass: true }), 'top-right');
    map.addControl(new maplibregl.AttributionControl({ compact: true }), 'bottom-right');

    map.on('load', () => {
      drawRoutes(map, routes);
    });

    mapInstanceRef.current = map;

    return () => {
      markersRef.current.forEach(m => m.remove());
      markersRef.current = [];
      map.remove();
    };
  }, []);


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
    drawRoutes(map, routes);


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
          {/* MapTiler status indicator */}
          <div
            className={`map-status-pill ${MAPTILER_KEY ? 'active' : 'fallback'}`}
            title={
              MAPTILER_KEY
                ? 'MapTiler vector tiles connected'
                : 'Using fallback tiles. Add VITE_MAPTILER_API_KEY in frontend/.env for MapTiler HD vector tiles'
            }
          >
            <span className="status-dot" />
            <span className="status-text">{MAPTILER_KEY ? 'MapTiler HD' : 'MapTiler (Key Needed)'}</span>
          </div>

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
                {(['streets', 'dark', 'satellite', 'outdoor'] as MapStyleKey[]).map(style => (
                  <button
                    key={style}
                    className={`style-option ${currentStyle === style ? 'active' : ''}`}
                    onClick={() => handleStyleChange(style)}
                  >
                    {MAP_STYLE_NAMES[style]}
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
