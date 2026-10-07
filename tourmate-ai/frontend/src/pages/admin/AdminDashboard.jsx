import { useState, useEffect } from "react";
import { Link } from "react-router-dom";
import api from "../../api/axios";
import { useAuth } from "../../context/AuthContext";
import {
  Users, MapPin, Tag, Building, Hotel, BookOpen, Map, BarChart3,
  ShieldCheck, ArrowRight, RefreshCw
} from "lucide-react";

const StatCard = ({ icon: Icon, label, value, color, link }) => (
  <Link
    to={link || "#"}
    className={`group relative overflow-hidden bg-white dark:bg-slate-800 rounded-2xl p-5 border border-gray-100 dark:border-slate-700 shadow-sm hover:shadow-lg transition-all duration-300 hover:-translate-y-0.5`}
  >
    <div className={`absolute top-0 right-0 w-24 h-24 ${color} rounded-full -translate-y-1/2 translate-x-1/2 opacity-10 group-hover:opacity-20 transition-opacity`}></div>
    <div className={`w-10 h-10 ${color} rounded-xl flex items-center justify-center mb-3`}>
      <Icon className="w-5 h-5 text-white" />
    </div>
    <p className="text-2xl font-black text-gray-900 dark:text-white">
      {value !== null && value !== undefined ? value : "—"}
    </p>
    <p className="text-xs font-semibold text-gray-500 dark:text-slate-400 uppercase tracking-wider mt-0.5">{label}</p>
    {link && (
      <div className="flex items-center gap-1 mt-3 text-xs font-bold text-brand-600 dark:text-brand-400 opacity-0 group-hover:opacity-100 transition-opacity">
        Manage <ArrowRight className="w-3 h-3" />
      </div>
    )}
  </Link>
);

const QuickActionCard = ({ to, icon, title, desc, color }) => (
  <Link
    to={to}
    className="group flex items-center gap-4 p-4 bg-white dark:bg-slate-800 border border-gray-100 dark:border-slate-700 rounded-2xl shadow-sm hover:shadow-md hover:border-brand-200 dark:hover:border-brand-700 transition-all duration-200"
  >
    <div className={`w-11 h-11 ${color} rounded-xl flex items-center justify-center shrink-0`}>
      <span className="text-xl">{icon}</span>
    </div>
    <div className="flex-1 min-w-0">
      <p className="font-bold text-sm text-gray-900 dark:text-white">{title}</p>
      <p className="text-xs text-gray-500 dark:text-slate-400 truncate">{desc}</p>
    </div>
    <ArrowRight className="w-4 h-4 text-gray-400 group-hover:text-brand-600 group-hover:translate-x-1 transition-all" />
  </Link>
);

