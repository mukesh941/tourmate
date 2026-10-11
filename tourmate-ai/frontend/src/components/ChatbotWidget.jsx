import { useState, useRef, useEffect, useCallback } from "react";
import api, { API_BASE_URL } from "../api/axios";
import { useAuth } from "../context/AuthContext";
import { useLocation } from "react-router-dom";
import { useTranslation } from "react-i18next";

const BTN_SIZE = 56; // 56px x 56px (w-14 h-14)
const STORAGE_KEY = "tourmate_chatbot_pos_v2";

export default function ChatbotWidget() {
  const { token, user } = useAuth();
  const [isOpen, setIsOpen] = useState(false);
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const messagesEndRef = useRef(null);
  const { i18n } = useTranslation();
  const location = useLocation();
  // User GPS coordinates for "near me" queries
  const [userCoords, setUserCoords] = useState(null);
  const [chatLanguage, setChatLanguage] = useState("en");
  const [playingMsgIndex, setPlayingMsgIndex] = useState(null);
  const [audioLoading, setAudioLoading] = useState(false);
  const audioRef = useRef(null);

  // Speech Recognition State
  const [isListening, setIsListening] = useState(false);
  const [speechError, setSpeechError] = useState("");
  const recognitionRef = useRef(null);

  // Position state: { x, y } in viewport pixels
  const [position, setPosition] = useState(() => {
    if (typeof window === "undefined") return { x: 0, y: 0 };
    const isMobile = window.innerWidth < 768;
    const defaultX = Math.max(12, window.innerWidth - BTN_SIZE - (isMobile ? 16 : 24));
    // Default Y on mobile accounts for the bottom navigation bar (~72px)
    const defaultY = Math.max(12, window.innerHeight - BTN_SIZE - (isMobile ? 80 : 24));

    try {
      const saved = localStorage.getItem(STORAGE_KEY);
      if (saved) {
        const parsed = JSON.parse(saved);
        if (
          typeof parsed.x === "number" &&
          typeof parsed.y === "number" &&
          Number.isFinite(parsed.x) &&
          Number.isFinite(parsed.y)
        ) {
          const clampedX = Math.min(Math.max(12, parsed.x), Math.max(12, window.innerWidth - BTN_SIZE - 12));
          const clampedY = Math.min(Math.max(12, parsed.y), Math.max(12, window.innerHeight - BTN_SIZE - 12));
          return { x: clampedX, y: clampedY };
        }
      }
    } catch {
      // Fallback on corrupt localStorage
    }
    return { x: defaultX, y: defaultY };
  });

  const [isDragging, setIsDragging] = useState(false);
  const dragInfoRef = useRef({
    startX: 0,
    startY: 0,
    initPosX: 0,
    initPosY: 0,
    hasMoved: false,
    pointerId: null,
  });
  const suppressClickRef = useRef(false);

  // Helper to clamp position within safe viewport boundaries
  const clampPosition = useCallback((x, y) => {
    if (typeof window === "undefined") return { x, y };
    const isMobile = window.innerWidth < 768;
    const minX = 12;
    const maxX = Math.max(minX, window.innerWidth - BTN_SIZE - 12);
    const minY = 12;
    // Keep bottom clearance for mobile nav if near bottom
    const bottomNavClearance = isMobile ? 76 : 12;
    const maxY = Math.max(minY, window.innerHeight - BTN_SIZE - bottomNavClearance);

    return {
      x: Math.min(Math.max(minX, x), maxX),
      y: Math.min(Math.max(minY, y), maxY),
    };
  }, []);

  // Re-clamp on window resize and orientation changes
  useEffect(() => {
    const handleResize = () => {
      setPosition((prev) => {
        const clamped = clampPosition(prev.x, prev.y);
        try {
          localStorage.setItem(STORAGE_KEY, JSON.stringify(clamped));
        } catch {
          // Ignore storage quota errors
        }
        return clamped;
      });
    };

    window.addEventListener("resize", handleResize);
    window.addEventListener("orientationchange", handleResize);
    return () => {
      window.removeEventListener("resize", handleResize);
      window.removeEventListener("orientationchange", handleResize);
    };
  }, [clampPosition]);

  // Silently attempt to get user location for "near me" support
  useEffect(() => {
    if (!navigator.geolocation) return;
    navigator.geolocation.getCurrentPosition(
      (pos) => setUserCoords({ lat: pos.coords.latitude, lng: pos.coords.longitude }),
      () => setUserCoords(null), // Permission denied or unavailable — silently ignore
      { timeout: 5000, maximumAge: 300000 } // 5s timeout, cache for 5 min
    );
  }, []);

  // Pointer drag handlers
  const handlePointerDown = (e) => {
    // Only respond to primary button
    if (e.button !== 0 && e.pointerType === "mouse") return;

    dragInfoRef.current = {
      startX: e.clientX,
      startY: e.clientY,
      initPosX: position.x,
      initPosY: position.y,
      hasMoved: false,
      pointerId: e.pointerId,
    };

    try {
      e.currentTarget.setPointerCapture(e.pointerId);
    } catch {
      // Ignore if pointer capture fails
    }

    const handlePointerMove = (moveEvent) => {
      const deltaX = moveEvent.clientX - dragInfoRef.current.startX;
      const deltaY = moveEvent.clientY - dragInfoRef.current.startY;
      const distance = Math.hypot(deltaX, deltaY);

      if (distance > 6) {
        dragInfoRef.current.hasMoved = true;
        setIsDragging(true);

        const newX = dragInfoRef.current.initPosX + deltaX;
        const newY = dragInfoRef.current.initPosY + deltaY;

        // Viewport bounds while dragging
        const clamped = clampPosition(newX, newY);
        setPosition(clamped);
      }
    };

    const handlePointerUp = (upEvent) => {
      window.removeEventListener("pointermove", handlePointerMove);
      window.removeEventListener("pointerup", handlePointerUp);
      window.removeEventListener("pointercancel", handlePointerUp);

      if (dragInfoRef.current.hasMoved) {
        suppressClickRef.current = true;
        setTimeout(() => {
          suppressClickRef.current = false;
        }, 120);

        setPosition((cur) => {
          const clamped = clampPosition(cur.x, cur.y);
          try {
            localStorage.setItem(STORAGE_KEY, JSON.stringify(clamped));
          } catch {
            // Ignore storage errors
          }
          return clamped;
        });
      }

      setIsDragging(false);
      try {
        if (upEvent.target?.releasePointerCapture && dragInfoRef.current.pointerId !== null) {
          upEvent.target.releasePointerCapture(dragInfoRef.current.pointerId);
        }
      } catch {
        // Ignore
      }
    };

    window.addEventListener("pointermove", handlePointerMove);
    window.addEventListener("pointerup", handlePointerUp);
    window.addEventListener("pointercancel", handlePointerUp);
  };

  const handleButtonClick = (e) => {
    e?.preventDefault();
    if (suppressClickRef.current || dragInfoRef.current.hasMoved) {
      dragInfoRef.current.hasMoved = false;
      return;
    }
    setIsOpen((prev) => !prev);
  };

  const handleKeyDown = (e) => {
    if (e.key === "Enter" || e.key === " ") {
      e.preventDefault();
      setIsOpen((prev) => !prev);
    }
  };

  // Auto-scroll to bottom of chat
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, isOpen]);

  // Pre-load voices for TTS
  const [voices, setVoices] = useState([]);
  useEffect(() => {
    if (typeof window !== "undefined" && window.speechSynthesis) {
      const loadVoices = () => setVoices(window.speechSynthesis.getVoices());
      loadVoices();
      window.speechSynthesis.onvoiceschanged = loadVoices;
      return () => {
        window.speechSynthesis.onvoiceschanged = null;
      };
    }
  }, []);

  useEffect(() => {
    return () => {
      if (audioRef.current) {
        audioRef.current.pause();
        audioRef.current = null;
      }
      if (typeof window !== "undefined" && window.speechSynthesis) {
         window.speechSynthesis.cancel();
      }
      if (recognitionRef.current) {
        recognitionRef.current.stop();
      }
    };
  }, []);

  // Initialize Speech Recognition
  useEffect(() => {
    if (typeof window !== "undefined") {
      const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
      if (SpeechRecognition) {
        const recognition = new SpeechRecognition();
        recognition.continuous = false;
        recognition.interimResults = false;
        
        recognition.onstart = () => {
          setIsListening(true);
          setSpeechError("");
        };
        
        recognition.onerror = (event) => {
          console.error("Speech recognition error", event.error);
          setIsListening(false);
          setSpeechError(event.error === 'not-allowed' ? "Mic permission denied." : "Speech recognition failed.");
          setTimeout(() => setSpeechError(""), 3000);
        };
        
        recognition.onend = () => {
          setIsListening(false);
        };
        
        recognition.onresult = (event) => {
          const transcript = event.results[0][0].transcript;
          if (transcript.trim()) {
            setInput("");
            handleSend(null, transcript);
          }
        };
        
        recognitionRef.current = recognition;
      }
    }
  }, []);

  const toggleListening = () => {
    if (!recognitionRef.current) {
      alert("Speech recognition is not supported in this browser.");
      return;
    }
    
    if (isListening) {
      recognitionRef.current.stop();
    } else {
      let langCode = 'en-IN';
      switch(chatLanguage) {
        case 'hi': langCode = 'hi-IN'; break;
        case 'kn': langCode = 'kn-IN'; break;
        case 'ta': langCode = 'ta-IN'; break;
        case 'ml': langCode = 'ml-IN'; break;
        default: langCode = 'en-IN'; break;
      }
      recognitionRef.current.lang = langCode;
      try {
        recognitionRef.current.start();
      } catch (e) {
        console.error("Error starting recognition", e);
      }
    }
  };

  // When language changes, cancel current audio
  useEffect(() => {
    if (audioRef.current) {
      audioRef.current.pause();
      setPlayingMsgIndex(null);
    }
    if (typeof window !== "undefined" && window.speechSynthesis) {
       window.speechSynthesis.cancel();
       setPlayingMsgIndex(null);
    }
  }, [chatLanguage]);

  const speakMessage = async (text, idx) => {
    if (typeof window === "undefined") return;
    
    if (audioRef.current) {
      audioRef.current.pause();
    }
    if (window.speechSynthesis) {
      window.speechSynthesis.cancel();
    }

    if (playingMsgIndex === idx && !audioLoading) {
      setPlayingMsgIndex(null);
      return;
    }

    setPlayingMsgIndex(idx);
    setAudioLoading(true);

    const cleanText = text.replace(/\*\*(.*?)\*\*/g, "$1").replace(/\*/g, "");
    
    let targetLang = 'en-IN';
    switch(chatLanguage) {
      case 'hi': targetLang = 'hi-IN'; break;
      case 'kn': targetLang = 'kn-IN'; break;
      case 'ta': targetLang = 'ta-IN'; break;
      case 'ml': targetLang = 'ml-IN'; break;
      default: targetLang = 'en-IN'; break;
    }

    // Use Backend Cloud TTS for Hindi
    if (chatLanguage === 'hi') {
      try {
        const res = await api.post('/ai/tts', { text: cleanText, language: targetLang }, { responseType: 'blob' });
        const url = URL.createObjectURL(res.data);
        const audio = new Audio(url);
        audioRef.current = audio;
        
        audio.onended = () => setPlayingMsgIndex(null);
        audio.onerror = () => {
           setPlayingMsgIndex(null);
           alert("Failed to play Hindi audio from cloud. Please try again.");
        };
        
        await audio.play();
        setAudioLoading(false);
        return;
      } catch (e) {
        console.error("Cloud TTS failed:", e);
        // Fall back to native if possible
        if (voices.length > 0) {
          const voice = voices.find(v => v.lang.replace('_', '-').toLowerCase() === targetLang.toLowerCase()) || 
                        voices.find(v => v.lang.replace('_', '-').toLowerCase().startsWith('hi'));
          if (!voice) {
            alert("Cloud TTS is unavailable and no local Hindi voice was found.");
            setAudioLoading(false);
            setPlayingMsgIndex(null);
            return;
          }
        }
      }
    }

    // Native browser fallback
    if (!window.speechSynthesis) {
      setAudioLoading(false);
      setPlayingMsgIndex(null);
      return;
    }
    
    const utterance = new SpeechSynthesisUtterance(cleanText);
    utterance.lang = targetLang;

    if (voices.length > 0) {
      const voice = voices.find(v => v.lang.replace('_', '-').toLowerCase() === targetLang.toLowerCase()) || 
                    voices.find(v => v.lang.replace('_', '-').toLowerCase().startsWith(targetLang.split('-')[0].toLowerCase()));
      if (voice) {
        utterance.voice = voice;
      } else if (chatLanguage !== 'en') {
        alert(`Note: No native voice found for ${chatLanguage.toUpperCase()} on your device. The browser might read it in English or remain silent.`);
      }
    }
    
    utterance.onstart = () => setAudioLoading(false);
    utterance.onend = () => setPlayingMsgIndex(null);
    utterance.onerror = (e) => {
      console.warn("Speech synthesis error", e);
      setAudioLoading(false);
      setPlayingMsgIndex(null);
    };

    window.speechSynthesis.speak(utterance);
    
    // Fallback loading cleanup just in case onstart never fires
    setTimeout(() => {
      setAudioLoading(false);
    }, 1000);
  };

  // Initial greeting
  useEffect(() => {
    if (isOpen && messages.length === 0) {
      let greeting = `Hi ${user?.name?.split(" ")[0] || "there"}! I'm your TourMate AI guide. What kind of trip are you planning today?`;
      if (chatLanguage === 'hi') {
        greeting = `नमस्ते ${user?.name?.split(" ")[0] || ""}! मैं आपका टूरमेट एआई गाइड हूं। आज आप किस तरह की यात्रा की योजना बना रहे हैं?`;
      } else if (chatLanguage === 'kn') {
        greeting = `ನಮಸ್ಕಾರ ${user?.name?.split(" ")[0] || ""}! ನಾನು ನಿಮ್ಮ TourMate AI ಮಾರ್ಗದರ್ಶಿ. ಇಂದು ನೀವು ಯಾವ ರೀತಿಯ ಪ್ರವಾಸವನ್ನು ಯೋಜಿಸುತ್ತಿದ್ದೀರಿ?`;
      } else if (chatLanguage === 'ta') {
        greeting = `வணக்கம் ${user?.name?.split(" ")[0] || ""}! நான் உங்கள் TourMate AI வழிகாட்டி. இன்று நீங்கள் எதைப் பற்றி திட்டமிடுகிறீர்கள்?`;
      } else if (chatLanguage === 'ml') {
        greeting = `നമസ്കാരം ${user?.name?.split(" ")[0] || ""}! ഞാൻ നിങ്ങളുടെ TourMate AI ഗൈഡാണ്. ഇന്ന് നിങ്ങൾ എന്ത് യാത്രയാണ് പ്ലാൻ ചെയ്യുന്നത്?`;
      }
      
      setMessages([
        {
          role: "model",
          content: greeting,
        },
      ]);
    }
  }, [isOpen, messages.length, user, chatLanguage]);

  const handleSend = async (e, directText = null) => {
    e?.preventDefault();
    const textToSend = directText || input;
    if (!textToSend.trim() || !token) return;

    const userMessage = textToSend.trim();
    if (!directText) setInput("");

    // Add user message to UI immediately
    const newMessages = [...messages, { role: "user", content: userMessage }];
    setMessages(newMessages);
    setIsLoading(true);

    try {
      let placeId = null;
      if (location.pathname.startsWith("/places/")) {
        placeId = location.pathname.split("/places/")[1];
      }

      const history = messages.map((m) => ({ role: m.role, content: m.content }));

      const res = await api.post(
        `/ai/chat`,
        {
          message: userMessage,
          history,
          place_id: placeId,
          language: chatLanguage,
          // Send GPS coords if available (enables "near me" queries)
          user_lat: userCoords?.lat ?? null,
          user_lng: userCoords?.lng ?? null,
        }
        // Authorization header is automatically attached by the api interceptor
      );

      const data = res.data?.data || {};
      const answerContent =
        data.answer || data.response || "I do not have verified knowledge about that in my database.";
      const sources = Array.isArray(data.sources) ? data.sources : [];
      const results = Array.isArray(data.results) ? data.results : [];

      setMessages([
        ...newMessages,
        {
          role: "model",
          content: answerContent,
          sources: sources,
          results: results,
          intent: data.intent,
          category: data.category,
          location: data.location,
          isGrounded: data.is_grounded !== false,
        },
      ]);
    } catch (err) {
      console.error("TourMate AI Chat error:", err);
      const rawErr = err.response?.data?.error;
      const errMsg =
        typeof rawErr === "string"
          ? rawErr
          : rawErr?.message ||
            rawErr?.detail ||
            (typeof err.response?.data?.detail === "string" ? err.response?.data?.detail : null) ||
            "Sorry, I'm having trouble connecting to TourMate assistant right now. Please try again.";
      setMessages([
        ...newMessages,
        {
          role: "model",
          content: errMsg,
          isError: true,
        },
      ]);
    } finally {
      setIsLoading(false);
    }
  };

  // Only show for logged in users
  if (!token) return null;

  // Calculate panel placement based on current button location
  const isMobile = typeof window !== "undefined" && window.innerWidth < 640;
  const panelWidth = isMobile ? Math.min(360, (typeof window !== "undefined" ? window.innerWidth : 360) - 24) : 384;
  const panelHeight = isMobile ? Math.min(480, (typeof window !== "undefined" ? window.innerHeight : 600) - 100) : 500;

  // Horizontal anchoring
  let panelLeft = position.x + BTN_SIZE - panelWidth;
  if (typeof window !== "undefined") {
    if (panelLeft < 12) panelLeft = 12;
    if (panelLeft + panelWidth > window.innerWidth - 12) {
      panelLeft = window.innerWidth - panelWidth - 12;
    }
  }

  // Vertical anchoring: open upwards if on lower half of screen, downwards if on upper half
  let panelTop = position.y - panelHeight - 12;
  if (typeof window !== "undefined") {
    if (panelTop < 12) {
      // Not enough room above, open downwards from button
      panelTop = position.y + BTN_SIZE + 12;
    }
    // Check if overflowing bottom
    if (panelTop + panelHeight > window.innerHeight - 12) {
      panelTop = Math.max(12, window.innerHeight - panelHeight - (isMobile ? 76 : 12));
    }
  }

  return (
    <>
      {/* Chat Window Panel */}
      {isOpen && (
        <div
          style={{
            position: "fixed",
            left: `${panelLeft}px`,
            top: `${panelTop}px`,
            width: `${panelWidth}px`,
            height: `${panelHeight}px`,
            maxHeight: "calc(100dvh - 5.5rem)",
          }}
          className="z-[55] glass dark:glass-dark rounded-2xl shadow-[0_20px_50px_rgba(0,0,0,0.15)] dark:shadow-[0_20px_50px_rgba(0,0,0,0.6)] border border-white/50 dark:border-slate-700/50 overflow-hidden flex flex-col transition-all animate-scale-in"
        >
          {/* Header */}
          <div className="bg-gradient-to-r from-brand-600/90 to-brand-500/90 backdrop-blur-md text-white p-3.5 sm:p-4 flex justify-between items-center z-10 border-b border-white/10 shrink-0">
            <div className="flex items-center gap-2.5">
              <div className="w-8 h-8 bg-white/20 rounded-full flex items-center justify-center text-xl shadow-inner shrink-0">
                🤖
              </div>
              <div>
                <h3 className="font-bold text-sm tracking-wide leading-tight">TourMate Guide</h3>
                <p className="text-[10px] text-brand-50 uppercase tracking-wider font-semibold">
                  Grounded AI Assistant
                </p>
              </div>
            </div>
            <div className="flex items-center gap-2">
              <select 
                value={chatLanguage} 
                onChange={(e) => setChatLanguage(e.target.value)}
                className="bg-brand-700/50 text-white text-[10px] rounded px-1.5 py-1 outline-none border border-white/20 hover:bg-brand-700/80 cursor-pointer"
              >
                <option value="en">EN</option>
                <option value="hi">HI</option>
                <option value="kn">KN</option>
                <option value="ta">TA</option>
                <option value="ml">ML</option>
              </select>
              <button
                onClick={() => setIsOpen(false)}
                aria-label="Close TourMate Guide"
                className="text-white hover:bg-white/20 p-1.5 rounded-lg transition-colors focus:outline-none focus-visible:ring-2 focus-visible:ring-white"
              >
                ✕
              </button>
            </div>
          </div>

          {/* Messages Area */}
          <div className="flex-1 overflow-y-auto p-3.5 sm:p-4 space-y-3.5 bg-gray-50 dark:bg-slate-900/50 custom-scrollbar">
            {messages.map((msg, idx) => (
              <div key={idx} className={`flex ${msg.role === "user" ? "justify-end" : "justify-start"}`}>
                <div
                  className={`max-w-[85%] rounded-2xl p-3 text-sm shadow-sm dark:shadow-none relative group ${
                    msg.role === "user"
                      ? "bg-brand-600 text-white rounded-br-sm"
                      : msg.isError
                      ? "bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 text-red-800 dark:text-red-300 rounded-bl-sm"
                      : "bg-white dark:bg-slate-800 border border-gray-100 dark:border-slate-700 text-gray-800 dark:text-slate-100 rounded-bl-sm"
                  }`}
                >
                  {msg.role !== "user" && !msg.isError && (
                    <button
                      onClick={() => speakMessage(msg.content, idx)}
                      className={`absolute top-2 right-2 transition-opacity p-1 rounded focus:outline-none ${playingMsgIndex === idx ? 'opacity-100 bg-brand-100 dark:bg-brand-900/50 text-brand-600 dark:text-brand-300' : 'opacity-0 group-hover:opacity-100 bg-gray-100 dark:bg-slate-700 text-gray-600 dark:text-gray-300 hover:bg-gray-200 dark:hover:bg-slate-600'}`}
                      title={playingMsgIndex === idx ? "Stop playing" : "Read aloud"}
                      aria-label={playingMsgIndex === idx ? "Stop playing" : "Read aloud"}
                    >
                      {playingMsgIndex === idx && audioLoading ? (
                        <div className="w-4 h-4 rounded-full border-2 border-brand-500 border-t-transparent animate-spin"></div>
                      ) : playingMsgIndex === idx ? (
                        <svg xmlns="http://www.w3.org/2000/svg" className="h-4 w-4" viewBox="0 0 20 20" fill="currentColor">
                          <rect x="5" y="4" width="3" height="12" rx="1" />
                          <rect x="12" y="4" width="3" height="12" rx="1" />
                        </svg>
                      ) : (
                        <svg xmlns="http://www.w3.org/2000/svg" className="h-4 w-4" viewBox="0 0 20 20" fill="currentColor">
                          <path fillRule="evenodd" d="M9.383 3.076A1 1 0 0110 4v12a1 1 0 01-1.707.707L4.586 13H2a1 1 0 01-1-1V8a1 1 0 011-1h2.586l3.707-3.707a1 1 0 011.09-.217zM14.657 2.929a1 1 0 011.414 0A9.972 9.972 0 0119 10a9.972 9.972 0 01-2.929 7.071 1 1 0 01-1.414-1.414A7.971 7.971 0 0017 10c0-2.21-.894-4.208-2.343-5.657a1 1 0 010-1.414zm-2.829 2.828a1 1 0 011.415 0A5.983 5.983 0 0115 10a5.984 5.984 0 01-1.757 4.243 1 1 0 01-1.415-1.415A3.984 3.984 0 0013 10a3.983 3.983 0 00-1.172-2.828 1 1 0 010-1.415z" clipRule="evenodd" />
                        </svg>
                      )}
                    </button>
                  )}
                  
                  {/* Basic markdown rendering for paragraphs */}
                  <div className={msg.role !== "user" ? "pr-6" : ""}>
                    {msg.content.split("\n").map((line, i) => (
                      <p key={i} className={i > 0 ? "mt-1.5" : ""}>
                        {line.replace(/\*\*(.*?)\*\*/g, "$1")}
                      </p>
                    ))}
                  </div>

                  {/* Place result cards (from nearby search) */}
                  {msg.results && msg.results.length > 0 && (
                    <div className="mt-3 space-y-2">
                      {msg.results.slice(0, 6).map((place, pIdx) => (
                        <div
                          key={pIdx}
                          className="bg-gray-50 dark:bg-slate-700/60 border border-gray-200 dark:border-slate-600 rounded-xl p-2.5 text-xs"
                        >
                          <div className="flex items-start justify-between gap-1">
                            <span className="font-semibold text-gray-800 dark:text-slate-100 leading-tight">
                              {place.name}
                            </span>
                            {place.rating && (
                              <span className="shrink-0 text-amber-500 font-bold text-[11px]">
                                ★ {place.rating}
                              </span>
                            )}
                          </div>
                          {place.address && (
                            <p className="text-gray-500 dark:text-slate-400 mt-0.5 leading-tight truncate">
                              {place.address}
                            </p>
                          )}
                          <div className="flex items-center gap-2 mt-1">
                            {place.distance_km != null && (
                              <span className="text-brand-600 dark:text-brand-400 font-medium">
                                {place.distance_km} km away
                              </span>
                            )}
                            {place.google_maps_url && (
                              <a
                                href={place.google_maps_url}
                                target="_blank"
                                rel="noopener noreferrer"
                                className="text-blue-500 hover:underline"
                              >
                                View on Map ↗
                              </a>
                            )}
                          </div>
                        </div>
                      ))}
                    </div>
                  )}

                  {/* Grounded Source Attribution Metadata */}
                  {msg.sources && msg.sources.length > 0 && !(msg.results && msg.results.length > 0) && (
                    <div className="mt-2.5 pt-2 border-t border-gray-200/70 dark:border-slate-700 text-[11px]">
                      <p className="font-semibold text-brand-600 dark:text-brand-400 mb-1 flex items-center gap-1">
                        <span>📚</span>
                        <span>Verified Sources ({msg.sources.length})</span>
                      </p>
                      <ul className="space-y-0.5 text-gray-500 dark:text-slate-400">
                        {msg.sources.slice(0, 3).map((src, sIdx) => (
                          <li key={sIdx} className="truncate" title={src.title}>
                            • <span className="font-medium text-gray-700 dark:text-slate-300">{src.title}</span>
                            {src.poi_name && ` (${src.poi_name})`}
                          </li>
                        ))}
                      </ul>
                    </div>
                  )}
                </div>
              </div>
            ))}

            {isLoading && (
              <div className="flex justify-start">
                <div className="bg-white dark:bg-slate-800 border border-gray-100 dark:border-slate-700 rounded-2xl rounded-bl-sm p-4 shadow-sm dark:shadow-none flex gap-1">
                  <div className="w-2 h-2 bg-gray-300 rounded-full animate-bounce"></div>
                  <div
                    className="w-2 h-2 bg-gray-300 rounded-full animate-bounce"
                    style={{ animationDelay: "0.15s" }}
                  ></div>
                  <div
                    className="w-2 h-2 bg-gray-300 rounded-full animate-bounce"
                    style={{ animationDelay: "0.3s" }}
                  ></div>
                </div>
              </div>
            )}
            <div ref={messagesEndRef} />
          </div>

          {/* Input Area */}
          <div className="p-3 bg-white dark:bg-slate-800 border-t border-gray-100 dark:border-slate-700 shrink-0">
            {speechError && (
              <div className="text-xs text-red-500 mb-2 text-center">{speechError}</div>
            )}
            <form onSubmit={(e) => handleSend(e, null)} className="flex items-center gap-2">
              <input
                type="text"
                value={input}
                onChange={(e) => setInput(e.target.value)}
                placeholder={isListening ? "Listening..." : "Ask about places, tips..."}
                className={`flex-1 bg-gray-100 dark:bg-slate-800/80 border ${isListening ? "border-red-400 bg-red-50 dark:bg-red-900/10" : "border-transparent"} focus:bg-white dark:focus:bg-slate-800 focus:border-brand-500 focus:ring-2 focus:ring-brand-200 rounded-full px-4 py-2 text-sm transition-all outline-none text-gray-900 dark:text-slate-100 placeholder-gray-500 dark:placeholder-slate-400`}
                disabled={isLoading}
              />
              <button
                type="button"
                onClick={toggleListening}
                disabled={isLoading}
                aria-label={isListening ? "Stop listening" : "Start voice input"}
                className={`${isListening ? "bg-red-500 hover:bg-red-600 animate-pulse" : "bg-gray-200 dark:bg-slate-700 text-gray-600 dark:text-gray-300 hover:bg-gray-300 dark:hover:bg-slate-600"} rounded-full w-9 h-9 flex items-center justify-center transition-colors shadow-sm dark:shadow-none shrink-0 focus:outline-none focus-visible:ring-2 focus-visible:ring-brand-400`}
              >
                <svg xmlns="http://www.w3.org/2000/svg" className="h-4 w-4" viewBox="0 0 20 20" fill="currentColor">
                  <path fillRule="evenodd" d="M7 4a3 3 0 016 0v4a3 3 0 11-6 0V4zm4 10.93A7.001 7.001 0 0017 8a1 1 0 10-2 0A5 5 0 015 8a1 1 0 00-2 0 7.001 7.001 0 006 6.93V17H6a1 1 0 100 2h8a1 1 0 100-2h-3v-2.07z" clipRule="evenodd" />
                </svg>
              </button>
              <button
                type="submit"
                disabled={!input.trim() || isLoading}
                aria-label="Send message"
                className="bg-brand-600 hover:bg-brand-700 disabled:opacity-50 text-white rounded-full w-9 h-9 flex items-center justify-center transition-colors shadow-sm dark:shadow-none shrink-0 focus:outline-none focus-visible:ring-2 focus-visible:ring-brand-400"
              >
                ↑
              </button>
            </form>
          </div>
        </div>
      )}

      {/* Floating Action Button (Draggable via Pointer Events) */}
      <div
        style={{
          position: "fixed",
          left: `${position.x}px`,
          top: `${position.y}px`,
          width: `${BTN_SIZE}px`,
          height: `${BTN_SIZE}px`,
          touchAction: "none",
          userSelect: "none",
        }}
        className="z-[50]"
      >
        <button
          onClick={handleButtonClick}
          onKeyDown={handleKeyDown}
          onPointerDown={handlePointerDown}
          aria-label={isOpen ? "Close TourMate AI Guide" : "Open TourMate AI Guide"}
          aria-expanded={isOpen}
          title="Drag to reposition, tap to open AI guide"
          className={`w-14 h-14 rounded-full bg-brand-600 hover:bg-brand-700 text-white flex items-center justify-center shadow-xl dark:shadow-2xl hover:shadow-brand-500/50 transition-transform select-none cursor-grab active:cursor-grabbing focus:outline-none focus-visible:ring-4 focus-visible:ring-brand-300 dark:focus-visible:ring-brand-800 ${
            isDragging ? "scale-105 opacity-90 shadow-2xl" : "hover:-translate-y-0.5"
          }`}
        >
          <span className="text-2xl pointer-events-none" aria-hidden="true">
            {isOpen ? "✕" : "💬"}
          </span>
          {!isOpen && (
            <span
              className="absolute -top-1 -right-1 bg-red-500 w-4 h-4 rounded-full border-2 border-white dark:border-slate-900 animate-pulse pointer-events-none"
              aria-hidden="true"
            ></span>
          )}
        </button>
      </div>
    </>
  );
}

