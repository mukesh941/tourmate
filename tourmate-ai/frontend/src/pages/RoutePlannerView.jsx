import { useState, useEffect, useRef } from "react";
import axios from "axios";
import { API_BASE_URL } from "../api/axios";
import { useAuth } from "../context/AuthContext";
import MapComponent from "../components/MapComponent";
import { MapPin, Navigation, Map as MapIcon, Compass, Crosshair, Search, Plus, Trash2, ArrowRight, Car, Bike, Footprints, Bus, Info } from "lucide-react";

export default function RoutePlannerView() {
  const { token } = useAuth();
  
  // Locations State
  const [origin, setOrigin] = useState({ query: "", lat: null, lng: null });
  const [destination, setDestination] = useState({ query: "", lat: null, lng: null });
  const [stops, setStops] = useState([]);
  
  const [transportMode, setTransportMode] = useState("car");
  
  // UI State
  const [loading, setLoading] = useState(false);
  const [calculating, setCalculating] = useState(false);
  const [errorMsg, setErrorMsg] = useState("");
  
  // Routing State
  const [routeData, setRouteData] = useState(null);
  const [navigating, setNavigating] = useState(false);
  const [userLocation, setUserLocation] = useState(null);
  
  // AI State
  const [discovering, setDiscovering] = useState(false);
  const [aiSuggestions, setAiSuggestions] = useState(null);

  const watchIdRef = useRef(null);

  useEffect(() => {
    return () => {
      if (watchIdRef.current) {
        navigator.geolocation.clearWatch(watchIdRef.current);
      }
    };
  }, []);

  const handleGetCurrentLocation = () => {
    if (!navigator.geolocation) {
      setErrorMsg("Geolocation is not supported by your browser");
      return;
    }
    setLoading(true);
    navigator.geolocation.getCurrentPosition(
      async (position) => {
        const { latitude, longitude } = position.coords;
        try {
          const res = await axios.get(`${API_BASE_URL}/locations/reverse?lat=${latitude}&lon=${longitude}`);
          setOrigin({
            query: res.data.data.display_name,
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
          setLoading(false);
        }
      },
      (error) => {
        setErrorMsg("Unable to retrieve your location. Please check your permissions.");
        setLoading(false);
      }
    );
  };

  const handleSearch = async (query, index = null) => {
    if (!query || query.length < 2) return;
    try {
      const res = await axios.get(`${API_BASE_URL}/locations/geocode?query=${query}`);
      const data = res.data.data;
      if (data) {
        if (index === 'origin') setOrigin({ query: data.display_name, lat: data.latitude, lng: data.longitude });
        else if (index === 'destination') setDestination({ query: data.display_name, lat: data.latitude, lng: data.longitude });
        else {
          const newStops = [...stops];
          newStops[index] = { query: data.display_name, lat: data.latitude, lng: data.longitude };
          setStops(newStops);
        }
      }
    } catch (err) {
      console.error(err);
    }
  };

  const handleAddStop = () => {
    setStops([...stops, { query: "", lat: null, lng: null }]);
  };

  const handleRemoveStop = (idx) => {
    setStops(stops.filter((_, i) => i !== idx));
  };

  const handleCalculateRoute = async () => {
    if (!origin.lat || !destination.lat) {
      setErrorMsg("Please provide valid origin and destination locations.");
      return;
    }
    
    setCalculating(true);
    setErrorMsg("");
    setRouteData(null);
    setAiSuggestions(null);
    
    try {
      const coordinates = [
        { latitude: origin.lat, longitude: origin.lng },
        ...stops.filter(s => s.lat).map(s => ({ latitude: s.lat, longitude: s.lng })),
        { latitude: destination.lat, longitude: destination.lng }
      ];
      
      const res = await axios.post(
        `${API_BASE_URL}/locations/route`,
        { coordinates, mode: transportMode }
      );
      
      setRouteData(res.data.data);
    } catch (err) {
      setErrorMsg("We couldn't calculate this route. Please check your locations and try again.");
    } finally {
      setCalculating(false);
    }
  };

  const handleStartNavigation = () => {
    if (!navigator.geolocation) {
      setErrorMsg("GPS tracking is unavailable.");
      return;
    }
    setNavigating(true);
    watchIdRef.current = navigator.geolocation.watchPosition(
      (position) => {
        setUserLocation({
          lat: position.coords.latitude,
          lng: position.coords.longitude
        });
      },
      (error) => console.error(error),
      { enableHighAccuracy: true, maximumAge: 10000, timeout: 5000 }
    );
  };

  const handleStopNavigation = () => {
    setNavigating(false);
    setUserLocation(null);
    if (watchIdRef.current) {
      navigator.geolocation.clearWatch(watchIdRef.current);
      watchIdRef.current = null;
    }
  };

  const handleDiscover = async () => {
    if (!routeData) return;
    setDiscovering(true);
    try {
      const res = await axios.post(
        `${API_BASE_URL}/ai/discover`,
        {
          origin: origin.query,
          destination: destination.query,
          mode: transportMode,
          stops: stops.length,
          distance: routeData.distance_km
        },
        { headers: { Authorization: `Bearer ${token}` } }
      );
      setAiSuggestions(res.data.data.suggestions);
    } catch (err) {
      console.error(err);
    } finally {
      setDiscovering(false);
    }
  };

  const mapCenter = userLocation 
    ? [userLocation.lat, userLocation.lng] 
    : origin.lat 
      ? [origin.lat, origin.lng] 
      : [20.5937, 78.9629];

  // Places for map markers
  const mapPlaces = [];
  if (origin.lat) mapPlaces.push({ id: "origin", name: "Origin", location: { coordinates: [origin.lng, origin.lat] } });
  stops.forEach((s, i) => {
    if (s.lat) mapPlaces.push({ id: `stop-${i}`, name: `Stop ${i+1}`, location: { coordinates: [s.lng, s.lat] } });
  });
  if (destination.lat) mapPlaces.push({ id: "dest", name: "Destination", location: { coordinates: [destination.lng, destination.lat] } });
  
  if (userLocation) mapPlaces.push({ id: "user", name: "Current Position", location: { coordinates: [userLocation.lng, userLocation.lat] } });

  return (
    <div className="flex flex-col md:flex-row h-[calc(100vh-64px)] bg-gray-50 dark:bg-[#0f172a] relative overflow-hidden">
      
      {/* Route Panel */}
      <div className={`w-full md:w-[420px] bg-white/95 dark:bg-slate-900/95 backdrop-blur-xl border-r border-gray-200 dark:border-slate-800 shadow-2xl flex flex-col z-20 transition-transform duration-300 ${navigating ? 'md:-translate-x-full md:w-0' : 'translate-x-0'}`}>
        <div className="p-5 border-b border-gray-100 dark:border-slate-800">
          <h1 className="text-2xl font-black text-gray-900 dark:text-white flex items-center gap-2">
            <Compass className="text-brand-500" /> Route Planner
          </h1>
          <p className="text-sm text-gray-500 dark:text-slate-400 mt-1">Calculate optimal routes & navigate</p>
        </div>

        <div className="flex-1 overflow-y-auto custom-scrollbar p-5 space-y-6">
          
          {errorMsg && (
            <div className="bg-red-50 dark:bg-red-900/30 text-red-600 dark:text-red-400 p-3 rounded-xl text-sm font-medium border border-red-200 dark:border-red-800/50">
              {errorMsg}
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
                <label className="text-xs font-bold text-gray-500 dark:text-slate-400 uppercase tracking-wider">From</label>
                <div className="flex flex-col gap-2">
                  <button onClick={handleGetCurrentLocation} disabled={loading} className="w-full text-left px-4 py-2.5 bg-blue-50 hover:bg-blue-100 dark:bg-blue-900/20 dark:hover:bg-blue-900/40 text-blue-700 dark:text-blue-400 rounded-xl text-sm font-bold flex items-center gap-2 transition-colors border border-blue-100 dark:border-blue-800/50">
                    <Crosshair className="w-4 h-4" /> {loading ? "Locating..." : "Use My Current Location"}
                  </button>
                  <div className="relative">
                    <Search className="w-4 h-4 absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" />
                    <input 
                      type="text" 
                      placeholder="Search origin..." 
                      value={origin.query} 
                      onChange={e => setOrigin({ ...origin, query: e.target.value })}
                      onBlur={() => handleSearch(origin.query, 'origin')}
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
                      placeholder="Add stop..." 
                      value={stop.query} 
                      onChange={e => {
                        const newStops = [...stops];
                        newStops[idx].query = e.target.value;
                        setStops(newStops);
                      }}
                      onBlur={() => handleSearch(stop.query, idx)}
                      className="w-full bg-gray-50 dark:bg-slate-800 border border-gray-200 dark:border-slate-700 rounded-xl px-4 py-2.5 text-sm focus:ring-2 focus:ring-brand-500 outline-none text-gray-900 dark:text-white"
                    />
                    <button onClick={() => handleRemoveStop(idx)} className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400 hover:text-red-500">
                      <Trash2 className="w-4 h-4" />
                    </button>
                  </div>
                </div>
              </div>
            ))}
            
            <div className="relative z-10 pl-11">
              <button onClick={handleAddStop} className="text-xs font-bold text-gray-500 hover:text-brand-600 dark:text-slate-400 dark:hover:text-brand-400 flex items-center gap-1 bg-white dark:bg-slate-800 px-3 py-1.5 rounded-lg border border-gray-200 dark:border-slate-700 shadow-sm transition-colors">
                <Plus className="w-3 h-3" /> Add Stop
              </button>
            </div>

            {/* Destination */}
            <div className="relative z-10 flex gap-3">
              <div className="w-8 h-8 rounded-full bg-red-100 dark:bg-red-900/50 flex items-center justify-center shrink-0 border-2 border-white dark:border-slate-900 shadow-sm mt-1">
                <MapPin className="w-4 h-4 text-red-600" />
              </div>
              <div className="flex-1 space-y-2">
                <label className="text-xs font-bold text-gray-500 dark:text-slate-400 uppercase tracking-wider">To</label>
                <div className="relative">
                  <Search className="w-4 h-4 absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" />
                  <input 
                    type="text" 
                    placeholder="Search destination..." 
                    value={destination.query} 
                    onChange={e => setDestination({ ...destination, query: e.target.value })}
                    onBlur={() => handleSearch(destination.query, 'destination')}
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
                  onClick={() => setTransportMode(mode.id)}
                  className={`flex-1 py-2 rounded-xl border flex flex-col items-center gap-1 transition-all ${transportMode === mode.id ? 'bg-gray-900 border-gray-900 text-white dark:bg-white dark:border-white dark:text-gray-900 shadow-md' : 'bg-white dark:bg-slate-800 border-gray-200 dark:border-slate-700 text-gray-600 dark:text-slate-400'}`}
                >
                  <mode.icon className="w-5 h-5" />
                  <span className="text-[10px] font-bold uppercase">{mode.label}</span>
                </button>
              ))}
            </div>
          </div>

          <button
            onClick={handleCalculateRoute}
            disabled={calculating || !origin.query || !destination.query}
            className="w-full bg-brand-600 hover:bg-brand-700 text-white font-bold py-3.5 px-4 rounded-xl shadow-lg transition-all disabled:opacity-50 disabled:shadow-none flex justify-center items-center gap-2"
          >
            {calculating ? (
              <><div className="w-5 h-5 border-2 border-white border-t-transparent rounded-full animate-spin"></div> Calculating...</>
            ) : "Calculate Route"}
          </button>
          
          {/* Route Summary */}
          {routeData && (
            <div className="bg-emerald-50 dark:bg-emerald-900/20 border border-emerald-200 dark:border-emerald-800/50 rounded-2xl p-5 animate-fade-in-up">
              <div className="flex justify-between items-start mb-4">
                <div>
                  <h3 className="text-lg font-black text-emerald-900 dark:text-emerald-100">Your Route</h3>
                  <p className="text-xs font-semibold text-emerald-700 dark:text-emerald-400 capitalize flex items-center gap-1">
                    {transportMode === 'car' ? <Car className="w-3 h-3"/> : transportMode === 'bike' ? <Bike className="w-3 h-3"/> : <Footprints className="w-3 h-3"/>}
                    Via {transportMode}
                  </p>
                </div>
                <div className="text-right">
                  <p className="text-2xl font-black text-emerald-600 dark:text-emerald-400">{routeData.distance_km} <span className="text-sm font-bold">km</span></p>
                  <p className="text-sm font-bold text-emerald-800 dark:text-emerald-300">{routeData.duration_minutes > 60 ? `${Math.floor(routeData.duration_minutes/60)}h ${routeData.duration_minutes%60}m` : `${routeData.duration_minutes} min`}</p>
                </div>
              </div>
              
              <button onClick={handleStartNavigation} className="w-full bg-emerald-600 hover:bg-emerald-700 text-white font-bold py-3 px-4 rounded-xl shadow-md transition-all flex justify-center items-center gap-2 mb-3">
                <Navigation className="w-4 h-4" /> Start Navigation
              </button>

              <button onClick={handleDiscover} disabled={discovering} className="w-full bg-white dark:bg-slate-800 text-brand-600 dark:text-brand-400 font-bold py-2.5 px-4 rounded-xl shadow-sm border border-emerald-100 dark:border-emerald-800 transition-all flex justify-center items-center gap-2 text-sm">
                {discovering ? <span className="animate-pulse">Asking AI...</span> : <><span>✦</span> Discover Along Your Route</>}
              </button>
            </div>
          )}

          {/* AI Suggestions */}
          {aiSuggestions && (
            <div className="bg-gradient-to-r from-brand-50 to-indigo-50 dark:from-brand-900/20 dark:to-indigo-900/20 border border-brand-200 dark:border-brand-800/50 rounded-2xl p-5">
              <h3 className="font-bold text-brand-900 dark:text-brand-100 flex items-center gap-2 mb-3 text-sm">
                <span>✦</span> AI Recommendations
              </h3>
              <p className="text-sm text-gray-700 dark:text-slate-300 whitespace-pre-wrap leading-relaxed">{aiSuggestions}</p>
            </div>
          )}

          {/* Turn by turn */}
          {routeData && routeData.steps && (
            <div className="border border-gray-200 dark:border-slate-800 rounded-2xl overflow-hidden bg-white dark:bg-slate-900">
              <div className="bg-gray-50 dark:bg-slate-800/80 p-3 border-b border-gray-200 dark:border-slate-700">
                <h3 className="font-bold text-sm text-gray-700 dark:text-slate-300">Route Details</h3>
              </div>
              <div className="max-h-64 overflow-y-auto custom-scrollbar p-1">
                {routeData.steps.map((step, idx) => (
                  <div key={idx} className="flex gap-3 p-3 border-b border-gray-100 dark:border-slate-800 last:border-0 hover:bg-gray-50 dark:hover:bg-slate-800/50">
                    <div className="mt-0.5 text-gray-400">
                      {step.instruction.toLowerCase().includes("turn left") ? "←" : 
                       step.instruction.toLowerCase().includes("turn right") ? "→" : 
                       step.instruction.toLowerCase().includes("arrive") ? "📍" : "↑"}
                    </div>
                    <div>
                      <p className="text-sm font-semibold text-gray-800 dark:text-slate-200">{step.instruction}</p>
                      {step.distance_m > 0 && (
                        <p className="text-xs text-gray-500 dark:text-slate-400 mt-0.5">
                          {step.distance_m > 1000 ? `${(step.distance_m/1000).toFixed(1)} km` : `${Math.round(step.distance_m)} m`}
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
          zoom={routeData ? 10 : 13}
        />
        
        {/* Navigation Overlay */}
        {navigating && (
          <div className="absolute top-4 left-4 right-4 md:left-1/2 md:-translate-x-1/2 md:w-96 bg-gray-900/90 backdrop-blur-md rounded-2xl p-5 shadow-2xl z-50 text-white animate-fade-in-up border border-gray-700">
            <div className="flex justify-between items-start mb-4">
              <div className="flex items-center gap-2 text-emerald-400 font-bold text-sm uppercase tracking-wider">
                <Navigation className="w-4 h-4 animate-pulse" /> Navigation Active
              </div>
              <button onClick={handleStopNavigation} className="text-gray-400 hover:text-white bg-gray-800 rounded-full p-1.5 transition">
                <Trash2 className="w-4 h-4" />
              </button>
            </div>
            
            <div className="flex items-end justify-between">
              <div>
                <p className="text-4xl font-black">{routeData?.distance_km} <span className="text-lg">km</span></p>
                <p className="text-gray-400 font-semibold mt-1">Remaining Distance</p>
              </div>
              <div className="text-right">
                <p className="text-2xl font-bold">{routeData?.duration_minutes > 60 ? `${Math.floor(routeData.duration_minutes/60)}h ${routeData.duration_minutes%60}m` : `${routeData.duration_minutes} min`}</p>
                <p className="text-gray-400 font-semibold mt-1">ETA</p>
              </div>
            </div>
            
            {userLocation ? (
              <div className="mt-4 pt-4 border-t border-gray-700 text-sm flex gap-2 text-blue-300">
                <Info className="w-4 h-4 shrink-0" />
                <p>Tracking your position. Follow the highlighted route on the map.</p>
              </div>
            ) : (
              <div className="mt-4 pt-4 border-t border-gray-700 text-sm flex gap-2 text-amber-300">
                <div className="w-4 h-4 border-2 border-amber-300 border-t-transparent rounded-full animate-spin shrink-0"></div>
                <p>Acquiring GPS signal...</p>
              </div>
            )}
          </div>
        )}
      </div>
      
    </div>
  );
}
