import { useState, useEffect } from "react";
import axios from "axios";
import { useAuth } from "../context/AuthContext";
import MapComponent from "../components/MapComponent";

export default function RoutePlannerView() {
  const { token } = useAuth();
  const [allPlaces, setAllPlaces] = useState([]);
  const [search, setSearch] = useState("");
  const [selectedPlaces, setSelectedPlaces] = useState([]);
  const [optimizedRoute, setOptimizedRoute] = useState(null);
  const [totalDistance, setTotalDistance] = useState(0);
  const [loading, setLoading] = useState(false);
  const [optimizing, setOptimizing] = useState(false);

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
      setOptimizedRoute(null); // Reset route if new place added
    }
  };

  const handleRemovePlace = (id) => {
    setSelectedPlaces(selectedPlaces.filter(p => p.id !== id));
    setOptimizedRoute(null);
  };

  const handleOptimize = async () => {
    if (selectedPlaces.length < 2) return;
    
    setOptimizing(true);
    try {
      const res = await axios.post(
        `${import.meta.env.VITE_API_BASE_URL}/places/route/optimize`,
        { place_ids: selectedPlaces.map(p => p.id) },
        { headers: { Authorization: `Bearer ${token}` } }
      );
      
      setOptimizedRoute(res.data.data.optimized_places);
      setTotalDistance(res.data.data.total_distance_km);
    } catch (err) {
      console.error(err);
    } finally {
      setOptimizing(false);
    }
  };

  const filteredPlaces = allPlaces.filter(p => 
    p.name.toLowerCase().includes(search.toLowerCase()) && 
    !selectedPlaces.find(sp => sp.id === p.id)
  );

  const placesToMap = optimizedRoute || selectedPlaces;
  
  // Calculate center based on selected places
  const center = placesToMap.length > 0 && placesToMap[0].location
    ? [placesToMap[0].location.coordinates[1], placesToMap[0].location.coordinates[0]]
    : [20.5937, 78.9629];

  return (
    <div className="flex flex-col md:flex-row h-[calc(100vh-64px)] bg-gray-50 dark:bg-slate-900/50">
      
      {/* Sidebar Left */}
      <div className="w-full md:w-96 bg-white dark:bg-slate-800 border-r shadow-lg dark:shadow-none flex flex-col z-10 overflow-hidden">
        <div className="p-4 border-b bg-brand-50">
          <h1 className="text-xl font-bold text-brand-800">A* Route Planner</h1>
          <p className="text-sm text-brand-600 mt-1">Select places to find the optimal path</p>
        </div>
        
        {/* Selected Itinerary */}
        <div className="p-4 flex-1 overflow-y-auto">
          <h2 className="font-semibold text-gray-700 dark:text-slate-200 mb-3 flex justify-between items-center">
            Your Stops ({selectedPlaces.length})
            {optimizedRoute && <span className="text-xs bg-green-100 text-green-700 px-2 py-1 rounded-full">Optimized ✨</span>}
          </h2>
          
          <div className="space-y-3 mb-6">
            {placesToMap.length === 0 ? (
              <div className="text-sm text-gray-400 italic text-center py-4 bg-gray-50 dark:bg-slate-900/50 rounded-lg border border-dashed">
                Search and add places below
              </div>
            ) : (
              placesToMap.map((p, idx) => (
                <div key={p.id} className="flex items-center gap-3 bg-white dark:bg-slate-800 border rounded-xl p-3 shadow-sm dark:shadow-none group">
                  <div className={`w-6 h-6 rounded-full flex items-center justify-center text-xs font-bold text-white shrink-0 ${optimizedRoute ? 'bg-green-500' : 'bg-brand-500'}`}>
                    {idx + 1}
                  </div>
                  <div className="flex-1 min-w-0">
                    <p className="font-semibold text-sm text-gray-800 dark:text-slate-100 truncate">{p.name}</p>
                    <p className="text-xs text-gray-500 dark:text-slate-400 truncate">{p.category?.name || "Attraction"}</p>
                  </div>
                  {!optimizedRoute && (
                    <button 
                      onClick={() => handleRemovePlace(p.id)}
                      className="text-gray-400 hover:text-red-500 transition-colors p-1"
                    >
                      ✕
                    </button>
                  )}
                </div>
              ))
            )}
          </div>
          
          {selectedPlaces.length > 1 && (
            <div className="mb-8">
              <button
                onClick={handleOptimize}
                disabled={optimizing}
                className="w-full bg-brand-600 hover:bg-brand-700 text-white font-bold py-3 px-4 rounded-xl shadow-md dark:shadow-none transition-all disabled:opacity-70 flex justify-center items-center gap-2"
              >
                {optimizing ? (
                  <><span className="animate-spin text-xl">↻</span> Optimizing...</>
                ) : (
                  <>✨ Optimize Route</>
                )}
              </button>
              
              {optimizedRoute && (
                <div className="mt-3 text-center text-sm font-medium text-gray-600 dark:text-slate-300 bg-white dark:bg-slate-800 border rounded-lg p-2">
                  Total Travel: <span className="text-brand-600 font-bold">{totalDistance} km</span>
                </div>
              )}
            </div>
          )}

          {/* Search to Add */}
          <div className="mt-auto border-t pt-4">
            <h2 className="font-semibold text-gray-700 dark:text-slate-200 mb-3">Add Places</h2>
            <input 
              type="text"
              placeholder="Search destinations..."
              value={search}
              onChange={e => setSearch(e.target.value)}
              className="w-full border rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-brand-500 outline-none mb-3"
            />
            <div className="max-h-48 overflow-y-auto space-y-2 pr-1 custom-scrollbar">
              {loading ? (
                <div className="text-center text-xs text-gray-400">Loading...</div>
              ) : filteredPlaces.length === 0 ? (
                <div className="text-center text-xs text-gray-400">No matches found</div>
              ) : (
                filteredPlaces.map(p => (
                  <button 
                    key={p.id}
                    onClick={() => handleAddPlace(p)}
                    className="w-full text-left flex justify-between items-center p-2 hover:bg-brand-50 rounded-lg transition-colors border border-transparent hover:border-brand-100"
                  >
                    <span className="text-sm font-medium text-gray-700 dark:text-slate-200 truncate pr-2">{p.name}</span>
                    <span className="text-brand-600 shrink-0">＋</span>
                  </button>
                ))
              )}
            </div>
          </div>
        </div>
      </div>
      
      {/* Map Right */}
      <div className="flex-1 bg-gray-200 dark:bg-slate-700 relative z-0">
        <MapComponent 
          places={placesToMap} 
          routePath={optimizedRoute ? optimizedRoute : null} 
          center={center}
          zoom={optimizedRoute ? 6 : 5}
        />
      </div>
    </div>
  );
}
