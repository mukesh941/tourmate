import { useState, useEffect } from "react";
import { getPlaces, getDestinations, getCategories } from "../../api/places";
import { createPlace, deletePlace } from "../../api/admin";

export default function ManagePlaces() {
  const [places, setPlaces] = useState([]);
  const [destinations, setDestinations] = useState([]);
  const [categories, setCategories] = useState([]);

  const [form, setForm] = useState({
    name: "", destination_id: "", category_id: "", description: "", price_level: 1, rating: 0
  });

  const loadData = async () => {
    const [p, d, c] = await Promise.all([getPlaces(), getDestinations(), getCategories()]);
    setPlaces(p);
    setDestinations(d);
    setCategories(c);
  };
  useEffect(() => { loadData(); }, []);

  const update = field => e => setForm({ ...form, [field]: e.target.value });

  const handleAdd = async (e) => {
    e.preventDefault();
    await createPlace({ ...form, price_level: parseInt(form.price_level), rating: parseFloat(form.rating) });
    setForm({ name: "", destination_id: "", category_id: "", description: "", price_level: 1, rating: 0 });
    loadData();
  };

  const handleDelete = async (id) => {
    if (confirm("Are you sure?")) {
      await deletePlace(id);
      loadData();
    }
  };

  return (
    <div className="max-w-4xl mx-auto p-4 space-y-6">
      <h1 className="text-3xl font-bold">Manage Places</h1>
      <form onSubmit={handleAdd} className="bg-white dark:bg-slate-800 p-6 rounded shadow space-y-4">
        <h2 className="text-xl font-semibold">Add New Tourist Place</h2>
        <div className="grid grid-cols-2 gap-4">
          <input required placeholder="Name" value={form.name} onChange={update("name")} className="border p-2 rounded" />
          <select required value={form.destination_id} onChange={update("destination_id")} className="border p-2 rounded">
            <option value="">Select Destination</option>
            {destinations.map(d => <option key={d.id} value={d.id}>{d.name}</option>)}
          </select>
          <select required value={form.category_id} onChange={update("category_id")} className="border p-2 rounded">
            <option value="">Select Category</option>
            {categories.map(c => <option key={c.id} value={c.id}>{c.name}</option>)}
          </select>
          <input type="number" min="1" max="4" placeholder="Price Level (1-4)" value={form.price_level} onChange={update("price_level")} className="border p-2 rounded" />
        </div>
        <textarea placeholder="Description" value={form.description} onChange={update("description")} className="border p-2 rounded w-full h-24" />
        <button type="submit" className="bg-brand-600 text-white px-4 py-2 rounded">Add Place</button>
      </form>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {places.map(p => (
          <div key={p.id} className="bg-white dark:bg-slate-800 p-4 rounded shadow flex flex-col justify-between">
            <div>
              <h3 className="text-lg font-bold">{p.name}</h3>
              <p className="text-sm text-gray-500 dark:text-slate-400">Destination: {destinations.find(d => d.id === p.destination_id)?.name}</p>
            </div>
            <button onClick={() => handleDelete(p.id)} className="text-red-600 self-start mt-4 hover:underline">Delete</button>
          </div>
        ))}
      </div>
    </div>
  );
}
