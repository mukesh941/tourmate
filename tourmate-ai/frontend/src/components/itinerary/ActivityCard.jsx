import React, { useState } from 'react';
import { MapPin, Star, Clock, IndianRupee, Navigation, Info, Users, CloudRain, ExternalLink, ChevronDown, ChevronUp, Image as ImageIcon, Heart } from 'lucide-react';

export default function ActivityCard({ activity, onMoveUp, onMoveDown, isFirst, isLast }) {
  const [expandedInfo, setExpandedInfo] = useState(false);
  const [expandedTips, setExpandedTips] = useState(false);
  
  const isTransit = activity.activity_type?.toLowerCase().includes("transit");
  const isMeal = activity.activity_type?.toLowerCase().includes("meal") || activity.category?.toLowerCase().includes("food");
  const isHotel = activity.activity_type?.toLowerCase().includes("hotel") || activity.category?.toLowerCase().includes("accommodation");
  
  const isOptional = activity.isOptional;

  return (
    <div className={`bg-white dark:bg-slate-800 rounded-3xl p-5 md:p-6 border ${isOptional ? 'border-dashed border-gray-300 dark:border-slate-600' : 'border-gray-200 dark:border-slate-700'} shadow-sm hover:shadow-md transition-all relative overflow-hidden group`}>
      
      {/* Optional Badge */}
      {isOptional && (
        <div className="absolute top-0 right-0 bg-gray-100 dark:bg-slate-700 text-gray-500 dark:text-slate-400 text-[10px] font-bold uppercase tracking-wider px-3 py-1 rounded-bl-xl z-10">
          Optional
        </div>
      )}

      <div className="flex flex-col md:flex-row gap-6">
        
        {/* Image Section */}
        {!isTransit && (
          <div className="w-full md:w-48 h-40 shrink-0 rounded-2xl bg-gray-100 dark:bg-slate-700 overflow-hidden relative">
            {activity.image ? (
              <img src={activity.image} alt={activity.name} className="w-full h-full object-cover" />
            ) : (
              <div className="w-full h-full flex items-center justify-center text-gray-300 dark:text-slate-600">
                <ImageIcon className="w-10 h-10" />
              </div>
            )}
            {/* Action Overlay */}
            <div className="absolute top-2 right-2 flex gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
              <button className="p-1.5 bg-white/80 dark:bg-slate-900/80 backdrop-blur-sm rounded-full text-gray-700 dark:text-slate-300 hover:text-rose-500 transition-colors">
                <Heart className="w-4 h-4" />
              </button>
            </div>
          </div>
        )}

        {/* Content Section */}
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 mb-2">
            {activity.activity_type && (
              <span className="text-[10px] font-bold uppercase tracking-wider text-brand-600 dark:text-brand-400 bg-brand-50 dark:bg-brand-900/30 px-2.5 py-0.5 rounded-full">
                {activity.activity_type}
              </span>
            )}
            {activity.rating && (
              <span className="flex items-center gap-1 text-[11px] font-bold text-amber-600 dark:text-amber-500 bg-amber-50 dark:bg-amber-900/20 px-2 py-0.5 rounded-full">
                <Star className="w-3 h-3 fill-amber-500 text-amber-500" /> {activity.rating} 
                {activity.reviewCount && <span className="text-amber-600/60 dark:text-amber-500/60 font-normal">({activity.reviewCount})</span>}
              </span>
            )}
          </div>
          
          <h3 className="text-xl md:text-2xl font-bold text-gray-900 dark:text-white mb-2 leading-tight">
            {activity.name}
          </h3>
          
          <div className="flex flex-wrap items-center gap-y-2 gap-x-4 text-xs font-semibold text-gray-500 dark:text-slate-400 mb-4">
            <span className="flex items-center gap-1.5 text-gray-700 dark:text-slate-300 bg-gray-100 dark:bg-slate-900/50 px-2 py-1 rounded-lg">
              <Clock className="w-3.5 h-3.5" /> {activity.start_time} - {activity.end_time}
            </span>
            {activity.location && (
              <span className="flex items-center gap-1">
                <MapPin className="w-3.5 h-3.5" /> {activity.location} {activity.distance && `· ${activity.distance}`}
              </span>
            )}
            {activity.estimated_cost > 0 && (
              <span className="flex items-center gap-1">
                <IndianRupee className="w-3.5 h-3.5" /> {activity.estimated_cost}
              </span>
            )}
          </div>

          <p className="text-sm text-gray-600 dark:text-slate-400 mb-6 leading-relaxed">
            {activity.description}
          </p>

          {/* AI Reason */}
          {activity.aiReason && (
            <div className="bg-brand-50/50 dark:bg-brand-900/10 border border-brand-100 dark:border-brand-800/50 rounded-xl p-3 mb-4 flex items-start gap-3">
              <div className="shrink-0 text-lg mt-0.5">✨</div>
              <div>
                <p className="text-[10px] font-bold text-brand-600 dark:text-brand-400 uppercase tracking-wider mb-0.5">Why AI recommends this</p>
                <p className="text-sm text-gray-700 dark:text-slate-300 italic">"{activity.aiReason}"</p>
              </div>
            </div>
          )}

          {/* Action Buttons */}
          <div className="flex flex-wrap items-center gap-3 mt-auto">
            <button className="px-4 py-2 bg-gray-900 dark:bg-white text-white dark:text-gray-900 font-bold rounded-xl text-xs flex items-center gap-2 hover:bg-gray-800 dark:hover:bg-gray-100 transition-colors">
              <Navigation className="w-3.5 h-3.5" /> Get Directions
            </button>
            {activity.bookingUrl && (
              <button className="px-4 py-2 bg-brand-600 text-white font-bold rounded-xl text-xs flex items-center gap-2 hover:bg-brand-700 transition-colors">
                <ExternalLink className="w-3.5 h-3.5" /> Book Now
              </button>
            )}
            <button 
              onClick={() => setExpandedInfo(!expandedInfo)}
              className="px-3 py-2 text-gray-600 dark:text-slate-300 font-bold rounded-xl text-xs flex items-center gap-1.5 hover:bg-gray-100 dark:hover:bg-slate-700 transition-colors ml-auto"
            >
              Visit Info {expandedInfo ? <ChevronUp className="w-3.5 h-3.5" /> : <ChevronDown className="w-3.5 h-3.5" />}
            </button>
          </div>
        </div>
      </div>

      {/* Expandable Info */}
      {expandedInfo && (
        <div className="mt-6 pt-6 border-t border-gray-100 dark:border-slate-700 grid md:grid-cols-2 gap-6 animate-fade-in-up">
          <div>
            <h4 className="text-xs font-bold text-gray-900 dark:text-white uppercase tracking-wider mb-4 flex items-center gap-2">
              <Info className="w-4 h-4 text-brand-500" /> Visit Information
            </h4>
            <div className="space-y-3">
              {activity.openingHours && (
                <div className="flex justify-between items-center text-sm">
                  <span className="text-gray-500 dark:text-slate-400 flex items-center gap-2"><Clock className="w-3.5 h-3.5"/> Opening Hours</span>
                  <span className="font-semibold text-gray-900 dark:text-white">{activity.openingHours}</span>
                </div>
              )}
              {activity.entryFee && (
                <div className="flex justify-between items-center text-sm">
                  <span className="text-gray-500 dark:text-slate-400 flex items-center gap-2"><IndianRupee className="w-3.5 h-3.5"/> Entry Fee</span>
                  <span className="font-semibold text-gray-900 dark:text-white">{activity.entryFee}</span>
                </div>
              )}
              {activity.crowdLevel && (
                <div className="flex justify-between items-center text-sm">
                  <span className="text-gray-500 dark:text-slate-400 flex items-center gap-2"><Users className="w-3.5 h-3.5"/> Expected Crowd</span>
                  <span className={`font-bold px-2 py-0.5 rounded ${
                    activity.crowdLevel.toLowerCase() === 'high' ? 'bg-rose-100 text-rose-700 dark:bg-rose-900/30 dark:text-rose-400' :
                    activity.crowdLevel.toLowerCase() === 'medium' ? 'bg-amber-100 text-amber-700 dark:bg-amber-900/30 dark:text-amber-400' :
                    'bg-emerald-100 text-emerald-700 dark:bg-emerald-900/30 dark:text-emerald-400'
                  }`}>{activity.crowdLevel}</span>
                </div>
              )}
              {activity.weatherSuitability && (
                <div className="flex justify-between items-center text-sm">
                  <span className="text-gray-500 dark:text-slate-400 flex items-center gap-2"><CloudRain className="w-3.5 h-3.5"/> Weather</span>
                  <span className="font-semibold text-gray-900 dark:text-white">{activity.weatherSuitability}</span>
                </div>
              )}
            </div>
          </div>
          
          {activity.aiTips && activity.aiTips.length > 0 && (
            <div>
              <h4 className="text-xs font-bold text-gray-900 dark:text-white uppercase tracking-wider mb-4 flex items-center gap-2">
                ✨ AI Travel Tips
              </h4>
              <ul className="space-y-2">
                {activity.aiTips.map((tip, idx) => (
                  <li key={idx} className="text-sm text-gray-600 dark:text-slate-400 flex items-start gap-2">
                    <span className="text-brand-500 font-bold">•</span> {tip}
                  </li>
                ))}
              </ul>
            </div>
          )}
        </div>
      )}

      {/* Floating Controls (Move/Delete) visible on hover */}
      <div className="absolute top-1/2 -translate-y-1/2 -left-12 group-hover:left-2 flex flex-col gap-1 transition-all">
         <button onClick={onMoveUp} disabled={isFirst} className="p-1.5 bg-white dark:bg-slate-700 border border-gray-200 dark:border-slate-600 rounded-lg shadow-sm text-gray-500 hover:text-brand-600 disabled:opacity-30">
           <ChevronUp className="w-4 h-4" />
         </button>
         <button onClick={onMoveDown} disabled={isLast} className="p-1.5 bg-white dark:bg-slate-700 border border-gray-200 dark:border-slate-600 rounded-lg shadow-sm text-gray-500 hover:text-brand-600 disabled:opacity-30">
           <ChevronDown className="w-4 h-4" />
         </button>
      </div>

    </div>
  );
}
