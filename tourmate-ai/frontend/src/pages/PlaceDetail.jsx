import { useState, useEffect } from "react";
import { useParams } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import api from "../api/axios";
import { toggleFavorite, getFavorites, addReview, getReviews, getSentimentSummary } from "../api/interactions";
import { useTranslation } from "react-i18next";
import ShareModal from "../components/ShareModal";

export default function PlaceDetail() {
  const { id } = useParams();
  const { user } = useAuth();
  const { t, i18n } = useTranslation();
  const [place, setPlace] = useState(null);
  const [isFavorite, setIsFavorite] = useState(false);
  const [reviews, setReviews] = useState([]);
  const [sentimentSummary, setSentimentSummary] = useState(null);
  const [newReview, setNewReview] = useState({ rating: 5, comment: "" });
  const [loading, setLoading] = useState(true);
  const [submitError, setSubmitError] = useState("");
  const [isPlaying, setIsPlaying] = useState(false);
  
  // Share modal state
  const [shareOpen, setShareOpen] = useState(false);

  useEffect(() => {
    const fetchData = async () => {
      try {
        const placeRes = await api.get(`/places/${id}`);
        setPlace(placeRes.data.data);
        
        const reviewsData = await getReviews(id);
        setReviews(reviewsData);

        try {
          const summary = await getSentimentSummary(id);
          setSentimentSummary(summary);
        } catch (e) {
          // Fallback if summary endpoint has minor hitch
        }

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
    
    utterance.lang = i18n.language === 'hi' ? 'hi-IN' : 'en-US';
    utterance.onend = () => setIsPlaying(false);
    
    window.speechSynthesis.speak(utterance);
    setIsPlaying(true);
  };
  
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
      
      try {
        const summary = await getSentimentSummary(id);
        setSentimentSummary(summary);
      } catch (e) {}

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
      {/* Place Details Card */}
      <div className="bg-white dark:bg-slate-800 rounded-xl shadow overflow-hidden">
        {place.images && place.images.length > 0 && (
          <img 
            src={place.images[0]} 
            alt={place.name} 
            className="w-full h-80 object-cover"
          />
        )}
        <div className="p-8">
          <div className="flex justify-between items-start mb-4">
            <div>
              <h1 className="text-3xl font-bold text-gray-900 dark:text-white">{place.name}</h1>
              <div className="flex items-center gap-2 mt-2">
                <span className="bg-brand-50 text-brand-700 px-2.5 py-0.5 rounded-full text-sm font-semibold">
                  ★ {place.rating ? place.rating.toFixed(1) : 'New'}
                </span>
                <span className="text-gray-500 dark:text-slate-400 text-sm">
                  ⏱️ {place.visit_duration_minutes || 60} mins
                </span>
                <button
                  onClick={handleAudioGuide}
                  className={`ml-2 px-3 py-1 rounded-full text-xs font-semibold flex items-center gap-1.5 transition-all ${
                    isPlaying 
                      ? "bg-red-500 text-white animate-pulse" 
                      : "bg-indigo-50 text-indigo-700 hover:bg-indigo-100 dark:bg-indigo-900/40 dark:text-indigo-300"
                  }`}
                >
                  <span>{isPlaying ? "⏹️" : "🔊"}</span>
                  <span>{isPlaying ? "Stop Audio" : "Listen Audio Guide"}</span>
                </button>
              </div>
            </div>

            {/* Favorite & Share Icons */}
            <div className="flex items-center gap-2">
              <button 
                onClick={() => setShareOpen(true)}
                className="p-2.5 rounded-full border border-gray-200 dark:border-slate-700 hover:bg-brand-50 text-brand-600 transition"
                title="Share this destination"
              >
                📤
              </button>
              <button 
                onClick={handleToggleFavorite}
                className={`p-2.5 rounded-full transition-colors ${
                  isFavorite ? "text-red-500 bg-red-50" : "text-gray-400 hover:text-red-500 border border-gray-200 dark:border-slate-700"
                }`}
                title={isFavorite ? "Remove from Favorites" : "Add to Favorites"}
              >
                <svg xmlns="http://www.w3.org/2000/svg" className="h-6 w-6" fill={isFavorite ? "currentColor" : "none"} viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4.318 6.318a4.5 4.5 0 000 6.364L12 20.364l7.682-7.682a4.5 4.5 0 00-6.364-6.364L12 7.636l-1.318-1.318a4.5 4.5 0 00-6.364 0z" />
                </svg>
              </button>
            </div>
          </div>

          <p className="text-gray-700 dark:text-slate-300 leading-relaxed text-lg mb-6">{place.description}</p>

          {/* Action Buttons Row */}
          <div className="flex flex-wrap gap-3 mb-6">
            {place.location?.coordinates && (
              <a
                href={`https://www.google.com/maps/dir/?api=1&destination=${place.location.coordinates[1]},${place.location.coordinates[0]}&travelmode=driving`}
                target="_blank"
                rel="noopener noreferrer"
                className="flex items-center gap-2 bg-blue-600 hover:bg-blue-700 text-white font-bold px-5 py-2.5 rounded-xl transition shadow-md hover:shadow-lg hover:-translate-y-0.5"
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
                className="flex items-center gap-2 bg-green-600 hover:bg-green-700 text-white font-bold px-5 py-2.5 rounded-xl transition shadow-md hover:shadow-lg hover:-translate-y-0.5"
              >
                <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" viewBox="0 0 20 20" fill="currentColor">
                  <path d="M9 9a2 2 0 114 0 2 2 0 01-4 0z" />
                  <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm1-13a4 4 0 00-3.446 6.032l-2.261 2.26a1 1 0 101.414 1.415l2.261-2.261A4 4 0 1011 5z" clipRule="evenodd" />
                </svg>
                View on Maps
              </a>
            )}
            <button
              onClick={() => setShareOpen(true)}
              className="flex items-center gap-2 bg-purple-600 hover:bg-purple-700 text-white font-bold px-5 py-2.5 rounded-xl transition shadow-md hover:shadow-lg hover:-translate-y-0.5"
            >
              <span>📤</span>
              <span>Share Destination</span>
            </button>
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

      {/* Reviews & NLP Sentiment Section */}
      <div className="bg-white dark:bg-slate-800 rounded-2xl shadow p-8">
        <div className="flex flex-wrap items-center justify-between gap-4 mb-6">
          <div>
            <h2 className="text-2xl font-bold text-gray-900 dark:text-white">Tourist Reviews</h2>
            <p className="text-xs text-gray-500 dark:text-slate-400">Real feedback with automated NLP sentiment intelligence</p>
          </div>
        </div>

        {/* NLP Sentiment Summary Bar */}
        {sentimentSummary && sentimentSummary.total_reviews > 0 && (
          <div className="mb-8 p-4 rounded-2xl bg-gradient-to-r from-emerald-50 via-teal-50 to-blue-50 dark:from-slate-700 dark:to-slate-700/80 border border-emerald-200 dark:border-slate-600">
            <div className="flex flex-wrap items-center justify-between gap-2 mb-3">
              <div className="flex items-center gap-2">
                <span className="text-2xl">{sentimentSummary.overall_emoji || "😊"}</span>
                <div>
                  <h4 className="font-bold text-sm text-gray-900 dark:text-white">
                    NLP Sentiment Analysis: {sentimentSummary.overall_sentiment} Tourist Perception
                  </h4>
                  <p className="text-xs text-gray-600 dark:text-slate-300">
                    Calculated from {sentimentSummary.total_reviews} verified tourist reviews using sentiment valence heuristics
                  </p>
                </div>
              </div>
              <div className="flex items-center gap-2 text-xs font-bold">
                <span className="px-2.5 py-1 rounded-full bg-emerald-100 text-emerald-800 dark:bg-emerald-900/60 dark:text-emerald-300">
                  {sentimentSummary.positive_pct}% Positive
                </span>
                {sentimentSummary.neutral_pct > 0 && (
                  <span className="px-2.5 py-1 rounded-full bg-amber-100 text-amber-800 dark:bg-amber-900/60 dark:text-amber-300">
                    {sentimentSummary.neutral_pct}% Neutral
                  </span>
                )}
                {sentimentSummary.negative_pct > 0 && (
                  <span className="px-2.5 py-1 rounded-full bg-rose-100 text-rose-800 dark:bg-rose-900/60 dark:text-rose-300">
                    {sentimentSummary.negative_pct}% Critical
                  </span>
                )}
              </div>
            </div>

            {/* Visual multi-segment bar */}
            <div className="w-full h-2.5 rounded-full overflow-hidden bg-gray-200 dark:bg-slate-600 flex">
              <div style={{ width: `${sentimentSummary.positive_pct}%` }} className="bg-emerald-500"></div>
              <div style={{ width: `${sentimentSummary.neutral_pct}%` }} className="bg-amber-400"></div>
              <div style={{ width: `${sentimentSummary.negative_pct}%` }} className="bg-rose-500"></div>
            </div>
          </div>
        )}
        
        {/* Write a Review Form */}
        {user ? (
          <form onSubmit={handleReviewSubmit} className="mb-8 p-5 bg-gray-50 dark:bg-slate-700/50 rounded-2xl border border-gray-100 dark:border-slate-700">
            <h3 className="font-bold mb-3 text-gray-900 dark:text-slate-100">Write a Tourist Review</h3>
            {submitError && <div className="text-red-500 mb-3 text-sm">{submitError}</div>}
            <div className="mb-3">
              <label className="block text-xs font-bold uppercase tracking-wider text-gray-600 dark:text-slate-300 mb-1">Your Rating</label>
              <select 
                value={newReview.rating} 
                onChange={e => setNewReview({...newReview, rating: Number(e.target.value)})}
                className="w-32 px-3 py-2 border dark:border-slate-600 dark:bg-slate-800 rounded-xl text-sm font-semibold"
              >
                {[5,4,3,2,1].map(num => (
                  <option key={num} value={num}>{num} Stars</option>
                ))}
              </select>
            </div>
            <div className="mb-4">
              <label className="block text-xs font-bold uppercase tracking-wider text-gray-600 dark:text-slate-300 mb-1">Your Experience</label>
              <textarea 
                value={newReview.comment}
                onChange={e => setNewReview({...newReview, comment: e.target.value})}
                required
                rows="3"
                className="w-full px-3 py-2.5 border dark:border-slate-600 dark:bg-slate-800 rounded-xl focus:ring-2 focus:ring-brand-500 text-sm"
                placeholder="Describe the atmosphere, cleanliness, accessibility, or tips for fellow travelers..."
              ></textarea>
            </div>
            <button type="submit" className="bg-brand-600 text-white px-5 py-2.5 rounded-xl hover:bg-brand-500 font-bold text-sm transition shadow">
              Submit Review & Analyze Sentiment
            </button>
          </form>
        ) : (
          <p className="text-gray-500 dark:text-slate-400 mb-8 text-sm">Please log in to share your review.</p>
        )}

        {/* Reviews List */}
        <div className="space-y-4">
          {reviews.length === 0 ? (
            <p className="text-gray-500 dark:text-slate-400 text-sm">No reviews yet. Be the first to share your experience!</p>
          ) : (
            reviews.map(rev => {
              const label = rev.sentiment_label || "Positive";
              const isPos = label === "Positive";
              const isNeg = label === "Negative";
              return (
                <div key={rev.id} className="border-b dark:border-slate-700 pb-5 last:border-0">
                  <div className="flex flex-wrap justify-between items-center gap-2 mb-1.5">
                    <div className="flex items-center gap-2">
                      <span className="font-bold text-gray-900 dark:text-slate-100 text-sm">{rev.user_name}</span>
                      {/* Sentiment Badge */}
                      <span className={`px-2 py-0.5 rounded-full text-xs font-bold flex items-center gap-1 ${
                        isPos 
                          ? "bg-emerald-100 text-emerald-800 dark:bg-emerald-900/50 dark:text-emerald-300"
                          : isNeg
                          ? "bg-rose-100 text-rose-800 dark:bg-rose-900/50 dark:text-rose-300"
                          : "bg-amber-100 text-amber-800 dark:bg-amber-900/50 dark:text-amber-300"
                      }`}>
                        <span>{rev.sentiment_emoji || (isPos ? "😊" : isNeg ? "🙁" : "😐")}</span>
                        <span>{label} {rev.sentiment_score ? `(${Math.round(rev.sentiment_score * 100)}%)` : ""}</span>
                      </span>
                    </div>
                    <span className="text-amber-500 font-bold text-sm">{'★'.repeat(rev.rating)}{'☆'.repeat(5-rev.rating)}</span>
                  </div>
                  <p className="text-xs text-gray-400 mb-2">{new Date(rev.created_at).toLocaleDateString()}</p>
                  <p className="text-gray-700 dark:text-slate-300 text-sm leading-relaxed">{rev.comment}</p>
                </div>
              );
            })
          )}
        </div>
      </div>

      {/* Social Share Modal */}
      <ShareModal
        isOpen={shareOpen}
        onClose={() => setShareOpen(false)}
        title={place.name}
        text={`✨ Discover ${place.name}: ${place.description?.slice(0, 140)}...`}
        url={window.location.href}
      />
    </div>
  );
}
