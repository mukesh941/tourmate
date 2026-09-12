import React, { useState, useEffect } from "react";
import axios from "axios";
import { Link } from "react-router-dom";
import { 
  Hotel, 
  MapPin, 
  Star, 
  Search, 
  SlidersHorizontal, 
  Wifi, 
  Coffee, 
  Waves, 
  Sparkles, 
  ArrowRight,
  ShieldCheck,
  Building,
  Check
} from "lucide-react";

export default function Hotels() {
  const [hotels, setHotels] = useState([]);
  const [loading, setLoading] = useState(true);

  // Filter states
  const [selectedCity, setSelectedCity] = useState("All");
  const [searchQuery, setSearchQuery] = useState("");
  const [priceFilter, setPriceFilter] = useState("all"); // all, budget (<$130), mid ($130-$200), luxury (>$200)
  const [minRating, setMinRating] = useState(0);
  const [selectedAmenity, setSelectedAmenity] = useState("");

  const cities = [
    "All",
    "Delhi",
    "Mumbai",
    "Goa",
    "Jaipur",
    "Udaipur",
    "Manali",
    "Kerala",
    "Agra",
    "Varanasi",
    "Kashmir",
    "Rishikesh",
    "Shimla",
    "Hyderabad",
    "Bengaluru",
    "Ladakh",
    "Jaisalmer",
    "Ooty",
    "Kolkata",
    "Darjeeling",
    "Amritsar"
  ];

  const amenitiesList = [
    { label: "Pool", query: "Pool", icon: Waves },
    { label: "Free Wi-Fi", query: "Wi-Fi", icon: Wifi },
    { label: "Breakfast", query: "Breakfast", icon: Coffee },
    { label: "Spa", query: "Spa", icon: Sparkles }
  ];

  useEffect(() => {
    fetchHotels();
  }, [selectedCity, searchQuery, priceFilter, minRating, selectedAmenity]);

  const fetchHotels = async () => {
    setLoading(true);
    try {
      const params = new URLSearchParams();
      if (selectedCity !== "All") params.append("city", selectedCity);
      if (searchQuery) params.append("q", searchQuery);
      if (minRating > 0) params.append("min_rating", minRating);
      if (selectedAmenity) params.append("amenity", selectedAmenity);

      if (priceFilter === "budget") {
        params.append("max_price", "130");
      } else if (priceFilter === "mid") {
        params.append("min_price", "130");
        params.append("max_price", "200");
      } else if (priceFilter === "luxury") {
        params.append("min_price", "200");
      }

      const res = await axios.get(`${import.meta.env.VITE_API_BASE_URL}/hotels?${params.toString()}`);
      setHotels(res.data.data || []);
    } catch (err) {
      console.error("Failed to fetch hotels:", err);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-slate-900 py-8 px-4 sm:px-6 lg:px-8">
      {/* Hero Header */}
      <div className="max-w-7xl mx-auto mb-10 text-center">
        <div className="inline-flex items-center gap-2 px-3.5 py-1 rounded-full text-xs font-semibold bg-brand-50 dark:bg-brand-950/60 text-brand-600 dark:text-brand-400 border border-brand-200 dark:border-brand-800 mb-3">
          <Hotel className="w-3.5 h-3.5" />
          <span>Curated Tourist Accommodations</span>
        </div>
        <h1 className="text-3xl sm:text-5xl font-extrabold text-gray-900 dark:text-slate-100 tracking-tight">
          Find Your Perfect Stay
        </h1>
        <p className="mt-3 text-lg text-gray-600 dark:text-slate-400 max-w-2xl mx-auto">
          Explore verified luxury resorts, heritage havelis, alpine mountain chalets, and beachfront villas with transparent pricing.
        </p>
      </div>

      {/* Filter and Search Bar Card */}
      <div className="max-w-7xl mx-auto bg-white dark:bg-slate-800 rounded-2xl shadow-sm border border-gray-200 dark:border-slate-700 p-6 mb-10">
        {/* City Filter Chips */}
        <div className="flex items-center gap-2 overflow-x-auto pb-4 mb-5 border-b border-gray-100 dark:border-slate-700/60">
          <span className="text-xs font-bold text-gray-400 uppercase tracking-wider mr-2 shrink-0">
            Destination:
          </span>
          {cities.map((city) => (
            <button
              key={city}
              onClick={() => setSelectedCity(city)}
              className={`px-4 py-1.5 rounded-full text-xs font-semibold transition shrink-0 ${
                selectedCity === city
                  ? "bg-brand-600 text-white shadow-sm"
                  : "bg-gray-100 dark:bg-slate-700 text-gray-700 dark:text-slate-200 hover:bg-gray-200 dark:hover:bg-slate-600"
              }`}
            >
              {city}
            </button>
          ))}
        </div>

        {/* Search Input & Secondary Filters */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          {/* Keyword Search */}
          <div className="relative">
            <Search className="w-4 h-4 text-gray-400 absolute left-3.5 top-3" />
            <input
              type="text"
              placeholder="Search hotel name, location..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full pl-10 pr-4 py-2.5 bg-gray-50 dark:bg-slate-900 border border-gray-200 dark:border-slate-700 rounded-xl text-sm outline-none focus:ring-2 focus:ring-brand-500 text-gray-900 dark:text-slate-100 placeholder-gray-400"
            />
          </div>

          {/* Price Range Filter */}
          <div>
            <select
              value={priceFilter}
              onChange={(e) => setPriceFilter(e.target.value)}
              className="w-full px-3.5 py-2.5 bg-gray-50 dark:bg-slate-900 border border-gray-200 dark:border-slate-700 rounded-xl text-sm outline-none focus:ring-2 focus:ring-brand-500 text-gray-900 dark:text-slate-100"
            >
              <option value="all">Any Price</option>
              <option value="budget">Under $130 / night</option>
              <option value="mid">$130 - $200 / night</option>
              <option value="luxury">$200+ / night (Luxury)</option>
            </select>
          </div>

          {/* Rating Filter */}
          <div>
            <select
              value={minRating}
              onChange={(e) => setMinRating(parseFloat(e.target.value))}
              className="w-full px-3.5 py-2.5 bg-gray-50 dark:bg-slate-900 border border-gray-200 dark:border-slate-700 rounded-xl text-sm outline-none focus:ring-2 focus:ring-brand-500 text-gray-900 dark:text-slate-100"
            >
              <option value="0">Any Guest Rating</option>
              <option value="4.5">★ 4.5 & above (Exceptional)</option>
              <option value="4.8">★ 4.8 & above (World Class)</option>
            </select>
          </div>

          {/* Amenity Filter */}
          <div>
            <select
              value={selectedAmenity}
              onChange={(e) => setSelectedAmenity(e.target.value)}
              className="w-full px-3.5 py-2.5 bg-gray-50 dark:bg-slate-900 border border-gray-200 dark:border-slate-700 rounded-xl text-sm outline-none focus:ring-2 focus:ring-brand-500 text-gray-900 dark:text-slate-100"
            >
              <option value="">Any Amenities</option>
              <option value="Pool">Swimming Pool</option>
              <option value="Breakfast">Breakfast Included</option>
              <option value="Spa">Spa & Wellness</option>
              <option value="Beach">Beach Access</option>
            </select>
          </div>
        </div>
      </div>

      {/* Hotel Cards Grid */}
      <div className="max-w-7xl mx-auto">
        {loading ? (
          <div className="flex justify-center items-center py-20">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-brand-600"></div>
          </div>
        ) : hotels.length === 0 ? (
          <div className="bg-white dark:bg-slate-800 rounded-2xl p-12 text-center border border-gray-200 dark:border-slate-700">
            <Building className="w-12 h-12 text-gray-400 mx-auto mb-3" />
            <h3 className="text-lg font-bold text-gray-800 dark:text-slate-200">No accommodations found</h3>
            <p className="text-sm text-gray-500 dark:text-slate-400 mt-1">
              Try adjusting your destination, price filters, or keyword search.
            </p>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
            {hotels.map((hotel) => (
              <div
                key={hotel.id}
                className="group bg-white dark:bg-slate-800 rounded-2xl overflow-hidden border border-gray-200 dark:border-slate-700 shadow-sm hover:shadow-xl hover:-translate-y-1 transition-all duration-300 flex flex-col justify-between"
              >
                <div>
                  {/* Photo Container */}
                  <div className="relative h-60 w-full overflow-hidden bg-gray-100 dark:bg-slate-700">
                    <img
                      src={hotel.cover_image}
                      alt={hotel.name}
                      className="w-full h-full object-cover group-hover:scale-105 transition duration-700 ease-out"
                      onError={(e) => {
                        e.target.src = "https://images.unsplash.com/photo-1566073771259-6a8506099945?auto=format&fit=crop&w=800&q=80";
                      }}
                    />
                    <span className="absolute top-3 left-3 px-3 py-1 bg-black/60 backdrop-blur-md rounded-full text-xs font-semibold text-white">
                      {hotel.hotel_type}
                    </span>
                    <div className="absolute top-3 right-3 px-2.5 py-1 bg-white/95 dark:bg-slate-900/90 backdrop-blur-md rounded-lg text-xs font-bold text-amber-600 dark:text-amber-400 flex items-center gap-1 shadow-sm">
                      <Star className="w-3.5 h-3.5 fill-amber-500 text-amber-500" />
                      <span>{hotel.rating.toFixed(1)}</span>
                      <span className="text-gray-400 font-normal">({hotel.review_count})</span>
                    </div>
                  </div>

                  {/* Body Content */}
                  <div className="p-6">
                    <div className="flex items-center gap-1 text-xs font-medium text-brand-600 dark:text-brand-400 mb-1.5">
                      <MapPin className="w-3.5 h-3.5" />
                      <span>{hotel.city}, India</span>
                    </div>
                    <h3 className="font-bold text-xl text-gray-900 dark:text-slate-100 group-hover:text-brand-600 dark:group-hover:text-brand-400 transition-colors line-clamp-1 mb-2">
                      {hotel.name}
                    </h3>
                    <p className="text-xs text-gray-500 dark:text-slate-400 line-clamp-2 leading-relaxed mb-4">
                      {hotel.description}
                    </p>

                    {/* Key Amenities */}
                    <div className="flex flex-wrap gap-1.5 mb-2">
                      {hotel.amenities.slice(0, 3).map((amenity, aIdx) => (
                        <span
                          key={aIdx}
                          className="px-2.5 py-1 bg-gray-50 dark:bg-slate-700/60 text-[11px] font-medium text-gray-600 dark:text-slate-300 rounded-lg border border-gray-100 dark:border-slate-600/50"
                        >
                          {amenity}
                        </span>
                      ))}
                      {hotel.amenities.length > 3 && (
                        <span className="px-2 py-1 bg-gray-50 dark:bg-slate-700/60 text-[11px] font-medium text-gray-400 rounded-lg">
                          +{hotel.amenities.length - 3} more
                        </span>
                      )}
                    </div>
                  </div>
                </div>

                {/* Footer Bar */}
                <div className="p-6 pt-0 border-t border-gray-100 dark:border-slate-700/60 mt-4 flex items-center justify-between">
                  <div>
                    <span className="text-xs text-gray-400">Starting from</span>
                    <div className="text-lg font-extrabold text-gray-900 dark:text-white">
                      {hotel.currency}{hotel.price_per_night_start}
                      <span className="text-xs font-normal text-gray-500 dark:text-slate-400"> / night</span>
                    </div>
                  </div>

                  <Link
                    to={`/hotels/${hotel.id}`}
                    className="px-4 py-2.5 bg-brand-600 hover:bg-brand-700 text-white rounded-xl text-xs font-bold shadow-sm flex items-center gap-1.5 transition transform active:scale-95"
                  >
                    <span>View Rooms</span>
                    <ArrowRight className="w-3.5 h-3.5" />
                  </Link>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
