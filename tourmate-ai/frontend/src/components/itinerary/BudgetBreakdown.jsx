import React from 'react';
import { IndianRupee, MapPin, Coffee, Car, Navigation } from 'lucide-react';

export default function BudgetBreakdown({ dayPlan, onViewFullBudget }) {
  if (!dayPlan || !dayPlan.activities) return null;

  let attractionsCost = 0;
  let foodCost = 0;
  let transportCost = 0;
  let otherCost = 0;

  dayPlan.activities.forEach(act => {
    const cost = typeof act.estimated_cost === 'number' ? act.estimated_cost : 0;
    const type = (act.activity_type || "").toLowerCase();
    const category = (act.category || "").toLowerCase();

    if (type.includes('transit') || type.includes('transport')) {
      transportCost += cost;
    } else if (type.includes('meal') || type.includes('food') || category.includes('food')) {
      foodCost += cost;
    } else if (type.includes('sightseeing') || category.includes('attraction')) {
      attractionsCost += cost;
    } else {
      otherCost += cost;
    }
  });

  const total = attractionsCost + foodCost + transportCost + otherCost;

  return (
    <div className="bg-white dark:bg-slate-800 rounded-3xl p-6 md:p-8 border border-gray-200 dark:border-slate-700 shadow-sm mt-8 animate-fade-in-up">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h3 className="text-xl font-bold text-gray-900 dark:text-white">Day {dayPlan.day} Cost Breakdown</h3>
          <p className="text-xs text-gray-500 dark:text-slate-400 mt-0.5">Verified monument fees & estimated daily incidentals</p>
        </div>
      </div>
      
      <div className="space-y-4 max-w-sm">
        <div className="flex justify-between items-center text-sm">
          <span className="text-gray-600 dark:text-slate-400 flex items-center gap-2">
            <MapPin className="w-4 h-4 text-brand-500" /> Attractions (Verified Entry)
          </span>
          <span className="font-semibold text-gray-900 dark:text-white">₹{attractionsCost.toLocaleString('en-IN')}</span>
        </div>
        <div className="flex justify-between items-center text-sm">
          <span className="text-gray-600 dark:text-slate-400 flex items-center gap-2">
            <Coffee className="w-4 h-4 text-amber-500" /> Food & Dining (Estimated)
          </span>
          <span className="font-semibold text-gray-900 dark:text-white">₹{foodCost.toLocaleString('en-IN')}</span>
        </div>
        <div className="flex justify-between items-center text-sm">
          <span className="text-gray-600 dark:text-slate-400 flex items-center gap-2">
            <Navigation className="w-4 h-4 text-blue-500" /> Local Transport (Estimated)
          </span>
          <span className="font-semibold text-gray-900 dark:text-white">₹{transportCost.toLocaleString('en-IN')}</span>
        </div>
        {otherCost > 0 && (
          <div className="flex justify-between items-center text-sm">
            <span className="text-gray-600 dark:text-slate-400 flex items-center gap-2">
              <span className="w-4 h-4 flex items-center justify-center text-gray-400">🛍️</span> Other Activities
            </span>
            <span className="font-semibold text-gray-900 dark:text-white">₹{otherCost.toLocaleString('en-IN')}</span>
          </div>
        )}
        
        <div className="pt-4 mt-2 border-t border-gray-100 dark:border-slate-700 flex justify-between items-end">
          <span className="text-xs font-bold text-gray-500 uppercase tracking-wider">Day Total</span>
          <span className="text-2xl font-black text-gray-900 dark:text-white">
            ₹{total.toLocaleString('en-IN')}
          </span>
        </div>
      </div>
      
      <div className="mt-6 pt-4 border-t border-gray-100 dark:border-slate-700">
        <button 
          onClick={onViewFullBudget}
          className="text-sm font-bold text-brand-600 dark:text-brand-400 hover:text-brand-700 dark:hover:text-brand-300 transition-colors flex items-center gap-1.5 group cursor-pointer"
        >
          View Full Trip Budget <span className="group-hover:translate-x-1 transition-transform">&rarr;</span>
        </button>
      </div>
    </div>
  );
}
