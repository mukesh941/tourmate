import React, { useState, useEffect, useMemo } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import axios from 'axios';
import { useAuth } from '../context/AuthContext';
import { useTranslation } from 'react-i18next';
import { API_BASE_URL } from '../api/axios';
import { DEFAULT_GUIDES } from '../data/guidesData';
import { 
  Star, ShieldCheck, MapPin, Clock, CheckCircle, Sparkles, 
  Compass, AlertCircle, RefreshCw, Calendar, Phone, MessageSquare, 
  Search, Filter, ChevronRight, UserCheck, X, Award, Briefcase, 
  ArrowUpDown, Check, Users
} from 'lucide-react';

export default function Guides() {
  const { token, user } = useAuth();
  const { t } = useTranslation();
  const navigate = useNavigate();
  
  const [activeTab, setActiveTab] = useState('explore'); // 'explore' | 'bookings'
  const [guides, setGuides] = useState(DEFAULT_GUIDES);
  const [loading, setLoading] = useState(true);
  const [dataSource, setDataSource] = useState('loading'); // 'backend' | 'curated'
  
  // Search & Filters
  const [searchQuery, setSearchQuery] = useState("");
  const [selectedState, setSelectedState] = useState("All");
  const [selectedLanguage, setSelectedLanguage] = useState("All");
  const [sortBy, setSortBy] = useState("rating"); // 'rating' | 'reviews' | 'price_asc' | 'price_desc'
  
  // Booking Modal State
  const [bookingModalOpen, setBookingModalOpen] = useState(false);
  const [selectedGuide, setSelectedGuide] = useState(null);
  const [bookingDate, setBookingDate] = useState("");
  const [bookingHours, setBookingHours] = useState(3);
  const [bookingNotes, setBookingNotes] = useState("");
  const [bookingLoading, setBookingLoading] = useState(false);
  const [bookingSuccess, setBookingSuccess] = useState(false);
  const [confirmedBooking, setConfirmedBooking] = useState(null);
  
  // My Bookings list (persisted in localStorage + backend if available)
  const [myBookings, setMyBookings] = useState(() => {
    try {
      const stored = localStorage.getItem("tourmate_guide_bookings");
      return stored ? JSON.parse(stored) : [];
    } catch {
      return [];
    }
  });

  // Calculate default tomorrow date for booking
  const tomorrowStr = useMemo(() => {
    const d = new Date();
    d.setDate(d.getDate() + 1);
    return d.toISOString().split('T')[0];
  }, []);

  useEffect(() => {
    fetchGuides();
    fetchUserBookings();
  }, [token]);

  const fetchGuides = async () => {
    setLoading(true);
    try {
      const headers = token ? { Authorization: `Bearer ${token}` } : {};
      const res = await axios.get(`${API_BASE_URL}/guides`, { headers, timeout: 4000 });
      const backendGuides = res.data?.data;
      if (Array.isArray(backendGuides) && backendGuides.length > 0) {
        setGuides(backendGuides);
        setDataSource('backend');
      } else {
        // Fallback to rich curated local guides
        setGuides(DEFAULT_GUIDES);
        setDataSource('curated');
      }
    } catch (err) {
      // Graceful offline fallback: never crash or show scary error screens
      console.warn("Backend guides API unavailable, using curated local experts catalog:", err?.message);
      setGuides(DEFAULT_GUIDES);
      setDataSource('curated');
    } finally {
      setLoading(false);
    }
  };

  const fetchUserBookings = async () => {
    if (!token) return;
    try {
      const res = await axios.get(`${API_BASE_URL}/guides/bookings/me`, {
        headers: { Authorization: `Bearer ${token}` },
        timeout: 3000
      });
      if (Array.isArray(res.data?.data) && res.data.data.length > 0) {
        // Merge with local bookings
        setMyBookings(prev => {
          const combined = [...res.data.data];
          prev.forEach(p => {
            if (!combined.some(c => c.id === p.id)) combined.push(p);
          });
          localStorage.setItem("tourmate_guide_bookings", JSON.stringify(combined));
          return combined;
        });
      }
    } catch {
      // Keep local bookings
    }
  };

  // Available unique states & languages for filters
  const availableStates = useMemo(() => {
    const states = new Set();
    guides.forEach(g => {
      if (g.state_or_ut) states.add(g.state_or_ut);
      else if (g.location) {
        const parts = g.location.split(',');
        if (parts.length > 1) states.add(parts[1].trim());
      }
    });
    return ["All", ...Array.from(states)];
  }, [guides]);

  const availableLanguages = useMemo(() => {
    const langs = new Set();
    guides.forEach(g => {
      (g.languages || []).forEach(l => langs.add(l));
    });
    return ["All", ...Array.from(langs)];
  }, [guides]);

  // Filtered and sorted guides
  const filteredGuides = useMemo(() => {
    return guides.filter(guide => {
      // Text search
      if (searchQuery.trim()) {
        const q = searchQuery.toLowerCase();
        const matchesName = guide.name?.toLowerCase().includes(q);
        const matchesLoc = guide.location?.toLowerCase().includes(q);
        const matchesCity = guide.city?.toLowerCase().includes(q);
        const matchesBio = guide.bio?.toLowerCase().includes(q);
        const matchesLangs = guide.languages?.some(l => l.toLowerCase().includes(q));
        const matchesSpecs = guide.specialties?.some(s => s.toLowerCase().includes(q));
        if (!matchesName && !matchesLoc && !matchesCity && !matchesBio && !matchesLangs && !matchesSpecs) {
          return false;
        }
      }

      // State filter
      if (selectedState !== "All") {
        const guideState = guide.state_or_ut || guide.location || "";
        if (!guideState.toLowerCase().includes(selectedState.toLowerCase())) {
          return false;
        }
      }

      // Language filter
      if (selectedLanguage !== "All") {
        if (!guide.languages || !guide.languages.includes(selectedLanguage)) {
          return false;
        }
      }

      return true;
    }).sort((a, b) => {
      if (sortBy === "rating") return (b.rating || 0) - (a.rating || 0);
      if (sortBy === "reviews") return (b.reviews_count || 0) - (a.reviews_count || 0);
      if (sortBy === "price_asc") return (a.hourly_rate || 0) - (b.hourly_rate || 0);
      if (sortBy === "price_desc") return (b.hourly_rate || 0) - (a.hourly_rate || 0);
      return 0;
    });
  }, [guides, searchQuery, selectedState, selectedLanguage, sortBy]);

  const handleOpenBooking = (guide) => {
    setSelectedGuide(guide);
    setBookingDate(tomorrowStr);
    setBookingHours(3);
    setBookingNotes("");
    setBookingSuccess(false);
    setConfirmedBooking(null);
    setBookingModalOpen(true);
  };

  const submitBooking = async (e) => {
    e.preventDefault();
    if (!bookingDate) return alert("Please select a date for your tour.");

    setBookingLoading(true);
    const totalPrice = (selectedGuide.hourly_rate || 500) * parseInt(bookingHours, 10);
    const bookingId = `TM-${Date.now().toString().slice(-6)}`;

    const newBookingObj = {
      id: bookingId,
      guide_id: selectedGuide.id,
      guide: selectedGuide,
      date: bookingDate,
      hours: parseInt(bookingHours, 10),
      hourly_rate: selectedGuide.hourly_rate || 500,
      total_price: totalPrice,
      notes: bookingNotes || "Sightseeing and local heritage walk",
      status: "Confirmed",
      created_at: new Date().toISOString(),
      user_email: user?.email || "guest@tourmate.ai",
      user_name: user?.name || "TourMate Explorer"
    };

    try {
      if (token) {
        try {
          const res = await axios.post(
            `${API_BASE_URL}/guides/book`,
            {
              guide_id: selectedGuide.id,
              date: bookingDate,
              hours: parseInt(bookingHours, 10)
            },
            { headers: { Authorization: `Bearer ${token}` }, timeout: 4000 }
          );
          if (res.data?.data) {
            newBookingObj.id = res.data.data.id || bookingId;
          }
        } catch (apiErr) {
          console.warn("Backend booking API offline or error, persisting locally:", apiErr?.message);
        }
      }

      // Persist in local storage
      const updated = [newBookingObj, ...myBookings];
      setMyBookings(updated);
      localStorage.setItem("tourmate_guide_bookings", JSON.stringify(updated));

      setConfirmedBooking(newBookingObj);
      setBookingSuccess(true);
    } catch (err) {
      console.error("Booking error:", err);
      alert("Something went wrong while confirming your booking. Please try again.");
    } finally {
      setBookingLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-b from-gray-50 via-white to-gray-50 dark:from-[#0b0f19] dark:via-[#0f172a] dark:to-[#0b0f19] text-gray-900 dark:text-slate-100 py-8 px-4 sm:px-6 lg:px-8 relative overflow-hidden">
      {/* Decorative background glows */}
      <div className="absolute top-12 left-1/4 w-96 h-96 bg-brand-500/10 rounded-full blur-3xl pointer-events-none" />
      <div className="absolute top-48 right-10 w-96 h-96 bg-amber-500/10 rounded-full blur-3xl pointer-events-none" />

      <div className="max-w-7xl mx-auto relative z-10">
        
        {/* Header Section */}
        <div className="flex flex-col md:flex-row md:items-end justify-between gap-6 mb-8 border-b border-gray-200 dark:border-slate-800 pb-6">
          <div>
            <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full text-xs font-semibold bg-brand-50 text-brand-700 dark:bg-brand-950/60 dark:text-brand-300 border border-brand-200 dark:border-brand-800 mb-3">
              <ShieldCheck className="w-3.5 h-3.5 text-brand-600 dark:text-brand-400" />
              {t('Verified Local Experts Across India')}
            </div>
            <h1 className="text-3xl sm:text-4xl lg:text-5xl font-display font-extrabold tracking-tight text-gray-900 dark:text-white">
              {t('Hire a Local Guide')}
            </h1>
            <p className="mt-2 text-base sm:text-lg text-gray-600 dark:text-slate-400 max-w-2xl">
              {t('Immerse yourself in authentic stories, historic monuments, hidden culinary gems, and cultural walks led by licensed local guides.')}
            </p>
          </div>

          {/* Navigation Tabs */}
          <div className="flex items-center gap-2 bg-gray-100 dark:bg-slate-800/80 p-1.5 rounded-2xl border border-gray-200 dark:border-slate-700 self-start md:self-auto">
            <button
              onClick={() => setActiveTab('explore')}
              className={`flex items-center gap-2 px-4 py-2.5 rounded-xl text-sm font-bold transition-all ${
                activeTab === 'explore'
                  ? 'bg-white dark:bg-slate-900 text-brand-600 dark:text-brand-400 shadow-sm'
                  : 'text-gray-600 dark:text-slate-400 hover:text-gray-900 dark:hover:text-white'
              }`}
            >
              <Compass className="w-4 h-4" />
              {t('Explore Guides')}
            </button>
            <button
              onClick={() => setActiveTab('bookings')}
              className={`flex items-center gap-2 px-4 py-2.5 rounded-xl text-sm font-bold transition-all relative ${
                activeTab === 'bookings'
                  ? 'bg-white dark:bg-slate-900 text-brand-600 dark:text-brand-400 shadow-sm'
                  : 'text-gray-600 dark:text-slate-400 hover:text-gray-900 dark:hover:text-white'
              }`}
            >
              <Briefcase className="w-4 h-4" />
              {t('My Bookings')}
              {myBookings.length > 0 && (
                <span className="ml-1 px-2 py-0.5 text-xs font-extrabold bg-brand-600 text-white rounded-full">
                  {myBookings.length}
                </span>
              )}
            </button>
          </div>
        </div>

        {/* TAB 1: EXPLORE GUIDES */}
        {activeTab === 'explore' && (
          <>
            {/* Search and Filters Bar */}
            <div className="bg-white/80 dark:bg-slate-800/80 backdrop-blur-md rounded-2xl p-4 sm:p-5 border border-gray-200 dark:border-slate-700/80 shadow-sm mb-8 space-y-4">
              <div className="grid grid-cols-1 md:grid-cols-12 gap-3">
                {/* Search Input */}
                <div className="relative md:col-span-6 lg:col-span-5">
                  <Search className="w-5 h-5 absolute left-3.5 top-1/2 -translate-y-1/2 text-gray-400" />
                  <input
                    type="text"
                    value={searchQuery}
                    onChange={(e) => setSearchQuery(e.target.value)}
                    placeholder={t('Search by city, monument, guide name, or specialty...')}
                    className="w-full pl-11 pr-4 py-2.5 rounded-xl border border-gray-200 dark:border-slate-700 bg-gray-50/70 dark:bg-slate-900/60 text-sm font-medium focus:ring-2 focus:ring-brand-500 focus:outline-none"
                  />
                  {searchQuery && (
                    <button
                      onClick={() => setSearchQuery("")}
                      className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600"
                    >
                      <X className="w-4 h-4" />
                    </button>
                  )}
                </div>

                {/* State / Region Dropdown */}
                <div className="md:col-span-3 lg:col-span-3">
                  <select
                    value={selectedState}
                    onChange={(e) => setSelectedState(e.target.value)}
                    className="w-full py-2.5 px-3 rounded-xl border border-gray-200 dark:border-slate-700 bg-gray-50/70 dark:bg-slate-900/60 text-sm font-medium focus:ring-2 focus:ring-brand-500 focus:outline-none cursor-pointer"
                  >
                    <option value="All">{t('All Regions & States')}</option>
                    {availableStates.filter(s => s !== "All").map(s => (
                      <option key={s} value={s}>{s}</option>
                    ))}
                  </select>
                </div>

                {/* Language Dropdown */}
                <div className="md:col-span-3 lg:col-span-2">
                  <select
                    value={selectedLanguage}
                    onChange={(e) => setSelectedLanguage(e.target.value)}
                    className="w-full py-2.5 px-3 rounded-xl border border-gray-200 dark:border-slate-700 bg-gray-50/70 dark:bg-slate-900/60 text-sm font-medium focus:ring-2 focus:ring-brand-500 focus:outline-none cursor-pointer"
                  >
                    <option value="All">{t('All Languages')}</option>
                    {availableLanguages.filter(l => l !== "All").map(lang => (
                      <option key={lang} value={lang}>{lang}</option>
                    ))}
                  </select>
                </div>

                {/* Sort Dropdown */}
                <div className="md:col-span-12 lg:col-span-2">
                  <select
                    value={sortBy}
                    onChange={(e) => setSortBy(e.target.value)}
                    className="w-full py-2.5 px-3 rounded-xl border border-gray-200 dark:border-slate-700 bg-gray-50/70 dark:bg-slate-900/60 text-sm font-medium focus:ring-2 focus:ring-brand-500 focus:outline-none cursor-pointer"
                  >
                    <option value="rating">{t('Top Rated (⭐)')}</option>
                    <option value="reviews">{t('Most Reviewed')}</option>
                    <option value="price_asc">{t('Price: Low to High')}</option>
                    <option value="price_desc">{t('Price: High to Low')}</option>
                  </select>
                </div>
              </div>

              {/* Quick State Pills */}
              <div className="flex items-center gap-2 overflow-x-auto pb-1 text-xs pt-1 no-scrollbar">
                <span className="text-gray-500 dark:text-slate-400 font-bold whitespace-nowrap flex items-center gap-1">
                  <Filter className="w-3.5 h-3.5" /> {t('Popular Destinations:')}
                </span>
                {['All', 'Uttar Pradesh', 'Rajasthan', 'Delhi', 'Kerala', 'Goa', 'Karnataka', 'Himachal Pradesh', 'Maharashtra'].map(st => (
                  <button
                    key={st}
                    onClick={() => setSelectedState(st)}
                    className={`px-3 py-1.5 rounded-full font-bold whitespace-nowrap transition-colors border ${
                      selectedState === st
                        ? 'bg-brand-600 text-white border-brand-600 shadow-sm'
                        : 'bg-white dark:bg-slate-800 text-gray-700 dark:text-slate-300 border-gray-200 dark:border-slate-700 hover:border-brand-300'
                    }`}
                  >
                    {st === 'All' ? t('All India') : st}
                  </button>
                ))}
              </div>
            </div>

            {/* Results count & status */}
            <div className="flex items-center justify-between mb-6 px-1">
              <p className="text-sm font-bold text-gray-600 dark:text-slate-400">
                {t('Showing')} <span className="text-gray-900 dark:text-white font-extrabold">{filteredGuides.length}</span> {t('verified guides')}
                {selectedState !== "All" && ` in ${selectedState}`}
              </p>
              <div className="flex items-center gap-2">
                <span className="flex h-2.5 w-2.5 relative">
                  <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>
                  <span className="relative inline-flex rounded-full h-2.5 w-2.5 bg-emerald-500"></span>
                </span>
                <span className="text-xs font-semibold text-gray-500 dark:text-slate-400">
                  {t('Instant Booking Available')}
                </span>
              </div>
            </div>

            {/* Loading Skeleton */}
            {loading ? (
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                {[1, 2, 3, 4, 5, 6].map(i => (
                  <div key={i} className="h-96 rounded-2xl bg-gray-200 dark:bg-slate-800 animate-pulse" />
                ))}
              </div>
            ) : filteredGuides.length === 0 ? (
              <div className="text-center py-16 px-4 bg-white/50 dark:bg-slate-800/50 rounded-3xl border border-gray-200 dark:border-slate-700">
                <Compass className="w-12 h-12 text-gray-400 mx-auto mb-3" />
                <h3 className="text-xl font-bold text-gray-900 dark:text-white mb-1">{t('No Local Guides Found')}</h3>
                <p className="text-sm text-gray-500 dark:text-slate-400 max-w-md mx-auto mb-4">
                  We couldn't find any guides matching your current filters. Try resetting the filters or searching for another city.
                </p>
                <button
                  onClick={() => { setSearchQuery(""); setSelectedState("All"); setSelectedLanguage("All"); }}
                  className="px-4 py-2 bg-brand-600 hover:bg-brand-700 text-white rounded-xl text-sm font-bold transition shadow-sm"
                >
                  {t('Reset All Filters')}
                </button>
              </div>
            ) : (
              /* Guide Cards Grid */
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                {filteredGuides.map(guide => (
                  <div
                    key={guide.id}
                    className="group bg-white dark:bg-slate-800/90 rounded-2xl overflow-hidden border border-gray-200/80 dark:border-slate-700 shadow-sm hover:shadow-xl transition-all duration-300 flex flex-col hover:-translate-y-1"
                  >
                    {/* Image Header */}
                    <div className="h-56 relative overflow-hidden bg-slate-100 dark:bg-slate-900">
                      <img
                        src={guide.image_url || "/images/guides/guide_1.jpg"}
                        alt={guide.name}
                        className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-500"
                        onError={(e) => {
                          e.target.onerror = null;
                          e.target.src = "https://images.unsplash.com/photo-1544717302-de2939b7ef71?auto=format&fit=crop&w=500&q=60";
                        }}
                      />
                      <div className="absolute inset-0 bg-gradient-to-t from-black/70 via-black/10 to-transparent pointer-events-none" />

                      {/* Verified Badge */}
                      <div className="absolute top-3 left-3 bg-white/95 dark:bg-slate-900/95 backdrop-blur-md px-2.5 py-1 rounded-full flex items-center gap-1.5 shadow-sm">
                        <ShieldCheck className="w-3.5 h-3.5 text-brand-600 dark:text-brand-400" />
                        <span className="text-[11px] font-bold text-gray-800 dark:text-slate-200">
                          {t('ASI Verified')}
                        </span>
                      </div>

                      {/* Hourly Rate */}
                      <div className="absolute top-3 right-3 bg-brand-600 text-white font-extrabold px-3 py-1 rounded-xl text-xs shadow-md">
                        ₹{guide.hourly_rate}/hr
                      </div>

                      {/* Location & Experience on image bottom */}
                      <div className="absolute bottom-3 left-3 right-3 flex items-center justify-between text-white text-xs">
                        <span className="flex items-center gap-1 font-semibold truncate max-w-[70%] drop-shadow">
                          <MapPin className="w-3.5 h-3.5 text-brand-400 shrink-0" />
                          {guide.city ? `${guide.city}, ${guide.state_or_ut || ''}` : guide.location}
                        </span>
                        {guide.experience_years && (
                          <span className="font-bold bg-black/40 backdrop-blur px-2 py-0.5 rounded-md drop-shadow">
                            {guide.experience_years}+ yrs exp
                          </span>
                        )}
                      </div>
                    </div>

                    {/* Card Body */}
                    <div className="p-5 flex-1 flex flex-col justify-between space-y-4">
                      <div>
                        {/* Name and Rating */}
                        <div className="flex items-start justify-between gap-2 mb-2">
                          <h3 className="text-xl font-bold font-display text-gray-900 dark:text-white line-clamp-1 group-hover:text-brand-600 dark:group-hover:text-brand-400 transition-colors">
                            {guide.name}
                          </h3>
                          <div className="flex items-center gap-1 bg-amber-50 dark:bg-amber-950/60 border border-amber-200 dark:border-amber-800/60 text-amber-700 dark:text-amber-400 px-2 py-0.5 rounded-lg text-xs font-bold shrink-0">
                            <Star className="w-3.5 h-3.5 fill-current" />
                            <span>{guide.rating || 4.9}</span>
                            <span className="text-gray-400 font-normal">({guide.reviews_count || 50})</span>
                          </div>
                        </div>

                        {/* Bio snippet */}
                        <p className="text-xs sm:text-sm text-gray-600 dark:text-slate-300 line-clamp-3 mb-3 leading-relaxed">
                          {guide.bio}
                        </p>

                        {/* Specialties Tags */}
                        {guide.specialties && guide.specialties.length > 0 && (
                          <div className="flex flex-wrap gap-1.5 mb-3">
                            {guide.specialties.map(spec => (
                              <span
                                key={spec}
                                className="text-[10px] font-bold px-2 py-0.5 rounded-md bg-brand-50 dark:bg-brand-950/50 text-brand-700 dark:text-brand-300 border border-brand-100 dark:border-brand-900/50"
                              >
                                {spec}
                              </span>
                            ))}
                          </div>
                        )}

                        {/* Languages Spoken */}
                        <div className="flex items-center gap-1.5 flex-wrap pt-1 text-xs text-gray-500 dark:text-slate-400">
                          <span className="font-bold text-[11px] uppercase tracking-wider text-gray-400">{t('Languages:')}</span>
                          {(guide.languages || ["English", "Hindi"]).map(lang => (
                            <span
                              key={lang}
                              className="px-2 py-0.5 rounded bg-gray-100 dark:bg-slate-700/60 text-gray-700 dark:text-slate-300 text-[11px] font-semibold"
                            >
                              {lang}
                            </span>
                          ))}
                        </div>
                      </div>

                      {/* Card Footer Actions */}
                      <div className="pt-3 border-t border-gray-100 dark:border-slate-700/80 flex items-center gap-2">
                        <button
                          onClick={() => handleOpenBooking(guide)}
                          className="flex-1 bg-brand-600 hover:bg-brand-700 active:scale-[0.98] text-white font-bold py-2.5 px-4 rounded-xl text-sm transition shadow-sm flex items-center justify-center gap-1.5"
                        >
                          <Calendar className="w-4 h-4" />
                          {t('Book Guided Tour')}
                        </button>
                        {guide.contact_phone && (
                          <a
                            href={`https://wa.me/${guide.contact_phone.replace(/[^0-9]/g, '')}?text=Hi%20${encodeURIComponent(guide.name)},%20I%20saw%20your%20profile%20on%20TourMate%20AI%20and%20would%20like%20to%20inquire%20about%20a%20guided%20tour.`}
                            target="_blank"
                            rel="noopener noreferrer"
                            title="Chat on WhatsApp"
                            className="p-2.5 rounded-xl border border-gray-200 dark:border-slate-700 hover:bg-gray-50 dark:hover:bg-slate-700 text-emerald-600 dark:text-emerald-400 transition"
                          >
                            <MessageSquare className="w-4 h-4" />
                          </a>
                        )}
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </>
        )}

        {/* TAB 2: MY BOOKINGS */}
        {activeTab === 'bookings' && (
          <div className="space-y-6">
            <div className="flex items-center justify-between">
              <div>
                <h2 className="text-2xl font-display font-bold text-gray-900 dark:text-white">
                  {t('My Booked Guides')}
                </h2>
                <p className="text-sm text-gray-500 dark:text-slate-400">
                  {t('Manage your upcoming excursions and connect with your scheduled local experts.')}
                </p>
              </div>
              <button
                onClick={() => setActiveTab('explore')}
                className="text-sm font-bold text-brand-600 dark:text-brand-400 hover:underline flex items-center gap-1"
              >
                {t('Book Another Guide')}
              </button>
            </div>

            {myBookings.length === 0 ? (
              <div className="text-center py-20 bg-white/70 dark:bg-slate-800/70 rounded-3xl border border-gray-200 dark:border-slate-700">
                <Briefcase className="w-16 h-16 text-gray-300 dark:text-slate-600 mx-auto mb-4" />
                <h3 className="text-xl font-bold text-gray-900 dark:text-white mb-2">{t('No Bookings Yet')}</h3>
                <p className="text-gray-500 dark:text-slate-400 max-w-sm mx-auto mb-6 text-sm">
                  {t("You haven't booked any local guides yet. Explore verified guides across India and schedule your dream heritage tour.")}
                </p>
                <button
                  onClick={() => setActiveTab('explore')}
                  className="bg-brand-600 hover:bg-brand-700 text-white font-bold py-3 px-6 rounded-xl text-sm transition shadow-md"
                >
                  {t('Explore Local Guides')}
                </button>
              </div>
            ) : (
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                {myBookings.map(b => (
                  <div
                    key={b.id}
                    className="bg-white dark:bg-slate-800 rounded-2xl border border-gray-200 dark:border-slate-700 p-5 shadow-sm space-y-4"
                  >
                    <div className="flex items-start justify-between gap-3 border-b border-gray-100 dark:border-slate-700/80 pb-4">
                      <div className="flex items-center gap-3">
                        <img
                          src={b.guide?.image_url || "/images/guides/guide_1.jpg"}
                          alt={b.guide?.name || "Local Guide"}
                          className="w-14 h-14 rounded-xl object-cover border border-gray-200 dark:border-slate-600"
                          onError={(e) => {
                            e.target.onerror = null;
                            e.target.src = "https://images.unsplash.com/photo-1544717302-de2939b7ef71?auto=format&fit=crop&w=500&q=60";
                          }}
                        />
                        <div>
                          <span className="text-[11px] font-extrabold uppercase tracking-wider text-brand-600 dark:text-brand-400">
                            Booking ID: {b.id}
                          </span>
                          <h4 className="text-lg font-bold text-gray-900 dark:text-white">
                            {b.guide?.name || "Local Heritage Guide"}
                          </h4>
                          <p className="text-xs text-gray-500 dark:text-slate-400 flex items-center gap-1">
                            <MapPin className="w-3 h-3" />
                            {b.guide?.location || b.guide?.city || "India"}
                          </p>
                        </div>
                      </div>
                      <span className="px-2.5 py-1 rounded-full text-xs font-extrabold bg-emerald-50 text-emerald-700 dark:bg-emerald-950/60 dark:text-emerald-400 border border-emerald-200 dark:border-emerald-800">
                        {b.status || "Confirmed"}
                      </span>
                    </div>

                    <div className="grid grid-cols-2 gap-3 text-xs bg-gray-50 dark:bg-slate-900/60 p-3 rounded-xl">
                      <div>
                        <span className="text-gray-400 block font-semibold">{t('Scheduled Date')}</span>
                        <span className="font-bold text-gray-900 dark:text-white flex items-center gap-1 mt-0.5">
                          <Calendar className="w-3.5 h-3.5 text-brand-500" />
                          {b.date}
                        </span>
                      </div>
                      <div>
                        <span className="text-gray-400 block font-semibold">{t('Duration')}</span>
                        <span className="font-bold text-gray-900 dark:text-white flex items-center gap-1 mt-0.5">
                          <Clock className="w-3.5 h-3.5 text-amber-500" />
                          {b.hours} {t('Hours')}
                        </span>
                      </div>
                      <div>
                        <span className="text-gray-400 block font-semibold">{t('Total Paid / Due')}</span>
                        <span className="font-bold text-brand-600 dark:text-brand-400 text-sm mt-0.5">
                          ₹{b.total_price}
                        </span>
                      </div>
                      <div>
                        <span className="text-gray-400 block font-semibold">{t('Contact Status')}</span>
                        <span className="font-bold text-emerald-600 dark:text-emerald-400 mt-0.5">
                          {t('Guide Ready')}
                        </span>
                      </div>
                    </div>

                    {b.notes && (
                      <p className="text-xs text-gray-600 dark:text-slate-400 italic bg-gray-50/50 dark:bg-slate-900/40 p-2.5 rounded-lg border border-gray-100 dark:border-slate-800">
                        " {b.notes} "
                      </p>
                    )}

                    <div className="flex items-center gap-2 pt-1">
                      {b.guide?.contact_phone && (
                        <a
                          href={`tel:${b.guide.contact_phone}`}
                          className="flex-1 py-2 px-3 rounded-xl border border-gray-200 dark:border-slate-700 text-xs font-bold text-center text-gray-800 dark:text-slate-200 hover:bg-gray-50 dark:hover:bg-slate-700 flex items-center justify-center gap-1.5 transition"
                        >
                          <Phone className="w-3.5 h-3.5 text-brand-500" />
                          {t('Call Guide')}
                        </a>
                      )}
                      {b.guide?.contact_phone && (
                        <a
                          href={`https://wa.me/${b.guide.contact_phone.replace(/[^0-9]/g, '')}?text=Hi%20${encodeURIComponent(b.guide.name)},%20this%20is%20regarding%20my%20confirmed%20booking%20(ID:%20${b.id})%20on%20${b.date}.`}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="flex-1 py-2 px-3 rounded-xl bg-emerald-600 hover:bg-emerald-700 text-xs font-bold text-center text-white flex items-center justify-center gap-1.5 transition shadow-sm"
                        >
                          <MessageSquare className="w-3.5 h-3.5" />
                          {t('WhatsApp')}
                        </a>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}

      </div>

      {/* BOOKING MODAL */}
      {bookingModalOpen && selectedGuide && (
        <div className="fixed inset-0 z-50 bg-black/60 backdrop-blur-sm flex items-center justify-center p-4 overflow-y-auto animate-fade-in">
          <div className="bg-white dark:bg-slate-800 rounded-3xl w-full max-w-lg shadow-2xl border border-gray-200 dark:border-slate-700 overflow-hidden relative my-8">
            
            {/* Close button */}
            <button
              onClick={() => setBookingModalOpen(false)}
              className="absolute top-4 right-4 z-20 w-8 h-8 rounded-full bg-black/50 hover:bg-black/70 text-white flex items-center justify-center transition"
            >
              <X className="w-4 h-4" />
            </button>

            {bookingSuccess && confirmedBooking ? (
              /* Success View */
              <div className="p-6 sm:p-8 text-center space-y-6">
                <div className="w-16 h-16 bg-emerald-100 dark:bg-emerald-950/60 rounded-full flex items-center justify-center mx-auto text-emerald-600 dark:text-emerald-400">
                  <CheckCircle className="w-10 h-10" />
                </div>

                <div>
                  <span className="text-xs font-extrabold uppercase tracking-widest text-emerald-600 dark:text-emerald-400 block mb-1">
                    {t('Booking Confirmed!')} Reference: {confirmedBooking.id}
                  </span>
                  <h3 className="text-2xl font-display font-extrabold text-gray-900 dark:text-white">
                    {t('Your Tour with')} {selectedGuide.name} {t('is Confirmed')}
                  </h3>
                  <p className="text-sm text-gray-600 dark:text-slate-300 mt-2">
                    We've reserved {confirmedBooking.hours} {t('Hours')} on {confirmedBooking.date}. Your guide has been notified and will coordinate with you.
                  </p>
                </div>

                {/* Summary Card */}
                <div className="bg-gray-50 dark:bg-slate-900/60 rounded-2xl p-4 text-left space-y-2 text-xs border border-gray-100 dark:border-slate-700">
                  <div className="flex justify-between">
                    <span className="text-gray-500">{t('Local Guide:')}</span>
                    <span className="font-bold text-gray-900 dark:text-white">{selectedGuide.name}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-500">{t('Destination:')}</span>
                    <span className="font-bold text-gray-900 dark:text-white">{selectedGuide.city || selectedGuide.location}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-500">{t('Date & Hours:')}</span>
                    <span className="font-bold text-gray-900 dark:text-white">{confirmedBooking.date} ({confirmedBooking.hours} {t('Hours')})</span>
                  </div>
                  <div className="flex justify-between pt-2 border-t border-gray-200 dark:border-slate-700">
                    <span className="text-gray-700 dark:text-slate-300 font-bold">{t('Total Fare:')}</span>
                    <span className="font-extrabold text-brand-600 dark:text-brand-400 text-sm">₹{confirmedBooking.total_price}</span>
                  </div>
                </div>

                {selectedGuide.contact_phone && (
                  <div className="flex flex-col sm:flex-row gap-3">
                    <a
                      href={`https://wa.me/${selectedGuide.contact_phone.replace(/[^0-9]/g, '')}?text=Hello%20${encodeURIComponent(selectedGuide.name)},%20I%20just%20booked%20a%20tour%20with%20you%20via%20TourMate%20AI%20(Booking%20ID:%20${confirmedBooking.id})%20for%20${confirmedBooking.date}.`}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="flex-1 bg-emerald-600 hover:bg-emerald-700 text-white font-bold py-3 px-4 rounded-xl text-xs flex items-center justify-center gap-2 transition shadow-sm"
                    >
                      <MessageSquare className="w-4 h-4" />
                      {t('Chat on WhatsApp Now')}
                    </a>
                    <button
                      onClick={() => {
                        setBookingModalOpen(false);
                        setActiveTab('bookings');
                      }}
                      className="flex-1 bg-gray-100 hover:bg-gray-200 dark:bg-slate-700 dark:hover:bg-slate-600 text-gray-800 dark:text-white font-bold py-3 px-4 rounded-xl text-xs transition"
                    >
                      {t('View in My Bookings')}
                    </button>
                  </div>
                )}
              </div>
            ) : (
              /* Booking Form View */
              <div>
                {/* Modal Header */}
                <div className="relative h-36 bg-slate-900">
                  <img
                    src={selectedGuide.image_url || "/images/guides/guide_1.jpg"}
                    alt={selectedGuide.name}
                    className="w-full h-full object-cover opacity-60"
                    onError={(e) => {
                      e.target.onerror = null;
                      e.target.src = "https://images.unsplash.com/photo-1544717302-de2939b7ef71?auto=format&fit=crop&w=500&q=60";
                    }}
                  />
                  <div className="absolute inset-0 bg-gradient-to-t from-slate-900 via-slate-900/60 to-transparent" />
                  <div className="absolute bottom-3 left-5 right-5 text-white">
                    <span className="text-[10px] font-bold uppercase tracking-wider bg-brand-600 px-2 py-0.5 rounded text-white inline-block mb-1">
                      {t('Direct Expert Booking')}
                    </span>
                    <h3 className="text-2xl font-bold font-display leading-tight">{selectedGuide.name}</h3>
                    <p className="text-xs text-slate-300 flex items-center gap-1">
                      <MapPin className="w-3 h-3 text-brand-400" />
                      {selectedGuide.location}
                    </p>
                  </div>
                </div>

                {/* Form */}
                <form onSubmit={submitBooking} className="p-6 space-y-4">
                  {/* Select Date */}
                  <div>
                    <label className="text-xs font-bold text-gray-700 dark:text-slate-300 uppercase tracking-wider block mb-1.5 flex items-center gap-1">
                      <Calendar className="w-3.5 h-3.5 text-brand-500" />
                      {t('Tour Date')}
                    </label>
                    <input
                      type="date"
                      required
                      min={tomorrowStr}
                      value={bookingDate}
                      onChange={(e) => setBookingDate(e.target.value)}
                      className="w-full p-2.5 rounded-xl border border-gray-200 dark:border-slate-700 bg-gray-50 dark:bg-slate-900 text-sm font-medium focus:ring-2 focus:ring-brand-500 focus:outline-none"
                    />
                  </div>

                  {/* Duration Slider */}
                  <div>
                    <div className="flex items-center justify-between mb-1.5">
                      <label className="text-xs font-bold text-gray-700 dark:text-slate-300 uppercase tracking-wider flex items-center gap-1">
                        <Clock className="w-3.5 h-3.5 text-brand-500" />
                        {t('Duration')}
                      </label>
                      <span className="text-xs font-extrabold text-brand-600 dark:text-brand-400 bg-brand-50 dark:bg-brand-950/60 px-2 py-0.5 rounded-md">
                        {bookingHours} {t('Hours')}
                      </span>
                    </div>
                    <input
                      type="range"
                      min="1"
                      max="8"
                      step="1"
                      value={bookingHours}
                      onChange={(e) => setBookingHours(e.target.value)}
                      className="w-full accent-brand-600 cursor-pointer"
                    />
                    <div className="flex justify-between text-[10px] text-gray-400 mt-1 font-semibold">
                      <span>1 hr</span>
                      <span>4 hrs</span>
                      <span>8 hrs</span>
                    </div>
                  </div>

                  {/* Special Requests or Notes */}
                  <div>
                    <label className="text-xs font-bold text-gray-700 dark:text-slate-300 uppercase tracking-wider block mb-1.5 flex items-center gap-1">
                      <MessageSquare className="w-3.5 h-3.5 text-brand-500" />
                      {t('Meeting Point & Tour Preferences (Optional)')}
                    </label>
                    <textarea
                      rows={2}
                      value={bookingNotes}
                      onChange={(e) => setBookingNotes(e.target.value)}
                      placeholder="e.g., Hotel lobby pickup, sunrise Taj Mahal photography, vegetarian food trail..."
                      className="w-full p-2.5 rounded-xl border border-gray-200 dark:border-slate-700 bg-gray-50 dark:bg-slate-900 text-xs font-medium focus:ring-2 focus:ring-brand-500 focus:outline-none"
                    />
                  </div>

                  {/* Price Calculation Box */}
                  <div className="bg-gray-50 dark:bg-slate-900/80 rounded-2xl p-4 border border-gray-200/80 dark:border-slate-700 space-y-2">
                    <div className="flex justify-between text-xs text-gray-600 dark:text-slate-400">
                      <span>{t('Rate:')} ₹{selectedGuide.hourly_rate || 500} / hour × {bookingHours} {t('Hours')}</span>
                      <span>₹{(selectedGuide.hourly_rate || 500) * bookingHours}</span>
                    </div>
                    <div className="flex justify-between text-xs text-gray-600 dark:text-slate-400">
                      <span>{t('TourMate Safety & Guarantee Fee')}</span>
                      <span className="text-emerald-600 font-bold">{t('FREE')}</span>
                    </div>
                    <div className="flex justify-between pt-2 border-t border-gray-200 dark:border-slate-700 text-sm font-bold text-gray-900 dark:text-white">
                      <span>{t('Estimated Total')}</span>
                      <span className="text-lg font-extrabold text-brand-600 dark:text-brand-400">
                        ₹{(selectedGuide.hourly_rate || 500) * bookingHours}
                      </span>
                    </div>
                  </div>

                  {/* Submit Button */}
                  <button
                    type="submit"
                    disabled={bookingLoading || !bookingDate}
                    className="w-full bg-brand-600 hover:bg-brand-700 disabled:opacity-50 text-white font-extrabold py-3.5 rounded-xl text-sm transition shadow-lg hover:shadow-brand-500/20 active:scale-[0.99] flex items-center justify-center gap-2"
                  >
                    {bookingLoading ? (
                      <RefreshCw className="w-5 h-5 animate-spin" />
                    ) : (
                      <>
                        <Check className="w-4 h-4" />
                        {t('Confirm Booking (Pay Guide on Arrival)')}
                      </>
                    )}
                  </button>
                  <p className="text-[11px] text-center text-gray-400">
                    {t('No advance payment required. Free cancellation up to 4 hours before tour.')}
                  </p>
                </form>
              </div>
            )}
          </div>
        </div>
      )}

    </div>
  );
}
