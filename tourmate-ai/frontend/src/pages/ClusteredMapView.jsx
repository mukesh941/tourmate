import { useState, useEffect, useRef, useCallback } from "react";
import { useAuth } from "../context/AuthContext";
import { useNavigate } from "react-router-dom";
import { Loader } from "@googlemaps/js-api-loader";
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

// ─── Constants ─────────────────────────────────────────────────────────────────

const INDIA_CENTER = { lat: 20.5937, lng: 78.9629 };
const INDIA_ZOOM = 5;
const CITY_ZOOM = 13;
const DEBOUNCE_MS = 800;

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

const INTERESTS = ["Photography", "History", "Nature", "Adventure", "Food", "Shopping", "Culture", "Architecture", "Relaxation"];

const DISTANCE_OPTIONS = [
  { value: "all", label: "Anywhere" },
  { value: "1", label: "Within 1 km" },
  { value: "5", label: "Within 5 km" },
  { value: "10", label: "Within 10 km" },
  { value: "25", label: "Within 25 km" },
  { value: "50", label: "Within 50 km" },
];

// ─── Helpers ──────────────────────────────────────────────────────────────────

function makeClusterIcon(count, color, google) {
  const size = count > 50 ? 48 : count > 20 ? 42 : 36;
  return {
    url: `data:image/svg+xml;charset=UTF-8,${encodeURIComponent(`
      <svg xmlns="http://www.w3.org/2000/svg" width="${size}" height="${size}">
        <circle cx="${size / 2}" cy="${size / 2}" r="${size / 2 - 2}" fill="${color}" opacity="0.9"/>
        <circle cx="${size / 2}" cy="${size / 2}" r="${size / 2 - 6}" fill="${color}" stroke="white" stroke-width="2"/>
        <text x="50%" y="50%" dominant-baseline="middle" text-anchor="middle" fill="white" font-size="${size > 40 ? 14 : 12}" font-weight="bold" font-family="Arial,sans-serif">${count}</text>
      </svg>
    `)}`,
    scaledSize: new google.maps.Size(size, size),
    anchor: new google.maps.Point(size / 2, size / 2),
  };
}

function makePlaceIcon(color, google) {
  return {
    url: `data:image/svg+xml;charset=UTF-8,${encodeURIComponent(`
      <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16">
        <circle cx="8" cy="8" r="7" fill="${color}" stroke="white" stroke-width="2"/>
      </svg>
    `)}`,
    scaledSize: new google.maps.Size(16, 16),
    anchor: new google.maps.Point(8, 8),
  };
}

function makeUserIcon(google) {
  return {
    url: `data:image/svg+xml;charset=UTF-8,${encodeURIComponent(`
      <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24">
        <circle cx="12" cy="12" r="10" fill="#10b981" stroke="white" stroke-width="3"/>
        <circle cx="12" cy="12" r="4" fill="white"/>
      </svg>
    `)}`,
    scaledSize: new google.maps.Size(24, 24),
    anchor: new google.maps.Point(12, 12),
  };
}

// ─── Main Component ────────────────────────────────────────────────────────────

