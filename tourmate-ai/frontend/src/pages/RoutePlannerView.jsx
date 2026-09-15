import { useState, useEffect } from "react";
import axios from "axios";
import { useAuth } from "../context/AuthContext";
import MapComponent from "../components/MapComponent";
import ShareModal from "../components/ShareModal";

export default function RoutePlannerView() {
  const { token } = useAuth();
  const [allPlaces, setAllPlaces] = useState([]);
  const [search, setSearch] = useState("");
  const [selectedPlaces, setSelectedPlaces] = useState([]);
  const [optimizedRoute, setOptimizedRoute] = useState(null);
  const [routeDetails, setRouteDetails] = useState(null);
  const [totalDistance, setTotalDistance] = useState(0);
  const [loading, setLoading] = useState(false);
  const [optimizing, setOptimizing] = useState(false);
  
  // Share modal state
  const [shareData, setShareData] = useState({
    isOpen: false,
    title: "",
    text: "",
    url: ""
  });

  useEffect(() => {
    const fetchPlaces = async () => {
      setLoading(true);
      try {
        const res = await axios.get(`${import.meta.env.VITE_API_BASE_URL}/places`, {
          headers: { Authorization: `Bearer ${token}` }
        });
        setAllPlaces(res.data.data || []);
      } catch (err) {
        console.error(err);
      } finally {
        setLoading(false);
      }
    };
    if (token) fetchPlaces();
  }, [token]);

  const handleAddPlace = (place) => {
    if (!selectedPlaces.find(p => p.id === place.id)) {
      setSelectedPlaces([...selectedPlaces, place]);
      setOptimizedRoute(null);
      setRouteDetails(null);
    }
  };

  const handleRemovePlace = (id) => {
    setSelectedPlaces(selectedPlaces.filter(p => p.id !== id));
    setOptimizedRoute(null);
    setRouteDetails(null);
  };

  const handleOptimize = async () => {
    if (selectedPlaces.length < 2) return;
    
    setOptimizing(true);
    try {
      const res = await axios.post(
        `${import.meta.env.VITE_API_BASE_URL}/places/route/optimize`,
        { 
          place_ids: selectedPlaces.map(p => p.id),
          algorithm: "astar"
        },
        { headers: { Authorization: `Bearer ${token}` } }
      );
      
      const data = res.data.data;
      setOptimizedRoute(data.optimized_places);
      setTotalDistance(data.total_distance_km);
      setRouteDetails(data);
    } catch (err) {
      console.error(err);
    } finally {
      setOptimizing(false);
    }
  };

  const handleShareRoute = () => {
    const stopNames = (optimizedRoute || selectedPlaces).map((p, i) => `${i + 1}. ${p.name}`).join(", ");
    setShareData({
      isOpen: true,
      title: `Optimized Route with ${selectedPlaces.length} Attractions`,
      text: `🗺️ TourMate A* Route: ${stopNames}. Total distance: ${totalDistance} km (${routeDetails?.estimated_travel_time_formatted || "quick trip"})!`,
      url: window.location.href
    });
  };

  const filteredPlaces = allPlaces.filter(p => 
    p.name.toLowerCase().includes(search.toLowerCase()) && 
    !selectedPlaces.find(sp => sp.id === p.id)
  );

  const placesToMap = optimizedRoute || selectedPlaces;
  
  const center = placesToMap.length > 0 && placesToMap[0].location
    ? [placesToMap[0].location.coordinates[1], placesToMap[0].location.coordinates[0]]
    : [20.5937, 78.9629];

  return (
    <div className="relative h-[calc(100vh-100px)] mx-4 mb-4 rounded-3xl overflow-hidden border border-gray-200 dark:border-slate-800 shadow-2xl">
      
      {/* Floating Sidebar Left */}
      <div className="absolute top-4 left-4 bottom-4 w-[calc(100%-32px)] md:w-[420px] z-[1000] flex flex-col pointer-events-none">
        <div className="bg-white/95 dark:bg-slate-900/95 backdrop-blur-xl border border-gray-200 dark:border-slate-700 shadow-2xl rounded-2xl flex-1 flex flex-col overflow-hidden pointer-events-auto">
          {/* Header */}
          <div className="p-4 border-b dark:border-slate-700 bg-gradient-to-r from-brand-50 to-teal-50 dark:from-slate-800 dark:to-slate-700/80">
            <div className="flex items-center justify-between">
              <div>
                <div className="flex items-center gap-1.5">
                  <span className="text-xs font-bold uppercase tracking-wider px-2 py-0.5 rounded-full bg-brand-100 text-brand-700 dark:bg-brand-900/50 dark:text-brand-300">
                    ML Algorithm
                  </span>
                  <span className="text-xs font-semibold text-emerald-600 dark:text-emerald-400">
                    A* Pathfinding
                  </span>
                </div>
                <h1 className="text-xl font-black text-gray-900 dark:text-white mt-1">
                  A* Route Navigator
                </h1>
                <p className="text-xs text-gray-500 dark:text-slate-400 mt-0.5">
                  Heuristic route optimization: <span className="font-mono text-brand-600 font-semibold">f(n) = g(n) + h(n)</span>
                </p>
              </div>
              {optimizedRoute && (
                <button
                  onClick={handleShareRoute}
                  className="p-2 rounded-xl bg-white dark:bg-slate-700 border border-gray-200 dark:border-slate-600 text-brand-600 dark:text-brand-400 hover:bg-brand-50 transition shadow-sm"
                  title="Share this route"
                >
                  📤
                </button>
              )}
            </div>
          </div>
          
          {/* Selected Itinerary Stops */}
          <div className="p-4 flex-1 overflow-y-auto custom-scrollbar">
            <div className="flex justify-between items-center mb-3">
              <h2 className="font-bold text-sm text-gray-800 dark:text-slate-200 flex items-center gap-2">
                <span>Your Waypoints</span>
                <span className="px-2 py-0.5 text-xs rounded-full bg-gray-100 dark:bg-slate-700 text-gray-600 dark:text-slate-300">
                  {selectedPlaces.length} stops
                </span>
              </h2>
              {optimizedRoute && (
                <span className="text-xs font-bold bg-emerald-100 text-emerald-800 dark:bg-emerald-900/50 dark:text-emerald-300 px-2.5 py-1 rounded-full flex items-center gap-1">
                  <span>⚡</span> A* Optimized
                </span>
              )}
            </div>
            
            <div className="space-y-2.5 mb-5">
              {placesToMap.length === 0 ? (
                <div className="text-xs text-gray-400 italic text-center py-6 bg-gray-50 dark:bg-slate-900/50 rounded-2xl border border-dashed dark:border-slate-700">
                  Search and add tourist spots below to generate optimal sequence
                </div>
              ) : (
                placesToMap.map((p, idx) => (
                  <div key={p.id} className="flex items-center gap-3 bg-white dark:bg-slate-800 border dark:border-slate-700 rounded-xl p-3 shadow-sm dark:shadow-none group transition hover:border-brand-300">
                    <div className={`w-6 h-6 rounded-full flex items-center justify-center text-xs font-bold text-white shrink-0 ${optimizedRoute ? 'bg-emerald-600' : 'bg-brand-600'}`}>
                      {idx + 1}
                    </div>
                    <div className="flex-1 min-w-0">
                      <p className="font-semibold text-xs text-gray-900 dark:text-slate-100 truncate">{p.name}</p>
                      <p className="text-[11px] text-gray-500 dark:text-slate-400 truncate">{p.category?.name || "Attraction"}</p>
                    </div>
                    {!optimizedRoute && (
                      <button 
                        onClick={() => handleRemovePlace(p.id)}
                        className="text-gray-400 hover:text-red-500 transition p-1"
                      >
                        ✕
                      </button>
                    )}
                  </div>
                ))
              )}
            </div>

            {/* Route Optimization Button & Metrics */}
            {selectedPlaces.length > 1 && (
              <div className="mb-5">
                <button
                  onClick={handleOptimize}
                  disabled={optimizing}
                  className="w-full bg-gradient-to-r from-brand-600 to-teal-600 hover:from-brand-700 hover:to-teal-700 text-white font-bold py-3 px-4 rounded-xl shadow-md transition disabled:opacity-70 flex justify-center items-center gap-2 text-sm"
                >
                  {optimizing ? (
                    <>
                      <span className="animate-spin text-lg">↻</span>
                      <span>Computing A* Optimal Path...</span>
                    </>
                  ) : (
                    <>
                      <span>⚡</span>
                      <span>Run A* Route Optimizer</span>
                    </>
                  )}
                </button>
                
                {/* Detailed Metrics Card */}
                {optimizedRoute && routeDetails && (
                  <div className="mt-3 bg-emerald-50/80 dark:bg-emerald-950/30 border border-emerald-200 dark:border-emerald-800 rounded-xl p-3.5 space-y-2">
                    <div className="flex justify-between items-center text-xs font-semibold text-emerald-900 dark:text-emerald-300">
                      <span>Algorithm:</span>
                      <span className="font-mono bg-emerald-100 dark:bg-emerald-900/60 px-2 py-0.5 rounded">A* Heuristic Search</span>
                    </div>
                    <div className="grid grid-cols-2 gap-2 pt-1">
                      <div className="bg-white dark:bg-slate-800 p-2 rounded-lg border border-emerald-100 dark:border-emerald-800/60 text-center">
                        <span className="text-[10px] text-gray-500 dark:text-slate-400 uppercase tracking-wider block font-semibold">Total Distance</span>
                        <span className="text-sm font-bold text-brand-700 dark:text-brand-300">{totalDistance} km</span>
                      </div>
                      <div className="bg-white dark:bg-slate-800 p-2 rounded-lg border border-emerald-100 dark:border-emerald-800/60 text-center">
                        <span className="text-[10px] text-gray-500 dark:text-slate-400 uppercase tracking-wider block font-semibold">Est. Transit Time</span>
                        <span className="text-sm font-bold text-emerald-700 dark:text-emerald-300">{routeDetails.estimated_travel_time_formatted}</span>
                      </div>
                    </div>

                    {/* Turn-by-turn navigation segments */}
                    {routeDetails.segments && routeDetails.segments.length > 0 && (
                      <div className="pt-2">
                        <p className="text-[11px] font-bold text-emerald-900 dark:text-emerald-300 uppercase tracking-wider mb-1.5">
                          Waypoint Directions:
                        </p>
                        <div className="space-y-1.5 max-h-36 overflow-y-auto custom-scrollbar pr-1">
                          {routeDetails.segments.map((seg, i) => (
                            <div key={i} className="text-[11px] bg-white dark:bg-slate-800 p-2 rounded-lg border border-emerald-100 dark:border-slate-700 flex justify-between items-center">
                              <span className="truncate pr-2 font-medium text-gray-700 dark:text-slate-300">
                                {seg.from_name} → {seg.to_name}
                              </span>
                              <span className="font-bold text-brand-600 dark:text-brand-400 shrink-0">
                                {seg.distance_km} km ({seg.estimated_time_mins}m)
                              </span>
                            </div>
                          ))}
                        </div>
                      </div>
                    )}

                    {/* Share button */}
                    <button
                      onClick={handleShareRoute}
                      className="w-full mt-2 py-2 px-3 rounded-lg bg-emerald-600 hover:bg-emerald-700 text-white font-semibold text-xs transition flex items-center justify-center gap-1.5"
                    >
                      <span>📤</span> Share Optimized Route
                    </button>
                  </div>
                )}
              </div>
            )}

            {/* Search to Add Places */}
            <div className="mt-auto border-t dark:border-slate-700 pt-4">
              <h2 className="font-bold text-xs text-gray-700 dark:text-slate-300 uppercase tracking-wider mb-2">
                Add Attractions
              </h2>
              <input 
                type="text"
                placeholder="Search attractions (e.g. Taj Mahal, Red Fort)..."
                value={search}
                onChange={e => setSearch(e.target.value)}
                className="w-full border dark:border-slate-700 dark:bg-slate-900 rounded-xl px-3 py-2 text-xs focus:ring-2 focus:ring-brand-500 outline-none mb-3"
              />
              <div className="max-h-44 overflow-y-auto space-y-1.5 pr-1 custom-scrollbar">
                {loading ? (
                  <div className="text-center text-xs text-gray-400 py-3">Loading places...</div>
                ) : filteredPlaces.length === 0 ? (
                  <div className="text-center text-xs text-gray-400 py-3">No matching attractions</div>
                ) : (
                  filteredPlaces.map(p => (
                    <button 
                      key={p.id}
                      onClick={() => handleAddPlace(p)}
                      className="w-full text-left flex justify-between items-center p-2 hover:bg-brand-50 dark:hover:bg-slate-700/50 rounded-xl transition border border-transparent hover:border-brand-200"
                    >
                      <div className="min-w-0 pr-2">
                        <span className="text-xs font-semibold text-gray-800 dark:text-slate-200 truncate block">{p.name}</span>
                        <span className="text-[10px] text-gray-500 dark:text-slate-400">{p.category?.name || "Attraction"}</span>
                      </div>
                      <span className="text-brand-600 font-bold text-sm shrink-0">＋</span>
                    </button>
                  ))
                )}
              </div>
            </div>
          </div>
        </div>
      </div>
      
      {/* Map filling Entire Screen Behind Sidebar */}
      <div className="absolute inset-0 z-0">
        <MapComponent 
          places={placesToMap} 
          routePath={optimizedRoute ? optimizedRoute : null} 
          center={center}
          zoom={optimizedRoute ? 6 : 5}
        />
      </div>

      {/* Social Share Modal */}
      <ShareModal
        isOpen={shareData.isOpen}
        onClose={() => setShareData({ ...shareData, isOpen: false })}
        title={shareData.title}
        text={shareData.text}
        url={shareData.url}
      />
    </div>
  );
}
