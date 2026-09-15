import { useState, useEffect } from "react";
import api from "../../api/axios";

export default function ManageUsers() {
  const [users, setUsers] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchUsers();
  }, []);

  const fetchUsers = async () => {
    try {
      const res = await api.get("/admin/users");
      setUsers(res.data.data);
    } catch (err) {
      console.error("Failed to fetch users", err);
    } finally {
      setLoading(false);
    }
  };

  const handleDeleteUser = async (userId) => {
    if (!window.confirm("Are you sure you want to completely remove this registered user? This cannot be undone.")) return;
    try {
      await api.delete(`/admin/users/${userId}`);
      setUsers(users.filter(u => u.id !== userId));
      alert("User removed successfully.");
    } catch (err) {
      alert(err.response?.data?.detail || "Failed to remove user");
    }
  };

  if (loading) return <div className="text-center p-10">Loading users...</div>;

  return (
    <div className="max-w-6xl mx-auto p-4 space-y-6">
      <h1 className="text-3xl font-bold text-gray-800 dark:text-slate-100 mb-6">Manage Users</h1>
      
      <div className="bg-white dark:bg-slate-800 rounded-xl shadow overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-left">
            <thead className="bg-gray-50 dark:bg-slate-700/50">
              <tr>
                <th className="px-6 py-4 font-semibold text-gray-600 dark:text-slate-300">Name</th>
                <th className="px-6 py-4 font-semibold text-gray-600 dark:text-slate-300">Email</th>
                <th className="px-6 py-4 font-semibold text-gray-600 dark:text-slate-300">Role</th>
                <th className="px-6 py-4 font-semibold text-gray-600 dark:text-slate-300">Joined</th>
                <th className="px-6 py-4 font-semibold text-gray-600 dark:text-slate-300 text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100 dark:divide-slate-700">
              {users.map((u) => (
                <tr key={u.id} className="hover:bg-gray-50 dark:hover:bg-slate-700/50">
                  <td className="px-6 py-4 text-gray-800 dark:text-slate-200">{u.name}</td>
                  <td className="px-6 py-4 text-gray-600 dark:text-slate-400">{u.email}</td>
                  <td className="px-6 py-4">
                    <span className={`px-2 py-1 rounded text-xs font-medium ${u.role === 'admin' ? 'bg-red-100 text-red-700' : 'bg-blue-100 text-blue-700'}`}>
                      {u.role}
                    </span>
                  </td>
                  <td className="px-6 py-4 text-gray-500 text-sm">
                    {new Date(u.created_at).toLocaleDateString()}
                  </td>
                  <td className="px-6 py-4 text-right">
                    {u.role !== 'admin' && (
                      <button 
                        onClick={() => handleDeleteUser(u.id)}
                        className="text-red-500 hover:text-red-700 font-medium text-sm transition-colors"
                      >
                        Remove
                      </button>
                    )}
                  </td>
                </tr>
              ))}
              {users.length === 0 && (
                <tr>
                  <td colSpan="5" className="px-6 py-4 text-center text-gray-500">No users found.</td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