export default function ClusteredMapView() {
  const { token } = useAuth();
  const navigate = useNavigate();
  const mapRef = useRef(null);
  const mapInstanceRef = useRef(null);
  const markersRef = useRef([]);
  const infoWindowRef = useRef(null);
  const debounceTimerRef = useRef(null);
  const searchInputRef = useRef(null);
  const autocompleteRef = useRef(null);

  // Map state
  const [googleLoaded, setGoogleLoaded] = useState(false);
  const [mapLoadError, setMapLoadError] = useState(null);
  const [googleObj, setGoogleObj] = useState(null);

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

  // ── Load Google Maps SDK ────────────────────────────────────────────────────
  useEffect(() => {
    const apiKey = import.meta.env.VITE_GOOGLE_MAPS_API_KEY;
    if (!apiKey) {
      setMapLoadError("VITE_GOOGLE_MAPS_API_KEY is not set in your frontend .env file.");
      return;
    }

    const loader = new Loader({
      apiKey,
      version: "weekly",
      libraries: ["places", "geometry"],
    });

    loader
      .load()
      .then((google) => {
        setGoogleObj(google);
        setGoogleLoaded(true);
      })
      .catch((err) => {
        console.error("Google Maps load error:", err);
        setMapLoadError("Failed to load Google Maps. Please check your API key and enabled APIs.");
      });
  }, []);

  // ── Initialize map once Google is loaded ────────────────────────────────────
  useEffect(() => {
    if (!googleLoaded || !mapRef.current || mapInstanceRef.current) return;

    const map = new googleObj.maps.Map(mapRef.current, {
      center: INDIA_CENTER,
      zoom: INDIA_ZOOM,
      mapTypeControl: true,
      mapTypeControlOptions: {
        style: googleObj.maps.MapTypeControlStyle.DROPDOWN_MENU,
        position: googleObj.maps.ControlPosition.TOP_RIGHT,
      },
      zoomControl: true,
      zoomControlOptions: { position: googleObj.maps.ControlPosition.RIGHT_CENTER },
      streetViewControl: false,
      fullscreenControl: true,
      fullscreenControlOptions: { position: googleObj.maps.ControlPosition.RIGHT_BOTTOM },
      styles: [
        { featureType: "poi", elementType: "labels", stylers: [{ visibility: "off" }] },
      ],
    });

    mapInstanceRef.current = map;
    infoWindowRef.current = new googleObj.maps.InfoWindow();

    // Attach idle listener with debounce (only fires after user stops moving)
    map.addListener("idle", () => {
      clearTimeout(debounceTimerRef.current);
      debounceTimerRef.current = setTimeout(() => {
        const zoom = map.getZoom();
        // Only auto-search if zoomed in enough (city level)
        if (zoom >= 11 && currentSearchCenter) {
          const center = map.getCenter();
          triggerPlaceSearch({ lat: center.lat(), lng: center.lng(), fromMap: true });
        }
      }, DEBOUNCE_MS);
    });

    // Attach Places Autocomplete to search input
    if (searchInputRef.current) {
      const ac = new googleObj.maps.places.Autocomplete(searchInputRef.current, {
        types: ["(cities)"],
        componentRestrictions: { country: "in" },
      });
      autocompleteRef.current = ac;

      ac.addListener("place_changed", () => {
        const place = ac.getPlace();
        if (!place.geometry?.location) return;
        const lat = place.geometry.location.lat();
        const lng = place.geometry.location.lng();
        setSearchQuery(place.name || place.formatted_address || "");
        map.setCenter({ lat, lng });
        map.setZoom(CITY_ZOOM);
        setCurrentSearchCenter({ lat, lng });
        triggerPlaceSearch({ lat, lng, fromMap: false });
      });
    }
  }, [googleLoaded]); // eslint-disable-line react-hooks/exhaustive-deps

  // ── Clear markers helper ──────────────────────────────────────────────────
  const clearMarkers = useCallback(() => {
    markersRef.current.forEach((m) => m.setMap(null));
    markersRef.current = [];
    if (infoWindowRef.current) infoWindowRef.current.close();
  }, []);

  // ── Place search logic ────────────────────────────────────────────────────
  const triggerPlaceSearch = useCallback(
    async ({ lat, lng, fromMap = false }) => {
      if (!token) return;
      setLoading(true);
      setApiError(null);

      try {
        let foundPlaces = [];

        if (distanceFilter !== "all") {
          // Nearby search with GPS radius
          const radiusKm = parseInt(distanceFilter);
          foundPlaces = await searchNearby({ lat, lng, radiusKm, category, token });
        } else {
          // Text search for city context
          const query = searchQuery || "India";
          foundPlaces = await searchByText({ query, lat, lng, radiusKm: 30, category, token });
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
        renderMarkersFromClusters(clustered, lat, lng);
      } catch (err) {
        console.error("Place search error:", err);
        const msg = err?.response?.data?.detail || "Failed to load places. Please try again.";
        setApiError(msg);
      } finally {
        setLoading(false);
      }
    },
    [token, category, distanceFilter, kValue, interests, searchQuery, clearMarkers] // eslint-disable-line react-hooks/exhaustive-deps
  );

  // ── Render Google Maps markers ────────────────────────────────────────────
  const renderMarkersFromClusters = useCallback(
    (clustered, centerLat, centerLng) => {
      if (!mapInstanceRef.current || !googleObj) return;
      clearMarkers();
      const map = mapInstanceRef.current;

      // Cluster centroid markers (big numbered circles)
      clustered.clusters?.forEach((cluster, idx) => {
        const color = CLUSTER_COLORS[idx % CLUSTER_COLORS.length];
        const [cLat, cLng] = cluster.centroid || [centerLat, centerLng];

        const centroidMarker = new googleObj.maps.Marker({
          position: { lat: cLat, lng: cLng },
          map,
          icon: makeClusterIcon(cluster.places.length, color, googleObj),
          title: `Cluster ${idx + 1} — ${cluster.places.length} places`,
          zIndex: 10,
        });

        centroidMarker.addListener("click", () => {
          handleClusterClick(cluster);
        });
        markersRef.current.push(centroidMarker);

        // Individual place dot markers
        cluster.places.forEach((place) => {
          const lat = place.latitude ?? place.location?.coordinates?.[1];
          const lng = place.longitude ?? place.location?.coordinates?.[0];
          if (!lat || !lng) return;

          const marker = new googleObj.maps.Marker({
            position: { lat, lng },
            map,
            icon: makePlaceIcon(color, googleObj),
            title: place.name,
            zIndex: 5,
          });

          marker.addListener("click", () => {
            const content = `
              <div style="min-width:200px;font-family:sans-serif;padding:4px">
                <div style="font-weight:bold;font-size:14px;margin-bottom:4px">${place.name}</div>
                ${place.address ? `<div style="font-size:12px;color:#666;margin-bottom:6px">${place.address}</div>` : ""}
                ${place.rating ? `<div style="font-size:12px;color:#f59e0b;margin-bottom:6px">⭐ ${place.rating}</div>` : ""}
                <div style="display:flex;gap:8px;flex-wrap:wrap">
                  <span style="background:${color};color:white;font-size:10px;font-weight:bold;padding:2px 8px;border-radius:9999px">${(place.category_name || place.category?.name || "place").toUpperCase()}</span>
                  ${place.google_maps_url ? `<a href="${place.google_maps_url}" target="_blank" rel="noopener noreferrer" style="font-size:11px;color:#3b82f6;text-decoration:none">View on Maps ↗</a>` : ""}
                </div>
                <button onclick="window.__tourmate_analyze_cluster(${idx})" style="margin-top:8px;width:100%;padding:6px;background:#0d6560;color:white;border:none;border-radius:8px;font-size:12px;font-weight:bold;cursor:pointer">🤖 Analyze Area</button>
              </div>`;
            infoWindowRef.current.setContent(content);
            infoWindowRef.current.open(map, marker);
          });

          markersRef.current.push(marker);
        });
      });

      // Expose cluster click handler globally for InfoWindow buttons
      window.__tourmate_analyze_cluster = (idx) => {
        const cluster = clustered.clusters?.[idx];
        if (cluster) handleClusterClick(cluster);
        infoWindowRef.current?.close();
      };

      // Fit map to markers
      if (markersRef.current.length > 0) {
        const bounds = new googleObj.maps.LatLngBounds();
        markersRef.current.forEach((m) => {
          const pos = m.getPosition();
          if (pos) bounds.extend(pos);
        });
        map.fitBounds(bounds, 60);
        if (map.getZoom() > 15) map.setZoom(15);
      }
    },
    [googleObj, clearMarkers] // eslint-disable-line react-hooks/exhaustive-deps
  );

  // ── GPS ───────────────────────────────────────────────────────────────────
  const handleLocate = useCallback(() => {
    if (!navigator.geolocation) return alert("Geolocation not supported by your browser.");
    setLoading(true);
    navigator.geolocation.getCurrentPosition(
      (pos) => {
        const { latitude: lat, longitude: lng } = pos.coords;
        setUserLocation({ lat, lng });
        setCurrentSearchCenter({ lat, lng });

        // Add user location marker
        if (mapInstanceRef.current && googleObj) {
          const userMarker = new googleObj.maps.Marker({
            position: { lat, lng },
            map: mapInstanceRef.current,
            icon: makeUserIcon(googleObj),
            title: "Your Location",
            zIndex: 100,
          });
          markersRef.current.push(userMarker);
          mapInstanceRef.current.setCenter({ lat, lng });
          mapInstanceRef.current.setZoom(13);
        }

        triggerPlaceSearch({ lat, lng });
      },
      (err) => {
        setLoading(false);
        console.error(err);
        alert("Could not get your location. Please allow location access and try again.");
      },
      { enableHighAccuracy: true, timeout: 10000 }
    );
  }, [googleObj, triggerPlaceSearch]);

  // ── Cluster selection & AI enrichment ────────────────────────────────────
  const handleClusterClick = useCallback(
    async (cluster) => {
      setSelectedCluster(cluster);
      setEnriching(true);
      setClusterDetails(null);

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

  // ── Plan My Day ───────────────────────────────────────────────────────────
  const handlePlanMyDay = useCallback(() => {
    if (!selectedCluster) return;
    // Normalize places for ItineraryBuilder
    const normalized = selectedCluster.places.map((p) => ({
      id: p.id || p.external_id,
      name: p.name,
      latitude: p.latitude,
      longitude: p.longitude,
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
      setLoading(true);
      // If autocomplete already handled it, no need to re-fetch
      // Otherwise do a text search with India center
      const center = currentSearchCenter || INDIA_CENTER;
      triggerPlaceSearch({ ...center, fromMap: false });
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
    if (currentSearchCenter) {
      triggerPlaceSearch({ ...currentSearchCenter });
    }
  }, [category, distanceFilter, kValue]); // eslint-disable-line react-hooks/exhaustive-deps

  // ─── Render ───────────────────────────────────────────────────────────────

  const allPlacesEmpty = !loading && places.length === 0 && currentSearchCenter !== null;

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
            className="flex-1 px-3 py-1.5 text-sm bg-gray-100 dark:bg-slate-800 border border-gray-200 dark:border-slate-700 rounded-lg outline-none focus:border-brand-500"
          />
          <button type="submit" className="p-1.5 bg-brand-600 text-white rounded-lg">
            <Search className="w-4 h-4" />
          </button>
        </form>
        <button onClick={() => setShowFilters(!showFilters)} className="p-1.5 bg-gray-100 dark:bg-slate-800 rounded-lg">
          <Filter className="w-4 h-4 text-gray-700 dark:text-slate-300" />
        </button>
      </div>

      {/* ── Left Sidebar ─────────────────────────────────────────────────── */}
      <div className={`absolute md:relative z-20 w-full md:w-72 h-full bg-white dark:bg-slate-900 shadow-xl border-r dark:border-slate-800 flex flex-col transition-transform duration-300 ${showFilters ? "translate-x-0" : "-translate-x-full md:translate-x-0"}`}>

        {/* Header */}
        <div className="p-4 border-b dark:border-slate-800 hidden md:block">
          <h1 className="text-lg font-black text-gray-900 dark:text-white flex items-center gap-2">
            <MapIcon className="text-brand-500 w-5 h-5" /> AI Cluster Map
          </h1>
          <p className="text-xs text-gray-500 dark:text-slate-400 mt-0.5">Explore India with AI-powered clusters</p>
        </div>

        {/* Search (desktop) */}
        <div className="p-4 border-b dark:border-slate-800 hidden md:block">
          <form onSubmit={handleSearchSubmit} className="relative">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
            <input
              ref={searchInputRef}
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="Search city or destination..."
              className="w-full pl-9 pr-10 py-2.5 text-sm bg-gray-50 dark:bg-slate-800 border border-gray-200 dark:border-slate-700 rounded-xl outline-none focus:border-brand-500 focus:ring-1 focus:ring-brand-500 dark:text-white"
            />
            <button type="submit" className="absolute right-2 top-1/2 -translate-y-1/2 p-1 bg-brand-600 text-white rounded-lg">
              <Search className="w-3 h-3" />
            </button>
          </form>
          <p className="text-[10px] text-gray-400 mt-1.5 pl-1">e.g. Bengaluru, Jaipur, Kerala, Goa...</p>
        </div>

        {/* Mobile close + filters header */}
        <div className="md:hidden flex justify-between items-center p-4 border-b dark:border-slate-800">
          <h2 className="font-bold text-gray-900 dark:text-white">Filters</h2>
          <button onClick={() => setShowFilters(false)}><X className="w-5 h-5" /></button>
        </div>

        {/* Filters */}
        <div className="flex-1 overflow-y-auto p-4 space-y-5 custom-scrollbar">

          {/* K Clusters */}
          <div>
            <label className="text-xs font-bold text-gray-500 dark:text-slate-400 uppercase tracking-wider flex justify-between mb-2">
              <span>Travel Clusters</span>
              <span className="text-brand-600">{kValue}</span>
            </label>
            <input
              type="range" min="2" max="8" value={kValue}
              onChange={(e) => setKValue(parseInt(e.target.value))}
              className="w-full accent-brand-600"
            />
          </div>

          {/* Distance */}
          <div>
            <label className="text-xs font-bold text-gray-500 dark:text-slate-400 uppercase tracking-wider mb-2 block">Distance</label>
            <select
              value={distanceFilter}
              onChange={(e) => setDistanceFilter(e.target.value)}
              className="w-full p-2.5 bg-gray-50 dark:bg-slate-800 border border-gray-200 dark:border-slate-700 rounded-xl text-sm dark:text-white outline-none focus:border-brand-500"
            >
              {DISTANCE_OPTIONS.map((o) => (
                <option key={o.value} value={o.value}>{o.label}</option>
              ))}
            </select>
            {distanceFilter !== "all" && !userLocation && (
              <button onClick={handleLocate} className="mt-1.5 text-[11px] text-brand-500 hover:text-brand-600 font-medium flex items-center gap-1">
                <Crosshair className="w-3 h-3" /> Enable GPS to use distance filter
              </button>
            )}
          </div>

          {/* Category */}
          <div>
            <label className="text-xs font-bold text-gray-500 dark:text-slate-400 uppercase tracking-wider mb-2 block">Category</label>
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
              <span>AI Interests {interests.length > 0 && <span className="text-brand-600 normal-case">({interests.length})</span>}</span>
              {showInterests ? <ChevronUp className="w-3 h-3" /> : <ChevronDown className="w-3 h-3" />}
            </button>
            {showInterests && (
              <div className="grid grid-cols-2 gap-1.5">
                {INTERESTS.map((int) => (
                  <label key={int} className="flex items-center gap-2 text-xs text-gray-700 dark:text-slate-300 cursor-pointer">
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
              <label className="text-xs font-bold text-gray-500 dark:text-slate-400 uppercase tracking-wider mb-2 block">Discovered Areas</label>
              <div className="space-y-1.5">
                {clustersData.clusters.filter((c) => c.places.length > 0).map((cluster, i) => (
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
                      <div className="w-3 h-3 rounded-full" style={{ backgroundColor: CLUSTER_COLORS[i % CLUSTER_COLORS.length] }} />
                      <span className="text-sm font-semibold text-gray-800 dark:text-slate-200 truncate">Area {i + 1}</span>
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

        {/* Google Map container */}
        <div ref={mapRef} className="w-full h-full" />

        {/* API Key Error */}
        {mapLoadError && (
          <div className="absolute inset-0 bg-slate-900 flex flex-col items-center justify-center p-8 text-center z-50">
            <div className="bg-red-900/30 border border-red-700 rounded-2xl p-8 max-w-md">
              <MapIcon className="w-12 h-12 text-red-400 mx-auto mb-4" />
              <h2 className="text-xl font-black text-white mb-2">Google Maps Unavailable</h2>
              <p className="text-sm text-slate-400 mb-4">{mapLoadError}</p>
              <div className="text-left bg-slate-800 rounded-xl p-4 text-xs text-slate-300 font-mono">
                <p className="text-slate-500 mb-1"># frontend/.env</p>
                <p>VITE_GOOGLE_MAPS_API_KEY=your-key-here</p>
              </div>
            </div>
          </div>
        )}

        {/* Loading */}
        {loading && (
          <div className="absolute inset-0 bg-white/40 dark:bg-slate-900/60 backdrop-blur-sm z-[50] flex flex-col items-center justify-center">
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
          <div className="absolute bottom-24 left-1/2 -translate-x-1/2 z-[60] bg-white dark:bg-slate-800 rounded-2xl shadow-2xl border border-red-200 dark:border-red-800 p-4 max-w-sm w-full mx-4">
            <div className="flex items-start gap-3">
              <X className="w-5 h-5 text-red-500 shrink-0 mt-0.5" />
              <div className="flex-1 min-w-0">
                <p className="text-sm font-bold text-gray-900 dark:text-white">Error</p>
                <p className="text-xs text-gray-500 dark:text-slate-400 mt-0.5">{apiError}</p>
              </div>
              <button onClick={() => setApiError(null)}><X className="w-4 h-4 text-gray-400" /></button>
            </div>
            <button
              onClick={() => currentSearchCenter && triggerPlaceSearch({ ...currentSearchCenter })}
              className="mt-3 w-full py-1.5 bg-brand-600 text-white rounded-xl text-xs font-bold"
            >
              Try Again
            </button>
          </div>
        )}

        {/* Empty State */}
        {allPlacesEmpty && !apiError && (
          <div className="absolute bottom-24 left-1/2 -translate-x-1/2 z-[60] bg-white dark:bg-slate-800 rounded-2xl shadow-2xl border border-gray-200 dark:border-slate-700 p-5 max-w-xs w-full mx-4 text-center">
            <MapPin className="w-8 h-8 text-gray-400 mx-auto mb-2" />
            <h3 className="font-bold text-gray-900 dark:text-white text-sm mb-1">No places found</h3>
            <p className="text-xs text-gray-500 dark:text-slate-400">Try zooming out, removing a filter, or searching a different area.</p>
          </div>
        )}

        {/* India welcome prompt (before any search) */}
        {!loading && !currentSearchCenter && !mapLoadError && googleLoaded && (
          <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 z-[40] pointer-events-none">
            <div className="bg-white/90 dark:bg-slate-800/90 backdrop-blur border border-gray-200 dark:border-slate-700 rounded-2xl shadow-2xl px-8 py-6 text-center max-w-sm">
              <div className="text-3xl mb-3">🇮🇳</div>
              <h2 className="font-black text-gray-900 dark:text-white text-lg mb-1">Explore India</h2>
              <p className="text-sm text-gray-500 dark:text-slate-400">Search any city, state, or destination to discover tourist clusters.</p>
            </div>
          </div>
        )}

        {/* Map Controls (top right) */}
        <div className="absolute right-14 top-3 z-[40] flex gap-2">
          <button
            onClick={handleLocate}
            className="bg-white dark:bg-slate-800 px-3 py-2 rounded-xl shadow-lg border border-gray-200 dark:border-slate-700 text-gray-700 dark:text-slate-300 hover:text-brand-600 transition flex items-center gap-2 text-xs font-bold"
          >
            <Crosshair className="w-4 h-4" /> Near Me
          </button>
        </div>

        {/* Cluster legend (top left of map) */}
        {clustersData?.clusters?.length > 0 && !loading && (
          <div className="absolute left-3 top-3 z-[40] bg-white/90 dark:bg-slate-900/90 backdrop-blur border border-gray-200 dark:border-slate-700 rounded-xl p-3 shadow-lg max-w-[160px] hidden md:block">
            <p className="text-[10px] font-black text-gray-500 dark:text-slate-400 uppercase tracking-wider mb-2">AI Travel Areas</p>
            {clustersData.clusters.filter((c) => c.places.length > 0).map((c, i) => (
              <div key={i} className="flex items-center gap-2 py-0.5 cursor-pointer hover:bg-gray-100 dark:hover:bg-slate-800 rounded px-1" onClick={() => handleClusterClick(c)}>
                <div className="w-2.5 h-2.5 rounded-full shrink-0" style={{ backgroundColor: CLUSTER_COLORS[i % CLUSTER_COLORS.length] }} />
                <span className="text-xs text-gray-700 dark:text-slate-300 truncate">Area {i + 1}</span>
                <span className="text-[10px] font-bold text-gray-500 ml-auto">{c.places.length}</span>
              </div>
            ))}
          </div>
        )}

        {/* ── Selected Cluster Detail Panel ────────────────────────────── */}
        {selectedCluster && (
          <div className="absolute bottom-0 left-0 right-0 md:bottom-4 md:left-auto md:right-4 md:w-96 bg-white dark:bg-slate-900 rounded-t-2xl md:rounded-2xl shadow-2xl z-[50] overflow-hidden border border-gray-200 dark:border-slate-700 max-h-[80vh] flex flex-col">

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
                    {clusterDetails?.cluster_name || `Travel Area ${(selectedCluster.cluster_id ?? 0) + 1}`}
                  </h2>
                  <p className="text-xs text-white/80 mt-0.5 flex items-center gap-1">
                    <Sparkles className="w-3 h-3" /> AI Analysis · {selectedCluster.places.length} places
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
                  <p className="text-xl font-black text-gray-900 dark:text-white">{selectedCluster.places.length}</p>
                </div>
                <div className="bg-gray-50 dark:bg-slate-800 rounded-xl p-3 text-center border border-gray-100 dark:border-slate-700">
                  <p className="text-[10px] text-gray-500 font-bold uppercase mb-0.5">Est. Time</p>
                  <p className="text-xl font-black text-gray-900 dark:text-white">
                    ~{Math.round((selectedCluster.places.length * 45) / 60 * 10) / 10}h
                  </p>
                </div>
              </div>

              {/* Reasons */}
              {!enriching && clusterDetails?.reasons?.length > 0 && (
                <div className="bg-emerald-50 dark:bg-emerald-900/10 border border-emerald-100 dark:border-emerald-900/30 rounded-xl p-3 space-y-2">
                  <p className="text-[10px] font-black text-emerald-700 dark:text-emerald-400 uppercase tracking-wider">Why visit this area?</p>
                  {clusterDetails.reasons.map((r, i) => (
                    <div key={i} className="flex items-start gap-2 text-xs text-emerald-800 dark:text-emerald-300">
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
                    <span key={i} className="px-2.5 py-0.5 bg-brand-50 dark:bg-brand-900/20 text-brand-700 dark:text-brand-300 text-xs font-semibold rounded-full border border-brand-100 dark:border-brand-800">
                      {c}
                    </span>
                  ))}
                </div>
              )}

              {/* Places list */}
              <div>
                <p className="text-[10px] font-black text-gray-500 dark:text-slate-400 uppercase tracking-wider mb-2">Included Places</p>
                <div className="space-y-1">
                  {selectedCluster.places.slice(0, 6).map((p, i) => (
                    <div key={p.id || i} className="flex items-center gap-3 p-2 rounded-lg hover:bg-gray-50 dark:hover:bg-slate-800 transition">
                      <div
                        className="w-6 h-6 rounded-full text-white text-xs font-bold flex items-center justify-center shrink-0"
                        style={{ backgroundColor: CLUSTER_COLORS[(selectedCluster.cluster_id ?? 0) % CLUSTER_COLORS.length] }}
                      >
                        {i + 1}
                      </div>
                      <div className="min-w-0 flex-1">
                        <p className="text-sm font-semibold text-gray-900 dark:text-white truncate">{p.name}</p>
                        <p className="text-[10px] text-gray-400 truncate capitalize">{p.category_name || p.category?.name || "attraction"}</p>
                      </div>
                      {p.rating && <span className="text-[10px] text-amber-500 font-bold shrink-0">⭐ {p.rating}</span>}
                      {p.google_maps_url && (
                        <a href={p.google_maps_url} target="_blank" rel="noopener noreferrer" className="shrink-0">
                          <ExternalLink className="w-3.5 h-3.5 text-gray-400 hover:text-brand-600" />
                        </a>
                      )}
                    </div>
                  ))}
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
                className="py-2.5 flex items-center justify-center gap-1.5 bg-brand-600 text-white font-bold text-xs rounded-xl hover:bg-brand-700 transition disabled:opacity-50"
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
