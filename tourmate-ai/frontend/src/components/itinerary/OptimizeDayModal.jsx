import React, { useState } from 'react';
import { Sparkles, Check, X, RefreshCw } from 'lucide-react';
import axios from 'axios';
import { useAuth } from '../../context/AuthContext';

export default function OptimizeDayModal({ isOpen, onClose, dayPlan, onApply }) {
  const { token } = useAuth();
  const [optimizing, setOptimizing] = useState(false);
  const [optimizedData, setOptimizedData] = useState(null);
  const [error, setError] = useState('');

  const handleOptimize = async () => {
    setOptimizing(true);
    setError('');
    try {
      const res = await axios.post(
        `${import.meta.env.VITE_API_BASE_URL}/itineraries/optimize`,
        {
          day_schedule: dayPlan,
          context: "Please reduce travel time and add buffers if schedule is too tight."
        },
        { headers: { Authorization: `Bearer ${token}` } }
      );
      setOptimizedData(res.data.data);
    } catch (err) {
      console.error("Optimization failed", err);
      setError("Failed to optimize day. Please try again.");
    } finally {
      setOptimizing(false);
    }
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black/60 backdrop-blur-sm z-50 flex items-center justify-center p-4">
      <div className="bg-white dark:bg-slate-900 w-full max-w-md rounded-3xl p-6 shadow-2xl border border-brand-100 dark:border-brand-800 animate-fade-in-up">
        
        {!optimizing && !optimizedData && (
          <div className="text-center">
            <div className="w-16 h-16 bg-brand-50 dark:bg-brand-900/30 text-brand-600 dark:text-brand-400 rounded-full flex items-center justify-center mx-auto mb-4">
              <Sparkles className="w-8 h-8" />
            </div>
            <h3 className="text-2xl font-bold text-gray-900 dark:text-white mb-2">Optimize My Day</h3>
            <p className="text-sm text-gray-600 dark:text-slate-400 mb-6">
              AI will analyze distance, travel time, crowd levels, and your budget to suggest a better schedule for Day {dayPlan.day}.
            </p>
            {error && <p className="text-rose-500 text-sm mb-4">{error}</p>}
            
            <div className="flex gap-3">
              <button onClick={onClose} className="flex-1 py-3 bg-gray-100 hover:bg-gray-200 dark:bg-slate-800 dark:hover:bg-slate-700 font-bold rounded-xl text-gray-700 dark:text-slate-300 transition-colors">
                Cancel
              </button>
              <button onClick={handleOptimize} className="flex-1 py-3 bg-brand-600 hover:bg-brand-700 text-white font-bold rounded-xl transition-colors shadow-sm flex items-center justify-center gap-2">
                <Sparkles className="w-4 h-4" /> Optimize
              </button>
            </div>
          </div>
        )}

        {optimizing && (
          <div className="text-center py-8">
            <div className="w-16 h-16 bg-brand-50 dark:bg-brand-900/30 text-brand-600 dark:text-brand-400 rounded-full flex items-center justify-center mx-auto mb-6">
              <RefreshCw className="w-8 h-8 animate-spin" />
            </div>
            <h3 className="text-lg font-bold text-gray-900 dark:text-white mb-2">AI is working its magic...</h3>
            <ul className="text-sm text-gray-500 dark:text-slate-400 space-y-2 text-left max-w-[200px] mx-auto mt-6">
              <li className="flex items-center gap-2"><Check className="w-4 h-4 text-emerald-500"/> Analyzing distance</li>
              <li className="flex items-center gap-2"><Check className="w-4 h-4 text-emerald-500"/> Checking opening hours</li>
              <li className="flex items-center gap-2 text-gray-400 animate-pulse"><RefreshCw className="w-3 h-3"/> Optimizing route</li>
            </ul>
          </div>
        )}

        {optimizedData && !optimizing && (
          <div>
            <div className="flex justify-between items-start mb-6">
              <div>
                <h3 className="text-xl font-bold text-gray-900 dark:text-white flex items-center gap-2">
                  <Sparkles className="w-5 h-5 text-brand-500" /> Day Optimized
                </h3>
                <p className="text-sm text-gray-600 dark:text-slate-400 mt-1">{optimizedData.message}</p>
              </div>
              <button onClick={onClose} className="text-gray-400 hover:text-gray-600 dark:hover:text-slate-300">
                <X className="w-5 h-5" />
              </button>
            </div>

            <div className="bg-gray-50 dark:bg-slate-800/50 rounded-xl p-4 border border-gray-100 dark:border-slate-700 mb-6">
              <p className="text-xs font-bold uppercase tracking-wider text-gray-500 mb-3">AI Changes:</p>
              <ul className="space-y-2 text-sm text-gray-700 dark:text-slate-300">
                <li className="flex items-start gap-2"><span className="text-brand-500 mt-0.5">•</span> Reduced travel by 15 minutes</li>
                <li className="flex items-start gap-2"><span className="text-brand-500 mt-0.5">•</span> Added a 30-minute buffer for lunch</li>
                <li className="flex items-start gap-2"><span className="text-brand-500 mt-0.5">•</span> Reordered activities to avoid peak traffic</li>
              </ul>
            </div>

            <div className="flex gap-3">
              <button onClick={onClose} className="flex-1 py-3 bg-gray-100 hover:bg-gray-200 dark:bg-slate-800 dark:hover:bg-slate-700 font-bold rounded-xl text-gray-700 dark:text-slate-300 transition-colors">
                Keep Current
              </button>
              <button 
                onClick={() => {
                  onApply(optimizedData.optimized_schedule);
                  onClose();
                }} 
                className="flex-1 py-3 bg-brand-600 hover:bg-brand-700 text-white font-bold rounded-xl transition-colors shadow-sm"
              >
                Apply Changes
              </button>
            </div>
          </div>
        )}

      </div>
    </div>
  );
}
