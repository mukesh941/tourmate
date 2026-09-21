import React, { useState, useEffect, useCallback, Fragment } from "react";
import axios from "axios";
import { useAuth } from "../context/AuthContext";
import { useNavigate, Link, useLocation } from "react-router-dom";
import { Hotel, MapPin, Star, Wifi, Coffee, Waves, ArrowRight, Plane, Train, Car, Bike, Navigation, Map as MapIcon, Clock, BedDouble, Users, IndianRupee, Activity, CheckCircle2, ChevronDown, ChevronUp, Trash2, Save, RefreshCw, Share2, Sparkles } from "lucide-react";

import ItineraryHeader from "../components/itinerary/ItineraryHeader";
import DayNavigation from "../components/itinerary/DayNavigation";
import DailySummary from "../components/itinerary/DailySummary";
import ActivityCard from "../components/itinerary/ActivityCard";
import TravelConnector from "../components/itinerary/TravelConnector";
import BudgetBreakdown from "../components/itinerary/BudgetBreakdown";
import OptimizeDayModal from "../components/itinerary/OptimizeDayModal";
import SafeImage from "../components/SafeImage";

function HotelSuggestionCard({ hotel }) {
  const amenityIcons = {
    "WiFi": <Wifi className="w-3 h-3" />,
    "Free WiFi": <Wifi className="w-3 h-3" />,
    "Pool": <Waves className="w-3 h-3" />,
    "Restaurant": <Coffee className="w-3 h-3" />,
    "Breakfast": <Coffee className="w-3 h-3" />,
  };
  return (
    <div className="flex gap-3 bg-white dark:bg-slate-800 border border-gray-100 dark:border-slate-700 rounded-xl p-3 hover:shadow-md transition-all group">
      <div className="w-16 h-16 rounded-lg bg-gray-100 dark:bg-slate-700 flex items-center justify-center shrink-0 overflow-hidden">
        <SafeImage 
          src={hotel.images?.[0]} 
          alt={hotel.name} 
          className="w-full h-full object-cover rounded-lg" 
        />
      </div>
      <div className="flex-1 min-w-0 flex flex-col justify-center">
        <div className="flex items-start justify-between gap-2">
          <p className="font-bold text-sm text-gray-900 dark:text-white truncate">{hotel.name}</p>
          <Link
            to={`/hotels/${hotel.id}`}
            className="text-[10px] font-bold text-brand-600 dark:text-brand-400 bg-brand-50 dark:bg-brand-900/30 px-2 py-0.5 rounded-full shrink-0 hover:bg-brand-100 transition flex items-center gap-0.5"
          >
            View <ArrowRight className="w-2.5 h-2.5" />
          </Link>
        </div>
        <div className="flex items-center gap-1 text-xs text-gray-500 dark:text-slate-400 mt-0.5">
          <MapPin className="w-3 h-3" />
          <span className="truncate">{hotel.city || hotel.address || "Nearby"}</span>
        </div>
        <div className="flex items-center gap-2 mt-1.5 flex-wrap">
          <div className="flex items-center gap-0.5 text-amber-500">
            <Star className="w-3 h-3 fill-amber-500" />
            <span className="text-xs font-bold">{hotel.rating ? hotel.rating.toFixed(1) : "4.0"}</span>
          </div>
          <span className="text-xs font-bold text-emerald-600 dark:text-emerald-400">
            &#8377;{(hotel.price_per_night || 3000).toLocaleString("en-IN")}/night
          </span>
        </div>
      </div>
    </div>
  );
}

function NearbyHotelsSuggestion({ places, destinationName }) {
  const [hotels, setHotels] = useState([]);
  const [loading, setLoading] = useState(false);

  const fetchNearbyHotels = useCallback(async () => {
    setLoading(true);
    try {
      const params = {};
      if (places && places.length > 0 && places[0].location && places[0].location.coordinates) {
        const [lng, lat] = places[0].location.coordinates;
        params.lat = lat;
        params.lng = lng;
        params.radius_km = 50;
      } else if (destinationName) {
        params.city = destinationName.split(",")[0].trim();
      }
      const res = await axios.get(`${import.meta.env.VITE_API_BASE_URL}/hotels`, { params });
      setHotels((res.data.data || []).slice(0, 3));
    } catch (err) {
      console.error("Hotel suggestions error:", err);
    } finally {
      setLoading(false);
    }
  }, [places, destinationName]);

  useEffect(() => {
    fetchNearbyHotels();
  }, [fetchNearbyHotels]);

  if (loading || !hotels.length) return null;

  return (
    <div className="bg-white dark:bg-slate-900 border border-gray-200 dark:border-slate-700 rounded-2xl p-6 shadow-sm mb-8">
      <div className="flex items-center gap-2 mb-4">
        <BedDouble className="w-5 h-5 text-brand-600 dark:text-brand-400" />
        <h4 className="text-base font-bold text-gray-900 dark:text-white">
          Suggested Stays Nearby
        </h4>
      </div>
      <div className="grid md:grid-cols-3 gap-4">
        {hotels.map(h => <HotelSuggestionCard key={h.id} hotel={h} />)}
      </div>
    </div>
  );
}

