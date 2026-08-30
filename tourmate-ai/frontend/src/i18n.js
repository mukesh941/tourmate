import i18n from 'i18next';
import { initReactI18next } from 'react-i18next';

const resources = {
  en: {
    translation: {
      "Destinations": "Destinations",
      "Explore Places": "Explore Places",
      "AI Cluster Map": "AI Cluster Map",
      "Route Planner": "Route Planner",
      "AI Itineraries": "AI Itineraries",
      "AI Lens": "AI Lens",
      "Dashboard": "Dashboard",
      "Admin": "Admin",
      "Logout": "Logout",
      "Log in": "Log in",
      "Sign up": "Sign up",
      "Top Places to Visit in": "Top Places to Visit in",
      "No places listed yet for this destination.": "No places listed yet for this destination.",
      "Listen": "Listen",
      "Loading...": "Loading..."
    }
  },
  hi: {
    translation: {
      "Destinations": "गंतव्य (Destinations)",
      "Explore Places": "स्थान खोजें (Explore Places)",
      "AI Cluster Map": "एआई क्लस्टर मैप (AI Cluster Map)",
      "Route Planner": "रूट प्लानर (Route Planner)",
      "AI Itineraries": "एआई यात्रा कार्यक्रम (AI Itineraries)",
      "AI Lens": "एआई लेंस (AI Lens)",
      "Dashboard": "डैशबोर्ड (Dashboard)",
      "Admin": "प्रशासक (Admin)",
      "Logout": "लॉग आउट (Logout)",
      "Log in": "लॉग इन (Log in)",
      "Sign up": "साइन अप (Sign up)",
      "Top Places to Visit in": "घूमने के लिए शीर्ष स्थान",
      "No places listed yet for this destination.": "इस गंतव्य के लिए अभी तक कोई स्थान सूचीबद्ध नहीं है।",
      "Listen": "सुने (Listen)",
      "Loading...": "लोड हो रहा है..."
    }
  }
};

i18n
  .use(initReactI18next)
  .init({
    resources,
    lng: "en",
    interpolation: {
      escapeValue: false
    }
  });

export default i18n;
