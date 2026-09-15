import React, { useState, useEffect } from 'react';
import { useLocation, Link, useNavigate } from 'react-router-dom';
import axios from 'axios';
import { MapContainer, TileLayer, Marker, Popup } from 'react-leaflet';
import 'leaflet/dist/leaflet.css';
import L from 'leaflet';
import { Compass, MapPin, Navigation, Calendar, Settings, SlidersHorizontal, Loader } from 'lucide-react';
import RecommendationCard from '../components/RecommendationCard';
import { useAuth } from '../context/AuthContext';

// Fix Leaflet default marker icon issue
delete L.Icon.Default.prototype._getIconUrl;
L.Icon.Default.mergeOptions({
  iconRetinaUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-icon-2x.png',
  iconUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-icon.png',
  shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-shadow.png',
});

// Custom Icons for map
const createIcon = (color) => new L.Icon({
  iconUrl: `https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-2x-${color}.png`,
  shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-shadow.png',
  iconSize: [25, 41],
  iconAnchor: [12, 41],
  popupAnchor: [1, -34],
  shadowSize: [41, 41]
});

const icons = {
  place: createIcon('green'),
  hotel: createIcon('blue'),
  restaurant: createIcon('orange'),
  activity: createIcon('violet'),
  center: createIcon('red')
};