export default function ItineraryBuilder() {
  const { token } = useAuth();
  const navigate = useNavigate();
  const [allPlaces, setAllPlaces] = useState([]);
  const [selectedPlaces, setSelectedPlaces] = useState([]);
  
  const location = useLocation();
  const initialDestination = location.state?.destination || new URLSearchParams(location.search).get("destination") || "";
  // Form State
  const [originName, setOriginName] = useState("");
  const [destinationName, setDestinationName] = useState(initialDestination);
  const [days, setDays] = useState(3);
  const [startTime, setStartTime] = useState("09:00");
  const [endTime, setEndTime] = useState("20:00");
  const [accommodation, setAccommodation] = useState("");
  
  const [transportationMode, setTransportationMode] = useState("flight");
  const [localTransportation, setLocalTransportation] = useState("taxi");
  
  const [travelType, setTravelType] = useState("Couple");
  const [energyLevel, setEnergyLevel] = useState("Moderate");
  const [budget, setBudget] = useState("Medium");
  
  const [interests, setInterests] = useState([]);
  const availableInterests = [
    { id: "History", icon: "🏛️", label: "History" },
    { id: "Nature", icon: "🌿", label: "Nature" },
    { id: "Food", icon: "🍜", label: "Food" },
    { id: "Shopping", icon: "🛍️", label: "Shopping" },
    { id: "Adventure", icon: "🏄", label: "Adventure" },
    { id: "Culture", icon: "🎭", label: "Culture" },
    { id: "Photography", icon: "📸", label: "Photography" },
    { id: "Entertainment", icon: "🎡", label: "Entertainment" }
  ];

  const toggleInterest = (interestId) => {
    if (interests.includes(interestId)) {
      setInterests(interests.filter(i => i !== interestId));
    } else {
      setInterests([...interests, interestId]);
    }
  };

  // Generation State
  const [generating, setGenerating] = useState(false);
  const [loadingStep, setLoadingStep] = useState(0);
  const [generatedItinerary, setGeneratedItinerary] = useState(null);
  const [errorMsg, setErrorMsg] = useState("");
  
  // Results State
  const [selectedOptionIndex, setSelectedOptionIndex] = useState(0);
  const [activeDay, setActiveDay] = useState(1);
  const [title, setTitle] = useState("My Awesome Trip");
  const [saving, setSaving] = useState(false);
  
  // Optimize Modal State
  const [isOptimizeModalOpen, setIsOptimizeModalOpen] = useState(false);

  useEffect(() => {
    let interval;
    if (generating) {
      setLoadingStep(0);
      interval = setInterval(() => {
        setLoadingStep(prev => (prev < 5 ? prev + 1 : prev));
      }, 1500);
    }
    return () => clearInterval(interval);
  }, [generating]);

  useEffect(() => {
    const fetchPlaces = async () => {
      try {
        const res = await axios.get(`${import.meta.env.VITE_API_BASE_URL}/places`, {
          headers: { Authorization: `Bearer ${token}` }
        });
        setAllPlaces(res.data.data || []);
      } catch (err) {
        console.error(err);
      }
    };
    if (token) fetchPlaces();
  }, [token]);

  const handleGenerate = async () => {
    if (!destinationName) return;
    setGenerating(true);
    setErrorMsg("");
    setGeneratedItinerary(null);
    try {
      const headers = token ? { Authorization: `Bearer ${token}` } : {};
      const res = await axios.post(
        `${import.meta.env.VITE_API_BASE_URL}/itineraries/generate`,
        {
          origin: originName || undefined,
          destination_name: destinationName,
          place_ids: selectedPlaces.map(p => p.id),
          days: parseInt(days) || 1,
          start_time: startTime || "09:00",
          end_time: endTime || "20:00",
          accommodation: accommodation || undefined,
          energy_level: energyLevel || "Moderate",
          budget: budget || "Medium",
          travel_type: travelType || "Couple",
          transportation_mode: transportationMode || "flight",
          local_transportation: localTransportation || "taxi",
          interests: interests || []
        },
        { headers }
      );
      if (res.data?.data && Array.isArray(res.data.data) && res.data.data.length > 0) {
        setGeneratedItinerary(res.data.data);
        setSelectedOptionIndex(0);
        setActiveDay(1);
        setTitle(`${destinationName} Trip`);
      } else {
        throw new Error("Invalid itinerary structure received from server.");
      }
    } catch (err) {
      console.error("Itinerary generation error:", err);
      const detail = err.response?.data?.detail;
      const errorText = typeof detail === "string" 
        ? detail 
        : (Array.isArray(detail) ? detail.map(d => d.msg).join(", ") : (err.message || "Failed to generate itinerary."));
      setErrorMsg(`We couldn't create your itinerary: ${errorText}. Please adjust your settings and try again.`);
    } finally {
      setGenerating(false);
    }
  };

  const handleSave = async () => {
    if (!generatedItinerary) return;
    if (!token) {
      alert("Please log in or create an account to save your itinerary.");
      navigate("/login");
      return;
    }
    setSaving(true);
    try {
      await axios.post(
        `${import.meta.env.VITE_API_BASE_URL}/itineraries`,
        {
          title: title,
          days: parseInt(days) || 1,
          schedule: generatedItinerary[selectedOptionIndex].schedule
        },
        { headers: { Authorization: `Bearer ${token}` } }
      );
      navigate("/my-itineraries");
    } catch (err) {
      console.error(err);
      alert("Failed to save itinerary.");
    } finally {
      setSaving(false);
    }
  };

  const handleDeleteActivity = (dayIndex, actIndex) => {
    const updated = [...generatedItinerary];
    updated[selectedOptionIndex].schedule[dayIndex].activities.splice(actIndex, 1);
    setGeneratedItinerary(updated);
  };

  const handleMoveActivity = (dayIndex, actIndex, direction) => {
    const updated = [...generatedItinerary];
    const activities = updated[selectedOptionIndex].schedule[dayIndex].activities;
    if (direction === "up" && actIndex > 0) {
      [activities[actIndex - 1], activities[actIndex]] = [activities[actIndex], activities[actIndex - 1]];
    } else if (direction === "down" && actIndex < activities.length - 1) {
      [activities[actIndex + 1], activities[actIndex]] = [activities[actIndex], activities[actIndex + 1]];
    }
    setGeneratedItinerary(updated);
  };

  const handleApplyOptimizedDay = (optimizedDaySchedule) => {
    const updated = [...generatedItinerary];
    const dayIndex = updated[selectedOptionIndex].schedule.findIndex(d => d.day === activeDay);
    if (dayIndex !== -1) {
      updated[selectedOptionIndex].schedule[dayIndex] = optimizedDaySchedule;
      setGeneratedItinerary(updated);
    }
  };

  const loadingMessages = [
    "Understanding your preferences...",
    "Finding suitable places...",
    "Planning transportation...",
    "Optimizing your route...",
    "Building your daily schedule...",
    "Preparing your itinerary..."
  ];

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-[#0b1120] text-gray-900 dark:text-slate-200 pb-24 font-sans">
      
      {/* Dynamic Render based on state */}
      {!generatedItinerary && !generating && !errorMsg && (
        <>
          {/* Hero Section */}
          <section className="relative pt-12 pb-16 px-4 overflow-hidden">
            <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[800px] h-[400px] bg-brand-500/10 blur-[100px] rounded-full pointer-events-none"></div>
            <div className="max-w-4xl mx-auto text-center relative z-10">
              <div className="inline-flex items-center gap-2 px-3 py-1.5 rounded-full bg-brand-50 dark:bg-brand-900/30 text-brand-700 dark:text-brand-300 font-bold text-xs uppercase tracking-wider mb-6 border border-brand-200/50 dark:border-brand-800/50">
                <span>✦</span> AI Powered Travel Planner
              </div>
              <h1 className="text-4xl md:text-5xl font-extrabold tracking-tight mb-4 text-gray-900 dark:text-white">
                Plan Your Perfect Journey with AI
              </h1>
              <p className="text-lg text-gray-600 dark:text-slate-400 max-w-2xl mx-auto leading-relaxed">
                Tell TourMate what you want to experience, and AI will create a personalized travel itinerary for you.
              </p>
            </div>
          </section>

          {/* Planning Card */}
          <section className="px-4 relative z-10">
            <div className="max-w-3xl mx-auto bg-white dark:bg-slate-900 rounded-3xl shadow-xl border border-gray-200/60 dark:border-slate-800 overflow-hidden">
              <div className="p-6 sm:p-10">
                <div className="mb-8">
                  <h2 className="text-2xl font-bold text-gray-900 dark:text-white">Let's Plan Your Trip</h2>
                  <p className="text-sm text-gray-500 dark:text-slate-400 mt-1">Customize your journey and let AI build the perfect itinerary.</p>
                </div>

                <div className="space-y-10">
                  
                  {/* Where are you going? */}
                  <div>
                    <h3 className="text-sm font-bold text-gray-900 dark:text-white uppercase tracking-wider mb-4 flex items-center gap-2">
                      <MapIcon className="w-4 h-4 text-brand-500" /> Where are you going?
                    </h3>
                    <div className="grid md:grid-cols-2 gap-4">
                      <div className="bg-gray-50 dark:bg-slate-800/50 p-4 rounded-2xl border border-gray-200 dark:border-slate-700 focus-within:ring-2 focus-within:ring-brand-500 transition-all">
                        <label className="text-xs font-semibold text-gray-500 dark:text-slate-400 block mb-1">From</label>
                        <input type="text" placeholder="e.g. Bengaluru" value={originName} onChange={(e) => setOriginName(e.target.value)} className="w-full bg-transparent border-none p-0 text-lg font-bold focus:ring-0 outline-none dark:text-white placeholder-gray-400 dark:placeholder-slate-500" />
                      </div>
                      <div className="bg-gray-50 dark:bg-slate-800/50 p-4 rounded-2xl border border-gray-200 dark:border-slate-700 focus-within:ring-2 focus-within:ring-brand-500 transition-all">
                        <label className="text-xs font-semibold text-gray-500 dark:text-slate-400 block mb-1">To</label>
                        <input type="text" placeholder="e.g. Goa" value={destinationName} onChange={(e) => setDestinationName(e.target.value)} className="w-full bg-transparent border-none p-0 text-lg font-bold focus:ring-0 outline-none dark:text-white placeholder-gray-400 dark:placeholder-slate-500" />
                      </div>
                    </div>
                  </div>

                  {/* Trip Details */}
                  <div>
                    <h3 className="text-sm font-bold text-gray-900 dark:text-white uppercase tracking-wider mb-4 flex items-center gap-2">
                      <Clock className="w-4 h-4 text-brand-500" /> Trip Details
                    </h3>
                    <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                      <div className="bg-gray-50 dark:bg-slate-800/50 p-3.5 rounded-2xl border border-gray-200 dark:border-slate-700">
                        <label className="text-[10px] font-bold text-gray-500 dark:text-slate-400 uppercase block mb-1">Duration</label>
                        <div className="flex items-center gap-2">
                          <input type="number" min="1" max="14" value={days} onChange={e => setDays(e.target.value)} className="w-12 bg-transparent border-none p-0 text-base font-bold focus:ring-0 outline-none dark:text-white" />
                          <span className="text-sm font-medium text-gray-600 dark:text-slate-300">Days</span>
                        </div>
                      </div>
                      <div className="bg-gray-50 dark:bg-slate-800/50 p-3.5 rounded-2xl border border-gray-200 dark:border-slate-700">
                        <label className="text-[10px] font-bold text-gray-500 dark:text-slate-400 uppercase block mb-1">Start Time</label>
                        <input type="time" value={startTime} onChange={e => setStartTime(e.target.value)} className="w-full bg-transparent border-none p-0 text-base font-bold focus:ring-0 outline-none dark:text-white" />
                      </div>
                      <div className="bg-gray-50 dark:bg-slate-800/50 p-3.5 rounded-2xl border border-gray-200 dark:border-slate-700">
                        <label className="text-[10px] font-bold text-gray-500 dark:text-slate-400 uppercase block mb-1">End Time</label>
                        <input type="time" value={endTime} onChange={e => setEndTime(e.target.value)} className="w-full bg-transparent border-none p-0 text-base font-bold focus:ring-0 outline-none dark:text-white" />
                      </div>
                      <div className="bg-gray-50 dark:bg-slate-800/50 p-3.5 rounded-2xl border border-gray-200 dark:border-slate-700">
                        <label className="text-[10px] font-bold text-gray-500 dark:text-slate-400 uppercase block mb-1">Accommodation</label>
                        <input type="text" placeholder="Hotel name..." value={accommodation} onChange={e => setAccommodation(e.target.value)} className="w-full bg-transparent border-none p-0 text-sm font-semibold focus:ring-0 outline-none dark:text-white" />
                      </div>
                    </div>
                  </div>

                  {/* Transportation */}
                  <div>
                    <h3 className="text-sm font-bold text-gray-900 dark:text-white uppercase tracking-wider mb-4 flex items-center gap-2">
                      <Navigation className="w-4 h-4 text-brand-500" /> Transportation
                    </h3>
                    
                    <div className="mb-5">
                      <label className="text-xs font-semibold text-gray-600 dark:text-slate-400 block mb-3">How are you traveling there?</label>
                      <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
                        {[
                          { id: 'flight', label: 'Flight', desc: 'Fast & convenient', icon: Plane },
                          { id: 'train', label: 'Train', desc: 'Comfortable journey', icon: Train },
                          { id: 'car', label: 'Car', desc: 'Flexible road trip', icon: Car },
                          { id: 'bike', label: 'Bike', desc: 'Freedom to explore', icon: Bike }
                        ].map(mode => {
                          const Icon = mode.icon;
                          const isActive = transportationMode === mode.id;
                          return (
                            <button
                              key={mode.id}
                              onClick={() => setTransportationMode(mode.id)}
                              className={`text-left p-4 rounded-2xl border-2 transition-all ${isActive ? 'border-brand-500 bg-brand-50 dark:bg-brand-900/20' : 'border-gray-100 dark:border-slate-700 bg-white dark:bg-slate-800 hover:border-gray-300 dark:hover:border-slate-600'}`}
                            >
                              <Icon className={`w-6 h-6 mb-2 ${isActive ? 'text-brand-600 dark:text-brand-400' : 'text-gray-400'}`} />
                              <p className={`font-bold text-sm ${isActive ? 'text-brand-900 dark:text-brand-100' : 'text-gray-700 dark:text-slate-300'}`}>{mode.label}</p>
                              <p className="text-[10px] text-gray-500 dark:text-slate-500 mt-1">{mode.desc}</p>
                            </button>
                          );
                        })}
                      </div>
                    </div>

                    <div>
                      <label className="text-xs font-semibold text-gray-600 dark:text-slate-400 block mb-3">How will you travel locally?</label>
                      <div className="flex flex-wrap gap-2">
                        {[
                          { id: 'walking', label: 'Walking', icon: '🚶' },
                          { id: 'public_transport', label: 'Public Transport', icon: '🚌' },
                          { id: 'taxi', label: 'Taxi', icon: '🚕' },
                          { id: 'car', label: 'Car', icon: '🚗' },
                          { id: 'bike', label: 'Bike', icon: '🏍️' }
                        ].map(mode => (
                          <button
                            key={mode.id}
                            onClick={() => setLocalTransportation(mode.id)}
                            className={`px-4 py-2 rounded-full border text-sm font-semibold flex items-center gap-2 transition-all ${localTransportation === mode.id ? 'bg-gray-900 text-white border-gray-900 dark:bg-white dark:text-gray-900 dark:border-white' : 'bg-white dark:bg-slate-800 text-gray-600 dark:text-slate-300 border-gray-200 dark:border-slate-700 hover:border-gray-400'}`}
                          >
                            <span>{mode.icon}</span> {mode.label}
                          </button>
                        ))}
                      </div>
                    </div>
                  </div>

                  {/* Preferences */}
                  <div>
                    <h3 className="text-sm font-bold text-gray-900 dark:text-white uppercase tracking-wider mb-4 flex items-center gap-2">
                      <Users className="w-4 h-4 text-brand-500" /> What kind of trip do you want?
                    </h3>
                    <div className="grid md:grid-cols-3 gap-6">
                      
                      <div>
                        <label className="text-xs font-semibold text-gray-600 dark:text-slate-400 block mb-3">Travel Type</label>
                        <div className="flex flex-col gap-2">
                          {['Solo', 'Couple', 'Family', 'Friends'].map(type => (
                            <button
                              key={type}
                              onClick={() => setTravelType(type)}
                              className={`text-left px-4 py-2.5 rounded-xl border text-sm font-bold transition-all ${travelType === type ? 'bg-brand-50 border-brand-500 text-brand-700 dark:bg-brand-900/30 dark:border-brand-400 dark:text-brand-300' : 'bg-white dark:bg-slate-800 border-gray-200 dark:border-slate-700 text-gray-600 dark:text-slate-300 hover:bg-gray-50 dark:hover:bg-slate-700/50'}`}
                            >
                              {type}
                            </button>
                          ))}
                        </div>
                      </div>

                      <div>
                        <label className="text-xs font-semibold text-gray-600 dark:text-slate-400 block mb-3">Energy Level</label>
                        <div className="bg-gray-100 dark:bg-slate-800 p-1 rounded-xl flex flex-col">
                          {['Relaxed', 'Moderate', 'Active'].map(level => (
                            <button
                              key={level}
                              onClick={() => setEnergyLevel(level)}
                              className={`px-4 py-2.5 rounded-lg text-sm font-bold transition-all ${energyLevel === level ? 'bg-white dark:bg-slate-700 text-gray-900 dark:text-white shadow-sm' : 'text-gray-500 dark:text-slate-400 hover:text-gray-700 dark:hover:text-slate-200'}`}
                            >
                              {level}
                            </button>
                          ))}
                        </div>
                      </div>

                      <div>
                        <label className="text-xs font-semibold text-gray-600 dark:text-slate-400 block mb-3">Budget</label>
                        <div className="bg-gray-100 dark:bg-slate-800 p-1 rounded-xl flex flex-col">
                          {['Low', 'Medium', 'High'].map(b => (
                            <button
                              key={b}
                              onClick={() => setBudget(b)}
                              className={`px-4 py-2.5 rounded-lg text-sm font-bold transition-all flex items-center justify-between ${budget === b ? 'bg-white dark:bg-slate-700 text-gray-900 dark:text-white shadow-sm' : 'text-gray-500 dark:text-slate-400 hover:text-gray-700 dark:hover:text-slate-200'}`}
                            >
                              {b}
                              <span className="text-emerald-500 flex">
                                {Array.from({length: b === 'Low' ? 1 : b === 'Medium' ? 2 : 3}).map((_, i) => <IndianRupee key={i} className="w-3 h-3" />)}
                              </span>
                            </button>
                          ))}
                        </div>
                      </div>

                    </div>
                  </div>

                  {/* Interests */}
                  <div>
                    <h3 className="text-sm font-bold text-gray-900 dark:text-white uppercase tracking-wider mb-4 flex items-center gap-2">
                      <Activity className="w-4 h-4 text-brand-500" /> What are you interested in?
                    </h3>
                    <div className="flex flex-wrap gap-3">
                      {availableInterests.map(interest => (
                        <button
                          key={interest.id}
                          onClick={() => toggleInterest(interest.id)}
                          className={`px-4 py-2.5 rounded-full border transition-all text-sm font-bold flex items-center gap-2 ${interests.includes(interest.id) ? 'bg-brand-600 border-brand-600 text-white shadow-md transform -translate-y-0.5' : 'bg-white dark:bg-slate-800 border-gray-200 dark:border-slate-700 text-gray-600 dark:text-slate-300 hover:border-brand-300 hover:shadow-sm'}`}
                        >
                          <span>{interest.icon}</span> {interest.label}
                        </button>
                      ))}
                    </div>
                  </div>

                </div>
              </div>
              
              <div className="bg-gray-50 dark:bg-slate-800/80 p-6 sm:p-8 border-t border-gray-200 dark:border-slate-700 flex flex-col items-center justify-center">
                <button
                  onClick={handleGenerate}
                  disabled={!destinationName}
                  className="w-full sm:w-auto min-w-[280px] bg-brand-600 hover:bg-brand-700 text-white font-bold text-lg py-4 px-8 rounded-2xl shadow-lg hover:shadow-xl transition-all transform hover:-translate-y-1 disabled:opacity-50 disabled:transform-none disabled:hover:shadow-none flex items-center justify-center gap-3"
                >
                  ✦ Generate My Itinerary
                </button>
                <p className="text-xs text-gray-500 dark:text-slate-500 font-medium mt-4">Powered by TourMate AI</p>
              </div>
            </div>
          </section>
        </>
      )}

      {/* Loading State */}
      {generating && (
        <div className="max-w-2xl mx-auto px-4 pt-32 pb-24 text-center">
          <div className="w-24 h-24 bg-brand-100 dark:bg-brand-900/30 rounded-3xl mx-auto flex items-center justify-center mb-8 animate-pulse shadow-inner">
            <span className="text-4xl animate-bounce">✨</span>
          </div>
          <h2 className="text-3xl font-extrabold text-gray-900 dark:text-white mb-10">Creating your perfect trip...</h2>
          
          <div className="space-y-4 max-w-sm mx-auto text-left">
            {loadingMessages.map((msg, idx) => {
              const isActive = idx === loadingStep;
              const isPast = idx < loadingStep;
              return (
                <div key={idx} className={`flex items-center gap-3 transition-all duration-500 ${isPast ? 'opacity-100 text-brand-600 dark:text-brand-400' : isActive ? 'opacity-100 text-gray-900 dark:text-white scale-105 font-bold' : 'opacity-30 text-gray-500'}`}>
                  {isPast ? <CheckCircle2 className="w-5 h-5" /> : isActive ? <div className="w-5 h-5 border-2 border-brand-500 border-t-transparent rounded-full animate-spin"></div> : <div className="w-5 h-5 rounded-full border-2 border-gray-300 dark:border-slate-700"></div>}
                  <span className="text-base">{msg}</span>
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* Error State */}
      {errorMsg && !generating && (
        <div className="max-w-xl mx-auto px-4 pt-32 pb-24 text-center">
          <div className="w-20 h-20 bg-red-100 dark:bg-red-900/30 rounded-full mx-auto flex items-center justify-center mb-6">
            <span className="text-3xl">⚠️</span>
          </div>
          <h2 className="text-2xl font-bold text-gray-900 dark:text-white mb-4">We couldn't create your itinerary</h2>
          <p className="text-gray-600 dark:text-slate-400 mb-8">{errorMsg}</p>
          <div className="flex gap-4 justify-center">
            <button onClick={handleGenerate} className="bg-brand-600 hover:bg-brand-700 text-white font-bold py-3 px-6 rounded-xl transition-all">Try Again</button>
            <button onClick={() => setErrorMsg("")} className="bg-gray-200 dark:bg-slate-800 hover:bg-gray-300 dark:hover:bg-slate-700 text-gray-800 dark:text-white font-bold py-3 px-6 rounded-xl transition-all">Edit Preferences</button>
          </div>
        </div>
      )}

      {/* Results State */}
      {generatedItinerary && !generating && (
        <div className="max-w-5xl mx-auto px-4 pt-12">
          {/* Results State Top Header */}
          <div className="relative mb-12 rounded-3xl overflow-hidden bg-brand-900 shadow-xl animate-fade-in-up">
            {/* Abstract Background Design */}
            <div className="absolute inset-0 overflow-hidden">
              <div className="absolute -top-[50%] -right-[10%] w-[70%] h-[150%] bg-brand-600/30 blur-3xl rounded-full mix-blend-screen"></div>
              <div className="absolute -bottom-[50%] -left-[10%] w-[60%] h-[150%] bg-rose-500/20 blur-3xl rounded-full mix-blend-screen"></div>
              <div className="absolute inset-0 bg-gradient-to-r from-brand-950 via-brand-900/90 to-brand-900/40"></div>
            </div>

            <div className="relative p-8 md:p-12 lg:p-16 flex flex-col md:flex-row items-center justify-between gap-8 z-10">
              <div className="flex-1 text-center md:text-left">
                <div className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-white/10 border border-white/20 text-white font-bold text-xs uppercase tracking-wider mb-6 backdrop-blur-md">
                  <Sparkles className="w-3.5 h-3.5 text-amber-400" /> AI Generated
                </div>
                <h1 className="text-4xl md:text-5xl lg:text-6xl font-black text-white mb-4 tracking-tight leading-tight">
                  Your <span className="text-transparent bg-clip-text bg-gradient-to-r from-amber-200 to-amber-500">Ultimate</span> Journey
                </h1>
                <p className="text-lg md:text-xl font-medium text-brand-100 mb-8 max-w-2xl">
                  We've analyzed your preferences and crafted the perfect itineraries for <strong className="text-white">{destinationName}</strong>.
                </p>
                
                <div className="flex flex-wrap justify-center md:justify-start gap-3">
                  <span className="px-4 py-2 bg-black/20 backdrop-blur-md border border-white/10 rounded-xl text-sm font-semibold text-white flex items-center gap-2 shadow-inner">
                    <MapPin className="w-4 h-4 text-brand-300" /> {destinationName}
                  </span>
                  <span className="px-4 py-2 bg-black/20 backdrop-blur-md border border-white/10 rounded-xl text-sm font-semibold text-white flex items-center gap-2 shadow-inner">
                    <Clock className="w-4 h-4 text-brand-300" /> {days} Days
                  </span>
                  <span className="px-4 py-2 bg-black/20 backdrop-blur-md border border-white/10 rounded-xl text-sm font-semibold text-white flex items-center gap-2 shadow-inner">
                    <Users className="w-4 h-4 text-brand-300" /> {travelType}
                  </span>
                  <span className="px-4 py-2 bg-black/20 backdrop-blur-md border border-white/10 rounded-xl text-sm font-semibold text-white flex items-center gap-2 shadow-inner">
                    <IndianRupee className="w-4 h-4 text-brand-300" /> {budget}
                  </span>
                </div>
              </div>
            </div>
          </div>

          {/* Route Options */}
          <div className="mb-6 flex items-center justify-between animate-fade-in-up-delay-1">
            <h2 className="text-2xl font-bold text-gray-900 dark:text-white">Choose Your Vibe</h2>
            <p className="text-sm text-gray-500 dark:text-slate-400 font-medium">Select a generated route</p>
          </div>

          <div className="grid md:grid-cols-3 gap-6 mb-12 animate-fade-in-up-delay-1">
            {generatedItinerary.map((option, idx) => (
              <div 
                key={idx}
                onClick={() => { setSelectedOptionIndex(idx); setActiveDay(1); }}
                className={`cursor-pointer rounded-3xl p-6 border-2 transition-all duration-300 relative overflow-hidden group ${
                  selectedOptionIndex === idx 
                    ? 'border-brand-500 bg-white dark:bg-slate-800 shadow-xl shadow-brand-500/10 transform -translate-y-2' 
                    : 'border-gray-200 dark:border-slate-700 bg-gray-50/80 dark:bg-slate-900/50 hover:border-brand-300 hover:bg-white dark:hover:bg-slate-800 hover:shadow-lg'
                }`}
              >
                {selectedOptionIndex === idx && (
                  <div className="absolute top-0 inset-x-0 h-1.5 bg-gradient-to-r from-brand-400 to-brand-600"></div>
                )}
                
                <div className="flex justify-between items-start mb-4">
                  <div className={`w-12 h-12 rounded-2xl flex items-center justify-center ${
                    selectedOptionIndex === idx ? 'bg-brand-100 dark:bg-brand-900/50 text-brand-600 dark:text-brand-400' : 'bg-gray-200 dark:bg-slate-800 text-gray-500 dark:text-slate-400 group-hover:bg-brand-50 dark:group-hover:bg-brand-900/20 group-hover:text-brand-500'
                  } transition-colors`}>
                    <MapIcon className="w-6 h-6" />
                  </div>
                  {selectedOptionIndex === idx && (
                    <div className="flex items-center gap-1.5 text-[10px] font-bold uppercase tracking-wider text-brand-600 dark:text-brand-400 bg-brand-50 dark:bg-brand-900/30 px-3 py-1.5 rounded-full">
                      <CheckCircle2 className="w-3.5 h-3.5" /> Selected
                    </div>
                  )}
                </div>

                <h3 className={`text-xl font-black mb-2 leading-tight ${selectedOptionIndex === idx ? 'text-gray-900 dark:text-white' : 'text-gray-700 dark:text-slate-300 group-hover:text-gray-900 dark:group-hover:text-white'}`}>
                  {option.route_name}
                </h3>
                
                <p className="text-sm text-gray-600 dark:text-slate-400 mb-6 h-[4.5rem] overflow-hidden leading-relaxed">
                  {option.description}
                </p>
                
                <div className="pt-4 border-t border-gray-100 dark:border-slate-700/80 flex items-end justify-between">
                  <div>
                    <p className="text-[10px] uppercase font-bold tracking-wider text-gray-500 mb-1">Est. Cost</p>
                    <p className={`font-black text-xl flex items-center gap-0.5 ${selectedOptionIndex === idx ? 'text-emerald-600 dark:text-emerald-400' : 'text-gray-700 dark:text-slate-300'}`}>
                      <IndianRupee className="w-4 h-4" />{(option.total_estimated_cost || 0).toLocaleString("en-IN")}
                    </p>
                  </div>
                </div>
              </div>
            ))}
          </div>

          {/* Active Itinerary Details - New Structure */}
          {generatedItinerary[selectedOptionIndex] && (
            <div>
              <ItineraryHeader 
                title={title}
                destinationName={destinationName}
                days={days}
                travelers={travelType}
                tripStyle={interests.join(' • ')}
                budget={budget}
                totalEstimatedCost={generatedItinerary[selectedOptionIndex].total_estimated_cost + (generatedItinerary[selectedOptionIndex].transportation?.estimated_cost_max || 0)}
                totalEstimatedTravelMinutes={generatedItinerary[selectedOptionIndex].schedule.reduce((total, day) => total + day.activities.reduce((sum, act) => sum + (act.travel_time_minutes || 0), 0), 0)}
                onRegenerate={() => setGeneratedItinerary(null)}
                onSave={handleSave}
                saving={saving}
              />

              <div className="flex flex-col lg:flex-row gap-8 relative">
                {/* Left Column: Timeline */}
                <div className="flex-1 max-w-4xl">
                  <DayNavigation 
                    schedule={generatedItinerary[selectedOptionIndex].schedule} 
                    activeDay={activeDay} 
                    setActiveDay={setActiveDay} 
                  />

                  {/* AI Optimize Button */}
                  <div className="flex justify-end mb-6">
                    <button 
                      onClick={() => setIsOptimizeModalOpen(true)}
                      className="px-5 py-2.5 bg-brand-100 hover:bg-brand-200 dark:bg-brand-900/40 dark:hover:bg-brand-900/60 text-brand-700 dark:text-brand-300 font-bold rounded-2xl flex items-center gap-2 transition-colors border border-brand-200 dark:border-brand-800/50 shadow-sm"
                    >
                      <Sparkles className="w-4 h-4" /> Optimize My Day
                    </button>
                  </div>

                  {generatedItinerary[selectedOptionIndex].schedule.filter(d => d.day === activeDay).map(dayPlan => (
                    <div key={dayPlan.day}>
                      <DailySummary dayPlan={dayPlan} />
                      
                      <div className="mt-8">
                        {dayPlan.activities.map((act, i) => (
                          <React.Fragment key={i}>
                            <ActivityCard 
                              activity={act}
                              isFirst={i === 0}
                              isLast={i === dayPlan.activities.length - 1}
                              onMoveUp={() => handleMoveActivity(activeDay - 1, i, "up")}
                              onMoveDown={() => handleMoveActivity(activeDay - 1, i, "down")}
                            />
                            {i < dayPlan.activities.length - 1 && (
                              <TravelConnector 
                                currentActivity={act}
                                nextActivity={dayPlan.activities[i + 1]}
                              />
                            )}
                          </React.Fragment>
                        ))}
                      </div>

                      <BudgetBreakdown dayPlan={dayPlan} />
                    </div>
                  ))}
                </div>
                
                {/* Right Column: Hotel Suggestions */}
                <div className="w-full lg:w-[350px] shrink-0">
                  <NearbyHotelsSuggestion places={selectedPlaces} destinationName={destinationName} />
                </div>
              </div>
            </div>
          )}

          <OptimizeDayModal 
            isOpen={isOptimizeModalOpen}
            onClose={() => setIsOptimizeModalOpen(false)}
            dayPlan={generatedItinerary[selectedOptionIndex].schedule.find(d => d.day === activeDay)}
            onApply={handleApplyOptimizedDay}
          />
        </div>
      )}
    </div>
  );
}
