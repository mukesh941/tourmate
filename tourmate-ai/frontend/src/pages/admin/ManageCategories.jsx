import { useState, useEffect } from "react";
import { getCategories } from "../../api/places";
import { createCategory, deleteCategory } from "../../api/admin";

export default function ManageCategories() {
  const [categories, setCategories] = useState([]);
  const [name, setName] = useState("");
  const [icon, setIcon] = useState("");

  const load = async () => {
    const data = await getCategories();
    setCategories(data);
  };

  useEffect(() => { load(); }, []);

  const handleAdd = async (e) => {
    e.preventDefault();
    await createCategory({ name, icon });
    setName("");
    setIcon("");
    load();
  };

  const handleDelete = async (id) => {
    if (confirm("Are you sure?")) {
      await deleteCategory(id);
      load();
    }
  };

  return (
    <div className="max-w-4xl mx-auto p-4 space-y-6">
      <h1 className="text-3xl font-bold">Manage Categories</h1>
      <form onSubmit={handleAdd} className="bg-white dark:bg-slate-800 p-6 rounded shadow space-y-4">
        <h2 className="text-xl font-semibold">Add New Category</h2>
        <div className="grid grid-cols-2 gap-4">
          <input required placeholder="Name" value={name} onChange={e => setName(e.target.value)} className="border p-2 rounded" />
          <input placeholder="Icon URL or Emoji" value={icon} onChange={e => setIcon(e.target.value)} className="border p-2 rounded" />
        </div>
        <button type="submit" className="bg-brand-600 text-white px-4 py-2 rounded">Add Category</button>
      </form>

      <div className="bg-white dark:bg-slate-800 rounded shadow divide-y">
        {categories.map(c => (
          <div key={c.id} className="p-4 flex justify-between items-center">
            <div>
              <span className="text-2xl mr-4">{c.icon}</span>
              <span className="font-medium text-lg">{c.name}</span>
            </div>
            <button onClick={() => handleDelete(c.id)} className="text-red-600 hover:underline">Delete</button>
          </div>
        ))}
      </div>
    </div>
  );
}
