import { useState, useEffect } from "react";
import axios from "axios";
import { Link } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import OnboardingModal from "../components/OnboardingModal";

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
    { name: "Nature", icon: "🌲", color: "bg-green-100 text-green-700" },
    { name: "History", icon: "🏛️", color: "bg-amber-100 text-amber-700" },
    { name: "Culture", icon: "🎭", color: "bg-purple-100 text-purple-700" },
    { name: "Adventure", icon: "🧗", color: "bg-red-100 text-red-700" },
    { name: "Food", icon: "🍜", color: "bg-orange-100 text-orange-700" },
  ];

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-slate-900/50 pb-20">
      <OnboardingModal 
        isOpen={showOnboarding} 
        onClose={() => setShowOnboarding(false)} 
        onComplete={handleOnboardingComplete}
      />

      {/* Hero Section */}
      <div className="relative bg-gradient-to-r from-brand-800 via-brand-600 to-accent-600 text-white py-20 px-6 overflow-hidden">
        {/* Animated background blobs */}
        <div className="absolute top-0 left-0 w-72 h-72 bg-accent-500 rounded-full mix-blend-multiply filter blur-3xl opacity-30 animate-blob"></div>
        <div className="absolute top-0 right-0 w-72 h-72 bg-brand-400 rounded-full mix-blend-multiply filter blur-3xl opacity-30 animate-blob animation-delay-2000"></div>
        <div className="absolute -bottom-8 left-20 w-72 h-72 bg-purple-500 rounded-full mix-blend-multiply filter blur-3xl opacity-30 animate-blob animation-delay-4000"></div>

        <div className="max-w-7xl mx-auto relative z-10 animate-fade-in-up">
          <h1 className="text-4xl md:text-6xl font-display font-extrabold tracking-tight mb-4 drop-shadow-md">
            Hello, {user?.name?.split(' ')[0] || 'Traveler'}! 🌍
          </h1>
          <p className="text-lg md:text-xl text-brand-50 max-w-2xl font-light">
            {preferences 
              ? `Ready for your next trip? We've found the perfect spots based on your love for ${preferences.interests.slice(0, 2).join(" and ")}.`
              : "Discover the world's most incredible destinations tailored perfectly to you."}
          </p>
          
          <div className="mt-8 flex flex-wrap gap-4">
            <Link to="/places" className="bg-white text-brand-700 font-bold px-8 py-3.5 rounded-full shadow-xl hover:shadow-2xl hover:scale-105 transition-all duration-300 inline-block">
              Explore Destinations
            </Link>
            <Link to="/itinerary-builder" className="glass text-white font-semibold px-8 py-3.5 rounded-full hover:bg-white/20 transition-all duration-300 inline-block">
              Plan an Itinerary
            </Link>
          </div>
        </div>
      </div>

      <div className="max-w-7xl mx-auto px-6 -mt-10 relative z-20">
        {/* Quick Categories */}
        <div className="glass rounded-2xl p-6 mb-12 flex flex-wrap gap-4 justify-between items-center shadow-lg animate-fade-in-up-delay-1">
          <span className="font-bold text-gray-800 dark:text-slate-200 text-sm uppercase tracking-widest font-display">Browse by Vibe</span>
          <div className="flex gap-4 overflow-x-auto pb-2 sm:pb-0 custom-scrollbar w-full sm:w-auto flex-1">
            {categories.map(c => (
              <button key={c.name} className={`flex items-center gap-2 ${c.color} px-5 py-2.5 rounded-xl font-bold hover:scale-105 hover:shadow-md transition-all duration-300 whitespace-nowrap`}>
                <span>{c.icon}</span>
                {c.name}
              </button>
            ))}
          </div>
        </div>

        {/* My Favorites */}
        {favorites.length > 0 && (
          <div className="mb-12 animate-fade-in-up-delay-2">
            <h2 className="text-3xl font-display font-extrabold text-gray-900 dark:text-white flex items-center mb-6">
              ❤️ My Favorites
            </h2>
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
              {favorites.map(place => (
                <Link to={`/places/${place.id}`} key={place.id} className="group glass rounded-2xl overflow-hidden hover:shadow-2xl hover:-translate-y-1 transition-all duration-300 flex flex-col h-full border border-gray-100 dark:border-slate-700">
                  <div className="relative h-48 overflow-hidden bg-gray-200 dark:bg-slate-700">
                    <img 
                      src={place.images?.[0] || "https://images.unsplash.com/photo-1469854523086-cc02fe5d8800?ixlib=rb-4.0.3&auto=format&fit=crop&w=800&q=80"} 
                      alt={place.name} 
                      className="w-full h-full object-cover group-hover:scale-110 transition duration-700 ease-out"
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
        <div className="animate-fade-in-up-delay-2">
          <div className="flex justify-between items-end mb-6">
            <div>
              <h2 className="text-3xl font-display font-extrabold text-gray-900 dark:text-white flex items-center">
                ✨ Recommended for You
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
                <div key={i} className="animate-pulse glass rounded-2xl h-80"></div>
              ))}
            </div>
          ) : recommendations.length > 0 ? (
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
              {recommendations.map(place => (
                <Link to={`/places/${place.id}`} key={place.id} className="group glass rounded-2xl overflow-hidden hover:shadow-2xl hover:-translate-y-1 transition-all duration-300 flex flex-col h-full border border-gray-100 dark:border-slate-700">
                  <div className="relative h-56 overflow-hidden bg-gray-200 dark:bg-slate-700">
                    <img 
                      src={place.images?.[0] || "https://images.unsplash.com/photo-1469854523086-cc02fe5d8800?ixlib=rb-4.0.3&auto=format&fit=crop&w=800&q=80"} 
                      alt={place.name} 
                      className="w-full h-full object-cover group-hover:scale-110 transition duration-700 ease-out"
                    />
                    <div className="absolute top-3 left-3 glass px-3 py-1 rounded-lg text-sm font-bold text-gray-900 flex items-center gap-1">
                      ⭐ {place.rating?.toFixed(1)}
                    </div>
                  </div>
                  
                  <div className="p-5 flex flex-col flex-1">
                    <h3 className="font-bold font-display text-xl text-gray-900 dark:text-white group-hover:text-transparent group-hover:bg-clip-text group-hover:bg-gradient-to-r group-hover:from-brand-600 group-hover:to-accent-500 transition-all duration-300 line-clamp-1 mb-2">{place.name}</h3>
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
            <div className="flex flex-col items-center justify-center py-20 glass rounded-2xl">
              <div className="text-6xl mb-6 animate-bounce">🏜️</div>
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