export default function AdminDashboard() {
  const { user } = useAuth();
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);

  const fetchStats = async () => {
    setLoading(true);
    try {
      const res = await api.get("/admin/stats");
      setStats(res.data.data);
    } catch (err) {
      console.error("Failed to fetch admin stats", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { fetchStats(); }, []);

  const statCards = [
    { icon: Users,     label: "Total Users",     value: stats?.users,        color: "bg-brand-500",   link: "/admin/users" },
    { icon: Map,       label: "Destinations",    value: stats?.destinations,  color: "bg-violet-500",  link: "/admin/destinations" },
    { icon: MapPin,    label: "Places",          value: stats?.places,        color: "bg-accent-500",  link: "/admin/places" },
    { icon: Tag,       label: "Categories",      value: stats?.categories,    color: "bg-teal-500",    link: "/admin/categories" },
    { icon: Hotel,     label: "Hotels",          value: stats?.hotels,        color: "bg-amber-500",   link: null },
    { icon: BookOpen,  label: "Itineraries",     value: stats?.itineraries,   color: "bg-rose-500",    link: null },
    { icon: Users,     label: "Local Guides",    value: stats?.guides,        color: "bg-emerald-500", link: null },
  ];

  const quickActions = [
    { to: "/admin/users",        icon: "👥", title: "Manage Users",        desc: "View, delete, or promote users to admin", color: "bg-brand-50 dark:bg-brand-900/20" },
    { to: "/admin/destinations", icon: "🌍", title: "Manage Destinations", desc: "Add or edit Indian destinations",           color: "bg-violet-50 dark:bg-violet-900/20" },
    { to: "/admin/places",       icon: "📍", title: "Manage Places",       desc: "Add or edit tourist attractions",           color: "bg-accent-50 dark:bg-accent-900/20" },
    { to: "/admin/categories",   icon: "🏷️", title: "Manage Categories",   desc: "Add or edit place categories",             color: "bg-teal-50 dark:bg-teal-900/20" },
  ];

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-slate-900/50">
      {/* Header Banner */}
      <div className="bg-gradient-to-r from-slate-900 via-brand-900 to-slate-900 px-6 py-10">
        <div className="max-w-6xl mx-auto">
          <div className="flex items-center gap-3 mb-2">
            <div className="w-9 h-9 rounded-xl bg-brand-500 flex items-center justify-center">
              <ShieldCheck className="w-5 h-5 text-white" />
            </div>
            <span className="text-brand-400 text-xs font-bold uppercase tracking-widest">Admin Control Panel</span>
          </div>
          <h1 className="text-3xl md:text-4xl font-display font-black text-white tracking-tight">
            Welcome back, {user?.name?.split(" ")[0] || "Admin"} 👋
          </h1>
          <p className="text-slate-400 mt-2 text-sm">
            Manage your TourMate AI platform — users, content, and data.
          </p>
        </div>
      </div>

      <div className="max-w-6xl mx-auto px-6 py-8 space-y-10">

        {/* Stats Grid */}
        <div>
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-sm font-black uppercase tracking-widest text-gray-500 dark:text-slate-400">Platform Overview</h2>
            <button
              onClick={fetchStats}
              className="flex items-center gap-1.5 text-xs font-bold text-brand-600 dark:text-brand-400 hover:underline"
            >
              <RefreshCw className={`w-3.5 h-3.5 ${loading ? "animate-spin" : ""}`} /> Refresh
            </button>
          </div>

          {loading ? (
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              {Array(7).fill(0).map((_, i) => (
                <div key={i} className="bg-white dark:bg-slate-800 rounded-2xl p-5 border border-gray-100 dark:border-slate-700 animate-pulse">
                  <div className="w-10 h-10 bg-gray-200 dark:bg-slate-700 rounded-xl mb-3"></div>
                  <div className="h-7 w-16 bg-gray-200 dark:bg-slate-700 rounded mb-1"></div>
                  <div className="h-3 w-20 bg-gray-100 dark:bg-slate-800 rounded"></div>
                </div>
              ))}
            </div>
          ) : (
            <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 gap-4">
              {statCards.map(card => <StatCard key={card.label} {...card} />)}
            </div>
          )}
        </div>

        {/* Quick Actions */}
        <div>
          <h2 className="text-sm font-black uppercase tracking-widest text-gray-500 dark:text-slate-400 mb-4">Quick Actions</h2>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
            {quickActions.map(a => <QuickActionCard key={a.to} {...a} />)}
          </div>
        </div>

        {/* Admin info box */}
        <div className="bg-brand-50 dark:bg-brand-950/20 border border-brand-200 dark:border-brand-800/40 rounded-2xl p-5 flex items-start gap-4">
          <div className="w-10 h-10 bg-brand-600 rounded-xl flex items-center justify-center shrink-0">
            <ShieldCheck className="w-5 h-5 text-white" />
          </div>
          <div>
            <p className="font-bold text-brand-800 dark:text-brand-300 text-sm">Admin Account Active</p>
            <p className="text-xs text-brand-600/80 dark:text-brand-400/70 mt-0.5">
              Logged in as <span className="font-bold">{user?.name}</span> ({user?.email}) with full admin privileges.
              To add more admins, go to <Link to="/admin/users" className="underline font-semibold">Manage Users</Link> and promote any user.
            </p>
          </div>
        </div>

      </div>
    </div>
  );
}
