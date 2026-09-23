import React from 'react';
import { 
  X, 
  IndianRupee, 
  MapPin, 
  Calendar, 
  Users, 
  BedDouble, 
  Plane, 
  Train, 
  Car, 
  Bike, 
  Ticket, 
  Coffee, 
  Navigation, 
  Info, 
  CheckCircle2, 
  AlertCircle 
} from 'lucide-react';

export default function FullTripBudgetModal({
  isOpen,
  onClose,
  itinerary,
  destinationName,
  days = 1,
  travelType = 'Couple',
  selectedHotel = null,
  transportationMode = 'flight',
  originName = ''
}) {
  if (!isOpen || !itinerary) return null;

  const numDays = Math.max(1, parseInt(days) || 1);
  const numNights = Math.max(0, numDays - 1);

  // 1. Calculate Activities Entry Fees
  const allActivities = [];
  let totalAttractionCost = 0;
  let activitiesWithKnownCost = 0;
  let activitiesFreeOrIncluded = 0;

  if (itinerary.schedule && Array.isArray(itinerary.schedule)) {
    itinerary.schedule.forEach(day => {
      if (day.activities && Array.isArray(day.activities)) {
        day.activities.forEach(act => {
          const cost = typeof act.estimated_cost === 'number' ? act.estimated_cost : 0;
          allActivities.push({
            day: day.day,
            name: act.name,
            cost: cost,
            type: act.activity_type || 'Sightseeing',
            entryFee: act.entryFee || (cost > 0 ? `₹${cost}` : 'Free')
          });
          if (cost > 0) {
            totalAttractionCost += cost;
            activitiesWithKnownCost += 1;
          } else {
            activitiesFreeOrIncluded += 1;
          }
        });
      }
    });
  }

  // 2. Calculate Accommodation Cost
  let hotelRatePerNight = null;
  let hotelSubtotal = null;
  let hotelName = selectedHotel?.name || itinerary.accommodation || null;

  if (selectedHotel && typeof selectedHotel.price_per_night === 'number' && selectedHotel.price_per_night > 0) {
    hotelRatePerNight = selectedHotel.price_per_night;
    hotelSubtotal = numNights > 0 ? hotelRatePerNight * numNights : hotelRatePerNight;
  }

  // 3. Transportation Cost
  const transportData = itinerary.transportation || {};
  const transportMin = typeof transportData.estimated_cost_min === 'number' ? transportData.estimated_cost_min : 0;
  const transportMax = typeof transportData.estimated_cost_max === 'number' ? transportData.estimated_cost_max : 0;
  const transportMode = transportData.mode || transportationMode || 'car';
  const hasTransportEstimate = transportMax > 0;

  // 4. Daily Dining & Local Transit Incidentals (Planning Estimate Range)
  // Moderate estimate: ₹600 - ₹1400 per day for food & local transit
  const dailyIncidentalMin = numDays * 600;
  const dailyIncidentalMax = numDays * 1400;

  // 5. Total Calculations (Transparent Breakdown)
  const knownVerifiedSubtotal = totalAttractionCost + (hotelSubtotal || 0);
  
  const estimatedTotalMin = knownVerifiedSubtotal + (hasTransportEstimate ? transportMin : 0) + dailyIncidentalMin;
  const estimatedTotalMax = knownVerifiedSubtotal + (hasTransportEstimate ? transportMax : 0) + dailyIncidentalMax;

  const TransportIcon = transportMode === 'flight' ? Plane : transportMode === 'train' ? Train : transportMode === 'bike' ? Bike : Car;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-sm animate-fade-in">
      <div className="bg-white dark:bg-slate-900 border border-gray-200 dark:border-slate-800 rounded-3xl max-w-3xl w-full max-h-[90vh] overflow-hidden flex flex-col shadow-2xl">
        
        {/* Modal Header */}
        <div className="p-6 border-b border-gray-100 dark:border-slate-800 flex items-center justify-between bg-gray-50/50 dark:bg-slate-800/40">
          <div>
            <div className="flex items-center gap-2 mb-1">
              <span className="text-xs font-bold uppercase tracking-wider text-brand-600 dark:text-brand-400 bg-brand-50 dark:bg-brand-900/30 px-2.5 py-0.5 rounded-full">
                Trip Budget Breakdown
              </span>
              <span className="text-xs text-gray-500 dark:text-slate-400">• Transparent & Verified</span>
            </div>
            <h2 className="text-2xl font-black text-gray-900 dark:text-white">
              {destinationName} Full Trip Budget
            </h2>
          </div>
          <button 
            onClick={onClose}
            className="p-2 text-gray-400 hover:text-gray-600 dark:hover:text-gray-200 rounded-full hover:bg-gray-100 dark:hover:bg-slate-800 transition"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Modal Content */}
        <div className="p-6 overflow-y-auto space-y-6 flex-1 text-gray-800 dark:text-slate-200">
          
          {/* Trip Summary Card */}
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 bg-brand-50/50 dark:bg-brand-950/20 border border-brand-100 dark:border-brand-900/50 rounded-2xl p-4 text-xs font-medium">
            <div>
              <span className="text-gray-500 dark:text-slate-400 block mb-0.5">Destination</span>
              <span className="font-bold text-gray-900 dark:text-white flex items-center gap-1">
                <MapPin className="w-3.5 h-3.5 text-brand-500" /> {destinationName}
              </span>
            </div>
            <div>
              <span className="text-gray-500 dark:text-slate-400 block mb-0.5">Duration</span>
              <span className="font-bold text-gray-900 dark:text-white flex items-center gap-1">
                <Calendar className="w-3.5 h-3.5 text-brand-500" /> {numDays} Days {numNights > 0 ? `(${numNights} Nights)` : '(Day Trip)'}
              </span>
            </div>
            <div>
              <span className="text-gray-500 dark:text-slate-400 block mb-0.5">Travelers</span>
              <span className="font-bold text-gray-900 dark:text-white flex items-center gap-1">
                <Users className="w-3.5 h-3.5 text-brand-500" /> {travelType}
              </span>
            </div>
            <div>
              <span className="text-gray-500 dark:text-slate-400 block mb-0.5">Itinerary Route</span>
              <span className="font-bold text-brand-700 dark:text-brand-300">
                {itinerary.route_name || 'Curated'}
              </span>
            </div>
          </div>

          {/* 1. Accommodation Section */}
          <div className="border border-gray-100 dark:border-slate-800 rounded-2xl p-4 bg-white dark:bg-slate-800/40">
            <div className="flex items-center justify-between mb-3">
              <div className="flex items-center gap-2">
                <BedDouble className="w-5 h-5 text-indigo-500" />
                <h3 className="font-bold text-gray-900 dark:text-white text-sm uppercase tracking-wide">
                  Accommodation
                </h3>
              </div>
              <span className="text-[11px] font-semibold text-gray-500 dark:text-slate-400">
                {numNights > 0 ? `${numNights} Nights` : '1 Night / Day stay'}
              </span>
            </div>

            {selectedHotel ? (
              <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-2 bg-gray-50 dark:bg-slate-800/80 p-3 rounded-xl">
                <div>
                  <p className="font-bold text-sm text-gray-900 dark:text-white">{selectedHotel.name}</p>
                  <p className="text-xs text-gray-500 dark:text-slate-400 flex items-center gap-1 mt-0.5">
                    <MapPin className="w-3 h-3" /> {selectedHotel.city || destinationName}
                    <span className="ml-1 text-[10px] font-bold px-1.5 py-0.2 rounded bg-emerald-100 dark:bg-emerald-900/40 text-emerald-700 dark:text-emerald-300">
                      From database
                    </span>
                  </p>
                </div>
                <div className="text-left sm:text-right">
                  {hotelRatePerNight ? (
                    <>
                      <p className="font-bold text-sm text-gray-900 dark:text-white">
                        ₹{hotelRatePerNight.toLocaleString('en-IN')}/night × {Math.max(1, numNights)} {numNights === 1 ? 'night' : 'nights'}
                      </p>
                      <p className="text-xs font-bold text-emerald-600 dark:text-emerald-400">
                        = ₹{(hotelSubtotal || 0).toLocaleString('en-IN')}
                      </p>
                    </>
                  ) : (
                    <span className="text-xs text-gray-500 font-semibold">Price unavailable</span>
                  )}
                </div>
              </div>
            ) : (
              <div className="p-3 bg-gray-50 dark:bg-slate-800/50 rounded-xl text-xs text-gray-500 dark:text-slate-400 flex items-center justify-between">
                <span>No hotel selected yet. Select a stay from "Suggested Stays" to calculate exact room cost.</span>
                <span className="font-bold text-gray-400 shrink-0 ml-2">Not included</span>
              </div>
            )}
          </div>

          {/* 2. Transportation Section */}
          <div className="border border-gray-100 dark:border-slate-800 rounded-2xl p-4 bg-white dark:bg-slate-800/40">
            <div className="flex items-center justify-between mb-3">
              <div className="flex items-center gap-2">
                <TransportIcon className="w-5 h-5 text-blue-500" />
                <h3 className="font-bold text-gray-900 dark:text-white text-sm uppercase tracking-wide">
                  Transportation ({transportMode.toUpperCase()})
                </h3>
              </div>
              <span className="text-[11px] font-bold px-2 py-0.5 rounded bg-blue-50 dark:bg-blue-900/30 text-blue-600 dark:text-blue-400">
                Estimated
              </span>
            </div>

            <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-2 bg-gray-50 dark:bg-slate-800/80 p-3 rounded-xl text-xs">
              <div>
                <p className="font-bold text-gray-900 dark:text-white text-sm capitalize">
                  {originName ? `${originName} → ${destinationName}` : `${destinationName} Transit & Travel`}
                </p>
                <p className="text-gray-500 dark:text-slate-400 mt-0.5">
                  {transportData.estimated_distance_km ? `~${transportData.estimated_distance_km} km distance` : 'Regional transport'}
                  {transportData.recommendation_note && ` • ${transportData.recommendation_note}`}
                </p>
              </div>
              <div className="text-left sm:text-right font-bold text-gray-900 dark:text-white">
                {hasTransportEstimate ? (
                  <span>₹{transportMin.toLocaleString('en-IN')} – ₹{transportMax.toLocaleString('en-IN')}</span>
                ) : (
                  <span className="text-gray-500 font-semibold">Transport cost unavailable</span>
                )}
              </div>
            </div>
          </div>

          {/* 3. Activities & Attractions Section */}
          <div className="border border-gray-100 dark:border-slate-800 rounded-2xl p-4 bg-white dark:bg-slate-800/40">
            <div className="flex items-center justify-between mb-3">
              <div className="flex items-center gap-2">
                <Ticket className="w-5 h-5 text-amber-500" />
                <h3 className="font-bold text-gray-900 dark:text-white text-sm uppercase tracking-wide">
                  Activities & Sightseeing Entry Fees
                </h3>
              </div>
              <span className="text-[11px] font-bold px-2 py-0.5 rounded bg-emerald-50 dark:bg-emerald-900/30 text-emerald-600 dark:text-emerald-400">
                From database
              </span>
            </div>

            <div className="divide-y divide-gray-100 dark:divide-slate-800 max-h-48 overflow-y-auto mb-3">
              {allActivities.map((act, i) => (
                <div key={i} className="py-2 flex items-center justify-between text-xs">
                  <div className="flex items-center gap-2">
                    <span className="font-bold text-gray-400 text-[10px]">D{act.day}</span>
                    <span className="font-semibold text-gray-800 dark:text-slate-200">{act.name}</span>
                    <span className="text-[10px] text-gray-400">({act.type})</span>
                  </div>
                  <span className="font-bold text-gray-900 dark:text-white">
                    {act.cost > 0 ? `₹${act.cost.toLocaleString('en-IN')}` : 'Free'}
                  </span>
                </div>
              ))}
            </div>

            <div className="pt-2 border-t border-gray-100 dark:border-slate-800 flex justify-between items-center text-xs font-bold text-gray-900 dark:text-white">
              <span>Attraction Entry Fees Subtotal ({allActivities.length} stops)</span>
              <span className="text-sm text-emerald-600 dark:text-emerald-400">
                ₹{totalAttractionCost.toLocaleString('en-IN')}
              </span>
            </div>
          </div>

          {/* 4. Dining & Incidentals Estimate */}
          <div className="border border-gray-100 dark:border-slate-800 rounded-2xl p-4 bg-white dark:bg-slate-800/40">
            <div className="flex items-center justify-between mb-2">
              <div className="flex items-center gap-2">
                <Coffee className="w-5 h-5 text-amber-600" />
                <h3 className="font-bold text-gray-900 dark:text-white text-sm uppercase tracking-wide">
                  Food, Dining & Local Incidentals
                </h3>
              </div>
              <span className="text-[11px] font-bold px-2 py-0.5 rounded bg-amber-50 dark:bg-amber-900/30 text-amber-600 dark:text-amber-400">
                Estimated
              </span>
            </div>
            <div className="flex justify-between items-center text-xs text-gray-600 dark:text-slate-400">
              <span>Meals & local transit (~₹600–₹1,400/day) × {numDays} days</span>
              <span className="font-bold text-gray-900 dark:text-white">
                ₹{dailyIncidentalMin.toLocaleString('en-IN')} – ₹{dailyIncidentalMax.toLocaleString('en-IN')}
              </span>
            </div>
          </div>

          {/* Budget Summary & Total */}
          <div className="bg-slate-900 text-white rounded-2xl p-6 space-y-4">
            <div className="flex items-center justify-between border-b border-slate-800 pb-3">
              <span className="text-xs uppercase font-bold tracking-wider text-slate-400">Known / Verified Costs</span>
              <span className="text-base font-bold text-emerald-400">
                ₹{knownVerifiedSubtotal.toLocaleString('en-IN')}
              </span>
            </div>
            <div className="flex items-center justify-between border-b border-slate-800 pb-3">
              <span className="text-xs uppercase font-bold tracking-wider text-slate-400">Variable Estimates (Transport + Incidentals)</span>
              <span className="text-sm font-semibold text-slate-300">
                ₹{( (hasTransportEstimate ? transportMin : 0) + dailyIncidentalMin ).toLocaleString('en-IN')} – ₹{( (hasTransportEstimate ? transportMax : 0) + dailyIncidentalMax ).toLocaleString('en-IN')}
              </span>
            </div>
            <div className="flex items-center justify-between pt-2">
              <div>
                <p className="text-xs uppercase font-black tracking-widest text-amber-400">Total Estimated Trip Budget</p>
                <p className="text-[11px] text-slate-400 mt-0.5">All fees and verified room rates included</p>
              </div>
              <div className="text-right">
                <p className="text-2xl sm:text-3xl font-black text-white">
                  ₹{estimatedTotalMin.toLocaleString('en-IN')} – ₹{estimatedTotalMax.toLocaleString('en-IN')}
                </p>
              </div>
            </div>
          </div>

          {/* Transparency Disclaimer */}
          <div className="flex items-start gap-2.5 text-[11px] text-gray-500 dark:text-slate-400 bg-gray-50 dark:bg-slate-800/50 p-3.5 rounded-xl border border-gray-100 dark:border-slate-800">
            <Info className="w-4 h-4 text-brand-500 shrink-0 mt-0.5" />
            <p>
              <strong>Pricing Transparency:</strong> Attraction entry fees and hotel rates are verified from TourMate canonical database records. Transportation and dining costs are planning estimates based on selected travel style and regional distances.
            </p>
          </div>

        </div>

        {/* Modal Footer */}
        <div className="p-4 border-t border-gray-100 dark:border-slate-800 bg-gray-50/50 dark:bg-slate-800/50 flex justify-end">
          <button
            onClick={onClose}
            className="px-6 py-2.5 bg-brand-600 hover:bg-brand-700 text-white font-bold rounded-xl text-sm transition shadow"
          >
            Close Budget Details
          </button>
        </div>

      </div>
    </div>
  );
}
