import { useState, useEffect } from "react";
import axios from "axios";
import { Link } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import OnboardingModal from "../components/OnboardingModal";
import VoiceSearch from "../components/VoiceSearch";
import ImageUpload from "../components/ImageUpload";
import { Trees, Landmark, Palette, Mountain, Utensils, Star, Heart, MapPin, Hotel, ArrowRight } from 'lucide-react';
import { motion } from 'framer-motion';
export default function Dashboard() {
  const { user, token } = useAuth();
  const [preferences, setPreferences] = useState(null);
  const [recommendations, setRecommendations] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showOnboarding, setShowOnboarding] = useState(false);

  const [favorites, setFavorites] = useState([]);

  const fetchData = async () => {
    setLoading(true);
    try {
      const prefRes = await axios.get(`${import.meta.env.VITE_API_BASE_URL}/users/preferences`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      
      if (!prefRes.data.data || prefRes.data.data.interests.length === 0) {
        setShowOnboarding(true);
      } else {
        setPreferences(prefRes.data.data);
      }

      const recRes = await axios.get(`${import.meta.env.VITE_API_BASE_URL}/places/recommendations`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setRecommendations(recRes.data.data || []);
      
      const favRes = await axios.get(`${import.meta.env.VITE_API_BASE_URL}/interactions/favorites`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setFavorites(favRes.data.data || []);
      
    } catch (err) {
      console.error("Failed to load dashboard data:", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (token) {
      fetchData();
    }
  }, [token]);

  const handleOnboardingComplete = () => {
    setShowOnboarding(false);
    fetchData(); 
  };

  const categories = [
    { name: "Nature", icon: <Trees className="w-5 h-5" />, color: "border border-gray-200 hover:border-green-500 text-gray-700 hover:text-green-600 bg-white" },
    { name: "History", icon: <Landmark className="w-5 h-5" />, color: "border border-gray-200 hover:border-amber-500 text-gray-700 hover:text-amber-600 bg-white" },
    { name: "Culture", icon: <Palette className="w-5 h-5" />, color: "border border-gray-200 hover:border-purple-500 text-gray-700 hover:text-purple-600 bg-white" },
    { name: "Adventure", icon: <Mountain className="w-5 h-5" />, color: "border border-gray-200 hover:border-red-500 text-gray-700 hover:text-red-600 bg-white" },
    { name: "Food", icon: <Utensils className="w-5 h-5" />, color: "border border-gray-200 hover:border-orange-500 text-gray-700 hover:text-orange-600 bg-white" },
  ];

  const handleCategoryClick = async (categoryName) => {
    setLoading(true);
    const match = categoryName.match(/\(([^)]+)\)/);
    const searchWord = match ? match[1] : categoryName.split(' ')[0];
    const categoryType = categoryName.split(' ')[0];
    
    try {
      // Try searching by the state first (e.g. Kerala)
      let res = await axios.get(`${import.meta.env.VITE_API_BASE_URL}/places?q=${searchWord}`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      
      // If no results, fallback to the category name (e.g. Nature)
      if (!res.data.data || res.data.data.length === 0) {
        res = await axios.get(`${import.meta.env.VITE_API_BASE_URL}/places?q=${categoryType}`, {
          headers: { Authorization: `Bearer ${token}` }
        });
      }
      
      setRecommendations(res.data.data || []);
      
      // Scroll to recommendations section
      const recSection = document.getElementById('recommendations-section');
      if (recSection) {
        recSection.scrollIntoView({ behavior: 'smooth' });
      }
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-slate-900/50 pb-20">
      <OnboardingModal 
        isOpen={showOnboarding} 
        onClose={() => setShowOnboarding(false)} 
        onComplete={handleOnboardingComplete}
      />

      {/* Hero Section */}
      <div className="relative bg-gray-900 text-white py-24 px-6 min-h-[450px] flex items-center justify-center overflow-hidden">
        {/* Background Image */}
        <div className="absolute inset-0 z-0">
          <img 
            src="https://images.unsplash.com/photo-1524492412937-b28074a5d7da?ixlib=rb-4.0.3&auto=format&fit=crop&w=2071&q=80" 
            alt="Beautiful landscape" 
            className="w-full h-full object-cover"
          />
          <div className="absolute inset-0 bg-black/40"></div>
        </div>

        <motion.div 
          initial={{ opacity: 0, y: 30 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.8 }}
          className="max-w-7xl mx-auto relative z-10 w-full text-center md:text-left"
        >
          <h1 className="text-4xl md:text-6xl font-display font-extrabold tracking-tight mb-4">
            Hello, {user?.name?.split(' ')[0] || 'Traveler'}.
          </h1>
          <p className="text-lg md:text-xl text-gray-100 max-w-2xl font-normal drop-shadow-md mx-auto md:mx-0">
            {preferences 
              ? `Ready for your next trip? We've found the perfect spots based on your love for ${preferences.interests.slice(0, 2).join(" and ")}.`
              : "Discover the world's most incredible destinations tailored perfectly to you."}
          </p>
          
          <div className="mt-8 flex flex-col sm:flex-row flex-wrap justify-center md:justify-start items-center gap-4">
            <Link to="/places" className="bg-white text-gray-900 font-bold px-8 py-3.5 rounded-xl shadow-[0_8px_30px_rgb(0,0,0,0.12)] hover:shadow-[0_8px_30px_rgb(255,255,255,0.2)] hover:bg-gray-50 transition-all duration-300 transform hover:-translate-y-1">
              Explore Destinations
            </Link>
            <Link to="/itinerary-builder" className="glass hover:glass-hover text-white font-bold px-8 py-3.5 rounded-xl transition-all duration-300">
              Plan an Itinerary
            </Link>
            <Link to="/hotels" className="glass hover:glass-hover text-white font-bold px-8 py-3.5 rounded-xl transition-all duration-300 flex items-center gap-2">
              <Hotel className="w-5 h-5 text-brand-400" /> Book Stays
            </Link>
            
            <div className="flex items-center gap-3 mt-2 sm:mt-0">
              <button 
                onClick={() => {
                  if (navigator.geolocation) {
                    navigator.geolocation.getCurrentPosition((position) => {
                      window.location.href = `/places?lat=${position.coords.latitude}&lng=${position.coords.longitude}&radius_km=50`;
                    }, (error) => {
                      alert("Unable to get your location. Please ensure location services are enabled.");
                    });
                  } else {
                    alert("Geolocation is not supported by your browser.");
                  }
                }}
                className="flex items-center justify-center p-3.5 bg-white/10 hover:bg-white/20 text-white border border-white/20 backdrop-blur-sm rounded-xl transition-all duration-300"
                title="Places Near Me"
              >
                <MapPin className="w-5 h-5" />
              </button>
              
              <VoiceSearch />
              <ImageUpload />
            </div>
          </div>
        </motion.div>
      </div>

      <div className="max-w-7xl mx-auto px-6 -mt-10 relative z-20">
        {/* Quick Categories */}
        <div className="bg-white border border-gray-200 rounded-2xl p-6 mb-12 flex flex-wrap gap-4 justify-between items-center shadow-sm animate-fade-in-up-delay-1">
          <span className="font-bold text-gray-800 dark:text-slate-200 text-sm uppercase tracking-widest font-display">Browse by Vibe</span>
          <div className="flex gap-4 overflow-x-auto pb-2 sm:pb-0 custom-scrollbar w-full sm:w-auto flex-1">
            {categories.map(c => (
              <Link 
                key={c.name} 
                to={`/category/${c.name.toLowerCase()}`}
                className={`flex items-center gap-2 ${c.color} px-5 py-2.5 rounded-xl font-bold hover:scale-105 hover:shadow-md transition-all duration-300 whitespace-nowrap`}
              >
                <span>{c.icon}</span>
                {c.name}
              </Link>
            ))}
          </div>
        </div>

        {/* Featured Hotels & Stays Banner */}
        <div className="bg-gradient-to-r from-blue-900 via-indigo-900 to-slate-900 text-white rounded-2xl p-6 sm:p-8 mb-12 shadow-lg flex flex-col md:flex-row items-center justify-between gap-6 border border-blue-800/60">
          <div className="flex items-center gap-4">
            <div className="p-3.5 bg-white/10 backdrop-blur-md rounded-2xl border border-white/20 text-white shrink-0">
              <Hotel className="w-8 h-8 text-brand-300" />
            </div>
            <div>
              <span className="px-2.5 py-0.5 rounded-full text-xs font-semibold bg-brand-500/30 text-brand-300 border border-brand-400/30 mb-1 inline-block">
                Accommodations for Tourists
              </span>
              <h3 className="text-xl sm:text-2xl font-bold font-display">Need a Place to Stay on Your Travels?</h3>
              <p className="text-sm text-blue-200 mt-1 max-w-xl">
                Browse verified heritage palaces, beachfront resorts, alpine chalets, and boutique stays across Udaipur, Jaipur, Goa, Manali, and more.
              </p>
            </div>
          </div>
          <Link
            to="/hotels"
            className="px-6 py-3 bg-white text-gray-900 hover:bg-gray-100 font-bold rounded-xl shadow-md transition flex items-center gap-2 whitespace-nowrap shrink-0 transform active:scale-95"
          >
            <span>Explore Hotels & Stays</span>
            <ArrowRight className="w-4 h-4" />
          </Link>
        </div>

        {/* My Favorites */}
        {favorites.length > 0 && (
          <div className="mb-12 animate-fade-in-up-delay-2">
            <h2 className="text-2xl font-display font-bold text-gray-900 dark:text-white flex items-center gap-2 mb-6">
              <Heart className="w-6 h-6 text-red-500 fill-red-500" /> My Favorites
            </h2>
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
              {favorites.map(place => (
                <Link to={`/places/${place.id}`} key={place.id} className="group bg-white rounded-2xl overflow-hidden shadow-sm hover:shadow-xl hover:-translate-y-1 transition-all duration-300 flex flex-col h-full border border-gray-200 dark:border-slate-700">
                  <div className="relative h-48 overflow-hidden bg-gray-200 dark:bg-slate-700">
                    <img 
                      src={place.images?.[0] || "https://images.unsplash.com/photo-1524492412937-b28074a5d7da?auto=format&fit=crop&w=800&q=80"} 
                      alt={place.name} 
                      className="w-full h-full object-cover group-hover:scale-110 transition duration-700 ease-out"
                      onError={(e) => {
                        e.target.src = "https://images.unsplash.com/photo-1524492412937-b28074a5d7da?auto=format&fit=crop&w=800&q=80";
                      }}
                    />
                  </div>
                  <div className="p-5 flex flex-col flex-1">
                    <h3 className="font-bold text-lg text-gray-900 dark:text-white group-hover:text-red-500 transition-colors line-clamp-1">{place.name}</h3>
                    <div className="flex justify-between items-center mt-auto pt-4">
                      <span className="text-sm text-brand-600 font-bold bg-brand-50 px-2 py-1 rounded-md">★ {place.rating?.toFixed(1) || "0.0"}</span>
                      <span className="text-sm text-gray-400 font-bold">{'💵'.repeat(place.price_level || 1)}</span>
                    </div>
                  </div>
                </Link>
              ))}
            </div>
          </div>
        )}

        {/* Recommended Places */}
        <div id="recommendations-section" className="animate-fade-in-up-delay-2">
          <div className="flex justify-between items-end mb-6">
            <div>
              <h2 className="text-2xl font-display font-bold text-gray-900 dark:text-white flex items-center gap-2">
                <Star className="w-6 h-6 text-brand-500 fill-brand-500" /> Recommended for You
              </h2>
              <p className="text-gray-500 dark:text-slate-400 text-sm mt-1 font-medium">Curated specifically for your travel style</p>
            </div>
            <button className="text-brand-600 font-bold hover:text-brand-700 hover:underline text-sm uppercase tracking-wider">
              View all &rarr;
            </button>
          </div>
          
          {loading ? (
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
              {[1,2,3,4].map(i => (
                <div key={i} className="animate-pulse bg-white border border-gray-200 rounded-2xl h-80 shadow-sm"></div>
              ))}
            </div>
          ) : recommendations.length > 0 ? (
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
              {recommendations.map(place => (
                <Link to={`/places/${place.id}`} key={place.id} className="group bg-white rounded-2xl overflow-hidden shadow-sm hover:shadow-xl hover:-translate-y-1 transition-all duration-300 flex flex-col h-full border border-gray-200 dark:border-slate-700">
                  <div className="relative h-56 overflow-hidden bg-gray-200 dark:bg-slate-700">
                    <img 
                      src={place.images?.[0] || "https://images.unsplash.com/photo-1524492412937-b28074a5d7da?auto=format&fit=crop&w=800&q=80"} 
                      alt={place.name} 
                      className="w-full h-full object-cover group-hover:scale-110 transition duration-700 ease-out"
                      onError={(e) => {
                        e.target.src = "https://images.unsplash.com/photo-1524492412937-b28074a5d7da?auto=format&fit=crop&w=800&q=80";
                      }}
                    />
                    <div className="absolute top-3 left-3 bg-white/90 backdrop-blur-md px-3 py-1 rounded-lg text-sm font-bold text-gray-900 flex items-center gap-1 shadow-sm">
                      <Star className="w-3.5 h-3.5 text-amber-500 fill-amber-500" /> {place.rating?.toFixed(1)}
                    </div>
                  </div>
                  
                  <div className="p-5 flex flex-col flex-1">
                    <h3 className="font-bold font-display text-xl text-gray-900 dark:text-white group-hover:text-brand-600 transition-colors duration-300 line-clamp-1 mb-2">{place.name}</h3>
                    <p className="text-sm text-gray-500 dark:text-slate-400 line-clamp-2 mb-4 flex-1">{place.description}</p>
                    
                    <div className="flex flex-wrap gap-2 mt-auto">
                      {place.feature_scores && Object.entries(place.feature_scores)
                        .filter(([_, score]) => score > 0.6)
                        .slice(0, 2)
                        .map(([feature]) => (
                          <span key={feature} className="bg-gradient-to-r from-brand-50 to-brand-100 text-brand-700 px-2.5 py-1 rounded-md text-[10px] uppercase font-bold tracking-widest border border-brand-200 shadow-sm">
                            {feature}
                          </span>
                        ))
                      }
                    </div>
                  </div>
                </Link>
              ))}
            </div>
          ) : (
            <div className="flex flex-col items-center justify-center py-20 bg-white border border-gray-200 rounded-2xl shadow-sm">
              <div className="mb-6"><MapPin className="w-16 h-16 text-gray-300" /></div>
              <h3 className="text-2xl font-display font-bold text-gray-800 dark:text-slate-100 mb-2">No recommendations found</h3>
              <p className="text-gray-500 dark:text-slate-400 mb-8 text-center max-w-sm text-lg">We couldn't find any places matching your exact preferences right now.</p>
              <button 
                onClick={() => setShowOnboarding(true)}
                className="bg-brand-600 hover:bg-brand-700 text-white font-bold px-6 py-3 rounded-full shadow-lg hover:shadow-xl hover:-translate-y-0.5 transition-all duration-300"
              >
                Update your preferences
              </button>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
