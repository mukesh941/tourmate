import { Routes, Route, Navigate } from "react-router-dom";
import Navbar from "./components/Navbar";
import ProtectedRoute from "./components/ProtectedRoute";
import ChatbotWidget from "./components/ChatbotWidget";
import Login from "./pages/Login";
import Register from "./pages/Register";
import Dashboard from "./pages/Dashboard";

import Destinations from "./pages/Destinations";
import DestinationDetail from "./pages/DestinationDetail";
import ExploreDestination from "./pages/ExploreDestination";
import Places from "./pages/Places";
import PlaceDetail from "./pages/PlaceDetail";
import CategoryPage from "./pages/CategoryPage";
import ClusteredMapView from "./pages/ClusteredMapView";
import RoutePlannerView from "./pages/RoutePlannerView";
import ItineraryBuilder from "./pages/ItineraryBuilder";
import MyItineraries from "./pages/MyItineraries";
import LandmarkRecognition from "./pages/LandmarkRecognition";
import Guides from "./pages/Guides";
import Hotels from "./pages/Hotels";
import HotelDetail from "./pages/HotelDetail";
import AdminDashboard from "./pages/admin/AdminDashboard";
import ManageDestinations from "./pages/admin/ManageDestinations";
import ManageCategories from "./pages/admin/ManageCategories";
import ManagePlaces from "./pages/admin/ManagePlaces";
import ManageUsers from "./pages/admin/ManageUsers";
import ChangePassword from "./pages/ChangePassword";

import { useState, useEffect } from "react";

export default function App() {
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

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-slate-900/50">
      <Navbar toggleDarkMode={toggleDarkMode} darkMode={darkMode} />
      <Routes>
        <Route path="/" element={<Navigate to="/dashboard" replace />} />
        <Route path="/login" element={<Login />} />
        <Route path="/register" element={<Register />} />
        
        <Route path="/destinations" element={<Destinations />} />
        <Route path="/destinations/:id" element={<DestinationDetail />} />
        <Route path="/explore" element={<ExploreDestination />} />
        <Route path="/places" element={<Places />} />
        <Route path="/places/:id" element={<PlaceDetail />} />
        <Route path="/category/:categoryName" element={<CategoryPage />} />
        <Route path="/map/clusters" element={<ClusteredMapView />} />
        <Route path="/map/route" element={<RoutePlannerView />} />
        <Route path="/itinerary-builder" element={<ProtectedRoute><ItineraryBuilder /></ProtectedRoute>} />
        <Route path="/my-itineraries" element={<ProtectedRoute><MyItineraries /></ProtectedRoute>} />
        <Route path="/landmark-recognition" element={<ProtectedRoute><LandmarkRecognition /></ProtectedRoute>} />
        <Route path="/guides" element={<ProtectedRoute><Guides /></ProtectedRoute>} />
        <Route path="/hotels" element={<Hotels />} />
        <Route path="/hotels/:id" element={<HotelDetail />} />
        <Route path="/change-password" element={<ProtectedRoute><ChangePassword /></ProtectedRoute>} />

        <Route
          path="/dashboard"
          element={
            <ProtectedRoute>
              <Dashboard />
            </ProtectedRoute>
          }
        />
        
        <Route path="/admin" element={<ProtectedRoute><AdminDashboard /></ProtectedRoute>} />
        <Route path="/admin/destinations" element={<ProtectedRoute><ManageDestinations /></ProtectedRoute>} />
        <Route path="/admin/categories" element={<ProtectedRoute><ManageCategories /></ProtectedRoute>} />
        <Route path="/admin/places" element={<ProtectedRoute><ManagePlaces /></ProtectedRoute>} />
        <Route path="/admin/users" element={<ProtectedRoute><ManageUsers /></ProtectedRoute>} />
      </Routes>
      <ChatbotWidget />
    </div>
  );
}
