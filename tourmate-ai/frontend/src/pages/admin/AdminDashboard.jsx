import { useState, useEffect } from "react";
import { Link } from "react-router-dom";
import api from "../../api/axios";

export default function AdminDashboard() {
  const [stats, setStats] = useState(null);

  useEffect(() => {
    const fetchStats = async () => {
      try {
        const res = await api.get("/admin/stats");
        setStats(res.data.data);
      } catch (err) {
        console.error("Failed to fetch admin stats", err);
      }
    };
    fetchStats();
  }, []);

  return (
    <div className="max-w-6xl mx-auto p-4 space-y-8">
      <h1 className="text-3xl font-bold text-gray-800 dark:text-slate-100 mb-2">Admin Dashboard</h1>
      
      {/* Metrics Overview */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-8">
        <div className="bg-white dark:bg-slate-800 p-6 rounded-xl shadow-sm border border-gray-100 dark:border-slate-700 text-center">
          <p className="text-sm text-gray-500 dark:text-slate-400 mb-1">Total Users</p>
          <p className="text-3xl font-bold text-brand-600">{stats ? stats.users : '-'}</p>
        </div>
        <div className="bg-white dark:bg-slate-800 p-6 rounded-xl shadow-sm border border-gray-100 dark:border-slate-700 text-center">
          <p className="text-sm text-gray-500 dark:text-slate-400 mb-1">Destinations</p>
          <p className="text-3xl font-bold text-brand-600">{stats ? stats.destinations : '-'}</p>
        </div>
        <div className="bg-white dark:bg-slate-800 p-6 rounded-xl shadow-sm border border-gray-100 dark:border-slate-700 text-center">
          <p className="text-sm text-gray-500 dark:text-slate-400 mb-1">Categories</p>
          <p className="text-3xl font-bold text-brand-600">{stats ? stats.categories : '-'}</p>
        </div>
        <div className="bg-white dark:bg-slate-800 p-6 rounded-xl shadow-sm border border-gray-100 dark:border-slate-700 text-center">
          <p className="text-sm text-gray-500 dark:text-slate-400 mb-1">Places</p>
          <p className="text-3xl font-bold text-brand-600">{stats ? stats.places : '-'}</p>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <Link to="/admin/users" className="block p-6 bg-white dark:bg-slate-800 rounded-xl shadow hover:shadow-lg dark:shadow-none transition border border-transparent hover:border-brand-200">
          <h2 className="text-xl font-semibold text-gray-800 dark:text-slate-100 mb-2">👥 Manage Users</h2>
          <p className="text-gray-600 dark:text-slate-300">View and manage registered users and administrators.</p>
        </Link>
        <Link to="/admin/destinations" className="block p-6 bg-white dark:bg-slate-800 rounded-xl shadow hover:shadow-lg dark:shadow-none transition border border-transparent hover:border-brand-200">
          <h2 className="text-xl font-semibold text-gray-800 dark:text-slate-100 mb-2">🌍 Manage Destinations</h2>
          <p className="text-gray-600 dark:text-slate-300">Add, edit, or remove destinations like cities or regions.</p>
        </Link>
        <Link to="/admin/categories" className="block p-6 bg-white dark:bg-slate-800 rounded-xl shadow hover:shadow-lg dark:shadow-none transition border border-transparent hover:border-brand-200">
          <h2 className="text-xl font-semibold text-gray-800 dark:text-slate-100 mb-2">🏷️ Manage Categories</h2>
          <p className="text-gray-600 dark:text-slate-300">Add, edit, or remove place categories (e.g., Historical, Nature).</p>
        </Link>
        <Link to="/admin/places" className="block p-6 bg-white dark:bg-slate-800 rounded-xl shadow hover:shadow-lg dark:shadow-none transition border border-transparent hover:border-brand-200">
          <h2 className="text-xl font-semibold text-gray-800 dark:text-slate-100 mb-2">📍 Manage Places</h2>
          <p className="text-gray-600 dark:text-slate-300">Add, edit, or remove specific tourist attractions.</p>
        </Link>
      </div>
    </div>
  );
}
