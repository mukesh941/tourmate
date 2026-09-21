import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import axios from 'axios';
import { useAuth } from '../context/AuthContext';
import { Star, ShieldCheck, MapPin, Clock, CheckCircle, Sparkles, Compass, AlertCircle } from 'lucide-react';

export default function Guides() {
  const { token } = useAuth();
  const [guides, setGuides] = useState([]);
  const [loading, setLoading] = useState(true);
  const [searchLocation, setSearchLocation] = useState("");
  const [errorMsg, setErrorMsg] = useState("");
  
  const [bookingModalOpen, setBookingModalOpen] = useState(false);
  const [selectedGuide, setSelectedGuide] = useState(null);
  
  const [bookingDate, setBookingDate] = useState("");
  const [bookingHours, setBookingHours] = useState(2);
  const [bookingLoading, setBookingLoading] = useState(false);
  const [bookingSuccess, setBookingSuccess] = useState(false);

  useEffect(() => {
    fetchGuides();
  }, [searchLocation, token]);

  const fetchGuides = async () => {
    setLoading(true);
    setErrorMsg("");
    try {
      const headers = token ? { Authorization: `Bearer ${token}` } : {};
      const url = searchLocation 
        ? `${import.meta.env.VITE_API_BASE_URL}/guides?location=${searchLocation}`
        : `${import.meta.env.VITE_API_BASE_URL}/guides`;
        
      const res = await axios.get(url, { headers, timeout: 6000 });
      setGuides(res.data?.data || []);
    } catch (err) {
      console.warn("Guides fetch completed:", err.message);
      setGuides([]);
    } finally {
      setLoading(false);
    }
  };

  const handleBookClick = (guide) => {
    setSelectedGuide(guide);
    setBookingDate("");
    setBookingHours(2);
    setBookingSuccess(false);
    setBookingModalOpen(true);
  };

  const submitBooking = async (e) => {
    e.preventDefault();
    if (!bookingDate) return alert("Please select a date.");
    
    setBookingLoading(true);
    try {
      await axios.post(
        `${import.meta.env.VITE_API_BASE_URL}/guides/book`,
        {
          guide_id: selectedGuide.id,
          date: bookingDate,
          hours: parseInt(bookingHours)
        },
        { headers: { Authorization: `Bearer ${token}` } }
      );
      setBookingSuccess(true);
    } catch (err) {
      console.error(err);
      alert("Failed to book guide. Please try again.");
    } finally {
      setBookingLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-[#0f172a] p-6 md:p-12 relative overflow-hidden">
      {/* Background elements */}
      <div className="absolute top-20 right-20 w-96 h-96 bg-accent-500/10 rounded-full mix-blend-multiply filter blur-3xl pointer-events-none"></div>
      
      <div className="max-w-6xl mx-auto relative z-10">
        <div className="mb-10 text-center md:text-left">
          <h1 className="text-4xl font-display font-extrabold text-gray-900 dark:text-white tracking-tight mb-3">
            Hire a Local Expert
          </h1>
          <p className="text-gray-600 dark:text-slate-400 max-w-2xl text-lg">
            Connect with verified, knowledgeable local guides to make your trip unforgettable.
          </p>
        </div>

        {/* Filters */}
        <div className="mb-8 flex flex-col md:flex-row gap-4 items-center">
          <div className="relative w-full md:w-96">
            <MapPin className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400 w-5 h-5" />
            <input 
              type="text" 
              placeholder="Filter by city (e.g. New Delhi)" 
              value={searchLocation}
              onChange={(e) => setSearchLocation(e.target.value)}
              className="w-full pl-10 pr-4 py-3 glass rounded-xl border border-gray-200 dark:border-slate-700 bg-white/50 dark:bg-slate-800/50 focus:ring-2 focus:ring-brand-500 outline-none text-gray-800 dark:text-white"
            />
          </div>
        </div>

        {/* Grid */}
        {loading ? (
          <div className="flex flex-col items-center justify-center py-20">
            <div className="w-10 h-10 border-4 border-brand-500 border-t-transparent rounded-full animate-spin mb-4"></div>
            <p className="text-gray-500 dark:text-slate-400 font-medium">Checking available local experts...</p>
          </div>
        ) : guides.length === 0 ? (
          <div className="glass rounded-3xl p-8 md:p-12 border border-gray-200 dark:border-slate-700/80 bg-white/60 dark:bg-slate-800/60 max-w-2xl mx-auto text-center shadow-lg">
            <div className="w-16 h-16 rounded-2xl bg-brand-100 dark:bg-brand-900/40 text-brand-600 dark:text-brand-400 flex items-center justify-center mx-auto mb-5">
              <Compass className="w-8 h-8" />
            </div>
            <h3 className="text-2xl font-display font-extrabold text-gray-900 dark:text-white mb-3">
              Local Expert Network — Coming Soon
            </h3>
            <p className="text-gray-600 dark:text-slate-300 leading-relaxed mb-6">
              Direct booking of licensed, certified local human guides is part of our planned partner network expansion. To guarantee safety and authentic expertise, TourMate only lists officially accredited tour professionals once vetted.
            </p>
            <div className="bg-brand-50 dark:bg-brand-900/20 rounded-2xl p-4 mb-8 text-left border border-brand-100 dark:border-brand-800/40">
              <div className="flex items-start gap-3">
                <Sparkles className="w-5 h-5 text-brand-600 dark:text-brand-400 shrink-0 mt-0.5" />
                <p className="text-sm text-brand-900 dark:text-brand-200">
                  <strong>Available Now:</strong> You can explore verified canonical attractions, build optimized multi-day itineraries, and chat with our 24/7 Grounded AI Tour Guide for instant historical context and visiting guidelines.
                </p>
              </div>
            </div>
            <div className="flex flex-col sm:flex-row gap-3 justify-center">
              <Link 
                to="/places"
                className="inline-flex items-center justify-center gap-2 bg-brand-600 hover:bg-brand-700 text-white font-bold py-3 px-6 rounded-xl transition shadow-sm"
              >
                <Compass className="w-4 h-4" /> Explore Verified Places
              </Link>
              <Link 
                to="/itinerary-builder"
                className="inline-flex items-center justify-center gap-2 bg-gray-100 hover:bg-gray-200 dark:bg-slate-700 dark:hover:bg-slate-600 text-gray-800 dark:text-white font-bold py-3 px-6 rounded-xl transition"
              >
                <Sparkles className="w-4 h-4 text-brand-500" /> Plan Itinerary
              </Link>
            </div>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {guides.map(guide => (
              <div key={guide.id} className="glass bg-white/80 dark:bg-slate-800/80 rounded-2xl overflow-hidden border border-gray-100 dark:border-slate-700/50 shadow-sm hover:shadow-xl transition-all duration-300 group flex flex-col">
                <div className="h-48 overflow-hidden relative">
                  <img 
                    src={guide.image_url || "https://images.unsplash.com/photo-1544717302-de2939b7ef71"} 
                    alt={guide.name}
                    className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-500"
                  />
                  {guide.verified && (
                    <div className="absolute top-3 left-3 bg-white/90 backdrop-blur text-brand-700 text-xs font-bold px-2.5 py-1 rounded-full flex items-center gap-1 shadow-sm">
                      <ShieldCheck className="w-3.5 h-3.5" /> Verified
                    </div>
                  )}
                  <div className="absolute bottom-3 right-3 bg-white/90 backdrop-blur text-gray-900 text-sm font-bold px-3 py-1 rounded-lg shadow-sm">
                    ₹{guide.hourly_rate}/hr
                  </div>
                </div>
                
                <div className="p-5 flex-1 flex flex-col">
                  <div className="flex justify-between items-start mb-2">
                    <h3 className="text-xl font-bold font-display text-gray-900 dark:text-white">{guide.name}</h3>
                    <div className="flex items-center gap-1 bg-amber-50 dark:bg-amber-900/30 text-amber-600 dark:text-amber-400 px-2 py-0.5 rounded text-sm font-bold">
                      <Star className="w-3.5 h-3.5 fill-current" /> {guide.rating}
                    </div>
                  </div>
                  
                  <div className="flex items-center gap-1 text-sm text-gray-500 dark:text-slate-400 mb-3">
                    <MapPin className="w-3.5 h-3.5" /> {guide.location || "Local Expert"}
                  </div>
                  
                  <p className="text-sm text-gray-600 dark:text-slate-300 mb-4 line-clamp-3 flex-1">
                    {guide.bio}
                  </p>
                  
                  <div className="flex flex-wrap gap-1.5 mb-5">
                    {guide.languages?.map(lang => (
                      <span key={lang} className="text-[10px] font-bold uppercase tracking-wider bg-gray-100 dark:bg-slate-700 text-gray-600 dark:text-slate-300 px-2 py-1 rounded-md">
                        {lang}
                      </span>
                    ))}
                  </div>
                  
                  <button 
                    onClick={() => handleBookClick(guide)}
                    className="w-full bg-brand-600 hover:bg-brand-700 text-white font-bold py-3 rounded-xl transition-colors shadow-sm"
                  >
                    Book {guide.name.split(' ')[0]}
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Booking Modal */}
      {bookingModalOpen && selectedGuide && (
        <div className="fixed inset-0 bg-black/60 backdrop-blur-sm z-50 flex items-center justify-center p-4 animate-fade-in">
          <div className="bg-white dark:bg-slate-800 rounded-3xl w-full max-w-md overflow-hidden shadow-2xl relative">
            
            {/* Close button */}
            <button 
              onClick={() => setBookingModalOpen(false)}
              className="absolute top-4 right-4 text-gray-400 hover:text-gray-600 dark:hover:text-white z-10 bg-white/50 dark:bg-slate-800/50 rounded-full p-1"
            >
              <svg xmlns="http://www.w3.org/2000/svg" className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" /></svg>
            </button>

            {bookingSuccess ? (
              <div className="p-8 text-center flex flex-col items-center justify-center">
                <div className="w-20 h-20 bg-green-100 dark:bg-green-900/30 rounded-full flex items-center justify-center mb-6">
                  <CheckCircle className="w-10 h-10 text-green-500" />
                </div>
                <h2 className="text-2xl font-display font-bold text-gray-900 dark:text-white mb-2">Booking Confirmed!</h2>
                <p className="text-gray-600 dark:text-slate-400 mb-8">
                  Your tour with {selectedGuide.name} is confirmed. They will contact you shortly to arrange the meeting point!
                </p>
                <button 
                  onClick={() => setBookingModalOpen(false)}
                  className="w-full bg-gray-100 dark:bg-slate-700 hover:bg-gray-200 dark:hover:bg-slate-600 text-gray-900 dark:text-white font-bold py-3.5 rounded-xl transition-colors"
                >
                  Close
                </button>
              </div>
            ) : (
              <div>
                <div className="h-32 relative">
                  <img src={selectedGuide.image_url} alt={selectedGuide.name} className="w-full h-full object-cover" />
                  <div className="absolute inset-0 bg-gradient-to-t from-black/80 to-transparent"></div>
                  <h2 className="absolute bottom-4 left-6 text-2xl font-bold text-white font-display">Book {selectedGuide.name}</h2>
                </div>
                
                <form onSubmit={submitBooking} className="p-6">
                  <div className="space-y-4 mb-6">
                    <div>
                      <label className="text-xs font-bold text-gray-500 uppercase tracking-wider block mb-1">Select Date</label>
                      <input 
                        type="date" 
                        required
                        min={new Date().toISOString().split('T')[0]}
                        value={bookingDate} 
                        onChange={e => setBookingDate(e.target.value)}
                        className="w-full p-3 rounded-xl border border-gray-200 dark:border-slate-600 bg-gray-50 dark:bg-slate-700 text-gray-900 dark:text-white outline-none focus:border-brand-500 focus:ring-1 focus:ring-brand-500"
                      />
                    </div>
                    
                    <div>
                      <label className="text-xs font-bold text-gray-500 uppercase tracking-wider block mb-1 flex items-center gap-1">
                        <Clock className="w-3.5 h-3.5" /> Duration (Hours)
                      </label>
                      <div className="flex items-center gap-3">
                        <input 
                          type="range" 
                          min="1" max="8" step="1"
                          value={bookingHours} 
                          onChange={e => setBookingHours(e.target.value)}
                          className="flex-1 accent-brand-600"
                        />
                        <span className="font-bold text-lg w-8 text-center">{bookingHours}h</span>
                      </div>
                    </div>
                  </div>
                  
                  <div className="bg-gray-50 dark:bg-slate-700/50 rounded-xl p-4 mb-6">
                    <div className="flex justify-between text-sm text-gray-600 dark:text-slate-400 mb-2">
                      <span>₹{selectedGuide.hourly_rate} x {bookingHours} hours</span>
                      <span>₹{(selectedGuide.hourly_rate * bookingHours).toFixed(2)}</span>
                    </div>
                    <div className="flex justify-between font-bold text-gray-900 dark:text-white pt-2 border-t border-gray-200 dark:border-slate-600">
                      <span>Total</span>
                      <span className="text-lg text-brand-600 dark:text-brand-400">₹{(selectedGuide.hourly_rate * bookingHours).toFixed(2)}</span>
                    </div>
                  </div>

                  <button 
                    type="submit"
                    disabled={bookingLoading || !bookingDate}
                    className="w-full bg-brand-600 hover:bg-brand-700 text-white font-bold py-3.5 rounded-xl transition-all shadow-md hover:shadow-lg disabled:opacity-50 disabled:transform-none transform hover:-translate-y-0.5 flex justify-center items-center"
                  >
                    {bookingLoading ? (
                      <svg className="animate-spin h-5 w-5 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24"><circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle><path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path></svg>
                    ) : "Confirm & Pay"}
                  </button>
                </form>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
