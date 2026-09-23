import { useState, useEffect, useRef, useCallback } from "react";
import { useAuth } from "../context/AuthContext";
import { useNavigate } from "react-router-dom";
import L from "leaflet";
import "leaflet/dist/leaflet.css";
import {
  searchNearby,
  searchByText,
  clusterPlaces,
  enrichCluster,
} from "../services/googlePlacesApi";
import {
  Crosshair,
  Map as MapIcon,
  Filter,
  Loader2,
  Sparkles,
  Calendar,
  X,
  Navigation2,
  CheckCircle2,
  Search,
  MapPin,
  ExternalLink,
  ChevronDown,
  ChevronUp,
} from "lucide-react";

// ─── Leaflet Default Marker Icon Fix ──────────────────────────────────────────

delete L.Icon.Default.prototype._getIconUrl;
L.Icon.Default.mergeOptions({
  iconRetinaUrl: "https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-icon-2x.png",
  iconUrl: "https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-icon.png",
  shadowUrl: "https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-shadow.png",
});

// ─── Constants ─────────────────────────────────────────────────────────────────

const INDIA_CENTER = [20.5937, 78.9629];
const INDIA_ZOOM = 5;
const CITY_ZOOM = 13;

const OSM_TILE_URL = "https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png";
const OSM_ATTRIBUTION =
  '&copy; <a href="https://www.openstreetmap.org/copyright" target="_blank" rel="noopener noreferrer">OpenStreetMap</a> contributors';

const CLUSTER_COLORS = [
  "#ef4444", "#3b82f6", "#10b981", "#f59e0b",
  "#8b5cf6", "#ec4899", "#14b8a6", "#f97316",
];

const CATEGORIES = [
  { id: "all", label: "All", icon: "🗺️" },
  { id: "heritage", label: "Heritage", icon: "🏛️" },
  { id: "nature", label: "Nature", icon: "🌳" },
  { id: "food", label: "Food", icon: "🍽️" },
  { id: "culture", label: "Culture", icon: "🎭" },
  { id: "shopping", label: "Shopping", icon: "🛍️" },
  { id: "adventure", label: "Adventure", icon: "🧗" },
  { id: "religious", label: "Religious", icon: "🛕" },
  { id: "entertainment", label: "Entertainment", icon: "🎡" },
];

const INTERESTS = [
  "Photography",
  "History",
  "Nature",
  "Adventure",
  "Food",
  "Shopping",
  "Culture",
  "Architecture",
  "Relaxation",
];

const DISTANCE_OPTIONS = [
  { value: "all", label: "Anywhere" },
  { value: "1", label: "Within 1 km" },
  { value: "5", label: "Within 5 km" },
  { value: "10", label: "Within 10 km" },
  { value: "25", label: "Within 25 km" },
  { value: "50", label: "Within 50 km" },
];

// ─── Coordinate Validator ──────────────────────────────────────────────────────

function isValidCoord(lat, lng) {
  return (
    typeof lat === "number" &&
    typeof lng === "number" &&
    !isNaN(lat) &&
    !isNaN(lng) &&
    lat >= -90 &&
    lat <= 90 &&
    lng >= -180 &&
    lng <= 180
  );
}

// ─── Custom Leaflet DivIcons ───────────────────────────────────────────────────

function makeClusterDivIcon(count, color) {
  const size = count > 50 ? 44 : count > 20 ? 38 : 32;
  return L.divIcon({
    className: "tourmate-cluster-centroid-icon",
    html: `
      <div style="
        width: ${size}px;
        height: ${size}px;
        border-radius: 50%;
        background-color: ${color};
        border: 3px solid #ffffff;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.35);
        display: flex;
        align-items: center;
        justify-content: center;
        color: #ffffff;
        font-weight: 800;
        font-family: system-ui, -apple-system, sans-serif;
        font-size: ${size > 36 ? 14 : 12}px;
        cursor: pointer;
        user-select: none;
      ">
        ${count}
      </div>
    `,
    iconSize: [size, size],
    iconAnchor: [size / 2, size / 2],
    popupAnchor: [0, -size / 2],
  });
}

function makePlaceDivIcon(color) {
  return L.divIcon({
    className: "tourmate-place-dot-icon",
    html: `
      <div style="
        width: 14px;
        height: 14px;
        border-radius: 50%;
        background-color: ${color};
        border: 2px solid #ffffff;
        box-shadow: 0 2px 6px rgba(0, 0, 0, 0.35);
        cursor: pointer;
      "></div>
    `,
    iconSize: [14, 14],
    iconAnchor: [7, 7],
    popupAnchor: [0, -7],
  });
}

