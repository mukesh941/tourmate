import { Routes, Route, Navigate } from "react-router-dom";
import { useState, useEffect, lazy, Suspense } from "react";
import Navbar from "./components/Navbar";
import ProtectedRoute from "./components/ProtectedRoute";
import ChatbotWidget from "./components/ChatbotWidget";
import { useAuth } from "./context/AuthContext";

// Eagerly loaded primary entry pages
import Login from "./pages/Login";
import Register from "./pages/Register";
import Dashboard from "./pages/Dashboard";
import Destinations from "./pages/Destinations";
import Places from "./pages/Places";
import VerifyEmail from "./pages/VerifyEmail";
import PaymentSuspended from "./pages/PaymentSuspended";
import { isServiceSuspended } from "./config/serviceStatus";

// Lazily loaded secondary and heavy route components for code-splitting
const DestinationDetail = lazy(() => import("./pages/DestinationDetail"));
const ExploreDestination = lazy(() => import("./pages/ExploreDestination"));
const PlaceDetail = lazy(() => import("./pages/PlaceDetail"));
const CategoryPage = lazy(() => import("./pages/CategoryPage"));
const ClusteredMapView = lazy(() => import("./pages/ClusteredMapView"));
const RoutePlannerView = lazy(() => import("./pages/RoutePlannerView"));
const ItineraryBuilder = lazy(() => import("./pages/ItineraryBuilder"));
const MyItineraries = lazy(() => import("./pages/MyItineraries"));
const LandmarkRecognition = lazy(() => import("./pages/LandmarkRecognition"));
const Guides = lazy(() => import("./pages/Guides"));
const Hotels = lazy(() => import("./pages/Hotels"));
const HotelDetail = lazy(() => import("./pages/HotelDetail"));
const ChangePassword = lazy(() => import("./pages/ChangePassword"));
const AdminDashboard = lazy(() => import("./pages/admin/AdminDashboard"));
const ManageDestinations = lazy(() => import("./pages/admin/ManageDestinations"));
const ManageCategories = lazy(() => import("./pages/admin/ManageCategories"));
const ManagePlaces = lazy(() => import("./pages/admin/ManagePlaces"));
const ManageUsers = lazy(() => import("./pages/admin/ManageUsers"));

function PageFallback() {
  return (
    <div className="flex flex-col items-center justify-center min-h-[60vh] space-y-3">
      <div className="w-10 h-10 border-4 border-brand-200 border-t-brand-600 rounded-full animate-spin"></div>
      <p className="text-xs font-semibold text-gray-500 dark:text-slate-400 uppercase tracking-wider">Loading...</p>
    </div>
  );
}

function RootRoute() {
  const { user, loading } = useAuth();
  if (loading) return <PageFallback />;
  if (!user) return <Navigate to="/login" replace />;
  return <Dashboard />;
}

export default function App() {
  const { user } = useAuth();
  const [darkMode, setDarkMode] = useState(() => {
    const saved = localStorage.getItem("theme");
    if (saved) return saved === "dark";
    // default to true as per user request
    return true;
  });

  useEffect(() => {
    if (darkMode) {
      document.documentElement.classList.add("dark");
      localStorage.setItem("theme", "dark");
    } else {
      document.documentElement.classList.remove("dark");
      localStorage.setItem("theme", "light");
    }
  }, [darkMode]);

  const toggleDarkMode = () => setDarkMode(!darkMode);

  if (isServiceSuspended()) {
    return <PaymentSuspended />;
  }

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-slate-900/50">
      <Navbar toggleDarkMode={toggleDarkMode} darkMode={darkMode} />
      <Suspense fallback={<PageFallback />}>
        <Routes>
          <Route path="/" element={<RootRoute />} />
          <Route path="/dashboard" element={<ProtectedRoute><Dashboard /></ProtectedRoute>} />
          <Route path="/login" element={<Login />} />
          <Route path="/register" element={<Register />} />
          <Route path="/verify-email" element={<VerifyEmail />} />
          
          <Route path="/destinations" element={<ProtectedRoute><Destinations /></ProtectedRoute>} />
          <Route path="/destinations/:id" element={<ProtectedRoute><DestinationDetail /></ProtectedRoute>} />
          <Route path="/explore" element={<ProtectedRoute><ExploreDestination /></ProtectedRoute>} />
          <Route path="/places" element={<ProtectedRoute><Places /></ProtectedRoute>} />
          <Route path="/places/:id" element={<ProtectedRoute><PlaceDetail /></ProtectedRoute>} />
          <Route path="/category/:categoryName" element={<ProtectedRoute><CategoryPage /></ProtectedRoute>} />
          <Route path="/map/clusters" element={<ProtectedRoute><ClusteredMapView /></ProtectedRoute>} />
          <Route path="/map/route" element={<ProtectedRoute><RoutePlannerView /></ProtectedRoute>} />
          <Route path="/itinerary-builder" element={<ProtectedRoute><ItineraryBuilder /></ProtectedRoute>} />
          <Route path="/my-itineraries" element={<ProtectedRoute><MyItineraries /></ProtectedRoute>} />
          <Route path="/landmark-recognition" element={<ProtectedRoute><LandmarkRecognition /></ProtectedRoute>} />
          <Route path="/guides" element={<ProtectedRoute><Guides /></ProtectedRoute>} />
          <Route path="/hotels" element={<ProtectedRoute><Hotels /></ProtectedRoute>} />
          <Route path="/hotels/:id" element={<ProtectedRoute><HotelDetail /></ProtectedRoute>} />
          <Route path="/change-password" element={<ProtectedRoute><ChangePassword /></ProtectedRoute>} />

          <Route path="/admin" element={<ProtectedRoute><AdminDashboard /></ProtectedRoute>} />
          <Route path="/admin/destinations" element={<ProtectedRoute><ManageDestinations /></ProtectedRoute>} />
          <Route path="/admin/categories" element={<ProtectedRoute><ManageCategories /></ProtectedRoute>} />
          <Route path="/admin/places" element={<ProtectedRoute><ManagePlaces /></ProtectedRoute>} />
          <Route path="/admin/users" element={<ProtectedRoute><ManageUsers /></ProtectedRoute>} />

          <Route path="*" element={<Navigate to="/login" replace />} />
        </Routes>
      </Suspense>
      {user && <ChatbotWidget />}
    </div>
  );
}
