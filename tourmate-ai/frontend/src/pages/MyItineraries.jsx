import { useState, useEffect } from "react";
import axios from "axios";
import { API_BASE_URL } from "../api/axios";
import { useAuth } from "../context/AuthContext";
import { Link } from "react-router-dom";
import ShareModal from "../components/ShareModal";
import {
  getOfflineItineraries,
  saveItineraryOffline,
  removeOfflineItinerary,
  exportItineraryJSON,
  printItineraryDocument
} from "../services/offlineService";

export default function MyItineraries() {
  const { token } = useAuth();
  const [itineraries, setItineraries] = useState([]);
  const [loading, setLoading] = useState(true);
  const [offlineIds, setOfflineIds] = useState(new Set());
  const [activeTab, setActiveTab] = useState("all"); // "all" | "offline"
  
  // Share modal state
  const [shareData, setShareData] = useState({
    isOpen: false,
    title: "",
    text: "",
    url: ""
  });

  useEffect(() => {
    fetchItineraries();
    refreshOfflineStatus();
  }, [token]);

  const refreshOfflineStatus = () => {
    const offlineList = getOfflineItineraries();
    setOfflineIds(new Set(offlineList.map(item => item.id)));
  };

  const fetchItineraries = async () => {
    setLoading(true);
    try {
      const res = await axios.get(`${API_BASE_URL}/itineraries`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setItineraries(res.data.data || []);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const handleDelete = async (id) => {
    if (!window.confirm("Are you sure you want to delete this itinerary?")) return;
    try {
      await axios.delete(`${API_BASE_URL}/itineraries/${id}`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      removeOfflineItinerary(id);
      fetchItineraries();
      refreshOfflineStatus();
    } catch (err) {
      console.error(err);
      alert("Failed to delete.");
    }
  };

  const handleToggleOffline = (itinerary) => {
    if (offlineIds.has(itinerary.id)) {
      removeOfflineItinerary(itinerary.id);
    } else {
      saveItineraryOffline(itinerary);
    }
    refreshOfflineStatus();
  };

  const handleOpenShare = (itinerary) => {
    const stopsCount = itinerary.schedule
      ? itinerary.schedule.reduce((acc, d) => acc + (d.activities?.length || 0), 0)
      : 0;
    setShareData({
      isOpen: true,
      title: `${itinerary.title} (${itinerary.days} Days)`,
      text: `🗺️ Check out my ${itinerary.days}-day tour "${itinerary.title}" with ${stopsCount} planned activities on TourMate!`,
      url: window.location.href
    });
  };

  // Determine which list to display
  const offlineItems = getOfflineItineraries();
  const displayedItineraries = activeTab === "offline" 
    ? offlineItems 
    : itineraries;

  if (loading) {
    return (
      <div className="p-12 text-center text-gray-500 dark:text-slate-400">
        <div className="inline-block animate-spin rounded-full h-8 w-8 border-4 border-brand-500 border-t-transparent mb-3"></div>
        <p>Loading your trips...</p>
      </div>
    );
  }

  return (
    <div className="max-w-6xl mx-auto p-4 md:p-8">
      {/* Header */}
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4 mb-6">
        <div>
          <h1 className="text-3xl font-bold text-gray-900 dark:text-white">My Itineraries</h1>
          <p className="text-gray-500 dark:text-slate-400 mt-1">
            Manage your AI-crafted trips • Offline travel pass enabled for low-network areas
          </p>
        </div>
        <div className="flex items-center gap-3">
          <Link
            to="/itinerary-builder"
            className="bg-brand-600 hover:bg-brand-700 text-white px-4 py-2 rounded-xl shadow font-semibold transition-colors flex items-center gap-1.5"
          >
            <span>＋</span> Create New Trip
          </Link>
        </div>
      </div>

      {/* Mode Filter Tabs: All vs Offline */}
      <div className="flex items-center gap-2 mb-8 bg-gray-100 dark:bg-slate-800 p-1.5 rounded-2xl w-fit border border-gray-200 dark:border-slate-700">
        <button
          onClick={() => setActiveTab("all")}
          className={`px-4 py-2 rounded-xl text-sm font-semibold transition ${
            activeTab === "all"
              ? "bg-white dark:bg-slate-700 text-brand-600 dark:text-brand-300 shadow-sm"
              : "text-gray-600 dark:text-slate-400 hover:text-gray-900"
          }`}
        >
          All Itineraries ({itineraries.length})
        </button>
        <button
          onClick={() => setActiveTab("offline")}
          className={`px-4 py-2 rounded-xl text-sm font-semibold transition flex items-center gap-1.5 ${
            activeTab === "offline"
              ? "bg-white dark:bg-slate-700 text-emerald-600 dark:text-emerald-400 shadow-sm"
              : "text-gray-600 dark:text-slate-400 hover:text-gray-900"
          }`}
        >
          <span>📶</span> Available Offline ({offlineIds.size})
        </button>
      </div>

      {displayedItineraries.length === 0 ? (
        <div className="text-center bg-white dark:bg-slate-800 p-12 rounded-2xl shadow-sm dark:shadow-none border border-gray-100 dark:border-slate-700">
          <div className="text-6xl mb-4">
            {activeTab === "offline" ? "📶" : "✈️"}
          </div>
          <h3 className="text-xl font-bold text-gray-800 dark:text-slate-100 mb-2">
            {activeTab === "offline" ? "No offline tours saved yet" : "No itineraries yet!"}
          </h3>
          <p className="text-gray-500 dark:text-slate-400 mb-6 max-w-md mx-auto">
            {activeTab === "offline"
              ? "Save any tour for offline browsing so you can access all schedules even without internet or in remote mountainous regions."
              : "Use our AI to generate the perfect personalized schedule for your next journey."}
          </p>
          {activeTab === "offline" ? (
            <button
              onClick={() => setActiveTab("all")}
              className="text-brand-600 font-semibold hover:underline"
            >
              Browse All Itineraries to Save Offline →
            </button>
          ) : (
            <Link to="/itinerary-builder" className="text-brand-600 font-semibold hover:underline">
              Try the Itinerary Builder →
            </Link>
          )}
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {displayedItineraries.map(it => {
            const isOffline = offlineIds.has(it.id);
            return (
              <div
                key={it.id}
                className="bg-white dark:bg-slate-800 rounded-2xl shadow-sm hover:shadow-md border border-gray-200 dark:border-slate-700 overflow-hidden transition group flex flex-col"
              >
                {/* Card Header */}
                <div className="bg-gradient-to-r from-brand-50 to-teal-50 dark:from-slate-800 dark:to-slate-700/70 p-4 border-b dark:border-slate-700 flex justify-between items-start">
                  <div className="pr-2">
                    <div className="flex items-center gap-2 mb-1">
                      <span className="text-xs font-bold uppercase tracking-wider px-2 py-0.5 rounded-full bg-brand-100 text-brand-700 dark:bg-brand-900/50 dark:text-brand-300">
                        {it.days} Days
                      </span>
                      {isOffline && (
                        <span className="text-xs font-bold px-2 py-0.5 rounded-full bg-emerald-100 text-emerald-700 dark:bg-emerald-900/50 dark:text-emerald-300 flex items-center gap-1">
                          <span>●</span> Offline Ready
                        </span>
                      )}
                    </div>
                    <h3 className="font-bold text-lg text-gray-900 dark:text-white truncate" title={it.title}>
                      {it.title}
                    </h3>
                    <p className="text-xs text-gray-500 dark:text-slate-400 mt-0.5">
                      Created {new Date(it.created_at).toLocaleDateString()}
                    </p>
                  </div>
                  <button
                    onClick={() => handleDelete(it.id)}
                    title="Delete Itinerary"
                    className="text-gray-400 hover:text-red-500 transition p-1.5 rounded-lg hover:bg-white dark:hover:bg-slate-600"
                  >
                    <svg xmlns="http://www.w3.org/2000/svg" className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                    </svg>
                  </button>
                </div>

                {/* Day-by-day Activities Preview */}
                <div className="p-4 flex-1 max-h-56 overflow-y-auto text-sm custom-scrollbar space-y-3">
                  {(it.schedule || []).map((day, i) => (
                    <div key={i} className="border-l-2 border-brand-300 dark:border-brand-600 pl-3">
                      <span className="font-bold text-brand-700 dark:text-brand-400 text-xs uppercase tracking-wider block mb-1">
                        Day {day.day}
                      </span>
                      <ul className="space-y-1">
                        {(day.activities || []).slice(0, 2).map((act, j) => (
                          <li key={j} className="text-gray-600 dark:text-slate-300 flex items-start text-xs">
                            <span className="text-gray-400 mr-1.5 shrink-0 font-medium">{act.time}</span>
                            <span className="truncate">{act.name}</span>
                          </li>
                        ))}
                        {(day.activities || []).length > 2 && (
                          <li className="text-gray-400 text-xs italic">
                            +{(day.activities || []).length - 2} more stops
                          </li>
                        )}
                      </ul>
                    </div>
                  ))}
                </div>

                {/* Action Toolbar (Social Share, Offline Save, Print/PDF, JSON) */}
                <div className="p-3 bg-gray-50 dark:bg-slate-800/80 border-t dark:border-slate-700 grid grid-cols-4 gap-1.5 text-xs">
                  {/* Share */}
                  <button
                    onClick={() => handleOpenShare(it)}
                    className="flex flex-col items-center justify-center p-2 rounded-xl bg-white dark:bg-slate-700 border border-gray-200 dark:border-slate-600 hover:bg-brand-50 hover:text-brand-600 dark:hover:bg-slate-600 transition text-gray-700 dark:text-slate-200"
                    title="Share with friends on WhatsApp or Social Media"
                  >
                    <span className="text-sm">📤</span>
                    <span className="font-semibold mt-0.5">Share</span>
                  </button>

                  {/* Offline Toggle */}
                  <button
                    onClick={() => handleToggleOffline(it)}
                    className={`flex flex-col items-center justify-center p-2 rounded-xl border transition ${
                      isOffline
                        ? "bg-emerald-50 border-emerald-300 text-emerald-700 dark:bg-emerald-900/30 dark:border-emerald-700 dark:text-emerald-300"
                        : "bg-white dark:bg-slate-700 border-gray-200 dark:border-slate-600 hover:bg-emerald-50 hover:text-emerald-600 text-gray-700 dark:text-slate-200"
                    }`}
                    title={isOffline ? "Remove from offline storage" : "Save offline for low-network areas"}
                  >
                    <span className="text-sm">{isOffline ? "💾" : "📶"}</span>
                    <span className="font-semibold mt-0.5">{isOffline ? "Saved" : "Offline"}</span>
                  </button>

                  {/* Printable PDF Pass */}
                  <button
                    onClick={() => printItineraryDocument(it)}
                    className="flex flex-col items-center justify-center p-2 rounded-xl bg-white dark:bg-slate-700 border border-gray-200 dark:border-slate-600 hover:bg-indigo-50 hover:text-indigo-600 dark:hover:bg-slate-600 transition text-gray-700 dark:text-slate-200"
                    title="Print or Save PDF offline travel pass with emergency helplines"
                  >
                    <span className="text-sm">🖨️</span>
                    <span className="font-semibold mt-0.5">PDF Pass</span>
                  </button>

                  {/* JSON Export */}
                  <button
                    onClick={() => exportItineraryJSON(it)}
                    className="flex flex-col items-center justify-center p-2 rounded-xl bg-white dark:bg-slate-700 border border-gray-200 dark:border-slate-600 hover:bg-purple-50 hover:text-purple-600 dark:hover:bg-slate-600 transition text-gray-700 dark:text-slate-200"
                    title="Download offline JSON file"
                  >
                    <span className="text-sm">⬇️</span>
                    <span className="font-semibold mt-0.5">Export</span>
                  </button>
                </div>
              </div>
            );
          })}
        </div>
      )}

      {/* Social Sharing Modal */}
      <ShareModal
        isOpen={shareData.isOpen}
        onClose={() => setShareData({ ...shareData, isOpen: false })}
        title={shareData.title}
        text={shareData.text}
        url={shareData.url}
      />
    </div>
  );
}
