import { useState, useEffect } from "react";
import { useParams } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import api from "../api/axios";
import { toggleFavorite, getFavorites, addReview, getReviews } from "../api/interactions";
import { useTranslation } from "react-i18next";

export default function PlaceDetail() {
  const { id } = useParams();
  const { user } = useAuth();
  const { t, i18n } = useTranslation();
  const [place, setPlace] = useState(null);
  const [isFavorite, setIsFavorite] = useState(false);
  const [reviews, setReviews] = useState([]);
  const [newReview, setNewReview] = useState({ rating: 5, comment: "" });
  const [loading, setLoading] = useState(true);
  const [submitError, setSubmitError] = useState("");
  const [isPlaying, setIsPlaying] = useState(false);

  useEffect(() => {
    const fetchData = async () => {
      try {
        const placeRes = await api.get(`/places/${id}`);
        setPlace(placeRes.data.data);
        
        const reviewsData = await getReviews(id);
        setReviews(reviewsData);

        if (user) {
          const favs = await getFavorites();
          setIsFavorite(favs.some(f => f.id === id));
        }
      } catch (err) {
        console.error("Error fetching place details:", err);
      } finally {
        setLoading(false);
      }
    };
    fetchData();
  }, [id, user]);

  const handleToggleFavorite = async () => {
    if (!user) return alert("Please log in to save favorites.");
    try {
      const res = await toggleFavorite(id);
      setIsFavorite(res.data.status === "added");
    } catch (err) {
      console.error(err);
    }
  };

  const handleAudioGuide = () => {
    if (!window.speechSynthesis) {
      alert("Text-to-speech is not supported in this browser.");
      return;
    }

    if (isPlaying) {
      window.speechSynthesis.cancel();
      setIsPlaying(false);
      return;
    }

    const text = `${place.name}. ${place.description}`;
    const utterance = new SpeechSynthesisUtterance(text);
    
    // Attempt to set language
    utterance.lang = i18n.language === 'hi' ? 'hi-IN' : 'en-US';
    
    utterance.onend = () => setIsPlaying(false);
    
    window.speechSynthesis.speak(utterance);
    setIsPlaying(true);
  };
  
  // Cleanup speech synthesis on unmount
  useEffect(() => {
    return () => {
      if (window.speechSynthesis) {
        window.speechSynthesis.cancel();
      }
    };
  }, []);

  const handleReviewSubmit = async (e) => {
    e.preventDefault();
    setSubmitError("");
    try {
      await addReview(id, newReview);
      setNewReview({ rating: 5, comment: "" });
      const reviewsData = await getReviews(id);
      setReviews(reviewsData);
      
      // refresh place to get new avg rating
      const placeRes = await api.get(`/places/${id}`);
      setPlace(placeRes.data.data);
    } catch (err) {
      setSubmitError(err.response?.data?.detail || "Failed to submit review");
    }
  };

  if (loading) return <div className="text-center p-10">{t('Loading...')}</div>;
  if (!place) return <div className="text-center p-10">Place not found</div>;

  return (
    <div className="max-w-4xl mx-auto p-4 space-y-8">
      {/* Place Details */}
      <div className="bg-white dark:bg-slate-800 rounded-xl shadow overflow-hidden">
        {place.images && place.images.length > 0 && (
          <img src={place.images[0]} alt={place.name} className="w-full h-72 object-cover" />
        )}
        <div className="p-8">
          <div className="flex justify-between items-start mb-4">
            <div>
              <h1 className="text-4xl font-bold text-gray-800 dark:text-slate-100">{place.name}</h1>
              <div className="flex items-center gap-4 mt-2">
                <span className="text-brand-600 font-bold text-lg">★ {place.rating.toFixed(1)}</span>
                <span className="text-gray-400">{'💵'.repeat(place.price_level)}</span>
                <button 
                  onClick={handleAudioGuide}
                  className={`flex items-center gap-2 px-3 py-1 text-sm rounded-full transition-colors ${isPlaying ? 'bg-brand-100 text-brand-600 dark:bg-brand-900/30' : 'bg-gray-100 text-gray-600 hover:bg-gray-200 dark:bg-slate-700 dark:text-slate-300 dark:hover:bg-slate-600'}`}
                >
                  <span>{isPlaying ? '⏹️ Stop' : `🔊 ${t('Listen')}`}</span>
                </button>
              </div>
            </div>
            <button 
              onClick={handleToggleFavorite}
              className={`p-3 rounded-full transition-colors ${isFavorite ? 'bg-red-100 text-red-500 hover:bg-red-200' : 'bg-gray-100 dark:bg-slate-700 text-gray-400 hover:bg-gray-200 dark:hover:bg-slate-600'}`}
              title={isFavorite ? "Remove from Favorites" : "Add to Favorites"}
            >
              <svg xmlns="http://www.w3.org/2000/svg" className="h-8 w-8" fill={isFavorite ? "currentColor" : "none"} viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4.318 6.318a4.5 4.5 0 000 6.364L12 20.364l7.682-7.682a4.5 4.5 0 00-6.364-6.364L12 7.636l-1.318-1.318a4.5 4.5 0 00-6.364 0z" />
              </svg>
            </button>
          </div>
          <p className="text-gray-700 dark:text-slate-300 leading-relaxed text-lg mb-6">{place.description}</p>

          {/* Action Buttons Row */}
          <div className="flex flex-wrap gap-3 mb-6">
            {place.location?.coordinates && (
              <a
                href={`https://www.google.com/maps/dir/?api=1&destination=${place.location.coordinates[1]},${place.location.coordinates[0]}&travelmode=driving`}
                target="_blank"
                rel="noopener noreferrer"
                className="flex items-center gap-2 bg-blue-600 hover:bg-blue-700 text-white font-bold px-5 py-2.5 rounded-xl transition-all duration-300 shadow-md hover:shadow-lg hover:-translate-y-0.5"
              >
                <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" viewBox="0 0 20 20" fill="currentColor">
                  <path fillRule="evenodd" d="M5.05 4.05a7 7 0 119.9 9.9L10 18.9l-4.95-4.95a7 7 0 010-9.9zM10 11a2 2 0 100-4 2 2 0 000 4z" clipRule="evenodd" />
                </svg>
                Get Directions
              </a>
            )}
            {place.location?.coordinates && (
              <a
                href={`https://www.google.com/maps/search/?api=1&query=${encodeURIComponent(place.name)}`}
                target="_blank"
                rel="noopener noreferrer"
                className="flex items-center gap-2 bg-green-600 hover:bg-green-700 text-white font-bold px-5 py-2.5 rounded-xl transition-all duration-300 shadow-md hover:shadow-lg hover:-translate-y-0.5"
              >
                <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" viewBox="0 0 20 20" fill="currentColor">
                  <path d="M9 9a2 2 0 114 0 2 2 0 01-4 0z" />
                  <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm1-13a4 4 0 00-3.446 6.032l-2.261 2.26a1 1 0 101.414 1.415l2.261-2.261A4 4 0 1011 5z" clipRule="evenodd" />
                </svg>
                View on Maps
              </a>
            )}
          </div>

          {/* Embedded Google Maps */}
          {place.location?.coordinates && (
            <div className="rounded-2xl overflow-hidden shadow-lg mb-6 border border-gray-200 dark:border-slate-600">
              <div className="bg-gray-100 dark:bg-slate-700 px-4 py-3 flex items-center gap-2">
                <span className="text-lg">📍</span>
                <span className="font-semibold text-gray-800 dark:text-slate-100 text-sm">Location — {place.name}</span>
              </div>
              <iframe
                title={`Map of ${place.name}`}
                width="100%"
                height="350"
                style={{ border: 0 }}
                loading="lazy"
                allowFullScreen
                referrerPolicy="no-referrer-when-downgrade"
                src={`https://maps.google.com/maps?q=${place.location.coordinates[1]},${place.location.coordinates[0]}&z=15&output=embed`}
              />
            </div>
          )}

          <div className="grid grid-cols-2 gap-4">
            {place.history && (
              <div>
                <h3 className="font-semibold text-gray-800 dark:text-slate-100 mb-1">History</h3>
                <p className="text-sm text-gray-600 dark:text-slate-400">{place.history}</p>
              </div>
            )}
            {place.cultural_significance && (
              <div>
                <h3 className="font-semibold text-gray-800 dark:text-slate-100 mb-1">Cultural Significance</h3>
                <p className="text-sm text-gray-600 dark:text-slate-400">{place.cultural_significance}</p>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Reviews Section */}
      <div className="bg-white dark:bg-slate-800 rounded-xl shadow p-8">
        <h2 className="text-2xl font-bold text-gray-800 dark:text-slate-100 mb-6">Reviews</h2>
        
        {user ? (
          <form onSubmit={handleReviewSubmit} className="mb-8 p-4 bg-gray-50 dark:bg-slate-700/50 rounded-lg">
            <h3 className="font-semibold mb-3 dark:text-slate-200">Write a Review</h3>
            {submitError && <div className="text-red-500 mb-3 text-sm">{submitError}</div>}
            <div className="mb-3">
              <label className="block text-sm font-medium text-gray-700 dark:text-slate-300 mb-1">Rating</label>
              <select 
                value={newReview.rating} 
                onChange={e => setNewReview({...newReview, rating: Number(e.target.value)})}
                className="w-24 px-3 py-2 border dark:border-slate-600 dark:bg-slate-800 rounded-md"
              >
                {[5,4,3,2,1].map(num => (
                  <option key={num} value={num}>{num} Stars</option>
                ))}
              </select>
            </div>
            <div className="mb-3">
              <label className="block text-sm font-medium text-gray-700 dark:text-slate-300 mb-1">Comment</label>
              <textarea 
                value={newReview.comment}
                onChange={e => setNewReview({...newReview, comment: e.target.value})}
                required
                rows="3"
                className="w-full px-3 py-2 border dark:border-slate-600 dark:bg-slate-800 rounded-md focus:ring-brand-500 focus:border-brand-500"
                placeholder="Share your experience..."
              ></textarea>
            </div>
            <button type="submit" className="bg-brand-600 text-white px-4 py-2 rounded hover:bg-brand-500 font-medium transition">
              Submit Review
            </button>
          </form>
        ) : (
          <p className="text-gray-500 dark:text-slate-400 mb-8">Please log in to write a review.</p>
        )}

        <div className="space-y-4">
          {reviews.length === 0 ? (
            <p className="text-gray-500 dark:text-slate-400">No reviews yet. Be the first!</p>
          ) : (
            reviews.map(rev => (
              <div key={rev.id} className="border-b dark:border-slate-700 pb-4 last:border-0">
                <div className="flex justify-between mb-1">
                  <span className="font-medium text-gray-800 dark:text-slate-200">{rev.user_name}</span>
                  <span className="text-brand-500">{'★'.repeat(rev.rating)}{'☆'.repeat(5-rev.rating)}</span>
                </div>
                <p className="text-sm text-gray-500 dark:text-slate-400 mb-2">{new Date(rev.created_at).toLocaleDateString()}</p>
                <p className="text-gray-700 dark:text-slate-300">{rev.comment}</p>
              </div>
            ))
          )}
        </div>
      </div>
    </div>
  );
}
