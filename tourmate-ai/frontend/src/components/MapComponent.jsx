import React, { useEffect, useState } from 'react';
import { MapContainer, TileLayer, Marker, Popup, useMap, Polyline, GeoJSON } from 'react-leaflet';
import 'leaflet/dist/leaflet.css';
import L from 'leaflet';
import { MAP_TILE_URL, MAP_ATTRIBUTION } from '../config/mapConfig';

// Fix for default marker icon in Leaflet with Webpack/Vite
delete L.Icon.Default.prototype._getIconUrl;
L.Icon.Default.mergeOptions({
  iconRetinaUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-icon-2x.png',
  iconUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-icon.png',
  shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-shadow.png',
});

// Component to dynamically fit bounds or recenter map
function ChangeView({ center, zoom, routePath, places }) {
  const map = useMap();

  useEffect(() => {
    if (routePath && !Array.isArray(routePath) && routePath.coordinates && routePath.coordinates.length > 0) {
      // GeoJSON LineString coordinates are [lng, lat]
      const latLngs = routePath.coordinates.map(c => [c[1], c[0]]);
      try {
        const bounds = L.latLngBounds(latLngs);
        if (bounds.isValid()) {
          map.fitBounds(bounds, { padding: [40, 40] });
          return;
        }
      } catch (err) {
        console.error("Failed to fit route bounds:", err);
      }
    }

    if (places && places.length > 1) {
      const validPoints = places
        .filter(p => p.location && p.location.coordinates)
        .map(p => [p.location.coordinates[1], p.location.coordinates[0]]);
      if (validPoints.length > 1) {
        try {
          const bounds = L.latLngBounds(validPoints);
          if (bounds.isValid()) {
            map.fitBounds(bounds, { padding: [40, 40] });
            return;
          }
        } catch (err) {
          console.error("Failed to fit places bounds:", err);
        }
      }
    }

    if (center) {
      map.setView(center, zoom);
    }
  }, [center, zoom, routePath, places, map]);

  return null;
}

const MapComponent = ({ places = [], routePath = null, center = [20.5937, 78.9629], zoom = 5, onMarkerClick }) => {
  const [isDark, setIsDark] = useState(
    typeof document !== 'undefined' && document.documentElement.classList.contains('dark')
  );

  useEffect(() => {
    if (typeof document === 'undefined') return;
    const observer = new MutationObserver(() => {
      setIsDark(document.documentElement.classList.contains('dark'));
    });
    observer.observe(document.documentElement, { attributes: true, attributeFilter: ['class'] });
    return () => observer.disconnect();
  }, []);

  // Compute a unique key for GeoJSON to force re-render on route update
  const routeKey = routePath && !Array.isArray(routePath) && routePath.coordinates
    ? `route-${routePath.coordinates.length}-${routePath.coordinates[0]?.[0] || 0}`
    : 'no-route';

  return (
    <div className="w-full h-full min-h-[400px] rounded-lg overflow-hidden shadow-md dark:shadow-none bg-gray-100 dark:bg-slate-800">
      <MapContainer center={center} zoom={zoom} scrollWheelZoom={true} style={{ height: '100%', width: '100%' }}>
        <ChangeView center={center} zoom={zoom} routePath={routePath} places={places} />
        <TileLayer
          attribution={MAP_ATTRIBUTION}
          url={MAP_TILE_URL}
        />
        {places.map((place) => {
          if (!place.location || !place.location.coordinates) return null;
          // GeoJSON is [lng, lat], Leaflet expects [lat, lng]
          const position = [place.location.coordinates[1], place.location.coordinates[0]];
          return (
            <Marker 
              key={place.id} 
              position={position}
              eventHandlers={{
                click: () => {
                  if (onMarkerClick) onMarkerClick(place);
                },
              }}
            >
              <Popup>
                <div className="text-sm">
                  <h3 className="font-bold">{place.name}</h3>
                  <p className="text-gray-600 dark:text-slate-300 line-clamp-2">{place.description}</p>
                </div>
              </Popup>
            </Marker>
          );
        })}
        {/* Legacy support for old route points */}
        {routePath && Array.isArray(routePath) && routePath.length > 1 && (
          <Polyline 
            positions={routePath.map(p => [p.location.coordinates[1], p.location.coordinates[0]])} 
            pathOptions={{ color: '#ec4899', weight: 4, opacity: 0.8, dashArray: '10, 10', lineCap: 'round' }} 
          />
        )}
        {/* Support for OSRM GeoJSON geometry with unique key for reactivity */}
        {routePath && !Array.isArray(routePath) && routePath.type === "LineString" && (
          <GeoJSON 
            key={routeKey}
            data={routePath} 
            style={{ color: '#3b82f6', weight: 5, opacity: 0.85 }} 
          />
        )}
      </MapContainer>
    </div>
  );
};

export default MapComponent;
