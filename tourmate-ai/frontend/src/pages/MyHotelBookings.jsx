import React, { useState, useEffect } from "react";
import axios from "axios";
import { Link } from "react-router-dom";
import { API_BASE_URL } from "../api/axios";
import { 
  Building, 
  CalendarDays, 
  Users, 
  MapPin, 
  CheckCircle2, 
  XCircle,
  CreditCard,
  ArrowLeft
} from "lucide-react";
import SafeImage from "../components/SafeImage";

export default function MyHotelBookings() {
  const [bookings, setBookings] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    fetchBookings();
  }, []);

  const fetchBookings = async () => {
    setLoading(true);
    try {
      const res = await axios.get(`${API_BASE_URL}/hotel-bookings/my`, {
        withCredentials: true,
      });
      setBookings(res.data.data || []);
      setError(null);
    } catch (err) {
      console.error("Failed to fetch bookings:", err);
      setError("Failed to load your bookings. Please try again later.");
    } finally {
      setLoading(false);
    }
  };

  const handleCancel = async (bookingId) => {
    if (!window.confirm("Are you sure you want to cancel this booking?")) return;
    
    try {
      await axios.post(`${API_BASE_URL}/hotel-bookings/${bookingId}/cancel`, {}, {
        withCredentials: true,
      });
      // Refresh bookings
      fetchBookings();
    } catch (err) {
      console.error("Failed to cancel booking:", err);
      alert("Failed to cancel booking. It may be non-refundable or an error occurred.");
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 dark:bg-slate-900 pt-20 px-4 flex justify-center">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-brand-600"></div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-slate-900 pt-8 pb-20 px-4 sm:px-6 lg:px-8">
      <div className="max-w-4xl mx-auto">
        {/* Header */}
        <div className="mb-8">
          <Link to="/hotels" className="inline-flex items-center gap-2 text-sm font-medium text-brand-600 dark:text-brand-400 hover:text-brand-700 dark:hover:text-brand-300 transition mb-4">
            <ArrowLeft className="w-4 h-4" />
            Back to Hotels
          </Link>
          <h1 className="text-3xl font-extrabold text-gray-900 dark:text-white">My Hotel Bookings</h1>
          <p className="mt-2 text-gray-600 dark:text-slate-400">View and manage your upcoming and past stays.</p>
        </div>

        {error && (
          <div className="mb-6 p-4 bg-red-50 dark:bg-red-900/20 text-red-600 dark:text-red-400 rounded-xl border border-red-100 dark:border-red-800/30 text-sm">
            {error}
          </div>
        )}

        {bookings.length === 0 && !error ? (
          <div className="bg-white dark:bg-slate-800 rounded-2xl p-12 text-center border border-gray-200 dark:border-slate-700 shadow-sm">
            <Building className="w-16 h-16 text-gray-300 dark:text-slate-600 mx-auto mb-4" />
            <h3 className="text-xl font-bold text-gray-900 dark:text-white mb-2">No Bookings Found</h3>
            <p className="text-gray-500 dark:text-slate-400 mb-6">You haven't made any hotel reservations yet.</p>
            <Link to="/hotels" className="inline-flex items-center gap-2 px-6 py-3 bg-brand-600 hover:bg-brand-700 text-white rounded-xl text-sm font-bold shadow-sm transition">
              Explore Hotels
            </Link>
          </div>
        ) : (
          <div className="space-y-6">
            {bookings.map((booking) => (
              <div key={booking.id} className="bg-white dark:bg-slate-800 rounded-2xl border border-gray-200 dark:border-slate-700 shadow-sm overflow-hidden flex flex-col md:flex-row">
                {/* Hotel Image */}
                <div className="w-full md:w-64 h-48 md:h-auto bg-gray-100 dark:bg-slate-700 shrink-0">
                  <SafeImage 
                    src={booking.hotel_image} 
                    alt={booking.hotel_name}
                    className="w-full h-full object-cover"
                  />
                </div>
                
                {/* Booking Details */}
                <div className="p-6 flex-1 flex flex-col justify-between">
                  <div>
                    <div className="flex items-start justify-between mb-2">
                      <div>
                        <h3 className="text-xl font-bold text-gray-900 dark:text-white mb-1">{booking.hotel_name}</h3>
                        <div className="flex items-center gap-1.5 text-sm text-gray-500 dark:text-slate-400">
                          <MapPin className="w-4 h-4" />
                          <span>{booking.hotel_city}</span>
                        </div>
                      </div>
                      
                      {/* Status Badge */}
                      {booking.status === "confirmed" ? (
                        <span className="inline-flex items-center gap-1 px-3 py-1 rounded-full text-xs font-bold bg-green-50 dark:bg-green-900/30 text-green-700 dark:text-green-400 border border-green-200 dark:border-green-800/50">
                          <CheckCircle2 className="w-3.5 h-3.5" />
                          Confirmed
                        </span>
                      ) : (
                        <span className="inline-flex items-center gap-1 px-3 py-1 rounded-full text-xs font-bold bg-red-50 dark:bg-red-900/30 text-red-700 dark:text-red-400 border border-red-200 dark:border-red-800/50">
                          <XCircle className="w-3.5 h-3.5" />
                          Cancelled
                        </span>
                      )}
                    </div>

                    <div className="mt-6 grid grid-cols-2 gap-4">
                      <div>
                        <span className="block text-xs font-semibold text-gray-400 uppercase tracking-wider mb-1">Check-in</span>
                        <div className="flex items-center gap-2 text-sm font-medium text-gray-900 dark:text-slate-200">
                          <CalendarDays className="w-4 h-4 text-brand-500" />
                          {booking.check_in_date}
                        </div>
                      </div>
                      <div>
                        <span className="block text-xs font-semibold text-gray-400 uppercase tracking-wider mb-1">Check-out</span>
                        <div className="flex items-center gap-2 text-sm font-medium text-gray-900 dark:text-slate-200">
                          <CalendarDays className="w-4 h-4 text-brand-500" />
                          {booking.check_out_date}
                        </div>
                      </div>
                      <div>
                        <span className="block text-xs font-semibold text-gray-400 uppercase tracking-wider mb-1">Room</span>
                        <div className="text-sm font-medium text-gray-900 dark:text-slate-200 truncate">
                          {booking.room_name}
                        </div>
                      </div>
                      <div>
                        <span className="block text-xs font-semibold text-gray-400 uppercase tracking-wider mb-1">Rooms & Guests</span>
                        <div className="flex items-center gap-2 text-sm font-medium text-gray-900 dark:text-slate-200">
                          <Users className="w-4 h-4 text-brand-500" />
                          {booking.rooms} {booking.rooms === 1 ? 'Room' : 'Rooms'}, {booking.guests} {booking.guests === 1 ? 'Guest' : 'Guests'}
                        </div>
                      </div>
                    </div>
                  </div>

                  <div className="mt-6 pt-6 border-t border-gray-100 dark:border-slate-700 flex flex-col sm:flex-row items-center justify-between gap-4">
                    <div className="flex items-center gap-3">
                      <div className="p-2 bg-brand-50 dark:bg-brand-900/30 rounded-lg text-brand-600 dark:text-brand-400">
                        <CreditCard className="w-5 h-5" />
                      </div>
                      <div>
                        <span className="block text-xs text-gray-500 dark:text-slate-400">Total Price</span>
                        <span className="block text-lg font-extrabold text-gray-900 dark:text-white">
                          {new Intl.NumberFormat("en-IN", { style: "currency", currency: "INR" }).format(booking.total_price)}
                        </span>
                      </div>
                    </div>

                    {booking.status === "confirmed" && (
                      <button 
                        onClick={() => handleCancel(booking.id)}
                        className="w-full sm:w-auto px-5 py-2.5 bg-white dark:bg-slate-800 hover:bg-red-50 dark:hover:bg-red-900/20 text-red-600 dark:text-red-400 text-sm font-bold rounded-xl border border-red-200 dark:border-red-800/50 shadow-sm transition"
                      >
                        Cancel Booking
                      </button>
                    )}
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
