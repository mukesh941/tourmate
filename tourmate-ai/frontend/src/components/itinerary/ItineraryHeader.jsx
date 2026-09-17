import React from 'react';
import { Calendar, Users, MapPin, Activity, Clock, IndianRupee, Save, Share2, Edit2, RefreshCw } from 'lucide-react';

export default function ItineraryHeader({ 
  title, 
  destinationName, 
  days, 
  travelers, 
  tripStyle, 
  budget, 
  totalEstimatedCost, 
  totalEstimatedTravelMinutes, 
  onRegenerate, 
  onSave, 
  saving 
}) {
  return (
    <div className="bg-white dark:bg-slate-900 rounded-3xl shadow-sm border border-gray-200 dark:border-slate-800 p-6 md:p-8 mb-8 animate-fade-in-up">
      <div className="flex flex-col md:flex-row justify-between gap-6">
        <div>
          <div className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-brand-50 dark:bg-brand-900/30 text-brand-600 dark:text-brand-400 font-bold text-xs uppercase tracking-wider mb-4 border border-brand-100 dark:border-brand-800/50">
            <span>✨</span> AI Optimized
          </div>
          <h1 className="text-3xl md:text-4xl font-extrabold text-gray-900 dark:text-white mb-2 tracking-tight">
            {title || `${destinationName} Trip`}
          </h1>
          <div className="flex items-center gap-2 text-gray-500 dark:text-slate-400 font-medium mb-6">
            <MapPin className="w-4 h-4" /> 
            <span>{destinationName}</span>
          </div>
          
          <div className="flex flex-wrap gap-4 text-sm">
            <div className="flex items-center gap-2 bg-gray-50 dark:bg-slate-800/50 px-3 py-1.5 rounded-lg border border-gray-100 dark:border-slate-700">
              <Calendar className="w-4 h-4 text-brand-500" />
              <span className="font-semibold text-gray-700 dark:text-slate-300">{days} Days</span>
            </div>
            <div className="flex items-center gap-2 bg-gray-50 dark:bg-slate-800/50 px-3 py-1.5 rounded-lg border border-gray-100 dark:border-slate-700">
              <Users className="w-4 h-4 text-brand-500" />
              <span className="font-semibold text-gray-700 dark:text-slate-300">{travelers || '2 Travelers'}</span>
            </div>
            <div className="flex items-center gap-2 bg-gray-50 dark:bg-slate-800/50 px-3 py-1.5 rounded-lg border border-gray-100 dark:border-slate-700">
              <Activity className="w-4 h-4 text-brand-500" />
              <span className="font-semibold text-gray-700 dark:text-slate-300">{tripStyle || 'Culture • Sightseeing'}</span>
            </div>
          </div>
        </div>

        <div className="flex flex-col justify-between items-start md:items-end gap-6">
          <div className="flex gap-2">
            <button onClick={onRegenerate} className="p-2 bg-gray-100 hover:bg-gray-200 dark:bg-slate-800 dark:hover:bg-slate-700 text-gray-700 dark:text-slate-300 rounded-xl transition-colors tooltip" title="Regenerate Itinerary">
              <RefreshCw className="w-4 h-4" />
            </button>
            <button className="p-2 bg-gray-100 hover:bg-gray-200 dark:bg-slate-800 dark:hover:bg-slate-700 text-gray-700 dark:text-slate-300 rounded-xl transition-colors tooltip" title="Edit Trip">
              <Edit2 className="w-4 h-4" />
            </button>
            <button className="p-2 bg-gray-100 hover:bg-gray-200 dark:bg-slate-800 dark:hover:bg-slate-700 text-gray-700 dark:text-slate-300 rounded-xl transition-colors tooltip" title="Share">
              <Share2 className="w-4 h-4" />
            </button>
            <button onClick={onSave} disabled={saving} className="px-4 py-2 bg-brand-600 hover:bg-brand-700 text-white font-bold rounded-xl text-sm flex items-center gap-2 transition-colors shadow-sm disabled:opacity-70">
              <Save className="w-4 h-4" /> {saving ? "Saving..." : "Save"}
            </button>
          </div>

          <div className="flex gap-6 text-right">
            <div>
              <p className="text-[10px] text-gray-500 dark:text-slate-500 uppercase tracking-wider font-bold mb-1">Total Est. Budget</p>
              <p className="text-xl font-black text-emerald-600 dark:text-emerald-400 flex items-center justify-end gap-1">
                <IndianRupee className="w-4 h-4" /> {totalEstimatedCost ? totalEstimatedCost.toLocaleString('en-IN') : '0'}
              </p>
            </div>
            {totalEstimatedTravelMinutes > 0 && (
              <div>
                <p className="text-[10px] text-gray-500 dark:text-slate-500 uppercase tracking-wider font-bold mb-1">Total Travel Time</p>
                <p className="text-xl font-black text-gray-900 dark:text-white flex items-center justify-end gap-1">
                  <Clock className="w-4 h-4 text-brand-500" /> {Math.floor(totalEstimatedTravelMinutes / 60)}h {totalEstimatedTravelMinutes % 60}m
                </p>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
