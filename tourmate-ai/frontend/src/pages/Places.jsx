import { useState, useEffect } from "react";
import { Link } from "react-router-dom";
import { getPlaces, getCategories, getDestinations } from "../api/places";
import MapComponent from "../components/MapComponent";
import { NEUTRAL_PLACEHOLDER_IMAGE, handleImageError } from "../config/imageConfig";

export default function Places() {
  const [places, setPlaces] = useState([]);
  const [loading, setLoading] = useState(true);
  const [categories, setCategories] = useState([]);
  const [destinations, setDestinations] = useState([]);
  const [showMap, setShowMap] = useState(true);
  const [mapCenter, setMapCenter] = useState([20.5937, 78.9629]); // Default to India center
  const [mapZoom, setMapZoom] = useState(5);
  const [isLocating, setIsLocating] = useState(false);
  
  const [filters, setFilters] = useState({ q: "", category_id: "", min_rating: "", lat: "", lng: "", radius_km: 10 });

  useEffect(() => {
    getCategories().then(setCategories);
    getDestinations().then(setDestinations);
  }, []);

  const loadPlaces = async () => {
    setLoading(true);
    try {
      const data = await getPlaces(filters);
      setPlaces(data || []);
    } catch (err) {
      console.error("Failed to load places:", err);
      setPlaces([]);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadPlaces();
  }, [filters]);

  const updateFilter = field => e => setFilters({ ...filters, [field]: e.target.value });

  const handleSearchNearMe = () => {
    setIsLocating(true);
    if ("geolocation" in navigator) {
      navigator.geolocation.getCurrentPosition(
        (position) => {
          const { latitude, longitude } = position.coords;
          setMapCenter([latitude, longitude]);
          setMapZoom(12);
          setFilters({ ...filters, lat: latitude, lng: longitude });
          setIsLocating(false);
        },
        (error) => {
          console.error("Error getting location", error);
          alert("Could not get your location.");
          setIsLocating(false);
        }
      );
    } else {
      alert("Geolocation is not supported by your browser.");
      setIsLocating(false);
    }
  };

  const clearLocationSearch = () => {
    setFilters({ ...filters, lat: "", lng: "" });
    setMapCenter([20.5937, 78.9629]);
    setMapZoom(5);
  };

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-[#0f172a]">
      {/* Header Section with Animated Blob Background */}
      <div className="relative bg-gradient-to-r from-brand-800 via-brand-600 to-accent-600 text-white py-16 px-4 overflow-hidden mb-8">
        <div className="absolute top-0 right-1/4 w-96 h-96 bg-accent-500 rounded-full mix-blend-multiply filter blur-3xl opacity-30 animate-blob"></div>
        <div className="absolute -bottom-10 left-10 w-72 h-72 bg-brand-400 rounded-full mix-blend-multiply filter blur-3xl opacity-30 animate-blob animation-delay-2000"></div>
        
        <div className="max-w-6xl mx-auto relative z-10 flex flex-col md:flex-row justify-between items-center gap-6 animate-fade-in-up">
          <div>
            <h1 className="text-4xl md:text-5xl font-display font-extrabold tracking-tight drop-shadow-sm">Explore Tourist Places</h1>
            <p className="text-brand-100 mt-2 font-light">Find hidden gems and popular destinations around the world.</p>
          </div>
          <button 
            onClick={() => setShowMap(!showMap)}
            className="glass text-white px-6 py-2.5 rounded-full font-bold hover:bg-white/20 transition-all duration-300 shadow-lg hover:shadow-xl hover:scale-105"
          >
            {showMap ? "Hide Map 🗺️" : "Show Map 🗺️"}
          </button>
        </div>
      </div>
      
      <div className="max-w-6xl mx-auto px-4 space-y-8 pb-20">
        
        {/* Filters Section */}
        <div className="glass rounded-2xl p-4 sm:p-6 shadow-lg animate-fade-in-up-delay-1 border border-white/20 dark:border-slate-700 flex flex-col md:flex-row gap-4 items-center relative z-20 -mt-16">
          <div className="relative flex-1 w-full">
            <span className="absolute left-4 top-1/2 -translate-y-1/2 text-gray-400">🔍</span>
            <input 
              placeholder="Search amazing places..." 
              value={filters.q} 
              onChange={updateFilter("q")} 
              className="w-full pl-10 pr-4 py-3 bg-white/50 dark:bg-slate-800/50 backdrop-blur-sm border border-gray-200 dark:border-slate-700 rounded-xl focus:ring-2 focus:ring-brand-400 outline-none transition-all dark:text-white"
            />
          </div>
          <select value={filters.category_id} onChange={updateFilter("category_id")} className="w-full md:w-auto py-3 px-4 bg-white/50 dark:bg-slate-800/50 backdrop-blur-sm border border-gray-200 dark:border-slate-700 rounded-xl focus:ring-2 focus:ring-brand-400 outline-none transition-all cursor-pointer font-medium dark:text-white">
            <option value="">All Categories</option>
            {categories.map(c => <option key={c.id} value={c.id}>{c.icon} {c.name}</option>)}
          </select>
          <select value={filters.min_rating} onChange={updateFilter("min_rating")} className="w-full md:w-auto py-3 px-4 bg-white/50 dark:bg-slate-800/50 backdrop-blur-sm border border-gray-200 dark:border-slate-700 rounded-xl focus:ring-2 focus:ring-brand-400 outline-none transition-all cursor-pointer font-medium dark:text-white">
            <option value="">Any Rating</option>
            <option value="4">4.0+ Stars ⭐</option>
            <option value="4.5">4.5+ Stars 🌟</option>
          </select>
          
          {filters.lat && filters.lng ? (
            <button 
              onClick={clearLocationSearch}
              className="w-full md:w-auto bg-red-50 dark:bg-red-900/30 text-red-600 dark:text-red-400 px-6 py-3 rounded-xl font-bold border border-red-200 dark:border-red-800 hover:bg-red-100 dark:hover:bg-red-900/50 transition-all whitespace-nowrap shadow-sm"
            >
              Clear Location
            </button>
          ) : (
            <button 
              onClick={handleSearchNearMe}
              disabled={isLocating}
              className="w-full md:w-auto bg-gradient-to-r from-brand-600 to-accent-600 hover:from-brand-500 hover:to-accent-500 text-white px-6 py-3 rounded-xl font-bold transition-all whitespace-nowrap shadow-md hover:shadow-lg disabled:opacity-70 transform hover:-translate-y-0.5"
            >
              {isLocating ? "Locating..." : "📍 Near Me"}
            </button>
          )}
        </div>

        {/* Map Section */}
        {showMap && (
          <div className="h-[450px] glass p-2 rounded-3xl shadow-xl border border-white/20 dark:border-slate-700 animate-fade-in-up-delay-1 overflow-hidden">
            <div className="w-full h-full rounded-2xl overflow-hidden">
              <MapComponent places={places} center={mapCenter} zoom={mapZoom} />
            </div>
          </div>
        )}

        {/* Places Grid */}
        <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-6 pt-4 animate-fade-in-up-delay-2">
          {places.map(p => (
            <Link to={`/places/${p.id}`} key={p.id} className="group flex flex-col glass rounded-2xl overflow-hidden hover:shadow-2xl hover:shadow-brand-500/20 hover:-translate-y-1 transition-all duration-300 border border-gray-100 dark:border-slate-700 h-full">
              {/* Image Header */}
              <div className="relative h-48 bg-gray-200 dark:bg-slate-700 overflow-hidden">
                <img 
                  src={p.images?.[0] || NEUTRAL_PLACEHOLDER_IMAGE} 
                  alt={p.name} 
                  referrerPolicy="no-referrer"
                  className="w-full h-full object-cover group-hover:scale-110 transition duration-700 ease-out"
                  onError={handleImageError}
                />
                <div className="absolute top-3 right-3 glass px-2 py-1 rounded-lg text-xs font-bold text-gray-900 shadow-sm flex items-center gap-1">
                  ⭐ {p.rating.toFixed(1)}
                </div>
              </div>
              
              {/* Card Body */}
              <div className="p-5 flex flex-col flex-1">
                <h3 className="text-xl font-display font-bold text-gray-800 dark:text-slate-100 group-hover:text-transparent group-hover:bg-clip-text group-hover:bg-gradient-to-r group-hover:from-brand-600 group-hover:to-accent-500 transition-all duration-300 mb-1 line-clamp-1">{p.name}</h3>
                <p className="text-xs text-brand-600 font-bold uppercase tracking-wider mb-3">
                  📍 {destinations.find(d => d.id === p.destination_id || d.name?.toLowerCase() === p.destination_id?.toLowerCase())?.name || p.destination_id || 'India'}
                </p>
                <p className="text-gray-600 dark:text-slate-300 text-sm line-clamp-2 mb-4 flex-1 font-light leading-relaxed">{p.description}</p>
                
                <div className="flex justify-between items-center text-sm pt-4 border-t border-gray-100 dark:border-slate-700 mt-auto">
                  <span className="text-brand-600 font-medium">View Details &rarr;</span>
                  <span className="text-gray-400 tracking-widest font-bold bg-gray-100 dark:bg-slate-800 px-2 py-1 rounded-md text-xs">{'💵'.repeat(p.price_level)}</span>
                </div>
              </div>
            </Link>
          ))}
          {loading && (
            <div className="col-span-full flex flex-col items-center justify-center py-20">
              <div className="w-10 h-10 border-4 border-brand-200 border-t-brand-600 rounded-full animate-spin mb-3"></div>
              <p className="text-gray-500 dark:text-slate-400 font-medium text-sm">Discovering amazing tourist destinations...</p>
            </div>
          )}
          {!loading && places.length === 0 && (
            <div className="col-span-full flex flex-col items-center justify-center py-20 glass rounded-3xl border border-dashed border-gray-300 dark:border-slate-600">
              <div className="text-5xl mb-4 animate-bounce">🗺️</div>
              <h3 className="text-2xl font-display font-bold text-gray-800 dark:text-slate-200 mb-2">No places found</h3>
              <p className="text-gray-500 dark:text-slate-400 text-center max-w-sm">Try adjusting your search filters or zooming out on the map to find more destinations.</p>
              <button onClick={() => setFilters({ q: "", category_id: "", min_rating: "", lat: "", lng: "", radius_km: 10 })} className="mt-6 text-brand-600 font-bold hover:underline">
                Clear all filters
              </button>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
