/**
 * Navigation utility for TourMate AI.
 * Generates reliable, standards-compliant Google Maps directions URLs
 * and opens them safely in external tabs/apps for desktop and mobile web.
 */

export function buildGoogleMapsUrl({ lat, lng, name, address, city }) {
  // Validate coordinates
  const validLat = typeof lat === 'number' && !isNaN(lat) && lat >= -90 && lat <= 90;
  const validLng = typeof lng === 'number' && !isNaN(lng) && lng >= -180 && lng <= 180;

  if (validLat && validLng) {
    // Exact coordinate destination
    return `https://www.google.com/maps/dir/?api=1&destination=${lat},${lng}&travelmode=driving`;
  }

  // Safe fallback if coordinates missing but unambiguous name/city exists
  const queryParts = [name, address, city].filter(Boolean);
  if (queryParts.length > 0) {
    const destinationQuery = encodeURIComponent(queryParts.join(', '));
    return `https://www.google.com/maps/dir/?api=1&destination=${destinationQuery}&travelmode=driving`;
  }

  return null;
}

export function openGoogleMapsNavigation(target) {
  if (!target) return false;

  // Extract coordinates and metadata supporting various data structures
  let lat = target.latitude ?? target.lat;
  let lng = target.longitude ?? target.lng;

  if (target.location) {
    lat = target.location.latitude ?? target.location.lat ?? lat;
    lng = target.location.longitude ?? target.location.lng ?? lng;
    // Support GeoJSON [lng, lat] format if coordinates array is present
    if (Array.isArray(target.location.coordinates) && target.location.coordinates.length >= 2) {
      lng = target.location.coordinates[0];
      lat = target.location.coordinates[1];
    }
  }

  const name = target.name || target.title || "";
  const address = target.address || (target.location && target.location.address) || "";
  const city = target.city || (target.location && target.location.city) || "";

  const url = buildGoogleMapsUrl({ lat, lng, name, address, city });

  if (!url) {
    console.warn("Navigation unavailable: no valid coordinates or destination query for place:", target);
    alert(`Directions unavailable for "${name || 'selected place'}". No location coordinates provided.`);
    return false;
  }

  // Open securely in new window/tab or mobile Google Maps app
  const opened = window.open(url, '_blank', 'noopener,noreferrer');
  if (!opened || opened.closed || typeof opened.closed === 'undefined') {
    // Popup was blocked by browser; navigate directly as safe fallback
    window.location.href = url;
  }
  return true;
}
