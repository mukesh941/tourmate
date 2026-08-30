import { useState, useEffect } from "react";
import { getDestinations } from "../../api/places";
import { createDestination, deleteDestination } from "../../api/admin";

export default function ManageDestinations() {
  const [destinations, setDestinations] = useState([]);
  const [form, setForm] = useState({ name: "", state: "", country: "", description: "", cover_image: "" });

  const load = async () => setDestinations(await getDestinations());
  useEffect(() => { load(); }, []);

  const update = field => e => setForm({ ...form, [field]: e.target.value });

  const handleAdd = async (e) => {
    e.preventDefault();
    await createDestination(form);
    setForm({ name: "", state: "", country: "", description: "", cover_image: "" });
    load();
  };

  const handleDelete = async (id) => {
    if (confirm("Are you sure?")) {
      await deleteDestination(id);
      load();
    }
  };

  return (
    <div className="max-w-4xl mx-auto p-4 space-y-6">
      <h1 className="text-3xl font-bold">Manage Destinations</h1>
      <form onSubmit={handleAdd} className="bg-white dark:bg-slate-800 p-6 rounded shadow space-y-4">
        <h2 className="text-xl font-semibold">Add New Destination</h2>
        <div className="grid grid-cols-2 gap-4">
          <input required placeholder="Name" value={form.name} onChange={update("name")} className="border p-2 rounded" />
          <input placeholder="State" value={form.state} onChange={update("state")} className="border p-2 rounded" />
          <input placeholder="Country" value={form.country} onChange={update("country")} className="border p-2 rounded" />
          <input placeholder="Cover Image URL" value={form.cover_image} onChange={update("cover_image")} className="border p-2 rounded" />
        </div>
        <textarea placeholder="Description" value={form.description} onChange={update("description")} className="border p-2 rounded w-full h-24" />
        <button type="submit" className="bg-brand-600 text-white px-4 py-2 rounded">Add Destination</button>
      </form>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {destinations.map(d => (
          <div key={d.id} className="bg-white dark:bg-slate-800 p-4 rounded shadow flex flex-col justify-between">
            <div>
              <h3 className="text-xl font-bold">{d.name}</h3>
              <p className="text-sm text-gray-500 dark:text-slate-400">{d.state}, {d.country}</p>
            </div>
            <button onClick={() => handleDelete(d.id)} className="text-red-600 self-start mt-4 hover:underline">Delete</button>
          </div>
        ))}
      </div>
    </div>
  );
}
