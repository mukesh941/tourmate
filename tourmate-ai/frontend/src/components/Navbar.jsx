import { Link, useNavigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import { useTranslation } from "react-i18next";

export default function Navbar({ toggleDarkMode, darkMode }) {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const { t, i18n } = useTranslation();

  const handleLogout = () => {
    logout();
    navigate("/login");
  };

  const toggleLanguage = () => {
    i18n.changeLanguage(i18n.language === 'en' ? 'hi' : 'en');
  };

  return (
    <nav className="glass sticky top-0 z-50 transition-colors">
      <div className="max-w-6xl mx-auto px-4 h-16 flex items-center justify-between">
        <Link to="/" className="text-2xl font-display font-bold text-gradient tracking-tight">TourMate AI</Link>
        <div className="space-x-1 md:space-x-4 flex items-center">
          {[
            { to: '/destinations', label: t('Destinations') },
            { to: '/places', label: t('Explore Places') },
            { to: '/map/clusters', label: t('AI Cluster Map') },
            { to: '/map/route', label: t('Route Planner') },
            { to: '/itinerary-builder', label: t('AI Itineraries') },
            { to: '/landmark-recognition', label: t('AI Lens') },
          ].map((link) => (
            <Link key={link.to} to={link.to} className="relative group text-gray-600 dark:text-slate-300 font-medium px-2 py-1 text-sm md:text-base hidden sm:block">
              {link.label}
              <span className="absolute -bottom-1 left-0 w-0 h-0.5 bg-accent-500 rounded-full transition-all duration-300 group-hover:w-full"></span>
            </Link>
          ))}
          
          <button 
            onClick={toggleLanguage}
            className="p-2 rounded-lg hover:bg-gray-100 dark:hover:bg-slate-800 text-gray-600 dark:text-slate-300 transition-colors text-sm font-bold ml-2"
            title="Toggle Language"
          >
            🌐 {i18n.language === 'hi' ? 'HI' : 'EN'}
          </button>

          <button 
            onClick={toggleDarkMode}
            className="p-2 rounded-full hover:bg-gray-100 dark:hover:bg-slate-800 text-gray-500 dark:text-slate-400 transition-colors hover:scale-110 transform"
            title="Toggle Dark Mode"
          >
            {darkMode ? "☀️" : "🌙"}
          </button>

          {user ? (
            <>
              {user.role === "admin" && (
                <Link to="/admin" className="text-red-600 font-medium hover:underline text-sm md:text-base ml-2">{t('Admin')}</Link>
              )}
              <Link to="/dashboard" className="text-brand-600 font-bold hover:text-brand-700 ml-2 hidden md:block">
                {t('Dashboard')}
              </Link>
              <button
                onClick={handleLogout}
                className="bg-gray-100 dark:bg-slate-800 hover:bg-gray-200 dark:hover:bg-slate-700 text-gray-700 dark:text-slate-200 px-4 py-2 rounded-lg font-medium transition shadow-sm hover:shadow-md ml-2 text-sm md:text-base"
              >
                {t('Logout')}
              </button>
            </>
          ) : (
            <div className="flex space-x-2 ml-2">
              <Link to="/login" className="text-gray-600 dark:text-slate-300 hover:text-brand-600 font-medium px-3 py-2 text-sm md:text-base">{t('Log in')}</Link>
              <Link to="/register" className="bg-gradient-to-r from-brand-500 to-accent-500 hover:from-brand-600 hover:to-accent-600 text-white px-4 py-2 rounded-lg font-medium transition shadow-md hover:shadow-lg transform hover:-translate-y-0.5 text-sm md:text-base">
                {t('Sign up')}
              </Link>
            </div>
          )}
        </div>
      </div>
    </nav>
  );
}
