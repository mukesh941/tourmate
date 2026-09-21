import { useState, useEffect } from "react";
import { Link } from "react-router-dom";
import { getDestinations } from "../api/places";
import { NEUTRAL_PLACEHOLDER_IMAGE, handleImageError } from "../config/imageConfig";

export default function Destinations() {
  const [destinations, setDestinations] = useState([]);

  useEffect(() => {
    getDestinations().then(setDestinations);
  }, []);

  return (
    <div className="max-w-6xl mx-auto p-4 space-y-6">
      <h1 className="text-4xl font-bold text-gray-800 dark:text-slate-100 text-center mb-10">Explore Destinations</h1>
      <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
        {destinations.map(d => (
          <Link key={d.id} to={`/destinations/${d.id}`} className="group block bg-white dark:bg-slate-800 rounded-xl shadow-md dark:shadow-none overflow-hidden hover:shadow-xl dark:shadow-none transition transform hover:-translate-y-1">
            <div className="h-48 bg-gray-200 dark:bg-slate-700 overflow-hidden relative">
              <img 
                src={d.cover_image || d.images?.[0] || NEUTRAL_PLACEHOLDER_IMAGE} 
                alt={d.name} 
                className="w-full h-full object-cover group-hover:scale-105 transition duration-300" 
                onError={handleImageError}
              />
            </div>
            <div className="p-5">
              <h2 className="text-2xl font-bold text-gray-800 dark:text-slate-100 mb-1">{d.name}</h2>
              <p className="text-sm text-gray-500 dark:text-slate-400 mb-3">{d.state}, {d.country}</p>
              <p className="text-gray-600 dark:text-slate-300 line-clamp-2">{d.description}</p>
            </div>
          </Link>
        ))}
      </div>
    </div>
  );
}
