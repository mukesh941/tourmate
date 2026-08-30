import { useState, useEffect } from "react";
import axios from "axios";
import { useAuth } from "../context/AuthContext";

export default function OnboardingModal({ isOpen, onClose, onComplete }) {
  const { token } = useAuth();
  const [step, setStep] = useState(1);
  const [submitting, setSubmitting] = useState(false);
  const [preferences, setPreferences] = useState({
    interests: [],
    travel_style: "",
    budget_range: "Moderate",
  });

  const INTERESTS = [
    "History", "Nature", "Culture", "Adventure", 
    "Food", "Shopping", "Architecture"
  ];
  
  const TRAVEL_STYLES = [
    "Solo Explorer", "Family Vacation", "Romantic Getaway", "Friends Trip"
  ];

  if (!isOpen) return null;

  const toggleInterest = (interest) => {
    setPreferences(prev => {
      const isSelected = prev.interests.includes(interest);
      if (isSelected) {
        return { ...prev, interests: prev.interests.filter(i => i !== interest) };
      } else {
        return { ...prev, interests: [...prev.interests, interest] };
      }
    });
  };

  const handleNext = () => setStep(2);
  const handleBack = () => setStep(1);

  const handleSubmit = async () => {
    setSubmitting(true);
    try {
      await axios.put(
        `${import.meta.env.VITE_API_BASE_URL}/users/preferences`,
        preferences,
        { headers: { Authorization: `Bearer ${token}` } }
      );
      onComplete();
      onClose();
    } catch (err) {
      console.error("Failed to save preferences:", err);
      alert("Failed to save preferences. Please try again.");
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="fixed inset-0 bg-black/60 backdrop-blur-sm flex items-center justify-center p-4 z-50">
      <div className="bg-white dark:bg-slate-800 rounded-2xl w-full max-w-lg shadow-2xl overflow-hidden animate-slide-up">
        <div className="bg-gradient-to-r from-brand-600 to-brand-700 p-6 text-white">
          <h2 className="text-2xl font-bold">Welcome to TourMate AI!</h2>
          <p className="text-brand-100 mt-1">Let's personalize your experience.</p>
        </div>
        
        <div className="p-6">
          {step === 1 && (
            <div className="space-y-6">
              <div>
                <h3 className="text-lg font-semibold text-gray-800 dark:text-slate-100 mb-3">What are your main interests?</h3>
                <div className="flex flex-wrap gap-2">
                  {INTERESTS.map(interest => {
                    const isSelected = preferences.interests.includes(interest);
                    return (
                      <button
                        key={interest}
                        type="button"
                        onClick={() => toggleInterest(interest)}
                        className={`px-4 py-2 rounded-full border text-sm font-medium transition-colors ${
                          isSelected 
                            ? "bg-brand-100 border-brand-500 text-brand-700" 
                            : "bg-white dark:bg-slate-800 border-gray-300 dark:border-slate-600 text-gray-700 dark:text-slate-200 hover:border-brand-300 hover:bg-brand-50"
                        }`}
                      >
                        {interest}
                      </button>
                    );
                  })}
                </div>
              </div>
              <div className="flex justify-end pt-4">
                <button
                  onClick={handleNext}
                  disabled={preferences.interests.length === 0}
                  className="bg-brand-600 hover:bg-brand-700 text-white px-6 py-2 rounded-xl font-medium transition disabled:opacity-50"
                >
                  Next Step &rarr;
                </button>
              </div>
            </div>
          )}

          {step === 2 && (
            <div className="space-y-6">
              <div>
                <h3 className="text-lg font-semibold text-gray-800 dark:text-slate-100 mb-3">What is your typical travel style?</h3>
                <div className="grid grid-cols-2 gap-3">
                  {TRAVEL_STYLES.map(style => (
                    <button
                      key={style}
                      type="button"
                      onClick={() => setPreferences({ ...preferences, travel_style: style })}
                      className={`p-3 border rounded-xl text-sm font-medium transition-colors text-left ${
                        preferences.travel_style === style
                          ? "bg-brand-100 border-brand-500 text-brand-700 ring-1 ring-brand-500"
                          : "bg-white dark:bg-slate-800 border-gray-200 dark:border-slate-700 text-gray-700 dark:text-slate-200 hover:border-brand-300 hover:bg-brand-50"
                      }`}
                    >
                      {style}
                    </button>
                  ))}
                </div>
              </div>

              <div>
                <h3 className="text-lg font-semibold text-gray-800 dark:text-slate-100 mb-3">Budget Range</h3>
                <select 
                  className="w-full border-gray-300 dark:border-slate-600 rounded-xl px-4 py-3 bg-gray-50 dark:bg-slate-900/50 text-gray-800 dark:text-slate-100 focus:ring-brand-500 focus:border-brand-500 border outline-none"
                  value={preferences.budget_range}
                  onChange={(e) => setPreferences({ ...preferences, budget_range: e.target.value })}
                >
                  <option value="Budget-friendly">Budget-friendly</option>
                  <option value="Moderate">Moderate</option>
                  <option value="Luxury">Luxury</option>
                </select>
              </div>

              <div className="flex justify-between pt-4 border-t border-gray-100 dark:border-slate-700">
                <button
                  onClick={handleBack}
                  className="text-gray-500 dark:text-slate-400 hover:text-gray-700 dark:text-slate-200 font-medium px-4 py-2"
                >
                  &larr; Back
                </button>
                <button
                  onClick={handleSubmit}
                  disabled={submitting || !preferences.travel_style}
                  className="bg-brand-600 hover:bg-brand-700 text-white px-6 py-2 rounded-xl font-medium transition disabled:opacity-50 shadow-md dark:shadow-none shadow-brand-500/20 flex items-center"
                >
                  {submitting ? "Saving..." : "Complete Setup"}
                </button>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
