import { useState, useEffect, useRef } from "react";
import axios from "axios";
import { API_BASE_URL } from "../api/axios";
import { useAuth } from "../context/AuthContext";
import MapComponent from "../components/MapComponent";
import { 
  MapPin, 
  Navigation, 
  Map as MapIcon, 
  Compass, 
  Crosshair, 
  Search, 
  Plus, 
  Trash2, 
  ArrowRight, 
  Car, 
  Bike, 
  Footprints, 
  ExternalLink, 
  Info,
  AlertCircle
} from "lucide-react";

export default function RoutePlannerView() {
  const { token } = useAuth();
  
  // Locations State
  const [origin, setOrigin] = useState({ query: "", lat: null, lng: null });
  const [destination, setDestination] = useState({ query: "", lat: null, lng: null });
  const [stops, setStops] = useState([]);
  
  const [transportMode, setTransportMode] = useState("car");
  
  // UI State
  const [locating, setLocating] = useState(false);
  const [calculating, setCalculating] = useState(false);
  const [errorMsg, setErrorMsg] = useState("");
  
  // Routing State
  const [routeData, setRouteData] = useState(null);
  
  // AI State
  const [discovering, setDiscovering] = useState(false);
  const [aiSuggestions, setAiSuggestions] = useState(null);

  // Request sequencing to prevent race conditions
  const reqSeqRef = useRef(0);
  const abortCtrlRef = useRef(null);

  // Clean up on unmount
  useEffect(() => {
    return () => {
      if (abortCtrlRef.current) {
        abortCtrlRef.current.abort();
      }
    };
  }, []);

  // Helper to resolve coordinates from query text synchronously before routing
  const resolveLocation = async (locObj) => {
    if (locObj.lat != null && locObj.lng != null) {
      return { lat: Number(locObj.lat), lng: Number(locObj.lng), query: locObj.query };
    }
    const q = (locObj.query || "").trim();
    if (q.length < 2) return null;

    try {
      const res = await axios.get(`${API_BASE_URL}/locations/geocode?query=${encodeURIComponent(q)}`);
      const data = res.data?.data;
      if (data && data.latitude != null && data.longitude != null) {
        return {
          lat: Number(data.latitude),
          lng: Number(data.longitude),
          query: data.display_name || q
        };
      }
    } catch (e) {
      // Fallback search in PostgreSQL locations / POIs
      try {
        const sRes = await axios.get(`${API_BASE_URL}/locations/search?query=${encodeURIComponent(q)}`);
        const items = sRes.data?.data;
        if (items && items.length > 0 && items[0].lat != null && items[0].lng != null) {
          return {
            lat: Number(items[0].lat),
            lng: Number(items[0].lng),
            query: items[0].name || q
          };
        }
      } catch (err2) {}
    }
    return null;
  };

  const handleGetCurrentLocation = () => {
    if (!navigator.geolocation) {
      setErrorMsg("Geolocation is not supported by your browser.");
      return;
    }
    setLocating(true);
    setErrorMsg("");
    navigator.geolocation.getCurrentPosition(
      async (position) => {
        const { latitude, longitude } = position.coords;
        try {
          const res = await axios.get(`${API_BASE_URL}/locations/reverse?lat=${latitude}&lon=${longitude}`);
          setOrigin({
            query: res.data?.data?.display_name || "Current Location",
            lat: latitude,
            lng: longitude
          });
        } catch (err) {
          setOrigin({
            query: "Current Location",
            lat: latitude,
            lng: longitude
          });
        } finally {
          setLocating(false);
        }
      },
      (error) => {
        setErrorMsg("Unable to retrieve your location. Please check your browser permissions.");
        setLocating(false);
      },
      { timeout: 8000 }
    );
  };

  const handleSearchBlur = async (query, index = null) => {
    if (!query || query.trim().length < 2) return;
    try {
      const resolved = await resolveLocation({ query });
      if (resolved) {
        if (index === 'origin') {
          setOrigin({ query: resolved.query, lat: resolved.lat, lng: resolved.lng });
        } else if (index === 'destination') {
          setDestination({ query: resolved.query, lat: resolved.lat, lng: resolved.lng });
        } else if (typeof index === 'number') {
          setStops(prev => {
            const updated = [...prev];
            if (updated[index]) {
              updated[index] = { query: resolved.query, lat: resolved.lat, lng: resolved.lng };
            }
            return updated;
          });
        }
      }
    } catch (err) {
      console.error("Geocoding blur error:", err);
    }
  };

  const handleAddStop = () => {
    setStops([...stops, { query: "", lat: null, lng: null }]);
  };

  const handleRemoveStop = (idx) => {
    setStops(stops.filter((_, i) => i !== idx));
  };

  const executeRouteCalculation = async (resolvedOrigin, resolvedDest, resolvedStops, mode) => {
    const seq = ++reqSeqRef.current;
    
    if (abortCtrlRef.current) {
      abortCtrlRef.current.abort();
    }
    abortCtrlRef.current = new AbortController();

    setCalculating(true);
    setErrorMsg("");
    setRouteData(null);
    setAiSuggestions(null);

    try {
      const coordinates = [
        { latitude: resolvedOrigin.lat, longitude: resolvedOrigin.lng },
        ...resolvedStops.map(s => ({ latitude: s.lat, longitude: s.lng })),
        { latitude: resolvedDest.lat, longitude: resolvedDest.lng }
      ];

      const res = await axios.post(
        `${API_BASE_URL}/locations/route`,
        { coordinates, mode },
        { signal: abortCtrlRef.current.signal }
      );

      // Only update if this is still the active request
      if (seq === reqSeqRef.current && res.data?.data) {
        setRouteData(res.data.data);
      }
    } catch (err) {
      if (axios.isCancel(err) || err.name === "CanceledError") return;
      if (seq === reqSeqRef.current) {
        setErrorMsg("We couldn't calculate this route. Please check your locations and try again.");
      }
    } finally {
      if (seq === reqSeqRef.current) {
        setCalculating(false);
      }
    }
  };

  const handleCalculateRoute = async () => {
    if (!origin.query?.trim() || !destination.query?.trim()) {
      setErrorMsg("Please select a start and destination.");
      return;
    }

    setCalculating(true);
    setErrorMsg("");

    // 1. Resolve Origin if coordinates not yet present
    let resolvedOrigin = await resolveLocation(origin);
    if (!resolvedOrigin) {
      setErrorMsg(`Unable to find location for '${origin.query}'. Please enter a valid address or landmark.`);
      setCalculating(false);
      return;
    }
    setOrigin(resolvedOrigin);

    // 2. Resolve Destination if coordinates not yet present
    let resolvedDest = await resolveLocation(destination);
    if (!resolvedDest) {
      setErrorMsg(`Unable to find location for '${destination.query}'. Please enter a valid address or landmark.`);
      setCalculating(false);
      return;
    }
    setDestination(resolvedDest);

    // 3. Resolve Stops
    const resolvedStops = [];
    for (let i = 0; i < stops.length; i++) {
      const s = stops[i];
      if (s.query?.trim()) {
        const resolved = await resolveLocation(s);
        if (resolved) {
          resolvedStops.push(resolved);
        }
      }
    }
    setStops(resolvedStops);

    // 4. Trigger Route Calculation directly with the resolved coordinates
    await executeRouteCalculation(resolvedOrigin, resolvedDest, resolvedStops, transportMode);
  };

  const handleModeChange = (newMode) => {
    setTransportMode(newMode);
    if (origin.lat && destination.lat) {
      const validStops = stops.filter(s => s.lat != null && s.lng != null);
      executeRouteCalculation(origin, destination, validStops, newMode);
    }
  };

  const handleStartNavigation = () => {
    if (!origin.lat || !destination.lat) {
      setErrorMsg("Please calculate a valid route before starting navigation.");
      return;
    }

    // Map TourMate mode to Google Maps travel mode
    let gmapsMode = "driving";
    if (transportMode === "bike") {
      gmapsMode = "bicycling";
    } else if (transportMode === "walk") {
      gmapsMode = "walking";
    }

    const originParam = `${origin.lat},${origin.lng}`;
    const destParam = `${destination.lat},${destination.lng}`;

    const validStops = stops.filter(s => s.lat != null && s.lng != null);
    const waypointsParam = validStops.length > 0 
      ? `&waypoints=${encodeURIComponent(validStops.map(s => `${s.lat},${s.lng}`).join('|'))}`
      : "";

    const googleMapsUrl = `https://www.google.com/maps/dir/?api=1&origin=${originParam}&destination=${destParam}${waypointsParam}&travelmode=${gmapsMode}`;
    
    // Launch Google Maps navigation in new window / native app handler
    window.open(googleMapsUrl, "_blank", "noopener,noreferrer");
  };

  const handleDiscover = async () => {
    if (!routeData) return;
    setDiscovering(true);
    setAiSuggestions(null);
    try {
      const headers = token ? { Authorization: `Bearer ${token}` } : {};
      const res = await axios.post(
        `${API_BASE_URL}/ai/discover`,
        {
          origin: origin.query || "Origin",
          destination: destination.query || "Destination",
          mode: transportMode,
          stops: stops.length,
          distance: routeData.distance_km || 0
        },
        { headers }
      );
      if (res.data?.data?.suggestions) {
        setAiSuggestions(res.data.data.suggestions);
      }
    } catch (err) {
      console.error("AI discover error:", err);
      setAiSuggestions("AI recommendations are temporarily unavailable. You can still explore the route and nearby places on the map.");
    } finally {
      setDiscovering(false);
    }
  };

  const mapCenter = origin.lat 
    ? [origin.lat, origin.lng] 
    : destination.lat
      ? [destination.lat, destination.lng]
      : [20.5937, 78.9629];

  // Places for map markers
  const mapPlaces = [];
  if (origin.lat) mapPlaces.push({ id: "origin", name: `Start: ${origin.query || "Origin"}`, location: { coordinates: [origin.lng, origin.lat] } });
  stops.forEach((s, i) => {
    if (s.lat) mapPlaces.push({ id: `stop-${i}`, name: `Stop ${i+1}: ${s.query || `Stop ${i+1}`}`, location: { coordinates: [s.lng, s.lat] } });
  });
  if (destination.lat) mapPlaces.push({ id: "dest", name: `Destination: ${destination.query || "Destination"}`, location: { coordinates: [destination.lng, destination.lat] } });

  return (
    <div className="flex flex-col md:flex-row h-[calc(100vh-64px)] bg-gray-50 dark:bg-[#0f172a] relative overflow-hidden">
      
      {/* Route Panel */}
      <div className="w-full md:w-[420px] bg-white/95 dark:bg-slate-900/95 backdrop-blur-xl border-r border-gray-200 dark:border-slate-800 shadow-2xl flex flex-col z-20">
        <div className="p-5 border-b border-gray-100 dark:border-slate-800">
          <h1 className="text-2xl font-black text-gray-900 dark:text-white flex items-center gap-2">
            <Compass className="text-brand-500" /> Route Planner
          </h1>
          <p className="text-sm text-gray-500 dark:text-slate-400 mt-1">Calculate optimal routes & navigate with Google Maps</p>
        </div>

        <div className="flex-1 overflow-y-auto custom-scrollbar p-5 space-y-6">
          
          {errorMsg && (
            <div className="bg-red-50 dark:bg-red-900/30 text-red-600 dark:text-red-400 p-3.5 rounded-xl text-sm font-medium border border-red-200 dark:border-red-800/50 flex items-start gap-2.5">
              <AlertCircle className="w-5 h-5 shrink-0 mt-0.5" />
              <div>{errorMsg}</div>
            </div>
          )}

          {/* Form */}
          <div className="space-y-4 relative">
            <div className="absolute left-[15px] top-8 bottom-8 w-[2px] bg-gray-200 dark:bg-slate-700 pointer-events-none z-0"></div>

            {/* Origin */}
            <div className="relative z-10 flex gap-3">
              <div className="w-8 h-8 rounded-full bg-brand-100 dark:bg-brand-900/50 flex items-center justify-center shrink-0 border-2 border-white dark:border-slate-900 shadow-sm mt-1">
                <div className="w-3 h-3 rounded-full bg-brand-600"></div>
              </div>
              <div className="flex-1 space-y-2">
                <label className="text-xs font-bold text-gray-500 dark:text-slate-400 uppercase tracking-wider">From (Origin)</label>
                <div className="flex flex-col gap-2">
                  <button 
                    type="button"
                    onClick={handleGetCurrentLocation} 
                    disabled={locating} 
                    className="w-full text-left px-4 py-2.5 bg-blue-50 hover:bg-blue-100 dark:bg-blue-900/20 dark:hover:bg-blue-900/40 text-blue-700 dark:text-blue-400 rounded-xl text-sm font-bold flex items-center gap-2 transition-colors border border-blue-100 dark:border-blue-800/50"
                  >
                    <Crosshair className="w-4 h-4" /> {locating ? "Locating..." : "Use My Current Location"}
                  </button>
                  <div className="relative">
                    <Search className="w-4 h-4 absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" />
                    <input 
                      type="text" 
                      placeholder="Search origin address or landmark..." 
                      value={origin.query} 
                      onChange={e => setOrigin({ ...origin, query: e.target.value, lat: null, lng: null })}
                      onBlur={() => handleSearchBlur(origin.query, 'origin')}
                      className="w-full bg-gray-50 dark:bg-slate-800 border border-gray-200 dark:border-slate-700 rounded-xl pl-9 pr-4 py-2.5 text-sm focus:ring-2 focus:ring-brand-500 outline-none text-gray-900 dark:text-white"
                    />
                  </div>
                </div>
              </div>
            </div>

            {/* Stops */}
            {stops.map((stop, idx) => (
              <div key={idx} className="relative z-10 flex gap-3">
                <div className="w-8 h-8 rounded-full bg-white dark:bg-slate-800 flex items-center justify-center shrink-0 border-2 border-gray-200 dark:border-slate-700 shadow-sm mt-1">
                  <div className="w-2.5 h-2.5 rounded-full bg-gray-400"></div>
                </div>
                <div className="flex-1 relative">
                  <div className="relative">
                    <input 
                      type="text" 
                      placeholder={`Add stop #${idx + 1}...`} 
                      value={stop.query} 
                      onChange={e => {
                        const newStops = [...stops];
                        newStops[idx] = { ...newStops[idx], query: e.target.value, lat: null, lng: null };
                        setStops(newStops);
                      }}
                      onBlur={() => handleSearchBlur(stop.query, idx)}
                      className="w-full bg-gray-50 dark:bg-slate-800 border border-gray-200 dark:border-slate-700 rounded-xl px-4 py-2.5 text-sm focus:ring-2 focus:ring-brand-500 outline-none text-gray-900 dark:text-white"
                    />
                    <button 
                      type="button"
                      onClick={() => handleRemoveStop(idx)} 
                      className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400 hover:text-red-500"
                    >
                      <Trash2 className="w-4 h-4" />
                    </button>
                  </div>
                </div>
              </div>
            ))}
            
            <div className="relative z-10 pl-11">
              <button 
                type="button"
                onClick={handleAddStop} 
                className="text-xs font-bold text-gray-500 hover:text-brand-600 dark:text-slate-400 dark:hover:text-brand-400 flex items-center gap-1 bg-white dark:bg-slate-800 px-3 py-1.5 rounded-lg border border-gray-200 dark:border-slate-700 shadow-sm transition-colors"
              >
                <Plus className="w-3 h-3" /> Add Stop
              </button>
            </div>

            {/* Destination */}
            <div className="relative z-10 flex gap-3">
              <div className="w-8 h-8 rounded-full bg-red-100 dark:bg-red-900/50 flex items-center justify-center shrink-0 border-2 border-white dark:border-slate-900 shadow-sm mt-1">
                <MapPin className="w-4 h-4 text-red-600" />
              </div>
              <div className="flex-1 space-y-2">
                <label className="text-xs font-bold text-gray-500 dark:text-slate-400 uppercase tracking-wider">To (Destination)</label>
                <div className="relative">
                  <Search className="w-4 h-4 absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" />
                  <input 
                    type="text" 
                    placeholder="Search destination address or landmark..." 
                    value={destination.query} 
                    onChange={e => setDestination({ ...destination, query: e.target.value, lat: null, lng: null })}
                    onBlur={() => handleSearchBlur(destination.query, 'destination')}
                    className="w-full bg-gray-50 dark:bg-slate-800 border border-gray-200 dark:border-slate-700 rounded-xl pl-9 pr-4 py-2.5 text-sm focus:ring-2 focus:ring-brand-500 outline-none text-gray-900 dark:text-white"
                  />
                </div>
              </div>
            </div>
          </div>

          <hr className="border-gray-100 dark:border-slate-800" />

          {/* Transportation */}
          <div>
            <label className="text-xs font-bold text-gray-500 dark:text-slate-400 uppercase tracking-wider block mb-3">Travel By</label>
            <div className="flex gap-2">
              {[
                { id: "car", icon: Car, label: "Car" },
                { id: "bike", icon: Bike, label: "Bike" },
                { id: "walk", icon: Footprints, label: "Walk" }
              ].map(mode => (
                <button
                  key={mode.id}
                  type="button"
                  onClick={() => handleModeChange(mode.id)}
                  className={`flex-1 py-2.5 rounded-xl border flex flex-col items-center gap-1 transition-all ${transportMode === mode.id ? 'bg-gray-900 border-gray-900 text-white dark:bg-white dark:border-white dark:text-gray-900 shadow-md ring-2 ring-brand-500/20' : 'bg-white dark:bg-slate-800 border-gray-200 dark:border-slate-700 text-gray-600 dark:text-slate-400 hover:border-gray-300'}`}
                >
                  <mode.icon className="w-5 h-5" />
                  <span className="text-[10px] font-bold uppercase tracking-wider">{mode.label}</span>
                </button>
              ))}
            </div>
          </div>

          <button
            type="button"
            onClick={handleCalculateRoute}
            disabled={calculating || !origin.query?.trim() || !destination.query?.trim()}
            className="w-full bg-brand-600 hover:bg-brand-700 text-white font-bold py-3.5 px-4 rounded-xl shadow-lg transition-all disabled:opacity-50 disabled:cursor-not-allowed flex justify-center items-center gap-2 text-base"
          >
            {calculating ? (
              <><div className="w-5 h-5 border-2 border-white border-t-transparent rounded-full animate-spin"></div> Calculating...</>
            ) : "Calculate Route"}
          </button>
          
          {/* Route Summary */}
          {routeData && (
            <div className="bg-emerald-50 dark:bg-emerald-900/20 border border-emerald-200 dark:border-emerald-800/50 rounded-2xl p-5 animate-fade-in-up space-y-4">
              <div className="flex justify-between items-start">
                <div>
                  <h3 className="text-lg font-black text-emerald-900 dark:text-emerald-100">Your Route</h3>
                  <p className="text-xs font-semibold text-emerald-700 dark:text-emerald-400 capitalize flex items-center gap-1.5 mt-0.5">
                    {transportMode === 'car' ? <Car className="w-3.5 h-3.5"/> : transportMode === 'bike' ? <Bike className="w-3.5 h-3.5"/> : <Footprints className="w-3.5 h-3.5"/>}
                    Via {transportMode}
                  </p>
                </div>
                <div className="text-right">
                  <p className="text-2xl font-black text-emerald-600 dark:text-emerald-400">{routeData.distance_km} <span className="text-sm font-bold">km</span></p>
                  <p className="text-sm font-bold text-emerald-800 dark:text-emerald-300">
                    {routeData.duration_minutes > 60 
                      ? `${Math.floor(routeData.duration_minutes / 60)}h ${Math.round(routeData.duration_minutes % 60)}m` 
                      : `${Math.round(routeData.duration_minutes)} min`}
                  </p>
                </div>
              </div>
              
              <button 
                type="button"
                onClick={handleStartNavigation} 
                className="w-full bg-emerald-600 hover:bg-emerald-700 text-white font-bold py-3 px-4 rounded-xl shadow-md transition-all flex justify-center items-center gap-2 text-sm"
              >
                <Navigation className="w-4 h-4" /> Start Navigation in Google Maps <ExternalLink className="w-3.5 h-3.5 ml-1 opacity-70" />
              </button>

              <button 
                type="button"
                onClick={handleDiscover} 
                disabled={discovering} 
                className="w-full bg-white dark:bg-slate-800 text-brand-600 dark:text-brand-400 font-bold py-2.5 px-4 rounded-xl shadow-sm border border-emerald-100 dark:border-emerald-800/80 transition-all flex justify-center items-center gap-2 text-sm hover:bg-emerald-50/50"
              >
                {discovering ? <span className="animate-pulse">Asking AI...</span> : <><span>✦</span> Discover Along Your Route</>}
              </button>
            </div>
          )}

          {/* AI Suggestions */}
          {aiSuggestions && (
            <div className="bg-gradient-to-r from-brand-50 to-indigo-50 dark:from-brand-900/20 dark:to-indigo-900/20 border border-brand-200 dark:border-brand-800/50 rounded-2xl p-5 animate-fade-in-up">
              <h3 className="font-bold text-brand-900 dark:text-brand-100 flex items-center gap-2 mb-3 text-sm">
                <span>✦</span> AI Recommendations
              </h3>
              <p className="text-sm text-gray-700 dark:text-slate-300 whitespace-pre-wrap leading-relaxed">{aiSuggestions}</p>
            </div>
          )}

          {/* Turn by turn */}
          {routeData && routeData.steps && routeData.steps.length > 0 && (
            <div className="border border-gray-200 dark:border-slate-800 rounded-2xl overflow-hidden bg-white dark:bg-slate-900">
              <div className="bg-gray-50 dark:bg-slate-800/80 p-3 border-b border-gray-200 dark:border-slate-700">
                <h3 className="font-bold text-sm text-gray-700 dark:text-slate-300">Route Directions ({routeData.steps.length} steps)</h3>
              </div>
              <div className="max-h-64 overflow-y-auto custom-scrollbar p-1">
                {routeData.steps.map((step, idx) => (
                  <div key={idx} className="flex gap-3 p-3 border-b border-gray-100 dark:border-slate-800 last:border-0 hover:bg-gray-50 dark:hover:bg-slate-800/50">
                    <div className="mt-0.5 text-gray-400 font-bold">
                      {step.instruction.toLowerCase().includes("turn left") ? "←" : 
                       step.instruction.toLowerCase().includes("turn right") ? "→" : 
                       step.instruction.toLowerCase().includes("arrive") ? "📍" : "↑"}
                    </div>
                    <div>
                      <p className="text-sm font-semibold text-gray-800 dark:text-slate-200">{step.instruction}</p>
                      {step.distance_m > 0 && (
                        <p className="text-xs text-gray-500 dark:text-slate-400 mt-0.5">
                          {step.distance_m >= 1000 ? `${(step.distance_m / 1000).toFixed(1)} km` : `${Math.round(step.distance_m)} m`}
                        </p>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

        </div>
      </div>
      
      {/* Map Area */}
      <div className="flex-1 relative z-0">
        <MapComponent 
          places={mapPlaces} 
          routePath={routeData ? routeData.geometry : null} 
          center={mapCenter}
          zoom={routeData ? 12 : 13}
        />
      </div>
      
    </div>
  );
}
