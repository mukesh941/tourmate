import React, { useState, useEffect } from "react";
import { useParams, Link, useNavigate } from "react-router-dom";
import axios from "axios";
import { useAuth } from "../context/AuthContext";
import { 
  MapPin, 
  Star, 
  Calendar, 
  Users, 
  Wifi, 
  Coffee, 
  Waves, 
  Sparkles, 
  ShieldCheck, 
  ArrowLeft, 
  CheckCircle, 
  X, 
  Bed, 
  Maximize2, 
  CreditCard,
  Building,
  Info,
  Share2
} from "lucide-react";
import ShareModal from "../components/ShareModal";
import { NEUTRAL_PLACEHOLDER_IMAGE, handleImageError } from "../config/imageConfig";

export default function HotelDetail() {
  const { id } = useParams();
  const navigate = useNavigate();
  const { token, user } = useAuth();

  const [hotel, setHotel] = useState(null);
  const [loading, setLoading] = useState(true);
  const [selectedImage, setSelectedImage] = useState("");

  // Booking Modal State
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [selectedRoom, setSelectedRoom] = useState(null);
  
  // Date calculations
  const today = new Date().toISOString().split("T")[0];
  const defaultOut = new Date(Date.now() + 86400000 * 2).toISOString().split("T")[0];

  const [checkIn, setCheckIn] = useState(today);
  const [checkOut, setCheckOut] = useState(defaultOut);
  const [guests, setGuests] = useState(2);
  const [specialRequests, setSpecialRequests] = useState("");
  const [bookingLoading, setBookingLoading] = useState(false);
  const [bookingSuccess, setBookingSuccess] = useState(null);
  const [shareOpen, setShareOpen] = useState(false);

  useEffect(() => {
    fetchHotel();
  }, [id]);

  const fetchHotel = async () => {
    setLoading(true);
    try {
      const res = await axios.get(`${import.meta.env.VITE_API_BASE_URL}/hotels/${id}`);
      setHotel(res.data.data);
      if (res.data.data?.cover_image) {
        setSelectedImage(res.data.data.cover_image);
      }
    } catch (err) {
      console.error("Failed to load hotel:", err);
    } finally {
      setLoading(false);
    }
  };

  // Calculate nights
  const calculateNights = () => {
    try {
      const d1 = new Date(checkIn);
      const d2 = new Date(checkOut);
      const diffTime = d2 - d1;
      const diffDays = Math.round(diffTime / (1000 * 60 * 60 * 24));
      return diffDays > 0 ? diffDays : 0;
    } catch {
      return 0;
    }
  };

  const nights = calculateNights();
  const roomPrice = selectedRoom?.price_per_night || hotel?.price_per_night_start || 100;
  const subtotal = nights > 0 ? roomPrice * nights : 0;
  const taxes = Math.round(subtotal * 0.12);
  const total = subtotal + taxes;

  const handleOpenBooking = (room) => {
    if (!token) {
      if (confirm("You need to log in to book a hotel stay. Go to login page?")) {
        navigate("/login");
      }
      return;
    }
    setSelectedRoom(room);
    setBookingSuccess(null);
    setIsModalOpen(true);
  };

  const handleConfirmBooking = async (e) => {
    e.preventDefault();
    setBookingLoading(true);
    try {
      const payload = {
        hotel_id: hotel.id,
        room_id: selectedRoom.id,
        room_name: selectedRoom.name,
        check_in_date: checkIn,
        check_out_date: checkOut,
        guests: parseInt(guests),
        special_requests: specialRequests
      };

      const res = await axios.post(
        `${import.meta.env.VITE_API_BASE_URL}/hotels/book`,
        payload,
        { headers: { Authorization: `Bearer ${token}` } }
      );

      setBookingSuccess(res.data.data);
    } catch (err) {
      console.error(err);
      alert(err.response?.data?.detail || "Failed to complete reservation. Please try again.");
    } finally {
      setBookingLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="flex justify-center items-center min-h-[70vh]">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-brand-600"></div>
      </div>
    );
  }

  if (!hotel) {
    return (
      <div className="max-w-4xl mx-auto py-16 px-4 text-center">
        <Building className="w-12 h-12 text-gray-400 mx-auto mb-3" />
        <h2 className="text-xl font-bold text-gray-800 dark:text-slate-100">Hotel not found</h2>
        <Link to="/hotels" className="text-brand-600 font-semibold mt-4 inline-block">
          ← Back to all stays
        </Link>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-slate-900 py-6 px-4 sm:px-6 lg:px-8">
      <div className="max-w-7xl mx-auto">
        {/* Navigation Breadcrumb */}
        <div className="mb-6 flex items-center justify-between">
          <Link
            to="/hotels"
            className="inline-flex items-center gap-1.5 text-sm font-semibold text-gray-600 dark:text-slate-400 hover:text-brand-600 dark:hover:text-brand-400 transition"
          >
            <ArrowLeft className="w-4 h-4" /> Back to all stays
          </Link>
          <span className="px-3 py-1 bg-brand-50 dark:bg-brand-950/60 text-brand-600 dark:text-brand-400 text-xs font-bold rounded-full border border-brand-200 dark:border-brand-800">
            {hotel.hotel_type}
          </span>
        </div>

        {/* Hotel Header Info */}
        <div className="mb-6">
          <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
            <div>
              <h1 className="text-2xl sm:text-4xl font-extrabold text-gray-900 dark:text-slate-100">
                {hotel.name}
              </h1>
              <p className="flex items-center gap-1 text-sm text-gray-600 dark:text-slate-400 mt-1">
                <MapPin className="w-4 h-4 text-brand-600" /> {hotel.address}
              </p>
            </div>
            <div className="flex items-center gap-3">
              <button
                onClick={() => setShareOpen(true)}
                className="p-3 bg-white dark:bg-slate-800 rounded-xl border border-gray-200 dark:border-slate-700 shadow-sm text-brand-600 hover:bg-brand-50 dark:hover:bg-slate-700 transition flex items-center gap-1.5 text-xs font-bold"
                title="Share this stay"
              >
                <Share2 className="w-4 h-4" />
                <span className="hidden sm:inline">Share Stay</span>
              </button>
              <div className="px-4 py-2 bg-white dark:bg-slate-800 rounded-xl border border-gray-200 dark:border-slate-700 shadow-sm flex items-center gap-2">
                <Star className="w-5 h-5 fill-amber-500 text-amber-500" />
                <div>
                  <div className="font-extrabold text-gray-900 dark:text-white leading-tight">
                    {hotel.rating.toFixed(1)} / 5.0
                  </div>
                  <div className="text-[11px] text-gray-400">
                    {hotel.review_count} verified reviews
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Real Photo Gallery */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-4 mb-10">
          {/* Main Large Image */}
          <div className="lg:col-span-2 h-80 sm:h-[420px] rounded-2xl overflow-hidden shadow-sm bg-gray-100 dark:bg-slate-800">
            <img
              src={selectedImage || hotel.cover_image || NEUTRAL_PLACEHOLDER_IMAGE}
              alt={hotel.name}
              className="w-full h-full object-cover transition-all duration-300"
              onError={handleImageError}
            />
          </div>

          {/* Thumbnail Strip */}
          <div className="grid grid-cols-2 lg:grid-cols-1 gap-4 h-auto lg:h-[420px]">
            {hotel.images.slice(0, 3).map((img, idx) => (
              <div
                key={idx}
                onClick={() => setSelectedImage(img)}
                className={`cursor-pointer rounded-2xl overflow-hidden border-2 transition h-36 sm:h-44 lg:h-[130px] ${
                  selectedImage === img
                    ? "border-brand-600 ring-2 ring-brand-500/20 shadow-md"
                    : "border-transparent opacity-80 hover:opacity-100"
                }`}
              >
                <img
                  src={img}
                  alt={`${hotel.name} preview ${idx + 1}`}
                  className="w-full h-full object-cover"
                />
              </div>
            ))}
          </div>
        </div>

        {/* Property Description & Amenities Section */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8 mb-12">
          <div className="lg:col-span-2 space-y-6">
            <div className="bg-white dark:bg-slate-800 rounded-2xl p-6 sm:p-8 border border-gray-200 dark:border-slate-700 shadow-sm">
              <h2 className="text-xl font-bold text-gray-900 dark:text-slate-100 mb-3">
                About the Property
              </h2>
              <p className="text-sm text-gray-600 dark:text-slate-300 leading-relaxed">
                {hotel.description}
              </p>

              <hr className="my-6 border-gray-100 dark:border-slate-700/60" />

              <h3 className="text-lg font-bold text-gray-900 dark:text-slate-100 mb-4">
                Property Amenities
              </h3>
              <div className="grid grid-cols-2 sm:grid-cols-3 gap-3">
                {hotel.amenities.map((amenity, aIdx) => (
                  <div
                    key={aIdx}
                    className="flex items-center gap-2 p-3 bg-gray-50 dark:bg-slate-900/60 rounded-xl border border-gray-100 dark:border-slate-700/50 text-xs font-semibold text-gray-700 dark:text-slate-300"
                  >
                    <CheckCircle className="w-4 h-4 text-emerald-500 shrink-0" />
                    <span>{amenity}</span>
                  </div>
                ))}
              </div>
            </div>
          </div>

          {/* Quick Stay Summary Sidebar */}
          <div>
            <div className="bg-white dark:bg-slate-800 rounded-2xl p-6 border border-gray-200 dark:border-slate-700 shadow-sm sticky top-24">
              <span className="text-xs font-semibold text-gray-400">Nightly starting rate</span>
              <div className="text-3xl font-extrabold text-gray-900 dark:text-white mt-1 mb-4">
                {hotel.currency}{hotel.price_per_night_start}
                <span className="text-xs font-normal text-gray-500 dark:text-slate-400"> / night</span>
              </div>

              <div className="p-4 bg-brand-50/60 dark:bg-brand-950/30 rounded-xl border border-brand-100 dark:border-brand-900/40 text-xs text-brand-900 dark:text-brand-300 space-y-2 mb-5">
                <div className="flex items-center gap-2">
                  <ShieldCheck className="w-4 h-4 text-brand-600 shrink-0" />
                  <span>Free cancellation up to 48 hours before check-in</span>
                </div>
                <div className="flex items-center gap-2">
                  <Coffee className="w-4 h-4 text-brand-600 shrink-0" />
                  <span>Complimentary breakfast included with select rooms</span>
                </div>
              </div>

              <button
                onClick={() => {
                  const roomsElement = document.getElementById("rooms-section");
                  if (roomsElement) roomsElement.scrollIntoView({ behavior: "smooth" });
                }}
                className="w-full py-3 bg-brand-600 hover:bg-brand-700 text-white rounded-xl text-sm font-bold shadow-sm transition transform active:scale-95 text-center"
              >
                Select Your Room
              </button>
            </div>
          </div>
        </div>

        {/* Available Room Types */}
        <div id="rooms-section" className="scroll-mt-24 mb-16">
          <div className="mb-6">
            <h2 className="text-2xl font-extrabold text-gray-900 dark:text-slate-100">
              Available Room Types ({hotel.rooms?.length || 0})
            </h2>
            <p className="text-sm text-gray-500 dark:text-slate-400 mt-1">
              Select your room to customize stay dates and finalize your reservation.
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {hotel.rooms?.map((room) => (
              <div
                key={room.id}
                className="bg-white dark:bg-slate-800 rounded-2xl border border-gray-200 dark:border-slate-700 overflow-hidden shadow-sm hover:shadow-md transition flex flex-col justify-between"
              >
                <div>
                  <div className="relative h-48 w-full overflow-hidden bg-gray-100 dark:bg-slate-700">
                    <img
                      src={room.image || hotel.cover_image || NEUTRAL_PLACEHOLDER_IMAGE}
                      alt={room.name}
                      className="w-full h-full object-cover"
                      onError={handleImageError}
                    />
                    <div className="absolute bottom-3 left-3 px-3 py-1 bg-black/70 backdrop-blur-md rounded-lg text-xs font-bold text-white">
                      {hotel.currency}{room.price_per_night} <span className="font-normal text-gray-300">/ night</span>
                    </div>
                  </div>

                  <div className="p-5">
                    <h3 className="font-bold text-lg text-gray-900 dark:text-slate-100 mb-1">
                      {room.name}
                    </h3>
                    
                    <div className="flex items-center gap-3 text-xs text-gray-500 dark:text-slate-400 mb-3">
                      <span className="flex items-center gap-1"><Maximize2 className="w-3.5 h-3.5" /> {room.size}</span>
                      <span>•</span>
                      <span className="flex items-center gap-1"><Bed className="w-3.5 h-3.5" /> {room.bed_type}</span>
                      <span>•</span>
                      <span className="flex items-center gap-1"><Users className="w-3.5 h-3.5" /> Up to {room.capacity}</span>
                    </div>

                    <p className="text-xs text-gray-600 dark:text-slate-300 mb-4 line-clamp-2">
                      {room.description}
                    </p>

                    <div className="flex flex-wrap gap-1.5 mb-2">
                      {room.amenities?.map((a, idx) => (
                        <span
                          key={idx}
                          className="px-2 py-0.5 bg-gray-100 dark:bg-slate-700/80 rounded-md text-[11px] font-medium text-gray-600 dark:text-slate-300"
                        >
                          {a}
                        </span>
                      ))}
                    </div>
                  </div>
                </div>

                <div className="p-5 pt-0">
                  <button
                    onClick={() => handleOpenBooking(room)}
                    className="w-full py-2.5 bg-brand-600 hover:bg-brand-700 text-white rounded-xl text-xs font-bold shadow-sm transition flex items-center justify-center gap-1.5"
                  >
                    <Calendar className="w-3.5 h-3.5" /> Book This Room
                  </button>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Reservation Modal */}
      {isModalOpen && (
        <div className="fixed inset-0 bg-black/60 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div className="bg-white dark:bg-slate-800 rounded-2xl max-w-lg w-full p-6 sm:p-8 shadow-2xl border border-gray-200 dark:border-slate-700 relative animate-scaleUp">
            <button
              onClick={() => setIsModalOpen(false)}
              className="absolute top-4 right-4 text-gray-400 hover:text-gray-600 dark:hover:text-slate-200"
            >
              <X className="w-5 h-5" />
            </button>

            {bookingSuccess ? (
              <div className="text-center py-4">
                <div className="w-14 h-14 bg-emerald-100 dark:bg-emerald-950/60 rounded-full flex items-center justify-center mx-auto mb-3">
                  <CheckCircle className="w-8 h-8 text-emerald-600 dark:text-emerald-400" />
                </div>
                <h3 className="text-2xl font-extrabold text-gray-900 dark:text-slate-100">
                  Reservation Confirmed!
                </h3>
                <p className="text-xs text-gray-500 dark:text-slate-400 mt-1 mb-6">
                  Booking Reference: <span className="font-mono font-bold text-gray-700 dark:text-slate-300">{bookingSuccess.id}</span>
                </p>

                <div className="p-4 bg-gray-50 dark:bg-slate-900/60 rounded-xl text-left border border-gray-100 dark:border-slate-700/50 space-y-2 text-xs text-gray-700 dark:text-slate-300 mb-6">
                  <div className="flex justify-between">
                    <span className="text-gray-400">Hotel:</span>
                    <span className="font-bold text-gray-900 dark:text-white">{bookingSuccess.hotel_name}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-400">Room:</span>
                    <span className="font-semibold">{bookingSuccess.room_name}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-400">Dates:</span>
                    <span>{bookingSuccess.check_in_date} to {bookingSuccess.check_out_date} ({bookingSuccess.nights} nights)</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-400">Guests:</span>
                    <span>{bookingSuccess.guests} Guests</span>
                  </div>
                  <div className="flex justify-between pt-2 border-t border-gray-200 dark:border-slate-700 font-bold text-sm">
                    <span>Total Paid:</span>
                    <span className="text-brand-600">{hotel?.currency || '₹'}{bookingSuccess.total_price}</span>
                  </div>
                </div>

                <button
                  onClick={() => setIsModalOpen(false)}
                  className="w-full py-2.5 bg-brand-600 hover:bg-brand-700 text-white rounded-xl text-xs font-bold transition"
                >
                  Done
                </button>
              </div>
            ) : (
              <form onSubmit={handleConfirmBooking} className="space-y-4">
                <div>
                  <span className="text-xs font-semibold px-2.5 py-0.5 rounded-full bg-brand-50 dark:bg-brand-950 text-brand-600 dark:text-brand-400">
                    Hotel Reservation
                  </span>
                  <h3 className="text-xl font-bold text-gray-900 dark:text-slate-100 mt-1">
                    {selectedRoom?.name}
                  </h3>
                  <p className="text-xs text-gray-500 dark:text-slate-400">
                    {hotel.name} • {hotel.city}
                  </p>
                </div>

                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="block text-xs font-semibold text-gray-700 dark:text-slate-300 mb-1">
                      Check-In Date
                    </label>
                    <input
                      type="date"
                      required
                      min={today}
                      value={checkIn}
                      onChange={(e) => setCheckIn(e.target.value)}
                      className="w-full px-3 py-2 text-sm bg-gray-50 dark:bg-slate-900 border border-gray-200 dark:border-slate-700 rounded-xl focus:ring-2 focus:ring-brand-500 outline-none text-gray-900 dark:text-slate-100"
                    />
                  </div>
                  <div>
                    <label className="block text-xs font-semibold text-gray-700 dark:text-slate-300 mb-1">
                      Check-Out Date
                    </label>
                    <input
                      type="date"
                      required
                      min={checkIn}
                      value={checkOut}
                      onChange={(e) => setCheckOut(e.target.value)}
                      className="w-full px-3 py-2 text-sm bg-gray-50 dark:bg-slate-900 border border-gray-200 dark:border-slate-700 rounded-xl focus:ring-2 focus:ring-brand-500 outline-none text-gray-900 dark:text-slate-100"
                    />
                  </div>
                </div>

                <div>
                  <label className="block text-xs font-semibold text-gray-700 dark:text-slate-300 mb-1">
                    Number of Guests
                  </label>
                  <input
                    type="number"
                    min="1"
                    max={selectedRoom?.capacity || 4}
                    value={guests}
                    onChange={(e) => setGuests(e.target.value)}
                    className="w-full px-3 py-2 text-sm bg-gray-50 dark:bg-slate-900 border border-gray-200 dark:border-slate-700 rounded-xl focus:ring-2 focus:ring-brand-500 outline-none text-gray-900 dark:text-slate-100"
                  />
                </div>

                <div>
                  <label className="block text-xs font-semibold text-gray-700 dark:text-slate-300 mb-1">
                    Special Requests (Optional)
                  </label>
                  <textarea
                    rows={2}
                    placeholder="Early check-in, quiet room, airport pickup..."
                    value={specialRequests}
                    onChange={(e) => setSpecialRequests(e.target.value)}
                    className="w-full px-3 py-2 text-sm bg-gray-50 dark:bg-slate-900 border border-gray-200 dark:border-slate-700 rounded-xl focus:ring-2 focus:ring-brand-500 outline-none text-gray-900 dark:text-slate-100"
                  />
                </div>

                {/* Price Summary Breakdown */}
                <div className="p-4 bg-gray-50 dark:bg-slate-900/60 rounded-xl border border-gray-100 dark:border-slate-700/50 space-y-1.5 text-xs text-gray-600 dark:text-slate-300">
                  <div className="flex justify-between">
                    <span>{hotel?.currency || '₹'}{roomPrice} × {nights} {nights === 1 ? 'night' : 'nights'}</span>
                    <span>{hotel?.currency || '₹'}{subtotal}</span>
                  </div>
                  <div className="flex justify-between">
                    <span>Taxes & Hotel Fees (12%)</span>
                    <span>{hotel?.currency || '₹'}{taxes}</span>
                  </div>
                  <div className="flex justify-between pt-2 border-t border-gray-200 dark:border-slate-700 font-bold text-sm text-gray-900 dark:text-white">
                    <span>Total Amount (Indicative)</span>
                    <span className="text-brand-600">{hotel?.currency || '₹'}{total}</span>
                  </div>
                </div>

                {nights <= 0 && (
                  <p className="text-xs text-rose-500 dark:text-rose-400 font-medium">
                    ⚠️ Check-out date must be at least one day after check-in date.
                  </p>
                )}

                <div className="pt-2 flex justify-end gap-3">
                  <button
                    type="button"
                    onClick={() => setIsModalOpen(false)}
                    className="px-4 py-2 text-sm font-semibold text-gray-600 dark:text-slate-300 hover:bg-gray-100 dark:hover:bg-slate-700 rounded-xl transition"
                  >
                    Cancel
                  </button>
                  <button
                    type="submit"
                    disabled={bookingLoading || nights <= 0}
                    className="px-5 py-2 text-sm font-semibold text-white bg-brand-600 hover:bg-brand-700 rounded-xl shadow-sm transition flex items-center gap-1.5 disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    {bookingLoading ? "Confirming..." : (nights <= 0 ? "Select Valid Dates" : `Confirm & Reserve (${hotel?.currency || '₹'}${total})`)}
                  </button>
                </div>
              </form>
            )}
          </div>
        </div>
      )}

      {/* Social Share Modal */}
      {hotel && (
        <ShareModal
          isOpen={shareOpen}
          onClose={() => setShareOpen(false)}
          title={`${hotel.name} — ${hotel.city}, ${hotel.state}`}
          text={`🏨 Check out ${hotel.name} on TourMate! Rooms starting from $${hotel.starting_price_usd}/night with ${hotel.rating.toFixed(1)}★ rating.`}
          url={window.location.href}
        />
      )}
    </div>
  );
}
