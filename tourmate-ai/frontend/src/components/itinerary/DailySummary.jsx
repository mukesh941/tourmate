import React from 'react';
import { Sun, Moon, MapPin, Map, Clock, IndianRupee } from 'lucide-react';

export default function DailySummary({ dayPlan }) {
  if (!dayPlan) return null;

  const activities = dayPlan.activities || [];
  
  // Calculate summary stats
  const firstActivity = activities[0];
  const lastActivity = activities[activities.length - 1];
  const startTime = firstActivity?.start_time || "09:00 AM";
  const endTime = lastActivity?.end_time || "06:00 PM";
  
  const placeCount = activities.filter(a => !a.activity_type?.toLowerCase().includes("transit")).length;
  
  // Approx distance calculation (mocked based on travel time if real distance not available)
  const totalTravelMins = activities.reduce((sum, a) => sum + (a.travel_time_minutes || 0), 0);
  const approxDistance = activities.reduce((sum, a) => {
    if (a.distance && a.distance.includes("km")) {
      return sum + parseFloat(a.distance);
    }
    // Very rough estimate: 1 km per 3 mins of travel
    return sum + ((a.travel_time_minutes || 0) / 3);
  }, 0);
  
  const dailyCost = activities.reduce((sum, act) => sum + (act.estimated_cost || 0), 0);
  const aiSummary = dayPlan.aiSummary || "Today features a balanced mix of sightseeing and local experiences.";

  return (
    <div className="bg-brand-50/50 dark:bg-brand-900/10 rounded-3xl p-6 md:p-8 border border-brand-100 dark:border-brand-800/50 mb-8">
      <h2 className="text-xl font-bold text-gray-900 dark:text-white mb-6">Today's Plan</h2>
      
      <div className="grid grid-cols-2 md:grid-cols-5 gap-6 mb-6">
        <div className="flex flex-col gap-1">
          <span className="flex items-center gap-1.5 text-xs font-bold text-gray-500 uppercase tracking-wider">
            <Sun className="w-4 h-4 text-amber-500" /> Start
          </span>
          <span className="font-semibold text-gray-900 dark:text-white">{startTime}</span>
        </div>
        
        <div className="flex flex-col gap-1">
          <span className="flex items-center gap-1.5 text-xs font-bold text-gray-500 uppercase tracking-wider">
            <Moon className="w-4 h-4 text-indigo-400" /> End
          </span>
          <span className="font-semibold text-gray-900 dark:text-white">{endTime}</span>
        </div>
        
        <div className="flex flex-col gap-1">
          <span className="flex items-center gap-1.5 text-xs font-bold text-gray-500 uppercase tracking-wider">
            <MapPin className="w-4 h-4 text-rose-500" /> Places
          </span>
          <span className="font-semibold text-gray-900 dark:text-white">{placeCount} Stops</span>
        </div>

        <div className="flex flex-col gap-1">
          <span className="flex items-center gap-1.5 text-xs font-bold text-gray-500 uppercase tracking-wider">
            <Clock className="w-4 h-4 text-blue-500" /> Travel
          </span>
          <span className="font-semibold text-gray-900 dark:text-white">
            {Math.floor(totalTravelMins / 60)}h {totalTravelMins % 60}m ({Math.round(approxDistance)} km)
          </span>
        </div>

        <div className="flex flex-col gap-1">
          <span className="flex items-center gap-1.5 text-xs font-bold text-gray-500 uppercase tracking-wider">
            <IndianRupee className="w-4 h-4 text-emerald-500" /> Est. Cost
          </span>
          <span className="font-semibold text-gray-900 dark:text-white text-lg">₹{dailyCost.toLocaleString('en-IN')}</span>
        </div>
      </div>
      
      <div className="bg-white dark:bg-slate-900 rounded-2xl p-4 border border-brand-100 dark:border-brand-800/30 flex items-start gap-3">
        <div className="shrink-0 text-xl mt-0.5">✨</div>
        <div>
          <p className="text-xs font-bold text-brand-600 dark:text-brand-400 uppercase tracking-wider mb-1">AI Note</p>
          <p className="text-sm text-gray-700 dark:text-slate-300 leading-relaxed">{aiSummary}</p>
        </div>
      </div>
    </div>
  );
}
