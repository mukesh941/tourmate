import { useState, useEffect } from "react";
import { Link } from "react-router-dom";
import api from "../../api/axios";
import { useAuth } from "../../context/AuthContext";
import { ShieldCheck, ShieldOff, Trash2, ArrowLeft, Search } from "lucide-react";

export default function ManageUsers() {
  const { user: me } = useAuth();
  const [users, setUsers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState("");
  const [actionLoading, setActionLoading] = useState(null);

  const fetchUsers = async () => {
    setLoading(true);
    try {
      const res = await api.get("/admin/users");
      setUsers(res.data.data || []);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { fetchUsers(); }, []);

  const handleDelete = async (id, name) => {
    if (!window.confirm(`Delete user "${name}"? This cannot be undone.`)) return;
    setActionLoading(id + "_delete");
    try {
      await api.delete(`/admin/users/${id}`);
      setUsers(users.filter(u => u.id !== id));
    } catch (err) {
      alert(err.response?.data?.detail || "Failed to delete user.");
    } finally {
      setActionLoading(null);
    }
  };

  const handlePromote = async (id, name) => {
    if (!window.confirm(`Promote "${name}" to Admin?`)) return;
    setActionLoading(id + "_promote");
    try {
      await api.put(`/admin/users/${id}/promote`);
      setUsers(users.map(u => u.id === id ? { ...u, role: "admin" } : u));
    } catch (err) {
      alert(err.response?.data?.detail || "Failed to promote user.");
    } finally {
      setActionLoading(null);
    }
  };

  const handleDemote = async (id, name) => {
    if (!window.confirm(`Demote "${name}" from Admin to regular user?`)) return;
    setActionLoading(id + "_demote");
    try {
      await api.put(`/admin/users/${id}/demote`);
      setUsers(users.map(u => u.id === id ? { ...u, role: "user" } : u));
    } catch (err) {
      alert(err.response?.data?.detail || "Failed to demote user.");
    } finally {
      setActionLoading(null);
    }
  };

  const filtered = users.filter(u =>
    u.name?.toLowerCase().includes(search.toLowerCase()) ||
    u.email?.toLowerCase().includes(search.toLowerCase())
  );

  const admins = filtered.filter(u => u.role === "admin");
  const regularUsers = filtered.filter(u => u.role !== "admin");

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-slate-900/50">
      {/* Header */}
      <div className="bg-gradient-to-r from-slate-900 via-brand-900 to-slate-900 px-6 py-8">
        <div className="max-w-5xl mx-auto">
          <Link to="/admin" className="flex items-center gap-1.5 text-slate-400 hover:text-white text-xs font-semibold mb-4 transition-colors">
            <ArrowLeft className="w-3.5 h-3.5" /> Back to Dashboard
          </Link>
          <h1 className="text-2xl md:text-3xl font-display font-black text-white tracking-tight">User Management</h1>
          <p className="text-slate-400 text-sm mt-1">Promote, demote, or remove users. Total: <span className="text-white font-bold">{users.length}</span></p>
        </div>
      </div>

      <div className="max-w-5xl mx-auto px-6 py-8 space-y-8">

        {/* Search */}
        <div className="relative">
          <Search className="absolute left-3.5 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
          <input
            type="text"
            placeholder="Search by name or email..."
            value={search}
            onChange={e => setSearch(e.target.value)}
            className="w-full pl-10 pr-4 py-2.5 bg-white dark:bg-slate-800 border border-gray-200 dark:border-slate-700 rounded-xl text-sm focus:ring-2 focus:ring-brand-500 outline-none dark:text-white"
          />
        </div>

        {loading ? (
          <div className="text-center py-12 text-gray-400 text-sm animate-pulse">Loading users...</div>
        ) : (
          <>
            {/* Admins */}
            {admins.length > 0 && (
              <div>
                <h2 className="text-xs font-black uppercase tracking-widest text-brand-600 dark:text-brand-400 mb-3 flex items-center gap-2">
                  <ShieldCheck className="w-4 h-4" /> Administrators ({admins.length})
                </h2>
                <div className="space-y-2">
                  {admins.map(u => (
                    <UserRow
                      key={u.id} user={u} isMe={u.id === me?.id}
                      onDelete={() => handleDelete(u.id, u.name)}
                      onPromote={() => handlePromote(u.id, u.name)}
                      onDemote={() => handleDemote(u.id, u.name)}
                      actionLoading={actionLoading}
                    />
                  ))}
                </div>
              </div>
            )}

            {/* Regular Users */}
            {regularUsers.length > 0 && (
              <div>
                <h2 className="text-xs font-black uppercase tracking-widest text-gray-500 dark:text-slate-400 mb-3">
                  Regular Users ({regularUsers.length})
                </h2>
                <div className="space-y-2">
                  {regularUsers.map(u => (
                    <UserRow
                      key={u.id} user={u} isMe={u.id === me?.id}
                      onDelete={() => handleDelete(u.id, u.name)}
                      onPromote={() => handlePromote(u.id, u.name)}
                      onDemote={() => handleDemote(u.id, u.name)}
                      actionLoading={actionLoading}
                    />
                  ))}
                </div>
              </div>
            )}

            {filtered.length === 0 && (
              <div className="text-center py-12 text-gray-400">No users match your search.</div>
            )}
          </>
        )}
      </div>
    </div>
  );
}

function UserRow({ user, isMe, onDelete, onPromote, onDemote, actionLoading }) {
  const isAdmin = user.role === "admin";
  const initials = (user.name || "U").split(" ").map(w => w[0]).join("").slice(0, 2).toUpperCase();

  return (
    <div className={`flex items-center gap-3 bg-white dark:bg-slate-800 border rounded-xl px-4 py-3 transition-all ${isAdmin ? "border-brand-200 dark:border-brand-800/50" : "border-gray-100 dark:border-slate-700"}`}>
      {/* Avatar */}
      <div className={`w-9 h-9 rounded-full flex items-center justify-center text-sm font-bold text-white shrink-0 ${isAdmin ? "bg-gradient-to-br from-brand-600 to-accent-600" : "bg-gray-400 dark:bg-slate-600"}`}>
        {initials}
      </div>

      {/* Info */}
      <div className="flex-1 min-w-0">
        <div className="flex items-center gap-2 flex-wrap">
          <p className="font-bold text-sm text-gray-900 dark:text-white truncate">{user.name || "Unknown"}</p>
          {isAdmin && (
            <span className="inline-flex items-center gap-1 text-[10px] font-bold bg-brand-100 dark:bg-brand-900/40 text-brand-700 dark:text-brand-300 px-2 py-0.5 rounded-full">
              <ShieldCheck className="w-3 h-3" /> Admin
            </span>
          )}
          {isMe && (
            <span className="text-[10px] font-bold text-gray-400 dark:text-slate-500">(you)</span>
          )}
        </div>
        <p className="text-xs text-gray-500 dark:text-slate-400 truncate">{user.email}</p>
      </div>

      {/* Actions */}
      {!isMe && (
        <div className="flex items-center gap-2 shrink-0">
          {isAdmin ? (
            <button
              onClick={onDemote}
              disabled={actionLoading === user.id + "_demote"}
              title="Remove Admin"
              className="flex items-center gap-1 text-xs font-bold px-3 py-1.5 rounded-lg bg-amber-50 dark:bg-amber-900/20 text-amber-700 dark:text-amber-400 border border-amber-200 dark:border-amber-800 hover:bg-amber-100 transition disabled:opacity-50"
            >
              <ShieldOff className="w-3.5 h-3.5" />
              {actionLoading === user.id + "_demote" ? "..." : "Demote"}
            </button>
          ) : (
            <button
              onClick={onPromote}
              disabled={actionLoading === user.id + "_promote"}
              title="Make Admin"
              className="flex items-center gap-1 text-xs font-bold px-3 py-1.5 rounded-lg bg-brand-50 dark:bg-brand-900/20 text-brand-700 dark:text-brand-300 border border-brand-200 dark:border-brand-800 hover:bg-brand-100 transition disabled:opacity-50"
            >
              <ShieldCheck className="w-3.5 h-3.5" />
              {actionLoading === user.id + "_promote" ? "..." : "Promote"}
            </button>
          )}
          <button
            onClick={onDelete}
            disabled={!!actionLoading}
            title="Delete user"
            className="p-1.5 rounded-lg text-gray-400 hover:text-red-500 hover:bg-red-50 dark:hover:bg-red-900/20 transition"
          >
            <Trash2 className="w-4 h-4" />
          </button>
        </div>
      )}
    </div>
  );
}
