# Google Maps Independent Architecture

## Overview
TourMate has been refactored to eliminate the hard dependency on Google Maps, replacing it with provider-independent interfaces and utilizing self-hosted/open alternatives (OSM, OSRM). The system gracefully handles the absence of a `GOOGLE_MAPS_API_KEY`.

## Key Changes
1. **Frontend Maps**: Replaced Google Maps iframes with `MapComponent` using `react-leaflet` and OpenStreetMap tiles.
2. **Navigation/Routing**: Changed external routing URLs from `google.com/maps` to `openstreetmap.org/directions` with OSRM and GraphHopper routing engines.
3. **Geocoding Abstraction**: Created `geocoding_service.py` to route geocoding requests to OpenStreetMap (Nominatim) rather than relying exclusively on Google.
4. **Backend Fallbacks**: Modified `google_places.py` to fallback to Postgres Database spatial searches using Haversine distance when the Google API Key is unavailable.
5. **UI Links**: Replaced raw Google Map Search links in `CategoryPage.jsx` and `ClusteredMapView.jsx` with OSM search links.

## Fallback Mechanisms
- **Places**: If `VITE_GOOGLE_MAPS_API_KEY` or `GOOGLE_MAPS_API_KEY` are unset, TourMate automatically queries its local Postgres DB via `poi_service.py`.
- **Geocoding**: `geocoding_service.py` will hit Nominatim for coordinate resolution.
- **Routing**: `routing_service.py` uses OSRM or falls back to Haversine distance estimation.

## Files Modified
- `frontend/src/config/mapConfig.js`
- `frontend/src/utils/navigation.js`
- `frontend/src/pages/PlaceDetail.jsx`
- `frontend/src/pages/RoutePlannerView.jsx`
- `frontend/src/pages/CategoryPage.jsx`
- `frontend/src/pages/ClusteredMapView.jsx`
- `backend/app/api/routes/google_places.py`
- `backend/app/services/geocoding_service.py`
- `backend/app/services/location_service.py`
