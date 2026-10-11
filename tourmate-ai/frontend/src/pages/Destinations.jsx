import { useState, useEffect } from "react";
import { Link } from "react-router-dom";
import { getDestinationsPaginated } from "../api/places";
import { Search } from "lucide-react";
import SafeImage from "../components/SafeImage";

export default function Destinations() {
  const [destinations, setDestinations] = useState([]);
  const [loading, setLoading] = useState(true);
  const [page, setPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [search, setSearch] = useState("");
  const [inputValue, setInputValue] = useState("");

  const fetchDestinations = (pageNum, searchTerm, append = false) => {
    setLoading(true);
    getDestinationsPaginated({ page: pageNum, page_size: 24, search: searchTerm })
      .then(res => {
        setDestinations(prev => append ? [...prev, ...res.results] : res.results);
        setTotalPages(res.total_pages);
      })
      .catch(err => console.error("Failed to fetch destinations:", err))
      .finally(() => setLoading(false));
  };

  useEffect(() => {
    fetchDestinations(1, search, false);
  }, [search]);

  const handleLoadMore = () => {
    const nextPage = page + 1;
    setPage(nextPage);
    fetchDestinations(nextPage, search, true);
  };

  const handleSearch = (e) => {
    e.preventDefault();
    setPage(1);
    setSearch(inputValue);
  };

  return (
    <div className="max-w-6xl mx-auto p-4 space-y-6">
      <h1 className="text-4xl font-bold text-gray-800 dark:text-slate-100 text-center mb-6">Explore Destinations</h1>
      
      <form onSubmit={handleSearch} className="max-w-xl mx-auto mb-10 relative">
        <input 
          type="text" 
          placeholder="Search destinations (e.g. 4 Arm, Kharwali)..."
          value={inputValue}
          onChange={(e) => setInputValue(e.target.value)}
          className="w-full px-5 py-3 pl-12 rounded-full border border-gray-300 dark:border-slate-700 bg-white dark:bg-slate-800 text-gray-900 dark:text-slate-100 focus:outline-none focus:ring-2 focus:ring-brand-500 shadow-sm"
        />
        <button type="submit" className="absolute left-4 top-1/2 transform -translate-y-1/2 text-gray-400 hover:text-brand-500">
          <Search className="w-5 h-5" />
        </button>
      </form>

      <div className="grid grid-cols-1 md:grid-cols-3 lg:grid-cols-4 gap-6">
        {destinations.map((d, idx) => (
          <Link key={`${d.id}-${idx}`} to={`/destinations/${d.id}`} className="group block bg-white dark:bg-slate-800 rounded-xl shadow-sm dark:shadow-none overflow-hidden hover:shadow-md dark:shadow-none transition transform hover:-translate-y-1 border border-gray-100 dark:border-slate-700/50">
            <div className="h-40 bg-gray-200 dark:bg-slate-700 overflow-hidden relative">
              <SafeImage 
                src={d.cover_image || d.images?.[0]} 
                alt={d.name} 
                className="w-full h-full object-cover group-hover:scale-105 transition duration-300" 
              />
            </div>
            <div className="p-4">
              <h2 className="text-xl font-bold text-gray-800 dark:text-slate-100 mb-1 truncate" title={d.name}>{d.name}</h2>
              <p className="text-xs text-brand-600 dark:text-brand-400 mb-2 truncate">{d.state ? `${d.state}, ` : ""}{d.country}</p>
              <p className="text-sm text-gray-600 dark:text-slate-300 line-clamp-2">{d.description}</p>
            </div>
          </Link>
        ))}
      </div>
      
      {destinations.length === 0 && !loading && (
        <div className="text-center py-16 text-gray-500 dark:text-slate-400">
          No destinations found matching "{search}".
        </div>
      )}

      {loading && (
        <div className="flex flex-col items-center justify-center py-10">
          <div className="w-8 h-8 border-4 border-brand-200 border-t-brand-600 rounded-full animate-spin mb-3"></div>
          <p className="text-gray-500 dark:text-slate-400 font-medium text-sm">Loading...</p>
        </div>
      )}

      {!loading && page < totalPages && (
        <div className="flex justify-center pt-8 pb-10">
          <button 
            onClick={handleLoadMore}
            className="px-6 py-2.5 bg-white dark:bg-slate-800 border border-gray-300 dark:border-slate-600 text-gray-700 dark:text-slate-300 rounded-full hover:bg-gray-50 dark:hover:bg-slate-700 transition font-medium text-sm shadow-sm"
          >
            Load More Destinations
          </button>
        </div>
      )}
    </div>
  );
}