function makeUserDivIcon() {
  return L.divIcon({
    className: "tourmate-user-location-icon",
    html: `
      <div style="position: relative; width: 24px; height: 24px; display: flex; align-items: center; justify-content: center;">
        <div style="
          position: absolute;
          width: 24px;
          height: 24px;
          border-radius: 50%;
          background-color: #10b981;
          opacity: 0.4;
          animation: ping 1.5s cubic-bezier(0, 0, 0.2, 1) infinite;
        "></div>
        <div style="
          width: 14px;
          height: 14px;
          border-radius: 50%;
          background-color: #10b981;
          border: 2px solid #ffffff;
          box-shadow: 0 2px 8px rgba(0, 0, 0, 0.4);
        "></div>
      </div>
    `,
    iconSize: [24, 24],
    iconAnchor: [12, 12],
    popupAnchor: [0, -12],
  });
}

// ─── Main Component ────────────────────────────────────────────────────────────

export default function ClusteredMapView() {
  const { token } = useAuth();
  const navigate = useNavigate();
  const mapContainerRef = useRef(null);
  const mapInstanceRef = useRef(null);
  const markersLayerRef = useRef(null);
  const userMarkerRef = useRef(null);
  const searchInputRef = useRef(null);

  // Data state
  const [places, setPlaces] = useState([]);
  const [clustersData, setClustersData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [apiError, setApiError] = useState(null);
  const [searchQuery, setSearchQuery] = useState("");
  const [currentSearchCenter, setCurrentSearchCenter] = useState(null);

  // Filter state
  const [kValue, setKValue] = useState(4);
  const [category, setCategory] = useState("all");
  const [distanceFilter, setDistanceFilter] = useState("all");
  const [interests, setInterests] = useState([]);
  const [showFilters, setShowFilters] = useState(false);
  const [showInterests, setShowInterests] = useState(false);

  // Location state
  const [userLocation, setUserLocation] = useState(null);

  // Selected cluster state
  const [selectedCluster, setSelectedCluster] = useState(null);
  const [enriching, setEnriching] = useState(false);
  const [clusterDetails, setClusterDetails] = useState(null);

  // ── Initialize Leaflet Map ──────────────────────────────────────────────────
  useEffect(() => {
    if (!mapContainerRef.current || mapInstanceRef.current) return;

    const map = L.map(mapContainerRef.current, {
      center: INDIA_CENTER,
      zoom: INDIA_ZOOM,
      zoomControl: false,
    });

    // Zoom control at bottom-right
    L.control.zoom({ position: "bottomright" }).addTo(map);

    // OpenStreetMap Tile Layer with visible attribution
    L.tileLayer(OSM_TILE_URL, {
      attribution: OSM_ATTRIBUTION,
      maxZoom: 19,
      crossOrigin: true,
    }).addTo(map);

    // Layer group for dynamic markers
    const markersLayer = L.layerGroup().addTo(map);
    markersLayerRef.current = markersLayer;
    mapInstanceRef.current = map;

    return () => {
      map.remove();
      mapInstanceRef.current = null;
      markersLayerRef.current = null;
    };
  }, []);

  // ── Clear markers helper ──────────────────────────────────────────────────
  const clearMarkers = useCallback(() => {
    if (markersLayerRef.current) {
      markersLayerRef.current.clearLayers();
    }
  }, []);

  // ── Cluster selection & AI enrichment ────────────────────────────────────
  const handleClusterClick = useCallback(
    async (cluster) => {
      setSelectedCluster(cluster);
      setEnriching(true);
      setClusterDetails(null);

      // Pan to centroid if valid
      if (cluster.centroid && isValidCoord(cluster.centroid[0], cluster.centroid[1])) {
        mapInstanceRef.current?.panTo([cluster.centroid[0], cluster.centroid[1]], {
          animate: true,
          duration: 0.8,
        });
      }

      try {
        const result = await enrichCluster({ places: cluster.places, interests, token });
        setClusterDetails(result);
      } catch {
        setClusterDetails({
          cluster_name: `Travel Area ${(cluster.cluster_id ?? 0) + 1}`,
          description: "A geographic cluster of tourist attractions.",
          categories: [],
          reasons: ["Geographically grouped for convenient exploration."],
        });
      } finally {
        setEnriching(false);
      }
    },
    [interests, token]
  );

  // Expose cluster selection globally for popup action buttons
  useEffect(() => {
    window.__tourmate_select_cluster_by_id = (clusterId) => {
      if (!clustersData?.clusters) return;
      const target = clustersData.clusters.find(
        (c, idx) => (c.cluster_id ?? idx) === clusterId
      );
      if (target) {
        handleClusterClick(target);
      }
    };
    return () => {
      delete window.__tourmate_select_cluster_by_id;
    };
  }, [clustersData, handleClusterClick]);

  // ── Render Leaflet markers from clusters ─────────────────────────────────
  const renderMarkersFromClusters = useCallback(
    (clustered, centerLat, centerLng) => {
      if (!mapInstanceRef.current || !markersLayerRef.current) return;
      clearMarkers();
      const layer = markersLayerRef.current;
      const validPoints = [];

      // Re-add user location marker if available
      if (userLocation && isValidCoord(userLocation.lat, userLocation.lng)) {
        const uMarker = L.marker([userLocation.lat, userLocation.lng], {
          icon: makeUserDivIcon(),
          zIndexOffset: 1000,
        }).bindPopup(
          '<div style="font-family:sans-serif;padding:2px;font-size:12px;font-weight:bold;">📍 Your Current Location</div>'
        );
        layer.addLayer(uMarker);
      }

      // Render clusters and POIs
      clustered.clusters?.forEach((cluster, idx) => {
        const color = CLUSTER_COLORS[idx % CLUSTER_COLORS.length];
        const clusterId = cluster.cluster_id ?? idx;
        const [cLat, cLng] = cluster.centroid || [centerLat, centerLng];

        // 1. Cluster Centroid Marker
        if (isValidCoord(cLat, cLng) && cluster.places.length > 0) {
          validPoints.push([cLat, cLng]);
          const centroidMarker = L.marker([cLat, cLng], {
            icon: makeClusterDivIcon(cluster.places.length, color),
            zIndexOffset: 500,
            title: `Area ${idx + 1} (${cluster.places.length} places)`,
          });

          centroidMarker.on("click", () => {
            handleClusterClick(cluster);
          });

          layer.addLayer(centroidMarker);
        }

        // 2. Individual Place POI Markers
        cluster.places.forEach((place) => {
          const lat = place.latitude ?? place.location?.coordinates?.[1];
          const lng = place.longitude ?? place.location?.coordinates?.[0];
          if (!isValidCoord(lat, lng)) return;

          validPoints.push([lat, lng]);

          const placeMarker = L.marker([lat, lng], {
            icon: makePlaceDivIcon(color),
            zIndexOffset: 100,
            title: place.name,
          });

          const mapsLink =
            place.google_maps_url ||
            `https://www.google.com/maps/search/?api=1&query=${encodeURIComponent(
              `${place.name} ${place.address || ""}`
            )}`;

          const popupContent = `
            <div style="min-width:210px;max-width:260px;font-family:system-ui,-apple-system,sans-serif;padding:4px">
              <div style="font-weight:700;font-size:14px;color:#0f172a;line-height:1.3;margin-bottom:4px">
                ${place.name}
              </div>
              ${
                place.address
                  ? `<div style="font-size:11px;color:#64748b;margin-bottom:6px;line-height:1.4">${place.address}</div>`
                  : ""
              }
              <div style="display:flex;align-items:center;gap:6px;margin-bottom:8px;flex-wrap:wrap">
                <span style="background:${color};color:#ffffff;font-size:10px;font-weight:700;padding:2px 8px;border-radius:9999px;text-transform:uppercase">
                  ${place.category_name || place.category?.name || "Attraction"}
                </span>
                ${
                  place.rating
                    ? `<span style="font-size:11px;color:#d97706;font-weight:700">⭐ ${place.rating}</span>`
                    : ""
                }
              </div>
              <div style="display:flex;flex-direction:column;gap:6px">
                <a href="${mapsLink}" target="_blank" rel="noopener noreferrer" style="font-size:11px;color:#2563eb;text-decoration:none;font-weight:600;display:inline-flex;align-items:center;gap:3px">
                  View on Google Maps ↗
                </a>
                <button
                  onclick="window.__tourmate_select_cluster_by_id(${clusterId})"
                  style="width:100%;padding:6px 10px;background:#0d6560;color:#ffffff;border:none;border-radius:8px;font-size:12px;font-weight:700;cursor:pointer;transition:background 0.2s"
                >
                  ✨ Analyze Area ${idx + 1}
                </button>
              </div>
            </div>
          `;

          placeMarker.bindPopup(popupContent, { maxWidth: 280 });
          layer.addLayer(placeMarker);
        });
      });

      // Fit bounds to markers
      if (validPoints.length > 1) {
        try {
          const bounds = L.latLngBounds(validPoints);
          if (bounds.isValid()) {
            mapInstanceRef.current.fitBounds(bounds, { padding: [50, 50], maxZoom: 15 });
          }
        } catch (err) {
          console.error("Leaflet fitBounds error:", err);
        }
      } else if (validPoints.length === 1) {
        mapInstanceRef.current.setView(validPoints[0], CITY_ZOOM);
      }
    },
    [clearMarkers, userLocation, handleClusterClick]
  );

  // ── Place search logic ────────────────────────────────────────────────────
  const triggerPlaceSearch = useCallback(
    async ({ lat, lng }) => {
      if (!token) return;
      setLoading(true);
      setApiError(null);

      try {
        let foundPlaces = [];

        if (distanceFilter !== "all" && lat && lng) {
          // Nearby search with GPS radius
          const radiusKm = parseInt(distanceFilter);
          foundPlaces = await searchNearby({ lat, lng, radiusKm, category, token });
        } else {
          // Text search for city/destination context
          const query = searchQuery.trim() || "India";
          foundPlaces = await searchByText({
            query,
            lat: lat || undefined,
            lng: lng || undefined,
            radiusKm: 30,
            category,
            token,
          });
        }

        if (foundPlaces.length === 0) {
          setPlaces([]);
          setClustersData(null);
          clearMarkers();
          setLoading(false);
          return;
        }

        setPlaces(foundPlaces);

        // Run K-Means clustering
        const k = Math.min(kValue, foundPlaces.length);
        const clustered = await clusterPlaces({ places: foundPlaces, k, interests, token });
        setClustersData(clustered);
        renderMarkersFromClusters(clustered, lat || INDIA_CENTER[0], lng || INDIA_CENTER[1]);
      } catch (err) {
        console.error("Place search error:", err);
        const msg =
          err?.response?.data?.detail || "Unable to load the cluster map. Please try again.";
        setApiError(msg);
      } finally {
        setLoading(false);
      }
    },
    [token, category, distanceFilter, kValue, interests, searchQuery, clearMarkers, renderMarkersFromClusters]
  );

  // ── GPS Locate ────────────────────────────────────────────────────────────
  const handleLocate = useCallback(() => {
    if (!navigator.geolocation) {
      alert("Geolocation is not supported by your browser.");
      return;
    }
    setLoading(true);
    navigator.geolocation.getCurrentPosition(
      (pos) => {
        const { latitude: lat, longitude: lng } = pos.coords;
        if (!isValidCoord(lat, lng)) {
          setLoading(false);
          alert("Invalid GPS coordinates received.");
          return;
        }

        setUserLocation({ lat, lng });
        setCurrentSearchCenter({ lat, lng });

        if (mapInstanceRef.current) {
          mapInstanceRef.current.setView([lat, lng], CITY_ZOOM);
        }

        triggerPlaceSearch({ lat, lng });
      },
      (err) => {
        setLoading(false);
        console.error("GPS error:", err);
        alert("Could not retrieve your location. Please allow location access and try again.");
      },
      { enableHighAccuracy: true, timeout: 10000 }
    );
  }, [triggerPlaceSearch]);

  // ── Plan My Day ───────────────────────────────────────────────────────────
  const handlePlanMyDay = useCallback(() => {
    if (!selectedCluster) return;
    const normalized = selectedCluster.places.map((p) => ({
      id: p.id || p.external_id,
      name: p.name,
      latitude: p.latitude ?? p.location?.coordinates?.[1],
      longitude: p.longitude ?? p.location?.coordinates?.[0],
      category: p.category_name || p.category?.name || "heritage",
      address: p.address || "",
      google_maps_url: p.google_maps_url || "",
      rating: p.rating || null,
      source: "google",
    }));
    localStorage.setItem("tourmate_ai_places", JSON.stringify(normalized));
    navigate("/itinerary-builder");
  }, [selectedCluster, navigate]);

  // ── Optimize Route ────────────────────────────────────────────────────────
  const handleOptimizeRoute = useCallback(() => {
    if (!selectedCluster) return;
    localStorage.setItem("tourmate_route_places", JSON.stringify(selectedCluster.places));
    navigate("/map/route");
  }, [selectedCluster, navigate]);

  // ── Manual search submit ──────────────────────────────────────────────────
  const handleSearchSubmit = useCallback(
    (e) => {
      e.preventDefault();
      if (!searchQuery.trim()) return;
      setApiError(null);
      const center = currentSearchCenter || { lat: INDIA_CENTER[0], lng: INDIA_CENTER[1] };
      triggerPlaceSearch(center);
    },
    [searchQuery, currentSearchCenter, triggerPlaceSearch]
  );

  // ── Interest toggle ───────────────────────────────────────────────────────
  const toggleInterest = (interest) => {
    setInterests((prev) =>
      prev.includes(interest) ? prev.filter((i) => i !== interest) : [...prev, interest]
    );
  };

  // ── Re-search when filters change ────────────────────────────────────────
  useEffect(() => {
    if (currentSearchCenter || searchQuery.trim()) {
      const center = currentSearchCenter || { lat: INDIA_CENTER[0], lng: INDIA_CENTER[1] };
      triggerPlaceSearch(center);
    }
  }, [category, distanceFilter, kValue]); // eslint-disable-line react-hooks/exhaustive-deps

  // ─── Render ───────────────────────────────────────────────────────────────

  const allPlacesEmpty =
    !loading && places.length === 0 && (currentSearchCenter !== null || searchQuery.trim() !== "");

  return (
    <div className="flex flex-col md:flex-row h-[calc(100vh-64px)] bg-gray-50 dark:bg-slate-900 relative overflow-hidden">
      {/* Mobile Header */}
      <div className="md:hidden p-3 bg-white dark:bg-slate-900 z-10 shadow-sm border-b dark:border-slate-800 flex items-center gap-3">
        <MapIcon className="text-brand-500 w-5 h-5 shrink-0" />
        <form onSubmit={handleSearchSubmit} className="flex-1 flex gap-2">
          <input
            ref={searchInputRef}
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Search India..."
            className="flex-1 px-3 py-1.5 text-sm bg-gray-100 dark:bg-slate-800 border border-gray-200 dark:border-slate-700 rounded-lg outline-none focus:border-brand-500 text-gray-900 dark:text-white"
          />
          <button
            type="submit"
            className="p-1.5 bg-brand-600 hover:bg-brand-700 text-white rounded-lg transition"
          >
            <Search className="w-4 h-4" />
          </button>
        </form>
        <button
          onClick={() => setShowFilters(!showFilters)}
          className="p-1.5 bg-gray-100 dark:bg-slate-800 rounded-lg text-gray-700 dark:text-slate-300"
        >
          <Filter className="w-4 h-4" />
        </button>
      </div>

      {/* ── Left Sidebar ─────────────────────────────────────────────────── */}
      <div
        className={`absolute md:relative z-20 w-full md:w-72 h-full bg-white dark:bg-slate-900 shadow-xl border-r dark:border-slate-800 flex flex-col transition-transform duration-300 ${
          showFilters ? "translate-x-0" : "-translate-x-full md:translate-x-0"
        }`}
      >
        {/* Header */}
        <div className="p-4 border-b dark:border-slate-800 hidden md:block">
          <h1 className="text-lg font-black text-gray-900 dark:text-white flex items-center gap-2">
            <MapIcon className="text-brand-500 w-5 h-5" /> AI Cluster Map
          </h1>
          <p className="text-xs text-gray-500 dark:text-slate-400 mt-0.5">
            Explore India with AI-powered clusters
          </p>
        </div>

        {/* Search (desktop) */}
        <div className="p-4 border-b dark:border-slate-800 hidden md:block">
          <form onSubmit={handleSearchSubmit} className="relative">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="Search city or destination..."
              className="w-full pl-9 pr-10 py-2.5 text-sm bg-gray-50 dark:bg-slate-800 border border-gray-200 dark:border-slate-700 rounded-xl outline-none focus:border-brand-500 focus:ring-1 focus:ring-brand-500 dark:text-white text-gray-900"
            />
            <button
              type="submit"
              className="absolute right-2 top-1/2 -translate-y-1/2 p-1 bg-brand-600 hover:bg-brand-700 text-white rounded-lg transition"
            >
              <Search className="w-3 h-3" />
            </button>
          </form>
          <p className="text-[10px] text-gray-400 mt-1.5 pl-1">
            e.g. Bengaluru, Jaipur, Kerala, Goa...
          </p>
        </div>

        {/* Mobile close + filters header */}
        <div className="md:hidden flex justify-between items-center p-4 border-b dark:border-slate-800">
          <h2 className="font-bold text-gray-900 dark:text-white">Filters</h2>
          <button onClick={() => setShowFilters(false)}>
            <X className="w-5 h-5 text-gray-500" />
          </button>
        </div>

        {/* Filters */}
        <div className="flex-1 overflow-y-auto p-4 space-y-5 custom-scrollbar">
          {/* K Clusters */}
          <div>
            <label className="text-xs font-bold text-gray-500 dark:text-slate-400 uppercase tracking-wider flex justify-between mb-2">
              <span>Travel Clusters</span>
              <span className="text-brand-600 font-black">{kValue}</span>
            </label>
            <input
              type="range"
              min="2"
              max="8"
              value={kValue}
              onChange={(e) => setKValue(parseInt(e.target.value))}
              className="w-full accent-brand-600"
            />
          </div>

          {/* Distance */}
          <div>
            <label className="text-xs font-bold text-gray-500 dark:text-slate-400 uppercase tracking-wider mb-2 block">
              Distance
            </label>
            <select
              value={distanceFilter}
              onChange={(e) => setDistanceFilter(e.target.value)}
              className="w-full p-2.5 bg-gray-50 dark:bg-slate-800 border border-gray-200 dark:border-slate-700 rounded-xl text-sm dark:text-white text-gray-900 outline-none focus:border-brand-500"
            >
              {DISTANCE_OPTIONS.map((o) => (
                <option key={o.value} value={o.value}>
                  {o.label}
                </option>
              ))}
            </select>
            {distanceFilter !== "all" && !userLocation && (
              <button
                onClick={handleLocate}
                className="mt-1.5 text-[11px] text-brand-500 hover:text-brand-600 font-medium flex items-center gap-1"
              >
                <Crosshair className="w-3 h-3" /> Enable GPS to use distance filter
              </button>
            )}
          </div>

          {/* Category */}
          <div>
            <label className="text-xs font-bold text-gray-500 dark:text-slate-400 uppercase tracking-wider mb-2 block">
              Category
            </label>
            <div className="flex flex-wrap gap-1.5">
              {CATEGORIES.map((cat) => (
                <button
                  key={cat.id}
                  onClick={() => setCategory(cat.id)}
                  className={`px-2.5 py-1 rounded-full text-xs font-semibold transition-all ${
                    category === cat.id
                      ? "bg-brand-600 text-white shadow-sm"
                      : "bg-gray-100 dark:bg-slate-800 text-gray-600 dark:text-slate-300 hover:bg-gray-200 dark:hover:bg-slate-700"
                  }`}
                >
                  {cat.icon} {cat.label}
                </button>
              ))}
            </div>
          </div>

          {/* Interests */}
          <div>
            <button
              onClick={() => setShowInterests(!showInterests)}
              className="text-xs font-bold text-gray-500 dark:text-slate-400 uppercase tracking-wider w-full flex justify-between items-center mb-2"
            >
              <span>
                AI Interests{" "}
                {interests.length > 0 && (
                  <span className="text-brand-600 normal-case font-bold">
                    ({interests.length})
                  </span>
                )}
              </span>
              {showInterests ? <ChevronUp className="w-3 h-3" /> : <ChevronDown className="w-3 h-3" />}
            </button>
            {showInterests && (
              <div className="grid grid-cols-2 gap-1.5">
                {INTERESTS.map((int) => (
                  <label
                    key={int}
                    className="flex items-center gap-2 text-xs text-gray-700 dark:text-slate-300 cursor-pointer select-none"
                  >
                    <input
                      type="checkbox"
                      checked={interests.includes(int)}
                      onChange={() => toggleInterest(int)}
                      className="rounded text-brand-600 focus:ring-brand-500"
                    />
                    {int}
                  </label>
                ))}
              </div>
            )}
          </div>

          {/* Cluster list */}
          {clustersData?.clusters?.length > 0 && (
            <div>
              <label className="text-xs font-bold text-gray-500 dark:text-slate-400 uppercase tracking-wider mb-2 block">
                Discovered Areas
              </label>
              <div className="space-y-1.5">
                {clustersData.clusters
                  .filter((c) => c.places.length > 0)
                  .map((cluster, i) => (
                    <button
                      key={i}
                      onClick={() => handleClusterClick(cluster)}
                      className={`w-full flex items-center justify-between px-2.5 py-2 rounded-xl transition-all text-left ${
                        selectedCluster?.cluster_id === cluster.cluster_id
                          ? "bg-brand-50 dark:bg-brand-900/20 border border-brand-200 dark:border-brand-800"
                          : "hover:bg-gray-100 dark:hover:bg-slate-800 border border-transparent"
                      }`}
                    >
                      <div className="flex items-center gap-2">
                        <div
                          className="w-3 h-3 rounded-full"
                          style={{
                            backgroundColor: CLUSTER_COLORS[i % CLUSTER_COLORS.length],
                          }}
                        />
                        <span className="text-sm font-semibold text-gray-800 dark:text-slate-200 truncate">
                          Area {i + 1}
                        </span>
                      </div>
                      <span className="text-xs font-bold bg-gray-100 dark:bg-slate-700 px-2 py-0.5 rounded-full text-gray-600 dark:text-slate-300">
                        {cluster.places.length}
                      </span>
                    </button>
                  ))}
              </div>
            </div>
          )}
        </div>
      </div>

      {/* ── Map Area ──────────────────────────────────────────────────────── */}
      <div className="flex-1 relative z-0">
        {/* Leaflet Map container */}
        <div ref={mapContainerRef} className="w-full h-full" />

        {/* Loading */}
        {loading && (
          <div className="absolute inset-0 bg-white/40 dark:bg-slate-900/60 backdrop-blur-sm z-[1000] flex flex-col items-center justify-center pointer-events-none">
            <div className="bg-white dark:bg-slate-800 rounded-2xl shadow-2xl px-8 py-6 flex flex-col items-center gap-3">
              <Loader2 className="w-8 h-8 text-brand-600 animate-spin" />
              <p className="text-sm font-bold text-gray-700 dark:text-slate-200">
                {places.length === 0 ? "Finding places..." : "Building travel clusters..."}
              </p>
            </div>
          </div>
        )}

        {/* Error */}
        {!loading && apiError && (
          <div className="absolute bottom-24 left-1/2 -translate-x-1/2 z-[1000] bg-white dark:bg-slate-800 rounded-2xl shadow-2xl border border-red-200 dark:border-red-800 p-4 max-w-sm w-full mx-4">
            <div className="flex items-start gap-3">
              <X className="w-5 h-5 text-red-500 shrink-0 mt-0.5" />
              <div className="flex-1 min-w-0">
                <p className="text-sm font-bold text-gray-900 dark:text-white">Notice</p>
                <p className="text-xs text-gray-500 dark:text-slate-400 mt-0.5">{apiError}</p>
              </div>
              <button onClick={() => setApiError(null)}>
                <X className="w-4 h-4 text-gray-400" />
              </button>
            </div>
            <button
              onClick={() => {
                const center = currentSearchCenter || {
                  lat: INDIA_CENTER[0],
                  lng: INDIA_CENTER[1],
                };
                triggerPlaceSearch(center);
              }}
              className="mt-3 w-full py-1.5 bg-brand-600 hover:bg-brand-700 text-white rounded-xl text-xs font-bold transition"
            >
              Try Again
            </button>
          </div>
        )}

        {/* Empty State */}
        {allPlacesEmpty && !apiError && (
          <div className="absolute bottom-24 left-1/2 -translate-x-1/2 z-[1000] bg-white dark:bg-slate-800 rounded-2xl shadow-2xl border border-gray-200 dark:border-slate-700 p-5 max-w-xs w-full mx-4 text-center">
            <MapPin className="w-8 h-8 text-gray-400 mx-auto mb-2" />
            <h3 className="font-bold text-gray-900 dark:text-white text-sm mb-1">
              No clustered places available
            </h3>
            <p className="text-xs text-gray-500 dark:text-slate-400">
              Try searching a different city or destination, or adjust distance/category filters.
            </p>
          </div>
        )}

        {/* India welcome prompt (before search) */}
        {!loading && !currentSearchCenter && !searchQuery && places.length === 0 && (
          <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 z-[800] pointer-events-none">
            <div className="bg-white/90 dark:bg-slate-800/90 backdrop-blur border border-gray-200 dark:border-slate-700 rounded-2xl shadow-2xl px-8 py-6 text-center max-w-sm">
              <div className="text-3xl mb-3">🇮🇳</div>
              <h2 className="font-black text-gray-900 dark:text-white text-lg mb-1">
                Explore India
              </h2>
              <p className="text-sm text-gray-500 dark:text-slate-400">
                Search any city, state, or destination to discover clustered tourist spots.
              </p>
            </div>
          </div>
        )}

        {/* Map Controls (top right) */}
        <div className="absolute right-4 top-3 z-[800] flex gap-2">
          <button
            onClick={handleLocate}
            className="bg-white dark:bg-slate-800 px-3 py-2 rounded-xl shadow-lg border border-gray-200 dark:border-slate-700 text-gray-700 dark:text-slate-300 hover:text-brand-600 transition flex items-center gap-2 text-xs font-bold"
          >
            <Crosshair className="w-4 h-4 text-brand-600" /> Near Me
          </button>
        </div>

        {/* Cluster legend (top left of map) */}
        {clustersData?.clusters?.length > 0 && !loading && (
          <div className="absolute left-3 top-3 z-[800] bg-white/90 dark:bg-slate-900/90 backdrop-blur border border-gray-200 dark:border-slate-700 rounded-xl p-3 shadow-lg max-w-[160px] hidden md:block">
            <p className="text-[10px] font-black text-gray-500 dark:text-slate-400 uppercase tracking-wider mb-2">
              AI Travel Areas
            </p>
            {clustersData.clusters
              .filter((c) => c.places.length > 0)
              .map((c, i) => (
                <div
                  key={i}
                  className="flex items-center gap-2 py-0.5 cursor-pointer hover:bg-gray-100 dark:hover:bg-slate-800 rounded px-1 transition"
                  onClick={() => handleClusterClick(c)}
                >
                  <div
                    className="w-2.5 h-2.5 rounded-full shrink-0"
                    style={{
                      backgroundColor: CLUSTER_COLORS[i % CLUSTER_COLORS.length],
                    }}
                  />
                  <span className="text-xs text-gray-700 dark:text-slate-300 truncate">
                    Area {i + 1}
                  </span>
                  <span className="text-[10px] font-bold text-gray-500 ml-auto">
                    {c.places.length}
                  </span>
                </div>
              ))}
          </div>
        )}

        {/* ── Selected Cluster Detail Panel ────────────────────────────── */}
        {selectedCluster && (
          <div className="absolute bottom-0 left-0 right-0 md:bottom-4 md:left-auto md:right-4 md:w-96 bg-white dark:bg-slate-900 rounded-t-2xl md:rounded-2xl shadow-2xl z-[900] overflow-hidden border border-gray-200 dark:border-slate-700 max-h-[80vh] flex flex-col">
            {/* Header */}
            <div className="p-4 bg-gradient-to-r from-brand-600 to-accent-500 text-white relative">
              <button
                onClick={() => setSelectedCluster(null)}
                className="absolute top-3 right-3 bg-black/20 hover:bg-black/40 p-1.5 rounded-full transition"
              >
                <X className="w-4 h-4" />
              </button>
              {enriching ? (
                <div className="space-y-2 pr-8">
                  <div className="h-5 w-3/4 bg-white/20 animate-pulse rounded" />
                  <div className="h-3 w-1/2 bg-white/20 animate-pulse rounded" />
                </div>
              ) : (
                <div className="pr-8">
                  <h2 className="font-black text-base leading-tight">
                    {clusterDetails?.cluster_name ||
                      `Travel Area ${(selectedCluster.cluster_id ?? 0) + 1}`}
                  </h2>
                  <p className="text-xs text-white/80 mt-0.5 flex items-center gap-1">
                    <Sparkles className="w-3 h-3" /> AI Analysis · {selectedCluster.places.length}{" "}
                    places
                  </p>
                </div>
              )}
            </div>

            {/* Content */}
            <div className="flex-1 overflow-y-auto p-4 space-y-4 custom-scrollbar">
              {/* Description */}
              {!enriching && clusterDetails?.description && (
                <p className="text-sm text-gray-600 dark:text-slate-400 italic leading-relaxed">
                  "{clusterDetails.description}"
                </p>
              )}

              {/* Stats */}
              <div className="grid grid-cols-2 gap-2">
                <div className="bg-gray-50 dark:bg-slate-800 rounded-xl p-3 text-center border border-gray-100 dark:border-slate-700">
                  <p className="text-[10px] text-gray-500 font-bold uppercase mb-0.5">Places</p>
                  <p className="text-xl font-black text-gray-900 dark:text-white">
                    {selectedCluster.places.length}
                  </p>
                </div>
                <div className="bg-gray-50 dark:bg-slate-800 rounded-xl p-3 text-center border border-gray-100 dark:border-slate-700">
                  <p className="text-[10px] text-gray-500 font-bold uppercase mb-0.5">Est. Time</p>
                  <p className="text-xl font-black text-gray-900 dark:text-white">
                    ~{Math.round(((selectedCluster.places.length * 45) / 60) * 10) / 10}h
                  </p>
                </div>
              </div>

              {/* Reasons */}
              {!enriching && clusterDetails?.reasons?.length > 0 && (
                <div className="bg-emerald-50 dark:bg-emerald-900/10 border border-emerald-100 dark:border-emerald-900/30 rounded-xl p-3 space-y-2">
                  <p className="text-[10px] font-black text-emerald-700 dark:text-emerald-400 uppercase tracking-wider">
                    Why visit this area?
                  </p>
                  {clusterDetails.reasons.map((r, i) => (
                    <div
                      key={i}
                      className="flex items-start gap-2 text-xs text-emerald-800 dark:text-emerald-300"
                    >
                      <CheckCircle2 className="w-3.5 h-3.5 shrink-0 mt-0.5 text-emerald-500" />
                      {r}
                    </div>
                  ))}
                </div>
              )}

              {/* Categories */}
              {!enriching && clusterDetails?.categories?.length > 0 && (
                <div className="flex flex-wrap gap-1.5">
                  {clusterDetails.categories.map((c, i) => (
                    <span
                      key={i}
                      className="px-2.5 py-0.5 bg-brand-50 dark:bg-brand-900/20 text-brand-700 dark:text-brand-300 text-xs font-semibold rounded-full border border-brand-100 dark:border-brand-800"
                    >
                      {c}
                    </span>
                  ))}
                </div>
              )}

              {/* Places list */}
              <div>
                <p className="text-[10px] font-black text-gray-500 dark:text-slate-400 uppercase tracking-wider mb-2">
                  Included Places
                </p>
                <div className="space-y-1">
                  {selectedCluster.places.slice(0, 6).map((p, i) => {
                    const placeMapsUrl =
                      p.google_maps_url ||
                      `https://www.google.com/maps/search/?api=1&query=${encodeURIComponent(
                        `${p.name} ${p.address || ""}`
                      )}`;
                    return (
                      <div
                        key={p.id || i}
                        className="flex items-center gap-3 p-2 rounded-lg hover:bg-gray-50 dark:hover:bg-slate-800 transition"
                      >
                        <div
                          className="w-6 h-6 rounded-full text-white text-xs font-bold flex items-center justify-center shrink-0"
                          style={{
                            backgroundColor:
                              CLUSTER_COLORS[
                                (selectedCluster.cluster_id ?? 0) % CLUSTER_COLORS.length
                              ],
                          }}
                        >
                          {i + 1}
                        </div>
                        <div className="min-w-0 flex-1">
                          <p className="text-sm font-semibold text-gray-900 dark:text-white truncate">
                            {p.name}
                          </p>
                          <p className="text-[10px] text-gray-400 truncate capitalize">
                            {p.category_name || p.category?.name || "attraction"}
                          </p>
                        </div>
                        {p.rating && (
                          <span className="text-[10px] text-amber-500 font-bold shrink-0">
                            ⭐ {p.rating}
                          </span>
                        )}
                        <a
                          href={placeMapsUrl}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="shrink-0"
                        >
                          <ExternalLink className="w-3.5 h-3.5 text-gray-400 hover:text-brand-600" />
                        </a>
                      </div>
                    );
                  })}
                  {selectedCluster.places.length > 6 && (
                    <p className="text-xs text-center text-gray-400 pt-1 font-semibold">
                      +{selectedCluster.places.length - 6} more places
                    </p>
                  )}
                </div>
              </div>
            </div>

            {/* Action Buttons */}
            <div className="p-3 bg-gray-50 dark:bg-slate-800/80 border-t dark:border-slate-700 grid grid-cols-2 gap-2 shrink-0">
              <button
                onClick={handlePlanMyDay}
                disabled={enriching}
                className="py-2.5 flex items-center justify-center gap-1.5 bg-white dark:bg-slate-700 border-2 border-brand-200 dark:border-brand-800 text-brand-700 dark:text-brand-400 font-bold text-xs rounded-xl hover:bg-brand-50 transition disabled:opacity-50"
              >
                <Calendar className="w-3.5 h-3.5" /> Plan My Day
              </button>
              <button
                onClick={handleOptimizeRoute}
                disabled={enriching}
                className="py-2.5 flex items-center justify-center gap-1.5 bg-brand-600 hover:bg-brand-700 text-white font-bold text-xs rounded-xl transition disabled:opacity-50"
              >
                <Navigation2 className="w-3.5 h-3.5" /> Optimize Route
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
