import React from 'react';

export default function DayNavigation({ schedule, activeDay, setActiveDay }) {
  if (!schedule || schedule.length === 0) return null;

  return (
    <div className="mb-8">
      <div className="flex overflow-x-auto custom-scrollbar gap-3 pb-4">
        {schedule.map(dayPlan => {
          const isActive = activeDay === dayPlan.day;
          
          // Calculate approx daily cost
          const dailyCost = dayPlan.activities.reduce((sum, act) => sum + (act.estimated_cost || 0), 0);
          const activityCount = dayPlan.activities.length;

          return (
            <button
              key={dayPlan.day}
              onClick={() => setActiveDay(dayPlan.day)}
              className={`shrink-0 min-w-[140px] p-4 rounded-2xl text-left transition-all border-2 ${
                isActive 
                  ? 'bg-gray-900 border-gray-900 text-white shadow-lg transform -translate-y-1' 
                  : 'bg-white dark:bg-slate-800 border-gray-200 dark:border-slate-700 text-gray-700 dark:text-slate-300 hover:border-gray-400 dark:hover:border-slate-500 hover:bg-gray-50 dark:hover:bg-slate-700/50'
              }`}
            >
              <div className="flex justify-between items-start mb-2">
                <span className={`text-xs font-bold uppercase tracking-wider ${isActive ? 'text-gray-400' : 'text-gray-500'}`}>
                  DAY {dayPlan.day}
                </span>
              </div>
              <div className="text-lg font-black mb-1">
                {activityCount} Activities
              </div>
              <div className={`text-sm font-semibold ${isActive ? 'text-emerald-400' : 'text-emerald-600 dark:text-emerald-400'}`}>
                ₹{dailyCost.toLocaleString('en-IN')}
              </div>
            </button>
          );
        })}
      </div>
    </div>
  );
}
