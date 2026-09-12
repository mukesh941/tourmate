import { useState, useEffect } from "react";
import { useParams, Link } from "react-router-dom";
import { getDestination, getPlaces } from "../api/places";
import { useTranslation } from "react-i18next";

export default function DestinationDetail() {
  const { id } = useParams();
  const [destination, setDestination] = useState(null);
  const [places, setPlaces] = useState([]);
  const { t, i18n } = useTranslation();

  useEffect(() => {
    getDestination(id).then(setDestination);
    getPlaces({ destination_id: id }).then(setPlaces);
  }, [id]);

  const speakDescription = () => {
    if ('speechSynthesis' in window) {
      // Cancel any ongoing speech
      window.speechSynthesis.cancel();
      
      const utterance = new SpeechSynthesisUtterance(destination.description);
      // Try to set language based on current i18n language
      utterance.lang = i18n.language === 'hi' ? 'hi-IN' : 'en-US';
      
      window.speechSynthesis.speak(utterance);
    } else {
      alert("Sorry, your browser doesn't support text to speech!");
    }
  };

  if (!destination) return <div className="text-center p-10">{t('Loading...')}</div>;

  return (
    <div className="max-w-6xl mx-auto p-4 space-y-8">
      <div className="bg-white dark:bg-slate-800 rounded-xl shadow overflow-hidden">
        <img 
          src={destination.cover_image || destination.images?.[0] || "https://images.unsplash.com/photo-1506744038136-46273834b3fb?auto=format&fit=crop&w=1200&q=80"} 
          alt={destination.name} 
          className="w-full h-72 object-cover" 
          onError={(e) => {
            e.target.src = "https://images.unsplash.com/photo-1506744038136-46273834b3fb?auto=format&fit=crop&w=1200&q=80";
          }}
        />
        <div className="p-8">
          <div className="flex justify-between items-start mb-2">
            <h1 className="text-4xl font-bold text-gray-800 dark:text-slate-100">{destination.name}</h1>
            <button 
              onClick={speakDescription}
              className="flex items-center gap-2 bg-brand-100 dark:bg-brand-900/50 text-brand-700 dark:text-brand-300 px-4 py-2 rounded-full font-medium hover:bg-brand-200 dark:hover:bg-brand-800 transition"
              title="Listen to description"
            >
              🔊 {t('Listen')}
            </button>
          </div>
          <p className="text-lg text-gray-500 dark:text-slate-400 mb-6">{destination.state}, {destination.country}</p>
          <p className="text-gray-700 dark:text-slate-200 leading-relaxed">{destination.description}</p>
        </div>
      </div>

      <div>
        <h2 className="text-2xl font-bold text-gray-800 dark:text-slate-100 mb-6">{t('Top Places to Visit in')} {destination.name}</h2>
        {places.length === 0 ? (
          <p className="text-gray-500 dark:text-slate-400">{t('No places listed yet for this destination.')}</p>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            {places.map(p => (
              <Link to={`/places/${p.id}`} key={p.id} className="block group">
                <div className="bg-white dark:bg-slate-800 rounded-xl shadow overflow-hidden h-full transition-transform transform group-hover:-translate-y-1 group-hover:shadow-lg flex flex-col">
                  <div className="h-44 overflow-hidden bg-gray-100 dark:bg-slate-700">
                    <img 
                      src={p.images?.[0] || "https://images.unsplash.com/photo-1524492412937-b28074a5d7da?auto=format&fit=crop&w=800&q=80"} 
                      alt={p.name} 
                      className="w-full h-full object-cover group-hover:scale-105 transition duration-300"
                      onError={(e) => {
                        e.target.src = "https://images.unsplash.com/photo-1524492412937-b28074a5d7da?auto=format&fit=crop&w=800&q=80";
                      }}
                    />
                  </div>
                  <div className="p-5 flex flex-col flex-1">
                    <h3 className="text-xl font-semibold mb-2 text-gray-800 dark:text-slate-100 group-hover:text-brand-600 transition-colors">{p.name}</h3>
                    <p className="text-gray-600 dark:text-slate-300 text-sm line-clamp-3 mb-4 flex-1">{p.description}</p>
                    <div className="flex justify-between items-center mt-auto">
                      <span className="text-brand-600 font-medium">★ {p.rating.toFixed(1)}</span>
                      <span className="text-gray-400">{'💵'.repeat(p.price_level)}</span>
                    </div>
                  </div>
                </div>
              </Link>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
