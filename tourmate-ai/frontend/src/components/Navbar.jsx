import React, { useState, useRef, useEffect } from "react";
import { Link, useNavigate, useLocation } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import { useTranslation } from "react-i18next";
import { ChevronDown, Menu, X, User, LogOut, Lock, Settings, Map, Compass, Navigation, MapPin, Building, Briefcase, Camera, Route } from "lucide-react";

export default function Navbar({ toggleDarkMode, darkMode }) {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  const { t, i18n } = useTranslation();
  
  const [openDropdown, setOpenDropdown] = useState(null);
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const navRef = useRef(null);

  useEffect(() => {
    function handleClickOutside(event) {
      if (navRef.current && !navRef.current.contains(event.target)) {
        setOpenDropdown(null);
      }
    }
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, [navRef]);

  useEffect(() => {
    setMobileMenuOpen(false);
    setOpenDropdown(null);
  }, [location.pathname]);

  const handleLogout = () => {
    logout();
    navigate("/login");
  };

  const toggleLanguage = () => {
    const langs = ['en', 'hi', 'kn', 'ta', 'ml'];
    const currentIndex = langs.indexOf(i18n.language);
    const nextIndex = (currentIndex + 1) % langs.length;
    i18n.changeLanguage(langs[nextIndex]);
  };

  const toggleDropdown = (name) => {
    if (openDropdown === name) setOpenDropdown(null);
    else setOpenDropdown(name);
  };

  const menuItems = {
    explore: [
      { to: '/destinations', label: t('Destinations'), icon: <MapPin className="w-4 h-4" /> },
      { to: '/places', label: t('Explore Places'), icon: <Compass className="w-4 h-4" /> },
      { to: '/guides', label: t('Local Guides'), icon: <User className="w-4 h-4" /> },
      { to: '/landmark-recognition', label: t('AI Lens'), icon: <Camera className="w-4 h-4" /> },
    ],
    plan: [
      { to: '/itinerary-builder', label: t('AI Itineraries'), icon: <Briefcase className="w-4 h-4" /> },
      { to: '/map/route', label: t('Route Planner'), icon: <Route className="w-4 h-4" /> },
      { to: '/map/clusters', label: t('AI Cluster Map'), icon: <Map className="w-4 h-4" /> },
    ]
  };

  return (
    <>
      <nav ref={navRef} className="glass sticky top-4 z-50 mx-4 md:mx-auto max-w-7xl rounded-2xl mb-4 transition-all duration-300 shadow-sm border border-gray-100 dark:border-slate-800">
        <div className="px-6 h-16 flex items-center justify-between">
          <Link to="/" className="text-2xl font-display font-bold text-gradient tracking-tight">TourMate AI</Link>
          
          <div className="hidden md:flex items-center space-x-1 lg:space-x-4">
            
            <div className="relative group">
              <button 
                onClick={() => toggleDropdown('explore')}
                className="flex items-center gap-1 text-gray-700 dark:text-slate-200 font-medium px-3 py-2 rounded-lg hover:bg-gray-100 dark:hover:bg-slate-800 transition-colors"
              >
                {t('Explore')} <ChevronDown className={`w-4 h-4 transition-transform ${openDropdown === 'explore' ? 'rotate-180' : ''}`} />
              </button>
              {openDropdown === 'explore' && (
                <div className="absolute top-full left-0 mt-2 w-56 bg-white dark:bg-slate-800 rounded-xl shadow-xl border border-gray-100 dark:border-slate-700 py-2 origin-top-left z-50">
                  {menuItems.explore.map((item) => (
                    <Link key={item.to} to={item.to} className="flex items-center gap-3 px-4 py-2.5 text-sm text-gray-700 dark:text-slate-200 hover:bg-gray-50 dark:hover:bg-slate-700 hover:text-brand-600 dark:hover:text-brand-400 transition-colors">
                      {item.icon} {item.label}
                    </Link>
                  ))}
                </div>
              )}
            </div>

            <Link to="/hotels" className="text-gray-700 dark:text-slate-200 font-medium px-3 py-2 rounded-lg hover:bg-gray-100 dark:hover:bg-slate-800 transition-colors">
              {t('Stays')}
            </Link>

            <div className="relative group">
              <button 
                onClick={() => toggleDropdown('plan')}
                className="flex items-center gap-1 text-gray-700 dark:text-slate-200 font-medium px-3 py-2 rounded-lg hover:bg-gray-100 dark:hover:bg-slate-800 transition-colors"
              >
                {t('Plan Trip')} <ChevronDown className={`w-4 h-4 transition-transform ${openDropdown === 'plan' ? 'rotate-180' : ''}`} />
              </button>
              {openDropdown === 'plan' && (
                <div className="absolute top-full left-0 mt-2 w-56 bg-white dark:bg-slate-800 rounded-xl shadow-xl border border-gray-100 dark:border-slate-700 py-2 origin-top-left z-50">
                  {menuItems.plan.map((item) => (
                    <Link key={item.to} to={item.to} className="flex items-center gap-3 px-4 py-2.5 text-sm text-gray-700 dark:text-slate-200 hover:bg-gray-50 dark:hover:bg-slate-700 hover:text-brand-600 dark:hover:text-brand-400 transition-colors">
                      {item.icon} {item.label}
                    </Link>
                  ))}
                </div>
              )}
            </div>
            
            <div className="h-6 w-px bg-gray-200 dark:bg-slate-700 mx-2"></div>

            <div className="relative group ml-2">
              <button 
                onClick={() => toggleDropdown('language')}
                className="flex items-center gap-1 p-2 rounded-lg hover:bg-gray-100 dark:hover:bg-slate-800 text-gray-600 dark:text-slate-300 transition-colors text-sm font-bold"
                title="Select Language"
              >
                🌐 {i18n.language ? i18n.language.toUpperCase() : 'EN'} <ChevronDown className={`w-3 h-3 transition-transform ${openDropdown === 'language' ? 'rotate-180' : ''}`} />
              </button>
              {openDropdown === 'language' && (
                <div className="absolute top-full right-0 mt-2 w-32 bg-white dark:bg-slate-800 rounded-xl shadow-xl border border-gray-100 dark:border-slate-700 py-2 origin-top-right z-50">
                  {['en', 'hi', 'kn', 'ta', 'ml'].map((lang) => (
                    <button
                      key={lang}
                      onClick={() => {
                        i18n.changeLanguage(lang);
                        setOpenDropdown(null);
                      }}
                      className={`w-full text-left px-4 py-2 text-sm transition-colors ${i18n.language === lang ? 'bg-brand-50 dark:bg-slate-700 text-brand-600 dark:text-brand-400 font-bold' : 'text-gray-700 dark:text-slate-200 hover:bg-gray-50 dark:hover:bg-slate-700'}`}
                    >
                      {lang === 'en' ? 'English' : lang === 'hi' ? 'हिंदी' : lang === 'kn' ? 'ಕನ್ನಡ' : lang === 'ta' ? 'தமிழ்' : 'മലയാളം'}
                    </button>
                  ))}
                </div>
              )}
            </div>

            <button 
              onClick={toggleDarkMode}
              className="p-2 rounded-full hover:bg-gray-100 dark:hover:bg-slate-800 text-gray-500 dark:text-slate-400 transition-colors ml-1"
              title="Toggle Dark Mode"
            >
              {darkMode ? "☀️" : "🌙"}
            </button>

            {user ? (
              <div className="relative ml-2">
                <button 
                  onClick={() => toggleDropdown('profile')}
                  className="flex items-center gap-2 bg-gray-100 dark:bg-slate-800 hover:bg-gray-200 dark:hover:bg-slate-700 text-gray-700 dark:text-slate-200 px-3 py-2 rounded-xl font-medium transition"
                >
                  <div className="w-6 h-6 bg-brand-500 text-white rounded-full flex items-center justify-center text-xs font-bold uppercase">
                    {user?.name ? user.name.charAt(0) : 'U'}
                  </div>
                  <ChevronDown className="w-4 h-4" />
                </button>
                {openDropdown === 'profile' && (
                  <div className="absolute top-full right-0 mt-2 w-56 bg-white dark:bg-slate-800 rounded-xl shadow-xl border border-gray-100 dark:border-slate-700 py-2 origin-top-right z-50">
                    <div className="px-4 py-2 border-b border-gray-100 dark:border-slate-700 mb-2">
                      <p className="text-sm font-bold text-gray-900 dark:text-white truncate">{user.name}</p>
                      <p className="text-xs text-gray-500 dark:text-slate-400 truncate">{user.email}</p>
                    </div>
                    {user.role === "admin" && (
                      <Link to="/admin" className="flex items-center gap-3 px-4 py-2.5 text-sm text-red-600 dark:text-red-400 hover:bg-red-50 dark:hover:bg-red-900/20 transition-colors">
                        <Settings className="w-4 h-4" /> {t('Admin')}
                      </Link>
                    )}
                    <Link to="/dashboard" className="flex items-center gap-3 px-4 py-2.5 text-sm text-gray-700 dark:text-slate-200 hover:bg-gray-50 dark:hover:bg-slate-700 transition-colors">
                      <User className="w-4 h-4" /> {t('Dashboard')}
                    </Link>
                    <Link to="/change-password" className="flex items-center gap-3 px-4 py-2.5 text-sm text-gray-700 dark:text-slate-200 hover:bg-gray-50 dark:hover:bg-slate-700 transition-colors">
                      <Lock className="w-4 h-4" /> Change Password
                    </Link>
                    <button onClick={handleLogout} className="w-full text-left flex items-center gap-3 px-4 py-2.5 text-sm text-gray-700 dark:text-slate-200 hover:bg-gray-50 dark:hover:bg-slate-700 transition-colors border-t border-gray-100 dark:border-slate-700 mt-2 pt-2">
                      <LogOut className="w-4 h-4" /> {t('Logout')}
                    </button>
                  </div>
                )}
              </div>
            ) : (
              <div className="flex items-center space-x-2 ml-2">
                <Link to="/login" className="text-gray-700 dark:text-slate-200 hover:text-brand-600 font-medium px-4 py-2 text-sm transition-colors">{t('Log in')}</Link>
                <Link to="/register" className="bg-gradient-to-r from-brand-500 to-accent-500 hover:from-brand-600 hover:to-accent-600 text-white px-5 py-2.5 rounded-xl font-bold transition shadow-md hover:shadow-lg transform hover:-translate-y-0.5 text-sm">
                  {t('Sign up')}
                </Link>
              </div>
            )}
          </div>

          <div className="md:hidden flex items-center gap-2">
            <div className="relative">
              <button onClick={() => toggleDropdown('mobileLanguage')} className="p-2 text-sm font-bold flex items-center gap-1 text-gray-700 dark:text-slate-200">
                🌐 {i18n.language ? i18n.language.toUpperCase() : 'EN'}
              </button>
              {openDropdown === 'mobileLanguage' && (
                <div className="absolute top-full right-0 mt-2 w-32 bg-white dark:bg-slate-800 rounded-xl shadow-xl border border-gray-100 dark:border-slate-700 py-2 origin-top-right z-50">
                  {['en', 'hi', 'kn', 'ta', 'ml'].map((lang) => (
                    <button
                      key={lang}
                      onClick={() => {
                        i18n.changeLanguage(lang);
                        setOpenDropdown(null);
                      }}
                      className={`w-full text-left px-4 py-2 text-sm transition-colors ${i18n.language === lang ? 'bg-brand-50 dark:bg-slate-700 text-brand-600 dark:text-brand-400 font-bold' : 'text-gray-700 dark:text-slate-200 hover:bg-gray-50 dark:hover:bg-slate-700'}`}
                    >
                      {lang === 'en' ? 'English' : lang === 'hi' ? 'हिंदी' : lang === 'kn' ? 'ಕನ್ನಡ' : lang === 'ta' ? 'தமிழ்' : 'മലയാളം'}
                    </button>
                  ))}
                </div>
              )}
            </div>
            <button onClick={toggleDarkMode} className="p-2">{darkMode ? "☀️" : "🌙"}</button>
            <button onClick={() => setMobileMenuOpen(!mobileMenuOpen)} className="p-2 text-gray-700 dark:text-slate-200">
              {mobileMenuOpen ? <X className="w-6 h-6" /> : <Menu className="w-6 h-6" />}
            </button>
          </div>
        </div>

        {mobileMenuOpen && (
          <div className="md:hidden border-t border-gray-100 dark:border-slate-700 bg-white dark:bg-slate-900 rounded-b-2xl overflow-hidden shadow-lg pb-4 px-4 pt-2">
            <div className="space-y-1">
              <div className="font-bold text-xs text-gray-400 uppercase mt-4 mb-2">Explore</div>
              {menuItems.explore.map(item => (
                <Link key={item.to} to={item.to} className="flex items-center gap-3 px-3 py-2.5 text-sm text-gray-700 dark:text-slate-200 rounded-lg hover:bg-gray-50 dark:hover:bg-slate-800">
                  {item.icon} {item.label}
                </Link>
              ))}
              <Link to="/hotels" className="flex items-center gap-3 px-3 py-2.5 text-sm text-gray-700 dark:text-slate-200 rounded-lg hover:bg-gray-50 dark:hover:bg-slate-800">
                <Building className="w-4 h-4" /> Stays
              </Link>
              
              <div className="font-bold text-xs text-gray-400 uppercase mt-4 mb-2">Plan Trip</div>
              {menuItems.plan.map(item => (
                <Link key={item.to} to={item.to} className="flex items-center gap-3 px-3 py-2.5 text-sm text-gray-700 dark:text-slate-200 rounded-lg hover:bg-gray-50 dark:hover:bg-slate-800">
                  {item.icon} {item.label}
                </Link>
              ))}
              
              {!user && (
                <div className="mt-6 flex gap-2">
                  <Link to="/login" className="flex-1 text-center bg-gray-100 dark:bg-slate-800 text-gray-700 dark:text-slate-200 font-bold px-4 py-2.5 rounded-xl">Login</Link>
                  <Link to="/register" className="flex-1 text-center bg-brand-600 text-white font-bold px-4 py-2.5 rounded-xl">Sign Up</Link>
                </div>
              )}
            </div>
          </div>
        )}
      </nav>

      <div className="md:hidden fixed bottom-0 left-0 right-0 bg-white/95 dark:bg-slate-900/95 backdrop-blur-lg border-t border-gray-200 dark:border-slate-800 flex justify-around items-center p-2 z-50 pb-safe shadow-[0_-4px_10px_rgba(0,0,0,0.05)]">
        <Link to="/dashboard" className={`flex flex-col items-center justify-center p-2 text-[10px] font-medium transition-colors ${location.pathname === '/dashboard' ? 'text-brand-600 dark:text-brand-400' : 'text-gray-500 dark:text-slate-400 hover:text-gray-900 dark:hover:text-white'}`}>
          <Compass className={`w-5 h-5 mb-1 ${location.pathname === '/dashboard' ? 'fill-brand-100 dark:fill-brand-900/50' : ''}`} />
          Home
        </Link>
        <Link to="/places" className={`flex flex-col items-center justify-center p-2 text-[10px] font-medium transition-colors ${location.pathname === '/places' ? 'text-brand-600 dark:text-brand-400' : 'text-gray-500 dark:text-slate-400 hover:text-gray-900 dark:hover:text-white'}`}>
          <MapPin className={`w-5 h-5 mb-1 ${location.pathname === '/places' ? 'fill-brand-100 dark:fill-brand-900/50' : ''}`} />
          Explore
        </Link>
        <Link to="/map/clusters" className={`flex flex-col items-center justify-center p-2 text-[10px] font-medium transition-colors ${location.pathname === '/map/clusters' ? 'text-brand-600 dark:text-brand-400' : 'text-gray-500 dark:text-slate-400 hover:text-gray-900 dark:hover:text-white'}`}>
          <Map className={`w-5 h-5 mb-1 ${location.pathname === '/map/clusters' ? 'fill-brand-100 dark:fill-brand-900/50' : ''}`} />
          Map
        </Link>
        <Link to="/itinerary-builder" className={`flex flex-col items-center justify-center p-2 text-[10px] font-medium transition-colors ${location.pathname === '/itinerary-builder' ? 'text-brand-600 dark:text-brand-400' : 'text-gray-500 dark:text-slate-400 hover:text-gray-900 dark:hover:text-white'}`}>
          <Briefcase className={`w-5 h-5 mb-1 ${location.pathname === '/itinerary-builder' ? 'fill-brand-100 dark:fill-brand-900/50' : ''}`} />
          Trips
        </Link>
        {user ? (
          <button onClick={() => toggleDropdown('mobileProfile')} className={`flex flex-col items-center justify-center p-2 text-[10px] font-medium transition-colors text-gray-500 dark:text-slate-400 hover:text-gray-900 dark:hover:text-white relative`}>
            <User className="w-5 h-5 mb-1" />
            Profile
            {openDropdown === 'mobileProfile' && (
              <div className="absolute bottom-full right-0 mb-4 w-48 bg-white dark:bg-slate-800 rounded-xl shadow-xl border border-gray-100 dark:border-slate-700 p-2 overflow-hidden origin-bottom-right">
                <Link to="/dashboard" className="flex items-center gap-2 px-3 py-2 text-sm text-gray-700 dark:text-slate-200 hover:bg-gray-50 dark:hover:bg-slate-700 rounded-lg">Dashboard</Link>
                <Link to="/change-password" className="flex items-center gap-2 px-3 py-2 text-sm text-gray-700 dark:text-slate-200 hover:bg-gray-50 dark:hover:bg-slate-700 rounded-lg">Settings</Link>
                <button onClick={handleLogout} className="w-full text-left flex items-center gap-2 px-3 py-2 text-sm text-gray-700 dark:text-slate-200 hover:bg-gray-50 dark:hover:bg-slate-700 rounded-lg text-red-500">Logout</button>
              </div>
            )}
          </button>
        ) : (
          <Link to="/login" className="flex flex-col items-center justify-center p-2 text-[10px] font-medium transition-colors text-gray-500 dark:text-slate-400 hover:text-gray-900 dark:hover:text-white">
            <User className="w-5 h-5 mb-1" />
            Login
          </Link>
        )}
      </div>
    </>
  );
}
