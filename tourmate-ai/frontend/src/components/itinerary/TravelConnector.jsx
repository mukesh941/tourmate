import React from 'react';
import { Navigation, Car, Bus, Train, Bike } from 'lucide-react';

export default function TravelConnector({ currentActivity, nextActivity }) {
  if (!currentActivity || !nextActivity) return null;

  // Ideally, travel info comes from the backend schedule array if it includes transit nodes
  // If not, we can infer or use a generic connector. The prompt mentioned:
  // "Allow transport options: Walk, Taxi, Bus, Metro, Car"
  // "Show recommended transport: AI Recommended"

  // We'll extract transit info if this is a transit activity, or use default props for now.
  const travelMode = nextActivity.travelMode || "Taxi";
  const travelTime = nextActivity.travel_time_minutes || currentActivity.travel_time_minutes || 30;
  const distance = nextActivity.distance || "4.8 km";
  const estCost = nextActivity.estimated_cost || 150;
  const aiNote = nextActivity.aiReason || "Take a cab because this route is faster during afternoon traffic.";

  const ModeIcon = travelMode.toLowerCase() === 'car' || travelMode.toLowerCase() === 'taxi' ? Car :
                   travelMode.toLowerCase() === 'bus' ? Bus :
                   travelMode.toLowerCase() === 'train' || travelMode.toLowerCase() === 'metro' ? Train : Bike;

  return (
    <div className="relative pl-14 my-2">
      {/* The actual line connecting nodes */}
      <div className="absolute top-0 bottom-0 left-[21px] w-[2px] bg-dashed-line border-l-2 border-dashed border-gray-300 dark:border-slate-700 h-full"></div>
      
      <div className="bg-gray-50/80 dark:bg-slate-800/40 rounded-2xl p-4 border border-gray-100 dark:border-slate-700/50 flex flex-col md:flex-row items-start md:items-center justify-between gap-4 py-3 ml-2 group">
        
        <div className="flex items-center gap-4">
          <div className="w-10 h-10 rounded-full bg-white dark:bg-slate-800 border border-gray-200 dark:border-slate-700 flex items-center justify-center text-gray-500 shadow-sm z-10 relative -ml-7 group-hover:scale-110 transition-transform">
            <ModeIcon className="w-4 h-4" />
          </div>
          
          <div>
            <div className="flex items-center gap-3">
              <span className="font-bold text-gray-900 dark:text-white text-sm">{travelTime} min</span>
              <span className="text-gray-500 text-xs font-semibold">{distance}</span>
              <span className="text-gray-500 text-xs font-semibold">{travelMode}</span>
            </div>
            <div className="text-emerald-600 dark:text-emerald-400 text-xs font-bold mt-0.5">
              Est. cost: ₹{estCost}
            </div>
          </div>
        </div>

        {aiNote && (
          <div className="bg-brand-50/50 dark:bg-brand-900/20 px-3 py-2 rounded-xl text-xs flex items-start gap-2 max-w-sm border border-brand-100 dark:border-brand-800/30">
            <span className="text-sm shrink-0">✨</span>
            <p className="text-gray-700 dark:text-slate-300">
              <span className="font-bold text-brand-600 dark:text-brand-400">AI Recommended: </span> 
              {aiNote}
            </p>
          </div>
        )}

      </div>
    </div>
  );
}
