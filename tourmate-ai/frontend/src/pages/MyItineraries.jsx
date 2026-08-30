import { useState, useEffect } from "react";
import axios from "axios";
import { useAuth } from "../context/AuthContext";
import { Link } from "react-router-dom";

export default function MyItineraries() {
  const { token } = useAuth();
  const [itineraries, setItineraries] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchItineraries();
  }, [token]);

  const fetchItineraries = async () => {
    setLoading(true);
    try {
      const res = await axios.get(`${import.meta.env.VITE_API_BASE_URL}/itineraries`, {
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
      await axios.delete(`${import.meta.env.VITE_API_BASE_URL}/itineraries/${id}`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      fetchItineraries();
    } catch (err) {
      console.error(err);
      alert("Failed to delete.");
    }
  };

  if (loading) {
    return <div className="p-8 text-center text-gray-500 dark:text-slate-400">Loading your trips...</div>;
  }

  return (
    <div className="max-w-6xl mx-auto p-4 md:p-8">
      <div className="flex justify-between items-center mb-8">
        <div>
          <h1 className="text-3xl font-bold text-gray-900 dark:text-white">My Itineraries</h1>
          <p className="text-gray-500 dark:text-slate-400 mt-1">Manage your generated AI trips</p>
        </div>
        <Link to="/itinerary-builder" className="bg-brand-600 hover:bg-brand-700 text-white px-4 py-2 rounded-lg shadow font-medium transition-colors">
          ＋ Create New
        </Link>
      </div>

      {itineraries.length === 0 ? (
        <div className="text-center bg-white dark:bg-slate-800 p-12 rounded-2xl shadow-sm dark:shadow-none border border-gray-100 dark:border-slate-700">
          <div className="text-6xl mb-4">✈️</div>
          <h3 className="text-xl font-bold text-gray-800 dark:text-slate-100 mb-2">No itineraries yet!</h3>
          <p className="text-gray-500 dark:text-slate-400 mb-6">Use our AI to generate the perfect schedule for your next trip.</p>
          <Link to="/itinerary-builder" className="text-brand-600 font-medium hover:underline">
            Try the Itinerary Builder →
          </Link>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {itineraries.map(it => (
            <div key={it.id} className="bg-white dark:bg-slate-800 rounded-xl shadow-sm dark:shadow-none border border-gray-200 dark:border-slate-700 overflow-hidden hover:shadow-md dark:shadow-none transition-shadow group">
              <div className="bg-brand-50 p-4 border-b flex justify-between items-start">
                <div>
                  <h3 className="font-bold text-lg text-gray-900 dark:text-white truncate" title={it.title}>{it.title}</h3>
                  <p className="text-xs text-gray-500 dark:text-slate-400 font-medium mt-1">{it.days} Days • Created {new Date(it.created_at).toLocaleDateString()}</p>
                </div>
                <button onClick={() => handleDelete(it.id)} className="text-gray-400 hover:text-red-500 transition-colors bg-white dark:bg-slate-800 rounded-full p-1 opacity-0 group-hover:opacity-100 shadow-sm dark:shadow-none">
                  <svg xmlns="http://www.w3.org/2000/svg" className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" /></svg>
                </button>
              </div>
              <div className="p-4 max-h-48 overflow-y-auto text-sm custom-scrollbar">
                {it.schedule.map((day, i) => (
                  <div key={i} className="mb-3 last:mb-0">
                    <span className="font-semibold text-brand-600 text-xs uppercase tracking-wider block mb-1">Day {day.day}</span>
                    <ul className="space-y-1">
                      {day.activities.slice(0, 2).map((act, j) => (
                        <li key={j} className="text-gray-600 dark:text-slate-300 flex items-start">
                          <span className="text-gray-400 mr-2 shrink-0">{act.time}</span>
                          <span className="truncate">{act.name}</span>
                        </li>
                      ))}
                      {day.activities.length > 2 && (
                        <li className="text-gray-400 text-xs italic">+{day.activities.length - 2} more activities</li>
                      )}
                    </ul>
                  </div>
                ))}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
