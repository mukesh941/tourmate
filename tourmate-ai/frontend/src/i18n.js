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
  },
  kn: {
    translation: {
      "Destinations": "ಗಮ್ಯಸ್ಥಾನಗಳು (Destinations)",
      "Explore Places": "ಸ್ಥಳಗಳನ್ನು ಅನ್ವೇಷಿಸಿ (Explore Places)",
      "AI Cluster Map": "ಎಐ ಕ್ಲಸ್ಟರ್ ಮ್ಯಾಪ್ (AI Cluster Map)",
      "Route Planner": "ಮಾರ್ಗ ಯೋಜಕ (Route Planner)",
      "AI Itineraries": "ಎಐ ಪ್ರಯಾಣ ಯೋಜನೆಗಳು (AI Itineraries)",
      "AI Lens": "ಎಐ ಲೆನ್ಸ್ (AI Lens)",
      "Dashboard": "ಡ್ಯಾಶ್‌ಬೋರ್ಡ್ (Dashboard)",
      "Admin": "ನಿರ್ವಾಹಕ (Admin)",
      "Logout": "ಲಾಗ್ ಔಟ್ (Logout)",
      "Log in": "ಲಾಗ್ ಇನ್ (Log in)",
      "Sign up": "ಸೈನ್ ಅಪ್ (Sign up)",
      "Top Places to Visit in": "ಭೇಟಿ ನೀಡಲು ಪ್ರಮುಖ ಸ್ಥಳಗಳು",
      "No places listed yet for this destination.": "ಈ ಗಮ್ಯಸ್ಥಾನಕ್ಕೆ ಇನ್ನೂ ಯಾವುದೇ ಸ್ಥಳಗಳನ್ನು ಪಟ್ಟಿ ಮಾಡಿಲ್ಲ.",
      "Listen": "ಆಲಿಸಿ (Listen)",
      "Loading...": "ಲೋಡ್ ಆಗುತ್ತಿದೆ..."
    }
  },
  ta: {
    translation: {
      "Destinations": "இடங்கள் (Destinations)",
      "Explore Places": "இடங்களை ஆராயுங்கள் (Explore Places)",
      "AI Cluster Map": "ஏஐ கிளஸ்டர் மேப் (AI Cluster Map)",
      "Route Planner": "வழித் திட்டமிடுபவர் (Route Planner)",
      "AI Itineraries": "ஏஐ பயணத் திட்டங்கள் (AI Itineraries)",
      "AI Lens": "ஏஐ லென்ஸ் (AI Lens)",
      "Dashboard": "டாஷ்போர்டு (Dashboard)",
      "Admin": "நிர்வாகி (Admin)",
      "Logout": "வெளியேறு (Logout)",
      "Log in": "உள்நுழைய (Log in)",
      "Sign up": "பதிவு செய்க (Sign up)",
      "Top Places to Visit in": "பார்வையிட சிறந்த இடங்கள்",
      "No places listed yet for this destination.": "இந்த இடத்திற்கு இன்னும் எந்த இடங்களும் பட்டியலிடப்படவில்லை.",
      "Listen": "கேளுங்கள் (Listen)",
      "Loading...": "ஏற்றுகிறது..."
    }
  },
  ml: {
    translation: {
      "Destinations": "ലക്ഷ്യസ്ഥാനങ്ങൾ (Destinations)",
      "Explore Places": "സ്ഥലങ്ങൾ പര്യവേക്ഷണം ചെയ്യുക (Explore Places)",
      "AI Cluster Map": "എഐ ക്ലസ്റ്റർ മാപ്പ് (AI Cluster Map)",
      "Route Planner": "റൂട്ട് പ്ലാനർ (Route Planner)",
      "AI Itineraries": "എഐ യാത്രാ വിവരണം (AI Itineraries)",
      "AI Lens": "എഐ ലെൻസ് (AI Lens)",
      "Dashboard": "ഡാഷ്‌ബോർഡ് (Dashboard)",
      "Admin": "അഡ്മിൻ (Admin)",
      "Logout": "ലോഗ് ഔട്ട് (Logout)",
      "Log in": "ലോഗിൻ (Log in)",
      "Sign up": "സൈൻ അപ്പ് (Sign up)",
      "Top Places to Visit in": "സന്ദർശിക്കാൻ മികച്ച സ്ഥലങ്ങൾ",
      "No places listed yet for this destination.": "ഈ ലക്ഷ്യസ്ഥാനത്തിനായി ഇതുവരെ സ്ഥലങ്ങളൊന്നും ലിസ്റ്റ് ചെയ്തിട്ടില്ല.",
      "Listen": "കേൾക്കുക (Listen)",
      "Loading...": "ലോഡ് ചെയ്യുന്നു..."
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
