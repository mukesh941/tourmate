import React, { useState, useEffect, useRef } from 'react';
import axios from 'axios';
import { useNavigate } from 'react-router-dom';
import { Search, MapPin } from 'lucide-react';
import { useAuth } from '../context/AuthContext';

export default function LocationSearch() {
  const [query, setQuery] = useState('');
  const [results, setResults] = useState([]);
  const [isLoading, setIsLoading] = useState(false);
  const [showDropdown, setShowDropdown] = useState(false);
  const { token } = useAuth();
  const navigate = useNavigate();
  const dropdownRef = useRef(null);

  useEffect(() => {
    const handleClickOutside = (event) => {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target)) {
        setShowDropdown(false);
      }
    };
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  useEffect(() => {
    const delayDebounceFn = setTimeout(async () => {
      if (query.length >= 2) {
        setIsLoading(true);
        try {
          const res = await axios.get(`${import.meta.env.VITE_API_BASE_URL}/locations/search?query=${query}`, {
            headers: token ? { Authorization: `Bearer ${token}` } : {}
          });
          setResults(res.data.data || []);
          setShowDropdown(true);
        } catch (err) {
          console.error("Location search failed", err);
        } finally {
          setIsLoading(false);
        }
      } else {
        setResults([]);
        setShowDropdown(false);
      }
    }, 500);

    return () => clearTimeout(delayDebounceFn);
  }, [query, token]);

  const handleSelect = (location) => {
    setShowDropdown(false);
    if (location.lat && location.lng) {
      navigate(`/explore?name=${encodeURIComponent(location.name)}&lat=${location.lat}&lng=${location.lng}`);
    } else {
      // Fallback if no coordinates
      navigate(`/explore?name=${encodeURIComponent(location.name)}`);
    }
  };

  return (
    <div className="relative w-full max-w-2xl mx-auto z-50" ref={dropdownRef}>
      <div className="relative flex items-center">
        <div className="absolute left-4 text-gray-500">
          <Search className="w-6 h-6" />
        </div>
        <input
          type="text"
          className="w-full bg-white/95 backdrop-blur-md text-gray-900 border-none rounded-2xl py-4 pl-14 pr-6 text-lg shadow-2xl focus:ring-4 focus:ring-brand-500 outline-none transition-all placeholder-gray-500"
          placeholder="Where do you want to go? (e.g. Jaipur, Agra, Goa)"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          onFocus={() => { if (query.length >= 2) setShowDropdown(true); }}
        />
        {isLoading && (
          <div className="absolute right-4 text-gray-500">
            <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-brand-500"></div>
          </div>
        )}
      </div>

      {showDropdown && results.length > 0 && (
        <div className="absolute top-full mt-2 w-full bg-white rounded-xl shadow-2xl overflow-hidden z-50 border border-gray-100 animate-fade-in">
          {results.map((loc, idx) => (
            <div
              key={idx}
              className="flex items-center gap-4 p-4 hover:bg-gray-50 cursor-pointer border-b border-gray-50 last:border-0 transition-colors"
              onClick={() => handleSelect(loc)}
            >
              <div className="bg-brand-100 p-2 rounded-full text-brand-600">
                <MapPin className="w-5 h-5" />
              </div>
              <div>
                <h4 className="font-bold text-gray-900 text-lg">{loc.name}</h4>
                <p className="text-sm text-gray-500 capitalize">{loc.type}</p>
              </div>
            </div>
          ))}
        </div>
      )}
      
      {showDropdown && query.length >= 2 && !isLoading && results.length === 0 && (
        <div className="absolute top-full mt-2 w-full bg-white rounded-xl shadow-2xl p-4 text-center z-50 border border-gray-100 text-gray-500">
          No locations found. Try searching for a city, landmark, or destination.
        </div>
      )}
    </div>
  );
}
