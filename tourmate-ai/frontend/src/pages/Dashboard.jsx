import { useState, useEffect } from "react";
import axios from "axios";
import { Link, useNavigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import { API_BASE_URL } from "../api/axios";
import OnboardingModal from "../components/OnboardingModal";
import LocationSearch from '../components/LocationSearch';
import RecommendationCard from "../components/RecommendationCard";
import { MapPin, Hotel, Navigation, Compass, ArrowRight, Utensils, Mountain } from 'lucide-react';

const DEFAULT_DESTINATIONS = [
  { id: "dest_1", name: "Taj Mahal, Agra", city: "Agra", state: "Uttar Pradesh", cover_image: "https://images.unsplash.com/photo-1564507592333-c60657eea523?auto=format&fit=crop&w=800&q=80", rating: 4.9, reviews_count: 1420 },
  { id: "dest_2", name: "Hawa Mahal, Jaipur", city: "Jaipur", state: "Rajasthan", cover_image: "https://images.unsplash.com/photo-1599661046289-e31897846e41?auto=format&fit=crop&w=800&q=80", rating: 4.8, reviews_count: 980 },
  { id: "dest_3", name: "Goa Beaches", city: "Goa", state: "Goa", cover_image: "https://images.unsplash.com/photo-1512343879784-a960bf40e7f2?auto=format&fit=crop&w=800&q=80", rating: 4.7, reviews_count: 2310 },
  { id: "dest_4", name: "Kerala Backwaters", city: "Alleppey", state: "Kerala", cover_image: "https://images.unsplash.com/photo-1602216056096-3b40cc0c9944?auto=format&fit=crop&w=800&q=80", rating: 4.9, reviews_count: 1150 },
  { id: "dest_5", name: "Gateway of India, Mumbai", city: "Mumbai", state: "Maharashtra", cover_image: "https://images.unsplash.com/photo-1570168007204-dfb528c6958f?auto=format&fit=crop&w=800&q=80", rating: 4.7, reviews_count: 1840 },
  { id: "dest_6", name: "Varanasi Ghats", city: "Varanasi", state: "Uttar Pradesh", cover_image: "https://images.unsplash.com/photo-1561361513-2d000a50f0dc?auto=format&fit=crop&w=800&q=80", rating: 4.8, reviews_count: 1530 }
];

const DEFAULT_RECOMMENDATIONS = [
  { id: "rec_1", name: "Amber Palace", city: "Jaipur", cover_image: "https://images.unsplash.com/photo-1599661046289-e31897846e41?auto=format&fit=crop&w=800&q=80", rating: 4.8, reviews_count: 820, price_level: 2 },
  { id: "rec_2", name: "Qutub Minar", city: "New Delhi", cover_image: "https://images.unsplash.com/photo-1587474260584-136574528ed5?auto=format&fit=crop&w=800&q=80", rating: 4.7, reviews_count: 1200, price_level: 1 },
  { id: "rec_3", name: "City Palace, Udaipur", city: "Udaipur", cover_image: "https://images.unsplash.com/photo-1615836245337-f5b9b2303f10?auto=format&fit=crop&w=800&q=80", rating: 4.9, reviews_count: 940, price_level: 2 },
  { id: "rec_4", name: "Baga Beach", city: "Goa", cover_image: "https://images.unsplash.com/photo-1507525428034-b723cf961d3e?auto=format&fit=crop&w=800&q=80", rating: 4.6, reviews_count: 1650, price_level: 1 }
];

const DEFAULT_HOTELS = [
  { id: "htl_1", name: "Taj Lake Palace", city: "Udaipur", cover_image: "https://images.unsplash.com/photo-1566073771259-6a8506099945?auto=format&fit=crop&w=800&q=80", rating: 4.9, reviews_count: 530, price_per_night_start: 32000, hotel_type: "Heritage Luxury" },
  { id: "htl_2", name: "The Leela Palace", city: "New Delhi", cover_image: "https://images.unsplash.com/photo-1582719508461-905c673771fd?auto=format&fit=crop&w=800&q=80", rating: 4.8, reviews_count: 780, price_per_night_start: 18500, hotel_type: "5-Star Luxury" },
  { id: "htl_3", name: "ITC Grand Chola", city: "Chennai", cover_image: "https://images.unsplash.com/photo-1542314831-068cd1dbfeeb?auto=format&fit=crop&w=800&q=80", rating: 4.8, reviews_count: 620, price_per_night_start: 14000, hotel_type: "Grand Luxury" },
  { id: "htl_4", name: "Goa Heritage Resort", city: "Calangute, Goa", cover_image: "https://images.unsplash.com/photo-1520250497591-112f2f40a3f4?auto=format&fit=crop&w=800&q=80", rating: 4.6, reviews_count: 410, price_per_night_start: 4500, hotel_type: "Beach Resort" }
];

const DEFAULT_FOODS = [
  { id: "food_1", name: "Karim's Historic Mughlai", city: "Old Delhi", cover_image: "https://images.unsplash.com/photo-1585937421612-70a008356fbe?auto=format&fit=crop&w=800&q=80", rating: 4.7, reviews_count: 3200, cuisine_type: ["Mughlai", "North Indian"] },
  { id: "food_2", name: "Britto's Beach Shack", city: "Baga, Goa", cover_image: "https://images.unsplash.com/photo-1555396273-367ea4eb4db5?auto=format&fit=crop&w=800&q=80", rating: 4.6, reviews_count: 2400, cuisine_type: ["Seafood", "Goan"] },
  { id: "food_3", name: "Laxmi Mishthan Bhandar (LMB)", city: "Jaipur", cover_image: "https://images.unsplash.com/photo-1601050690597-df0568f70950?auto=format&fit=crop&w=800&q=80", rating: 4.6, reviews_count: 1900, cuisine_type: ["Rajasthani", "Thali"] },
  { id: "food_4", name: "Bademiya Kebabs", city: "Colaba, Mumbai", cover_image: "https://images.unsplash.com/photo-1504674900247-0877df9cc836?auto=format&fit=crop&w=800&q=80", rating: 4.5, reviews_count: 2800, cuisine_type: ["Street Food", "Kebabs"] }
];

const DEFAULT_ACTIVITIES = [
  { id: "act_1", name: "Hot Air Ballooning over Jaipur", city: "Jaipur", cover_image: "https://images.unsplash.com/photo-1507525428034-b723cf961d3e?auto=format&fit=crop&w=800&q=80", rating: 4.9, reviews_count: 320, price: 8500, currency: "₹", activity_type: "Adventure" },
  { id: "act_2", name: "Houseboat Cruise in Alleppey", city: "Alleppey", cover_image: "https://images.unsplash.com/photo-1602216056096-3b40cc0c9944?auto=format&fit=crop&w=800&q=80", rating: 4.9, reviews_count: 670, price: 6000, currency: "₹", activity_type: "Experience" },
  { id: "act_3", name: "Scuba Diving & Watersports", city: "Grand Island, Goa", cover_image: "https://images.unsplash.com/photo-1544551763-46a013bb70d5?auto=format&fit=crop&w=800&q=80", rating: 4.7, reviews_count: 480, price: 2500, currency: "₹", activity_type: "Water Sports" },
  { id: "act_4", name: "Ganga Aarti Evening Boat Tour", city: "Varanasi", cover_image: "https://images.unsplash.com/photo-1561361513-2d000a50f0dc?auto=format&fit=crop&w=800&q=80", rating: 4.9, reviews_count: 890, price: 500, currency: "₹", activity_type: "Spiritual & Cultural" }
];

export default function Dashboard() {
  const { user, token } = useAuth();
  const navigate = useNavigate();
  
  const [loading, setLoading] = useState(true);
  const [showOnboarding, setShowOnboarding] = useState(false);
  
  const [destinations, setDestinations] = useState([]);
  const [recommendations, setRecommendations] = useState([]);
  const [hotels, setHotels] = useState([]);
  const [foods, setFoods] = useState([]);
  const [activities, setActivities] = useState([]);

  const fetchData = async () => {
    setLoading(true);
    try {
      // Check user preferences: first from localStorage, then API if token exists
      const localPref = localStorage.getItem("tourmate_user_preferences");
      let hasPreferences = false;
      if (localPref) {
        try {
          const parsed = JSON.parse(localPref);
          if (parsed && (parsed.interests?.length > 0 || parsed.travel_style)) {
            hasPreferences = true;
          }
        } catch {}
      }

      if (token && !hasPreferences) {
        const prefRes = await axios.get(`${API_BASE_URL}/users/preferences`, {
          headers: { Authorization: `Bearer ${token}` }
        }).catch(() => null);
        
        if (!prefRes?.data?.data || (prefRes.data.data.interests?.length === 0 && !prefRes.data.data.travel_style)) {
          setShowOnboarding(true);
        } else {
          try {
            localStorage.setItem("tourmate_user_preferences", JSON.stringify(prefRes.data.data));
          } catch {}
        }
      }

      // Parallel data fetching for homepage sections with robust fallbacks
      const headers = token ? { Authorization: `Bearer ${token}` } : {};
      const [destRes, recRes, hotelRes, foodRes, actRes] = await Promise.allSettled([
        axios.get(`${API_BASE_URL}/destinations`, { headers }),
        axios.get(`${API_BASE_URL}/places/recommendations`, { headers }),
        axios.get(`${API_BASE_URL}/hotels`, { headers }),
        axios.get(`${API_BASE_URL}/places?q=restaurant`, { headers }),
        axios.get(`${API_BASE_URL}/places?q=adventure`, { headers }),
      ]);

      const loadedDests = (destRes.status === 'fulfilled' && destRes.value.data?.data?.length > 0) 
        ? destRes.value.data.data.slice(0, 8) 
        : DEFAULT_DESTINATIONS;
      setDestinations(loadedDests);

      const loadedRecs = (recRes.status === 'fulfilled' && recRes.value.data?.data?.length > 0) 
        ? recRes.value.data.data.slice(0, 4) 
        : DEFAULT_RECOMMENDATIONS;
      setRecommendations(loadedRecs);

      const loadedHotels = (hotelRes.status === 'fulfilled' && hotelRes.value.data?.data?.length > 0) 
        ? hotelRes.value.data.data.slice(0, 4) 
        : DEFAULT_HOTELS;
      setHotels(loadedHotels);

      const loadedFoods = (foodRes.status === 'fulfilled' && foodRes.value.data?.data?.length > 0) 
        ? foodRes.value.data.data.slice(0, 4) 
        : DEFAULT_FOODS;
      setFoods(loadedFoods);

      const loadedActs = (actRes.status === 'fulfilled' && actRes.value.data?.data?.length > 0) 
        ? actRes.value.data.data.slice(0, 4) 
        : DEFAULT_ACTIVITIES;
      setActivities(loadedActs);

    } catch (err) {
      console.error("Failed to load dashboard data:", err);
      setDestinations(DEFAULT_DESTINATIONS);
      setRecommendations(DEFAULT_RECOMMENDATIONS);
      setHotels(DEFAULT_HOTELS);
      setFoods(DEFAULT_FOODS);
      setActivities(DEFAULT_ACTIVITIES);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, [token]);

  const quickSearches = ["Goa", "Agra", "Jaipur", "Mumbai", "New Delhi", "Manali", "Udaipur", "Varanasi"];

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-slate-900 pb-20">
      <OnboardingModal 
        isOpen={showOnboarding} 
        onClose={() => setShowOnboarding(false)} 
        onComplete={fetchData}
      />

      {/* Hero Section */}
      <div className="relative w-full h-[85vh] min-h-[600px] max-h-[800px] flex items-center justify-center overflow-hidden mx-auto md:max-w-[98%] md:rounded-3xl md:mt-2">
        <div className="absolute inset-0 z-0">
          <img 
            src="https://images.unsplash.com/photo-1524492412937-b28074a5d7da?auto=format&fit=crop&w=2071&q=80" 
            alt="Beautiful landscape" 
            className="w-full h-full object-cover"
          />
          <div className="absolute inset-0 bg-gradient-to-b from-black/60 via-black/40 to-black/70"></div>
        </div>

        <div className="relative z-10 w-full max-w-4xl mx-auto px-6 text-center animate-fade-in-up">
          <h1 className="text-5xl md:text-7xl font-display font-extrabold tracking-tight text-white mb-6 drop-shadow-xl">
            Explore India.<br/>
            <span className="text-brand-300">One Journey at a Time.</span>
          </h1>
          <p className="text-lg md:text-xl text-gray-200 mb-10 max-w-2xl mx-auto font-medium drop-shadow-md">
            Discover beautiful places, find the perfect stay, taste local food, and build your perfect trip with AI.
          </p>

          <div className="max-w-3xl mx-auto">
            <LocationSearch />
          </div>

          <div className="mt-8 flex flex-wrap justify-center items-center gap-2 md:gap-3">
            <span className="text-gray-300 text-sm font-medium mr-2 drop-shadow-sm">Popular Destinations:</span>
            {quickSearches.map(term => (
              <Link 
                key={term} 
                to={`/places?destination=${encodeURIComponent(term)}`}
                className="px-4 py-1.5 rounded-full bg-white/10 hover:bg-white/25 text-white border border-white/20 backdrop-blur-md transition-all text-sm font-bold shadow-sm"
              >
                {term}
              </Link>
            ))}
          </div>
        </div>
      </div>

      <div className="max-w-7xl mx-auto px-6 py-20 space-y-24">
        
        {/* Explore India Section */}
        {destinations.length > 0 && (
          <section>
            <div className="flex justify-between items-end mb-8">
              <div>
                <h2 className="text-3xl md:text-4xl font-display font-bold text-gray-900 dark:text-white flex items-center gap-3">
                  🇮🇳 Explore India
                </h2>
                <p className="text-gray-500 dark:text-slate-400 mt-2 font-medium">Discover unforgettable destinations across the country.</p>
              </div>
              <Link to="/destinations" className="hidden sm:flex text-brand-600 font-bold hover:text-brand-700 items-center gap-1 transition-colors">
                View All <ArrowRight className="w-4 h-4" />
              </Link>
            </div>
            <div className="flex overflow-x-auto pb-6 gap-6 custom-scrollbar snap-x">
              {destinations.map(dest => (
                <RecommendationCard key={dest.id} item={dest} type="destination" />
              ))}
            </div>
          </section>
        )}

        {/* Recommended For You Section */}
        {recommendations.length > 0 && (
          <section>
            <div className="flex justify-between items-end mb-8">
              <div>
                <h2 className="text-3xl md:text-4xl font-display font-bold text-gray-900 dark:text-white flex items-center gap-3">
                  ✨ Recommended For You
                </h2>
                <p className="text-gray-500 dark:text-slate-400 mt-2 font-medium">Curated destinations based on your travel style.</p>
              </div>
              <Link to="/places" className="hidden sm:flex text-brand-600 font-bold hover:text-brand-700 items-center gap-1 transition-colors">
                Explore More <ArrowRight className="w-4 h-4" />
              </Link>
            </div>
            <div className="flex overflow-x-auto pb-6 gap-6 custom-scrollbar snap-x">
              {recommendations.map(place => (
                <RecommendationCard key={place.id} item={place} type="place" />
              ))}
            </div>
          </section>
        )}

        {/* Find Your Perfect Stay */}
        {hotels.length > 0 && (
          <section>
            <div className="flex justify-between items-end mb-8">
              <div>
                <h2 className="text-3xl md:text-4xl font-display font-bold text-gray-900 dark:text-white flex items-center gap-3">
                  🏨 Find Your Perfect Stay
                </h2>
                <p className="text-gray-500 dark:text-slate-400 mt-2 font-medium">Comfortable stays, from budget-friendly hotels to luxury escapes.</p>
              </div>
              <Link to="/hotels" className="hidden sm:flex text-brand-600 font-bold hover:text-brand-700 items-center gap-1 transition-colors">
                View All Stays <ArrowRight className="w-4 h-4" />
              </Link>
            </div>
            <div className="flex overflow-x-auto pb-6 gap-6 custom-scrollbar snap-x">
              {hotels.map(hotel => (
                <RecommendationCard key={hotel.id} item={hotel} type="hotel" />
              ))}
            </div>
          </section>
        )}

        {/* Taste India */}
        {foods.length > 0 && (
          <section>
            <div className="flex justify-between items-end mb-8">
              <div>
                <h2 className="text-3xl md:text-4xl font-display font-bold text-gray-900 dark:text-white flex items-center gap-3">
                  🍛 Taste India
                </h2>
                <p className="text-gray-500 dark:text-slate-400 mt-2 font-medium">Discover the flavors that make every destination special.</p>
              </div>
              <Link to="/places?q=restaurant" className="hidden sm:flex text-brand-600 font-bold hover:text-brand-700 items-center gap-1 transition-colors">
                Find Restaurants <ArrowRight className="w-4 h-4" />
              </Link>
            </div>
            <div className="flex overflow-x-auto pb-6 gap-6 custom-scrollbar snap-x">
              {foods.map(food => (
                <RecommendationCard key={food.id} item={food} type="restaurant" />
              ))}
            </div>
          </section>
        )}

        {/* Things To Do */}
        {activities.length > 0 && (
          <section>
            <div className="flex justify-between items-end mb-8">
              <div>
                <h2 className="text-3xl md:text-4xl font-display font-bold text-gray-900 dark:text-white flex items-center gap-3">
                  🎯 Things To Do
                </h2>
                <p className="text-gray-500 dark:text-slate-400 mt-2 font-medium">Unforgettable activities and experiences.</p>
              </div>
              <Link to="/places?q=adventure" className="hidden sm:flex text-brand-600 font-bold hover:text-brand-700 items-center gap-1 transition-colors">
                Explore Activities <ArrowRight className="w-4 h-4" />
              </Link>
            </div>
            <div className="flex overflow-x-auto pb-6 gap-6 custom-scrollbar snap-x">
              {activities.map(activity => (
                <RecommendationCard key={activity.id} item={activity} type="activity" />
              ))}
            </div>
          </section>
        )}

        {/* Map Discovery Section */}
        <section className="bg-gradient-to-br from-indigo-900 via-slate-900 to-brand-900 rounded-3xl p-8 md:p-12 text-white shadow-2xl relative overflow-hidden border border-indigo-500/30">
          <div className="absolute top-0 right-0 p-8 opacity-20">
            <Compass className="w-64 h-64 text-brand-400" />
          </div>
          <div className="relative z-10 max-w-2xl">
            <h2 className="text-3xl md:text-4xl font-display font-bold mb-4">🗺️ Discover Places Around You</h2>
            <p className="text-lg text-indigo-200 mb-8 font-medium leading-relaxed">
              Find tourist places, top-rated restaurants, and comfortable stays near your current location using our interactive AI Cluster Map.
            </p>
            <div className="flex flex-wrap gap-4">
              <button 
                onClick={() => {
                  if (navigator.geolocation) {
                    navigator.geolocation.getCurrentPosition((position) => {
                      navigate(`/places?lat=${position.coords.latitude}&lng=${position.coords.longitude}&radius_km=25`);
                    });
                  }
                }}
                className="bg-white text-indigo-900 hover:bg-gray-100 font-bold px-8 py-4 rounded-xl transition shadow-lg flex items-center gap-2 transform hover:-translate-y-1"
              >
                <MapPin className="w-5 h-5" /> Find Near Me
              </button>
              <Link 
                to="/map/clusters"
                className="bg-brand-600/30 hover:bg-brand-600/50 backdrop-blur-md text-white border border-brand-400/50 font-bold px-8 py-4 rounded-xl transition flex items-center gap-2 transform hover:-translate-y-1"
              >
                <Navigation className="w-5 h-5" /> Open Interactive Map
              </Link>
            </div>
          </div>
        </section>

        {/* AI Planner CTA */}
        <section className="bg-gradient-to-r from-brand-600 to-accent-600 rounded-3xl p-8 md:p-12 text-white shadow-2xl text-center relative overflow-hidden">
          <div className="relative z-10 max-w-3xl mx-auto">
            <h2 className="text-3xl md:text-5xl font-display font-extrabold mb-6 tracking-tight">✨ Let AI Plan Your Trip</h2>
            <p className="text-lg md:text-xl text-brand-100 mb-10 font-medium">
              Tell us your destination, budget, and interests. TourMate will instantly generate a highly personalized day-by-day itinerary just for you.
            </p>
            <Link 
              to="/itinerary-builder"
              className="inline-flex items-center gap-2 bg-white text-brand-700 hover:bg-gray-50 font-extrabold px-10 py-5 rounded-2xl transition shadow-xl hover:shadow-2xl transform hover:-translate-y-1 text-lg"
            >
              Plan My Trip Now <ArrowRight className="w-6 h-6" />
            </Link>
          </div>
        </section>

      </div>
    </div>
  );
}
