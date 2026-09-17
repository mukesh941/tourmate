/**
 * Frontend API service for Google Places Backend Proxy.
 * All calls go through the TourMate FastAPI backend — the Google API key
 * is NEVER used on the frontend directly.
 */
import axios from "axios";

const BASE = import.meta.env.VITE_API_BASE_URL;

/**
 * Nearby Search — find tourist places around a geographic point.
 */
export async function searchNearby({ lat, lng, radiusKm = 5, category = "all", token }) {
  const res = await axios.get(`${BASE}/google/places/nearby`, {
    params: { lat, lng, radius_km: radiusKm, category: category !== "all" ? category : undefined, max_results: 20 },
    headers: { Authorization: `Bearer ${token}` },
  });
  return res.data.data?.places || [];
}

/**
 * Text Search — search for tourist places in a city / destination.
 */
export async function searchByText({ query, lat, lng, radiusKm = 50, category = "all", token }) {
  const res = await axios.post(
    `${BASE}/google/places/search`,
    {
      query,
      lat: lat || null,
      lng: lng || null,
      radius_km: radiusKm,
      category: category !== "all" ? category : null,
      max_results: 20,
    },
    { headers: { Authorization: `Bearer ${token}` } }
  );
  return res.data.data?.places || [];
}

/**
 * Cluster a list of places into K geographic groups using K-Means.
 */
export async function clusterPlaces({ places, k = 4, interests = [], token }) {
  const res = await axios.post(
    `${BASE}/google/places/cluster`,
    { places, k, interests },
    { headers: { Authorization: `Bearer ${token}` } }
  );
  return res.data.data;
}

/**
 * AI-enrich a cluster using Gemini — generates name, description, and reasons.
 */
export async function enrichCluster({ places, interests = [], token }) {
  const res = await axios.post(
    `${BASE}/google/places/cluster/enrich`,
    { places, interests },
    { headers: { Authorization: `Bearer ${token}` } }
  );
  return res.data.data;
}

/**
 * Get full details for a single Google Place by ID.
 */
export async function getPlaceDetails({ placeId, token }) {
  const res = await axios.get(`${BASE}/google/places/details/${placeId}`, {
    headers: { Authorization: `Bearer ${token}` },
  });
  return res.data.data;
}
