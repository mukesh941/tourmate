import React from 'react';
import { Link } from 'react-router-dom';
import { Star, ArrowRight, Navigation, MapPin } from 'lucide-react';

import { NEUTRAL_PLACEHOLDER_IMAGE, handleImageError } from '../config/imageConfig';

export default function RecommendationCard({ 
  item, 
  type, // "place", "hotel", "restaurant", "activity", "destination"
  className = ""
}) {
  const getBadgeColor = () => {
    switch (type) {
      case 'place': return 'bg-emerald-100 text-emerald-800 border-emerald-200';
      case 'hotel': return 'bg-blue-100 text-blue-800 border-blue-200';
      case 'restaurant': return 'bg-orange-100 text-orange-800 border-orange-200';
      case 'activity': return 'bg-purple-100 text-purple-800 border-purple-200';
      case 'destination': return 'bg-indigo-100 text-indigo-800 border-indigo-200';
      default: return 'bg-gray-100 text-gray-800';
    }
  };

  const getPriceBadge = () => {
    if (type === 'hotel') return <span className="font-bold">{item.currency || '₹'}{item.price_per_night_start}/night</span>;
    if (type === 'activity') return <span className="font-bold">{item.currency || '₹'}{item.price}</span>;
    if (item.price_level) return <span className="font-bold text-emerald-700">{'₹'.repeat(item.price_level)}</span>;
    return null;
  };

  const getSubInfo = () => {
    if (type === 'destination') return item.state || 'India';
    if (type === 'hotel') return item.hotel_type || 'Accommodation';
    if (type === 'restaurant') return item.cuisine_type?.[0] || 'Local Cuisine';
    if (type === 'activity') return item.activity_type || 'Experience';
    if (item.feature_scores) {
      const topFeature = Object.entries(item.feature_scores)
        .sort((a, b) => b[1] - a[1])[0];
      return topFeature ? topFeature[0] : 'Attraction';
    }
    return item.city || 'Location';
  };

  const linkTarget = 
    type === 'hotel' ? `/hotels/${item.id}` 
    : type === 'destination' ? `/destinations/${item.id}`
    : `/places/${item.id}`;

  return (
    <Link 
      to={linkTarget}
      className={`flex-none w-72 md:w-80 bg-white rounded-2xl overflow-hidden shadow-sm hover:shadow-xl hover:-translate-y-1 transition-all duration-300 border border-gray-100 flex flex-col group snap-start ${className}`}
    >
      {/* 4:3 Aspect Ratio Image Container */}
      <div className="relative aspect-[4/3] w-full overflow-hidden bg-gray-100">
        <img 
          src={item.cover_image || (item.images && item.images[0]) || NEUTRAL_PLACEHOLDER_IMAGE} 
          alt={item.name} 
          referrerPolicy="no-referrer"
          className="w-full h-full object-cover group-hover:scale-105 transition duration-700 ease-out"
          onError={handleImageError}
        />
        
        {/* Rating Badge */}
        {(item.rating || type !== 'destination') && (
          <div className="absolute top-3 left-3 bg-white/95 backdrop-blur-sm px-2.5 py-1 rounded-lg text-xs font-bold text-gray-900 flex items-center gap-1 shadow-sm">
            <Star className="w-3 h-3 text-amber-500 fill-amber-500" /> 
            {item.rating?.toFixed(1) || (type === 'destination' ? "Explore" : "New")}
          </div>
        )}

        {/* Type Badge */}
        <div className={`absolute top-3 right-3 px-2 py-1 text-[10px] uppercase font-bold tracking-widest rounded shadow-sm border backdrop-blur-sm ${getBadgeColor()}`}>
          {type}
        </div>
      </div>
      
      {/* Content Area */}
      <div className="p-5 flex flex-col flex-1 bg-white">
        
        {/* Title and Metadata */}
        <div className="flex items-center gap-1.5 text-xs font-semibold text-brand-600 mb-1.5 uppercase tracking-wide">
          <MapPin className="w-3.5 h-3.5" />
          <span className="truncate">{getSubInfo()}</span>
        </div>
        
        <h3 className="font-bold font-display text-lg text-gray-900 group-hover:text-brand-600 transition-colors line-clamp-1 mb-2">
          {item.name}
        </h3>
        
        {item.description && (
          <p className="text-sm text-gray-500 line-clamp-2 mb-4 leading-relaxed">
            {item.description}
          </p>
        )}
        
        {/* Footer Area */}
        <div className="flex items-center justify-between border-t border-gray-50 pt-4 mt-auto">
          <div className="flex items-center text-gray-900 text-sm">
            {getPriceBadge()}
          </div>
          <div className="flex items-center text-sm font-bold text-brand-600 group-hover:text-brand-700 transition-colors">
            {type === 'hotel' ? 'View Stay' : 'Explore'} <ArrowRight className="w-4 h-4 ml-1" />
          </div>
        </div>
      </div>
    </Link>
  );
}