export default function ExploreDestination() {
  const { search } = useLocation();
  const navigate = useNavigate();
  const { token } = useAuth();
  
  const queryParams = new URLSearchParams(search);
  const locationName = queryParams.get('name') || 'Unknown Location';
  const latParam = queryParams.get('lat');
  const lngParam = queryParams.get('lng');
  
  const [center, setCenter] = useState([latParam ? parseFloat(latParam) : 28.2096, lngParam ? parseFloat(lngParam) : 83.9856]);
  const [radius, setRadius] = useState(15); // Default 15km
  
  const [loading, setLoading] = useState(true);
  const [places, setPlaces] = useState([]);
  const [hotels, setHotels] = useState([]);
  const [restaurants, setRestaurants] = useState([]);
  const [activities, setActivities] = useState([]);

  useEffect(() => {
    if (!latParam || !lngParam) {
      // For now, if no lat/lng is provided, we can't do distance search easily.
      // Ideally, geocode the locationName here if missing.
      setLoading(false);
      return;
    }
    
    setCenter([parseFloat(latParam), parseFloat(lngParam)]);
    fetchRecommendations(parseFloat(latParam), parseFloat(lngParam), radius);
  }, [latParam, lngParam, radius, token]);

  const fetchRecommendations = async (latitude, longitude, rad) => {
    setLoading(true);
    const headers = token ? { Authorization: `Bearer ${token}` } : {};
    const qs = `?lat=${latitude}&lng=${longitude}&radius_km=${rad}`;
    
    try {
      const [placesRes, hotelsRes, restsRes, actsRes] = await Promise.all([
        axios.get(`${import.meta.env.VITE_API_BASE_URL}/places${qs}`, { headers }),
        axios.get(`${import.meta.env.VITE_API_BASE_URL}/hotels${qs}`, { headers }),
        axios.get(`${import.meta.env.VITE_API_BASE_URL}/restaurants${qs}`, { headers }),
        axios.get(`${import.meta.env.VITE_API_BASE_URL}/activities${qs}`, { headers })
      ]);
      
      setPlaces(placesRes.data.data || []);
      setHotels(hotelsRes.data.data || []);
      setRestaurants(restsRes.data.data || []);
      setActivities(actsRes.data.data || []);
    } catch (err) {
      console.error("Failed to fetch recommendations", err);
    } finally {
      setLoading(false);
    }
  };

  const renderSection = (title, items, type, icon) => {
    if (!items || items.length === 0) return null;
    return (
      <div className="mb-12">
        <div className="flex items-center justify-between mb-6">
          <h2 className="text-2xl font-display font-bold text-gray-900 flex items-center gap-2">
            {icon} {title}
          </h2>
          <span className="text-sm font-bold text-brand-600 bg-brand-50 px-3 py-1 rounded-full border border-brand-100">
            {items.length} {items.length === 1 ? 'place' : 'places'} found
          </span>
        </div>
        <div className="flex overflow-x-auto pb-6 gap-6 snap-x snap-mandatory custom-scrollbar">
          {items.map(item => (
            <RecommendationCard key={item.id} item={item} type={type} />
          ))}
        </div>
      </div>
    );
  };

  return (
    <div className="min-h-screen bg-gray-50 pb-20">
      {/* Header */}
      <div className="bg-white border-b border-gray-200 pt-24 pb-10 shadow-sm sticky top-0 z-40">
        <div className="max-w-7xl mx-auto px-6 flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
          <div>
            <div className="flex items-center gap-2 text-gray-500 text-sm font-bold mb-2 uppercase tracking-widest">
              <Compass className="w-4 h-4 text-brand-500" /> Destination Overview
            </div>
            <h1 className="text-4xl md:text-5xl font-display font-extrabold text-gray-900 flex items-center gap-3">
              <MapPin className="text-brand-500" /> {locationName}
            </h1>
          </div>
          
          <div className="flex items-center gap-4 bg-gray-50 p-2 rounded-xl border border-gray-200">
            <span className="text-sm font-bold text-gray-600 pl-3">Search Radius:</span>
            <select 
              value={radius} 
              onChange={(e) => setRadius(Number(e.target.value))}
              className="bg-white border border-gray-200 rounded-lg px-4 py-2 font-bold text-gray-800 outline-none focus:ring-2 focus:ring-brand-500 shadow-sm"
            >
              <option value={5}>5 km</option>
              <option value={15}>15 km</option>
              <option value={30}>30 km</option>
              <option value={50}>50 km</option>
            </select>
          </div>
        </div>
      </div>

      <div className="max-w-7xl mx-auto px-6 mt-8 grid grid-cols-1 lg:grid-cols-3 gap-8">
        
        {/* Main Content Column */}
        <div className="lg:col-span-2">
          {loading ? (
            <div className="flex flex-col items-center justify-center py-20">
              <Loader className="w-10 h-10 text-brand-500 animate-spin mb-4" />
              <p className="text-gray-500 font-bold">Scanning area for the best spots...</p>
            </div>
          ) : (
            <>
              {(!latParam || !lngParam) ? (
                <div className="bg-amber-50 border border-amber-200 p-6 rounded-2xl text-amber-800">
                  <h3 className="font-bold text-lg mb-2">Location Coordinates Missing</h3>
                  <p>Please use the search bar on the dashboard to select a valid location.</p>
                </div>
              ) : (
                <>
                  {renderSection("Tourist Places Near You", places, "place", <MapPin className="text-emerald-500" />)}
                  {renderSection("Where Should I Stay?", hotels, "hotel", <span className="text-blue-500">🏨</span>)}
                  {renderSection("Where Should I Eat?", restaurants, "restaurant", <span className="text-orange-500">🍽️</span>)}
                  {renderSection("Things To Do Nearby", activities, "activity", <span className="text-purple-500">🎯</span>)}
                  
                  {(places.length === 0 && hotels.length === 0 && restaurants.length === 0 && activities.length === 0) && (
                    <div className="bg-white border border-gray-200 p-12 rounded-2xl text-center shadow-sm">
                      <div className="text-4xl mb-4">🏜️</div>
                      <h3 className="text-2xl font-display font-bold text-gray-800 mb-2">No recommendations found</h3>
                      <p className="text-gray-500">Try increasing your search radius or exploring a different area.</p>
                    </div>
                  )}
                </>
              )}
            </>
          )}
        </div>

        {/* Sidebar / Map / Plan Your Visit */}
        <div className="space-y-6">
          
          {/* Interactive Map */}
          <div className="bg-white rounded-2xl p-4 shadow-sm border border-gray-200 sticky top-[220px]">
            <h3 className="font-display font-bold text-lg text-gray-900 mb-4 flex items-center gap-2">
              <Navigation className="w-5 h-5 text-brand-500" /> Interactive Map
            </h3>
            
            <div className="h-[400px] rounded-xl overflow-hidden border border-gray-100 z-10 relative">
              {(latParam && lngParam) ? (
                <MapContainer center={center} zoom={12} scrollWheelZoom={true} style={{ height: '100%', width: '100%' }}>
                  <TileLayer
                    attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
                    url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
                  />
                  
                  {/* Center Marker */}
                  <Marker position={center} icon={icons.center}>
                    <Popup>
                      <strong>{locationName}</strong> <br/> Searched Location
                    </Popup>
                  </Marker>
                  
                  {/* Places Markers */}
                  {places.map(p => p.location && p.location.coordinates && (
                    <Marker key={`p_${p.id}`} position={[p.location.coordinates[1], p.location.coordinates[0]]} icon={icons.place}>
                      <Popup>
                        <strong className="text-emerald-700">{p.name}</strong><br/>
                        {p.rating && `⭐ ${p.rating.toFixed(1)}`}<br/>
                        <Link to={`/map/route`} className="inline-block mt-2 text-xs font-bold bg-emerald-100 text-emerald-800 px-2 py-1 rounded">Get Directions</Link>
                      </Popup>
                    </Marker>
                  ))}
                  
                  {/* Hotel Markers */}
                  {hotels.map(h => h.location && h.location.coordinates && (
                    <Marker key={`h_${h.id}`} position={[h.location.coordinates[1], h.location.coordinates[0]]} icon={icons.hotel}>
                      <Popup>
                        <strong className="text-blue-700">{h.name}</strong><br/>
                        {h.price_per_night_start && `₹${h.price_per_night_start}/night`}<br/>
                        <Link to={`/map/route`} className="inline-block mt-2 text-xs font-bold bg-blue-100 text-blue-800 px-2 py-1 rounded">Get Directions</Link>
                      </Popup>
                    </Marker>
                  ))}
                  
                  {/* Restaurant Markers */}
                  {restaurants.map(r => r.location && r.location.coordinates && (
                    <Marker key={`r_${r.id}`} position={[r.location.coordinates[1], r.location.coordinates[0]]} icon={icons.restaurant}>
                      <Popup>
                        <strong className="text-orange-700">{r.name}</strong><br/>
                        <Link to={`/map/route`} className="inline-block mt-2 text-xs font-bold bg-orange-100 text-orange-800 px-2 py-1 rounded">Get Directions</Link>
                      </Popup>
                    </Marker>
                  ))}
                  
                  {/* Activity Markers */}
                  {activities.map(a => a.location && a.location.coordinates && (
                    <Marker key={`a_${a.id}`} position={[a.location.coordinates[1], a.location.coordinates[0]]} icon={icons.activity}>
                      <Popup>
                        <strong className="text-purple-700">{a.name}</strong><br/>
                        <Link to={`/map/route`} className="inline-block mt-2 text-xs font-bold bg-purple-100 text-purple-800 px-2 py-1 rounded">Get Directions</Link>
                      </Popup>
                    </Marker>
                  ))}
                  
                </MapContainer>
              ) : (
                <div className="w-full h-full bg-gray-100 flex items-center justify-center text-gray-400">Map Unavailable</div>
              )}
            </div>
            
            {/* Map Legend */}
            <div className="flex flex-wrap gap-3 mt-4 text-xs font-bold text-gray-600">
              <span className="flex items-center gap-1"><span className="w-3 h-3 rounded-full bg-emerald-500"></span> Places</span>
              <span className="flex items-center gap-1"><span className="w-3 h-3 rounded-full bg-blue-500"></span> Hotels</span>
              <span className="flex items-center gap-1"><span className="w-3 h-3 rounded-full bg-orange-500"></span> Food</span>
              <span className="flex items-center gap-1"><span className="w-3 h-3 rounded-full bg-purple-500"></span> Activities</span>
            </div>
          </div>
          
          {/* Plan Your Visit */}
          {!loading && (latParam && lngParam) && (
            <div className="bg-gradient-to-br from-brand-900 to-slate-900 rounded-2xl p-6 shadow-xl text-white">
              <h3 className="font-display font-bold text-xl mb-6 flex items-center gap-2">
                ✨ Plan Your Visit
              </h3>
              
              <div className="space-y-3 mb-8">
                <div className="flex justify-between items-center border-b border-white/10 pb-2">
                  <span className="text-brand-100">Tourist Places</span>
                  <span className="font-bold text-lg">{places.length}</span>
                </div>
                <div className="flex justify-between items-center border-b border-white/10 pb-2">
                  <span className="text-brand-100">Hotels</span>
                  <span className="font-bold text-lg">{hotels.length}</span>
                </div>
                <div className="flex justify-between items-center border-b border-white/10 pb-2">
                  <span className="text-brand-100">Restaurants</span>
                  <span className="font-bold text-lg">{restaurants.length}</span>
                </div>
                <div className="flex justify-between items-center border-b border-white/10 pb-2">
                  <span className="text-brand-100">Activities</span>
                  <span className="font-bold text-lg">{activities.length}</span>
                </div>
              </div>
              
              <Link 
                to="/itinerary-builder" 
                className="w-full flex items-center justify-center gap-2 bg-brand-500 hover:bg-brand-400 text-white font-bold py-3.5 rounded-xl transition-colors shadow-lg"
              >
                <Calendar className="w-5 h-5" /> Create My Trip
              </Link>
            </div>
          )}

        </div>
      </div>
    </div>
  );
}
