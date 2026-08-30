import { useState, useEffect } from "react";
import axios from "axios";
import { useAuth } from "../context/AuthContext";
import { useNavigate } from "react-router-dom";

export default function ItineraryBuilder() {
  const { token } = useAuth();
  const navigate = useNavigate();
  
  const [allPlaces, setAllPlaces] = useState([]);
  const [search, setSearch] = useState("");
  const [selectedPlaces, setSelectedPlaces] = useState([]);
  
  const [days, setDays] = useState(3);
  const [startTime, setStartTime] = useState("09:00");
  const [endTime, setEndTime] = useState("20:00");
  const [title, setTitle] = useState("My Awesome Trip");
  
  const [generatedItinerary, setGeneratedItinerary] = useState(null);
  const [loadingPlaces, setLoadingPlaces] = useState(false);
  const [generating, setGenerating] = useState(false);
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    const fetchPlaces = async () => {
      setLoadingPlaces(true);
      try {
        const res = await axios.get(`${import.meta.env.VITE_API_BASE_URL}/places`, {
          headers: { Authorization: `Bearer ${token}` }
        });
        setAllPlaces(res.data.data || []);
      } catch (err) {
        console.error(err);
      } finally {
        setLoadingPlaces(false);
      }
    };
    if (token) fetchPlaces();
  }, [token]);

  const handleAddPlace = (place) => {
    if (!selectedPlaces.find(p => p.id === place.id)) {
      setSelectedPlaces([...selectedPlaces, place]);
      setGeneratedItinerary(null);
    }
  };

  const handleRemovePlace = (id) => {
    setSelectedPlaces(selectedPlaces.filter(p => p.id !== id));
    setGeneratedItinerary(null);
  };

  const handleGenerate = async () => {
    if (selectedPlaces.length === 0) return;
    setGenerating(true);
    try {
      const res = await axios.post(
        `${import.meta.env.VITE_API_BASE_URL}/itineraries/generate`,
        {
          place_ids: selectedPlaces.map(p => p.id),
          days: parseInt(days),
          start_time: startTime,
          end_time: endTime
        },
        { headers: { Authorization: `Bearer ${token}` } }
      );
      setGeneratedItinerary(res.data.data);
    } catch (err) {
      console.error(err);
      const msg = err.response?.data?.detail || "Failed to generate itinerary. Please try again.";
      alert(msg);
    } finally {
      setGenerating(false);
    }
  };

  const handleSave = async () => {
    if (!generatedItinerary) return;
    setSaving(true);
    try {
      await axios.post(
        `${import.meta.env.VITE_API_BASE_URL}/itineraries`,
        {
          title: title,
          days: parseInt(days),
          schedule: generatedItinerary
        },
        { headers: { Authorization: `Bearer ${token}` } }
      );
      alert("Itinerary saved successfully!");
      navigate("/my-itineraries");
    } catch (err) {
      console.error(err);
      alert("Failed to save itinerary.");
    } finally {
      setSaving(false);
    }
  };

  const filteredPlaces = allPlaces.filter(p => 
    p.name.toLowerCase().includes(search.toLowerCase()) && 
    !selectedPlaces.find(sp => sp.id === p.id)
  );

  return (
    <div className="flex flex-col md:flex-row h-[calc(100vh-64px)] bg-gray-50 dark:bg-[#0f172a] overflow-hidden relative">
      
      {/* Animated background blobs */}
      <div className="absolute top-20 right-20 w-96 h-96 bg-accent-500/20 rounded-full mix-blend-multiply filter blur-3xl animate-blob pointer-events-none"></div>
      <div className="absolute bottom-20 left-1/3 w-96 h-96 bg-brand-400/20 rounded-full mix-blend-multiply filter blur-3xl animate-blob animation-delay-2000 pointer-events-none"></div>

      {/* Sidebar Left: Form */}
      <div className="w-full md:w-[420px] glass border-r border-white/20 dark:border-slate-700/50 flex flex-col z-10 shrink-0">
        <div className="p-6 bg-gradient-to-r from-brand-800 to-brand-600 border-b border-brand-700 relative overflow-hidden">
          <div className="absolute top-0 right-0 w-32 h-32 bg-white/10 rounded-full -translate-y-1/2 translate-x-1/3 blur-xl"></div>
          <h1 className="text-2xl font-display font-extrabold text-white tracking-tight relative z-10">AI Trip Builder ✨</h1>
          <p className="text-sm text-brand-100 mt-1 relative z-10 font-light">Let Gemini plan your perfect itinerary</p>
        </div>
        
        <div className="p-6 flex-1 overflow-y-auto space-y-8 custom-scrollbar">
          {/* Settings */}
          <div className="space-y-4 animate-fade-in-up-delay-1">
            <h2 className="text-xs font-bold text-gray-500 dark:text-slate-400 uppercase tracking-widest mb-3">Trip Settings</h2>
            <div className="grid grid-cols-2 gap-4">
              <div className="glass rounded-xl p-3 border border-gray-100 dark:border-slate-700/50 shadow-sm focus-within:ring-2 focus-within:ring-brand-400 transition-all">
                <label className="text-[10px] font-bold text-brand-600 dark:text-brand-400 uppercase tracking-wider block mb-1">Days</label>
                <input type="number" min="1" max="14" value={days} onChange={e => setDays(e.target.value)} className="w-full bg-transparent border-none p-0 text-gray-800 dark:text-slate-100 font-semibold focus:ring-0 outline-none" />
              </div>
            </div>
            <div className="grid grid-cols-2 gap-4">
              <div className="glass rounded-xl p-3 border border-gray-100 dark:border-slate-700/50 shadow-sm focus-within:ring-2 focus-within:ring-brand-400 transition-all">
                <label className="text-[10px] font-bold text-brand-600 dark:text-brand-400 uppercase tracking-wider block mb-1">Start Time</label>
                <input type="time" value={startTime} onChange={e => setStartTime(e.target.value)} className="w-full bg-transparent border-none p-0 text-gray-800 dark:text-slate-100 font-semibold focus:ring-0 outline-none" />
              </div>
              <div className="glass rounded-xl p-3 border border-gray-100 dark:border-slate-700/50 shadow-sm focus-within:ring-2 focus-within:ring-brand-400 transition-all">
                <label className="text-[10px] font-bold text-brand-600 dark:text-brand-400 uppercase tracking-wider block mb-1">End Time</label>
                <input type="time" value={endTime} onChange={e => setEndTime(e.target.value)} className="w-full bg-transparent border-none p-0 text-gray-800 dark:text-slate-100 font-semibold focus:ring-0 outline-none" />
              </div>
            </div>
          </div>

          {/* Selected Places */}
          <div className="animate-fade-in-up-delay-1">
            <h2 className="text-xs font-bold text-gray-500 dark:text-slate-400 uppercase tracking-widest mb-3 flex items-center justify-between">
              Must-Visit Places
              <span className="bg-brand-100 dark:bg-brand-900/40 text-brand-700 dark:text-brand-300 px-2 py-0.5 rounded-full text-[10px] font-black">{selectedPlaces.length}</span>
            </h2>
            <div className="space-y-2 max-h-40 overflow-y-auto custom-scrollbar pr-2">
              {selectedPlaces.length === 0 ? (
                <div className="text-sm text-gray-400 dark:text-slate-500 italic p-4 text-center border border-dashed border-gray-200 dark:border-slate-700 rounded-xl">No places selected yet. Search below!</div>
              ) : (
                selectedPlaces.map(p => (
                  <div key={p.id} className="flex justify-between items-center glass border border-gray-100 dark:border-slate-700/50 p-2.5 rounded-xl shadow-sm group transition-all hover:border-brand-200">
                    <span className="text-sm font-semibold text-gray-800 dark:text-slate-200 truncate pr-2">{p.name}</span>
                    <button onClick={() => handleRemovePlace(p.id)} className="text-gray-400 hover:text-red-500 hover:bg-red-50 dark:hover:bg-red-900/30 rounded-lg p-1.5 transition-colors">
                      <svg xmlns="http://www.w3.org/2000/svg" className="h-4 w-4" viewBox="0 0 20 20" fill="currentColor"><path fillRule="evenodd" d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z" clipRule="evenodd" /></svg>
                    </button>
                  </div>
                ))
              )}
            </div>
          </div>

          {/* Search Places */}
          <div className="animate-fade-in-up-delay-2">
            <div className="relative mb-3">
              <span className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400 text-sm">🔍</span>
              <input 
                type="text" placeholder="Search destinations..." value={search} onChange={e => setSearch(e.target.value)}
                className="w-full pl-9 pr-4 py-2.5 glass border-gray-200 dark:border-slate-700 rounded-xl text-sm focus:ring-2 focus:ring-brand-400 outline-none transition-all dark:text-white"
              />
            </div>
            <div className="max-h-48 overflow-y-auto space-y-1.5 custom-scrollbar pr-2">
              {loadingPlaces ? (
                <div className="text-center text-sm text-gray-400 py-4 animate-pulse">Loading places...</div>
              ) : filteredPlaces.length === 0 ? (
                <div className="text-center text-sm text-gray-400 py-4">No matching places found.</div>
              ) : filteredPlaces.map(p => (
                <button key={p.id} onClick={() => handleAddPlace(p)} className="w-full text-left flex justify-between items-center p-3 hover:bg-brand-50 dark:hover:bg-brand-900/20 rounded-xl text-sm border border-transparent hover:border-brand-100 dark:hover:border-brand-800 transition-all group">
                  <span className="truncate pr-2 font-medium text-gray-700 dark:text-slate-300 group-hover:text-brand-700 dark:group-hover:text-brand-300">{p.name}</span>
                  <span className="text-brand-400 group-hover:text-brand-600 bg-white dark:bg-slate-800 rounded-full p-1 shadow-sm font-bold">＋</span>
                </button>
              ))}
            </div>
          </div>
        </div>

        <div className="p-6 bg-white/50 dark:bg-slate-800/50 backdrop-blur-md border-t border-gray-100 dark:border-slate-700/50 z-20 relative">
          <button
            onClick={handleGenerate}
            disabled={generating || selectedPlaces.length === 0}
            className="w-full bg-gradient-to-r from-brand-600 to-accent-600 hover:from-brand-500 hover:to-accent-500 text-white font-bold py-3.5 px-4 rounded-xl shadow-lg hover:shadow-xl transition-all duration-300 disabled:opacity-50 disabled:transform-none transform hover:-translate-y-0.5 flex justify-center items-center gap-2"
          >
            {generating ? (
              <span className="flex items-center gap-2">
                <svg className="animate-spin h-5 w-5 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24"><circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle><path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path></svg>
                Crafting magic...
              </span>
            ) : "✨ Generate AI Itinerary"}
          </button>
        </div>
      </div>
      
      {/* Main Right: Results */}
      <div className="flex-1 overflow-y-auto p-4 md:p-8 relative z-10 custom-scrollbar">
        {!generatedItinerary ? (
          <div className="h-full flex flex-col items-center justify-center text-gray-400 space-y-6 animate-fade-in-up">
            <div className="w-32 h-32 bg-brand-50 dark:bg-slate-800 rounded-full flex items-center justify-center shadow-inner border border-brand-100 dark:border-slate-700">
              <span className="text-6xl animate-bounce">🗺️</span>
            </div>
            <div className="text-center">
              <h2 className="text-2xl font-display font-bold text-gray-700 dark:text-slate-300 mb-2">Your blank canvas awaits</h2>
              <p className="text-gray-500 max-w-md mx-auto">Select your favorite places on the left, adjust your times, and let our AI craft the perfect minute-by-minute adventure for you.</p>
            </div>
          </div>
        ) : (
          <div className="max-w-4xl mx-auto glass rounded-3xl shadow-xl border border-white/20 dark:border-slate-700 overflow-hidden animate-fade-in-up">
            {/* Header Banner */}
            <div className="bg-gradient-to-r from-accent-600 to-brand-600 p-8 sm:p-10 relative overflow-hidden text-white">
              <div className="absolute top-0 right-0 w-64 h-64 bg-white/10 rounded-full -translate-y-1/2 translate-x-1/3 blur-2xl pointer-events-none"></div>
              
              <div className="flex flex-col md:flex-row md:items-end justify-between gap-6 relative z-10">
                <div className="flex-1">
                  <span className="text-brand-100 font-bold tracking-widest text-xs uppercase mb-2 block">Your AI-Generated Plan</span>
                  <input 
                    type="text" 
                    value={title} 
                    onChange={e => setTitle(e.target.value)}
                    className="text-3xl sm:text-4xl font-display font-extrabold bg-transparent border-b-2 border-transparent hover:border-white/30 focus:border-white focus:bg-white/10 rounded-t px-1 py-2 outline-none w-full transition-all text-white placeholder-brand-200"
                    placeholder="Name your amazing trip..."
                  />
                </div>
                <button 
                  onClick={handleSave}
                  disabled={saving}
                  className="bg-white text-brand-700 hover:bg-gray-50 px-8 py-3 rounded-xl font-bold shadow-lg transition-all duration-300 transform hover:-translate-y-1 disabled:opacity-70 disabled:transform-none shrink-0"
                >
                  {saving ? "Saving..." : "💾 Save to Profile"}
                </button>
              </div>
            </div>

            <div className="p-6 sm:p-10 space-y-12 bg-white/50 dark:bg-slate-900/50">
              {generatedItinerary.map((dayPlan, idx) => (
                <div key={idx} className="relative">
                  <h3 className="text-2xl font-display font-black text-transparent bg-clip-text bg-gradient-to-r from-brand-600 to-accent-600 mb-6 flex items-center gap-3">
                    <span className="bg-gradient-to-r from-brand-600 to-accent-600 text-white w-10 h-10 rounded-xl flex items-center justify-center text-lg shadow-md">
                      {dayPlan.day}
                    </span>
                    Day {dayPlan.day}
                  </h3>
                  
                  <div className="space-y-6 pl-5 sm:pl-10 relative">
                    {/* Continuous vertical timeline line */}
                    <div className="absolute top-4 bottom-4 left-[27px] sm:left-[47px] w-0.5 bg-gradient-to-b from-brand-300 via-accent-300 to-transparent"></div>
                    
                    {dayPlan.activities?.map((act, i) => (
                      <div key={i} className="relative z-10 group">
                        {/* Timeline dot */}
                        <div className="absolute w-4 h-4 bg-white dark:bg-slate-800 rounded-full -left-[19px] top-4 border-4 border-brand-500 shadow-sm dark:shadow-none group-hover:scale-125 transition-transform duration-300 group-hover:border-accent-500"></div>
                        
                        <div className="glass bg-white dark:bg-slate-800 rounded-2xl p-5 border border-gray-100 dark:border-slate-700 hover:shadow-xl dark:hover:shadow-brand-900/20 hover:-translate-y-1 transition-all duration-300 ml-4">
                          <div className="flex flex-col sm:flex-row sm:justify-between sm:items-start gap-2 mb-2">
                            <span className="font-bold font-display text-gray-900 dark:text-white text-xl">{act.name}</span>
                            <span className="text-brand-700 dark:text-brand-300 font-bold bg-brand-50 dark:bg-brand-900/40 px-3 py-1 rounded-lg text-sm shrink-0 border border-brand-100 dark:border-brand-800 shadow-sm self-start">
                              {act.time}
                            </span>
                          </div>
                          <p className="text-gray-600 dark:text-slate-300 text-sm leading-relaxed mt-2">{act.description}</p>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
