import { useState, useRef, useEffect, useCallback } from "react";
import api from "../api/axios";
import { useAuth } from "../context/AuthContext";
import { useLocation } from "react-router-dom";
import { useTranslation } from "react-i18next";

const BTN_SIZE = 56;
const VOICE_STORAGE_KEY = "tourmate_voice_assistant_pos_v1";

export default function VoiceAssistantWidget() {
  const { token, user } = useAuth();
  const { i18n } = useTranslation();
  const location = useLocation();

  const [isOpen, setIsOpen] = useState(false);
  const [isListening, setIsListening] = useState(false);
  const [isProcessing, setIsProcessing] = useState(false);
  const [isSpeaking, setIsSpeaking] = useState(false);
  const [assistantText, setAssistantText] = useState("");
  const [transcript, setTranscript] = useState("");
  const [voiceLang, setVoiceLang] = useState("en");
  const [errorMessage, setErrorMessage] = useState("");
  const [userCoords, setUserCoords] = useState(null);

  const recognitionRef = useRef(null);
  const audioRef = useRef(null);
  const synthUtteranceRef = useRef(null);
  const [voices, setVoices] = useState([]);

  // Position state (positioned by default above the Chatbot button)
  const [position, setPosition] = useState(() => {
    if (typeof window === "undefined") return { x: 0, y: 0 };
    const isMobile = window.innerWidth < 768;
    const defaultX = Math.max(12, window.innerWidth - BTN_SIZE - (isMobile ? 16 : 24));
    // Placed 70px above the regular Chatbot button
    const defaultY = Math.max(12, window.innerHeight - BTN_SIZE - (isMobile ? 80 : 24) - 70);

    try {
      const saved = localStorage.getItem(VOICE_STORAGE_KEY);
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
      // Fallback
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

  const clampPosition = useCallback((x, y) => {
    if (typeof window === "undefined") return { x, y };
    const isMobile = window.innerWidth < 768;
    const minX = 12;
    const maxX = Math.max(minX, window.innerWidth - BTN_SIZE - 12);
    const minY = 12;
    const bottomNavClearance = isMobile ? 76 : 12;
    const maxY = Math.max(minY, window.innerHeight - BTN_SIZE - bottomNavClearance);

    return {
      x: Math.min(Math.max(minX, x), maxX),
      y: Math.min(Math.max(minY, y), maxY),
    };
  }, []);

  useEffect(() => {
    const handleResize = () => {
      setPosition((prev) => {
        const clamped = clampPosition(prev.x, prev.y);
        try {
          localStorage.setItem(VOICE_STORAGE_KEY, JSON.stringify(clamped));
        } catch {}
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

  // Geolocation for nearby context
  useEffect(() => {
    if (!navigator.geolocation) return;
    navigator.geolocation.getCurrentPosition(
      (pos) => setUserCoords({ lat: pos.coords.latitude, lng: pos.coords.longitude }),
      () => setUserCoords(null),
      { timeout: 5000, maximumAge: 300000 }
    );
  }, []);

  // Preload local speech synthesis voices
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

  // Drag handlers
  const handlePointerDown = (e) => {
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
    } catch {}

    const handlePointerMove = (moveEvent) => {
      const deltaX = moveEvent.clientX - dragInfoRef.current.startX;
      const deltaY = moveEvent.clientY - dragInfoRef.current.startY;
      if (Math.hypot(deltaX, deltaY) > 6) {
        dragInfoRef.current.hasMoved = true;
        setIsDragging(true);
        setPosition(clampPosition(dragInfoRef.current.initPosX + deltaX, dragInfoRef.current.initPosY + deltaY));
      }
    };

    const handlePointerUp = (upEvent) => {
      window.removeEventListener("pointermove", handlePointerMove);
      window.removeEventListener("pointerup", handlePointerUp);
      window.removeEventListener("pointercancel", handlePointerUp);
      if (dragInfoRef.current.hasMoved) {
        suppressClickRef.current = true;
        setTimeout(() => { suppressClickRef.current = false; }, 120);
        setPosition((cur) => {
          const clamped = clampPosition(cur.x, cur.y);
          try { localStorage.setItem(VOICE_STORAGE_KEY, JSON.stringify(clamped)); } catch {}
          return clamped;
        });
      }
      setIsDragging(false);
      try {
        if (upEvent.target?.releasePointerCapture && dragInfoRef.current.pointerId !== null) {
          upEvent.target.releasePointerCapture(dragInfoRef.current.pointerId);
        }
      } catch {}
    };

    window.addEventListener("pointermove", handlePointerMove);
    window.addEventListener("pointerup", handlePointerUp);
    window.addEventListener("pointercancel", handlePointerUp);
  };

  const stopAudio = useCallback(() => {
    if (audioRef.current) {
      audioRef.current.pause();
      audioRef.current = null;
    }
    if (typeof window !== "undefined" && window.speechSynthesis) {
      window.speechSynthesis.cancel();
    }
    setIsSpeaking(false);
  }, []);

  useEffect(() => {
    return () => {
      stopAudio();
      if (recognitionRef.current) {
        recognitionRef.current.stop();
      }
    };
  }, [stopAudio]);

  const speakGuideResponse = useCallback(async (text, lang) => {
    if (typeof window === "undefined" || !text) return;
    stopAudio();
    setIsSpeaking(true);

    const cleanText = text.replace(/\*\*(.*?)\*\*/g, "$1").replace(/\*/g, "").trim();

    let targetLangCode = "en-IN";
    switch (lang) {
      case "hi": targetLangCode = "hi-IN"; break;
      case "kn": targetLangCode = "kn-IN"; break;
      case "ta": targetLangCode = "ta-IN"; break;
      case "ml": targetLangCode = "ml-IN"; break;
      default: targetLangCode = "en-IN"; break;
    }

    if (lang === "hi") {
      try {
        const res = await api.post("/ai/tts", { text: cleanText, language: targetLangCode }, { responseType: "blob" });
        const url = URL.createObjectURL(res.data);
        const audio = new Audio(url);
        audioRef.current = audio;
        audio.onended = () => setIsSpeaking(false);
        audio.onerror = () => {
          setIsSpeaking(false);
          setErrorMessage("Voice playback error. Please try again.");
        };
        await audio.play();
        return;
      } catch (e) {
        console.warn("Cloud TTS failed, falling back to local speech synthesis", e);
      }
    }

    if (!window.speechSynthesis) {
      setIsSpeaking(false);
      return;
    }

    const utterance = new SpeechSynthesisUtterance(cleanText);
    utterance.lang = targetLangCode;
    synthUtteranceRef.current = utterance;

    if (voices.length > 0) {
      const matchedVoice = voices.find(
        (v) => v.lang.replace("_", "-").toLowerCase() === targetLangCode.toLowerCase()
      ) || voices.find(
        (v) => v.lang.replace("_", "-").toLowerCase().startsWith(targetLangCode.split("-")[0].toLowerCase())
      );
      if (matchedVoice) utterance.voice = matchedVoice;
    }

    utterance.onend = () => setIsSpeaking(false);
    utterance.onerror = () => setIsSpeaking(false);
    window.speechSynthesis.speak(utterance);
  }, [stopAudio, voices]);

  const sendVoiceQuery = useCallback(async (userSpeech) => {
    if (!userSpeech || !token) return;
    setIsProcessing(true);
    setErrorMessage("");

    try {
      let placeId = null;
      if (location.pathname.startsWith("/places/")) {
        placeId = location.pathname.split("/places/")[1];
      }

      const promptMessage = `As my direct AI audio guide, please answer concisely and conversationally: ${userSpeech}`;

      const res = await api.post("/ai/chat", {
        message: promptMessage,
        history: [],
        place_id: placeId,
        language: voiceLang,
        user_lat: userCoords?.lat ?? null,
        user_lng: userCoords?.lng ?? null,
      });

      const data = res.data?.data || {};
      const answer = data.answer || data.response || "I am right here with you! Let me know where you'd like to explore.";
      setAssistantText(answer);
      setIsProcessing(false);

      speakGuideResponse(answer, voiceLang);
    } catch (err) {
      console.error("AI Assistant voice query error:", err);
      setIsProcessing(false);
      const fallbackError = "I couldn't reach the TourMate guide service right now. Please try again.";
      setErrorMessage(fallbackError);
      speakGuideResponse(fallbackError, voiceLang);
    }
  }, [token, location.pathname, voiceLang, userCoords, speakGuideResponse]);

  const startListening = useCallback(() => {
    if (typeof window === "undefined") return;
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!SpeechRecognition) {
      setErrorMessage("Speech recognition is not supported in this browser. Please use Chrome/Edge.");
      return;
    }

    stopAudio();
    setErrorMessage("");
    setTranscript("");

    const recognition = new SpeechRecognition();
    recognition.continuous = false;
    recognition.interimResults = true;

    let langCode = "en-IN";
    switch (voiceLang) {
      case "hi": langCode = "hi-IN"; break;
      case "kn": langCode = "kn-IN"; break;
      case "ta": langCode = "ta-IN"; break;
      case "ml": langCode = "ml-IN"; break;
      default: langCode = "en-IN"; break;
    }
    recognition.lang = langCode;

    recognition.onstart = () => {
      setIsListening(true);
    };

    recognition.onresult = (event) => {
      let currentTranscript = "";
      for (let i = event.resultIndex; i < event.results.length; i++) {
        currentTranscript += event.results[i][0].transcript;
      }
      setTranscript(currentTranscript);

      if (event.results[0].isFinal) {
        setIsListening(false);
        sendVoiceQuery(currentTranscript);
      }
    };

    recognition.onerror = (event) => {
      console.error("Voice recognition error:", event.error);
      setIsListening(false);
      if (event.error === "not-allowed") {
        setErrorMessage("Microphone access was denied. Please allow microphone permissions.");
      } else if (event.error !== "no-speech") {
        setErrorMessage("Could not hear your voice clearly. Tap Speak to try again.");
      }
    };

    recognition.onend = () => {
      setIsListening(false);
    };

    recognitionRef.current = recognition;
    try {
      recognition.start();
    } catch (e) {
      console.error("Error starting speech recognition:", e);
    }
  }, [voiceLang, stopAudio, sendVoiceQuery]);

  const handleOpenAssistant = () => {
    if (suppressClickRef.current || dragInfoRef.current.hasMoved) {
      dragInfoRef.current.hasMoved = false;
      return;
    }

    if (!isOpen) {
      setIsOpen(true);
      const userName = user?.name ? user.name.split(" ")[0] : "traveler";
      let greeting = `Hello ${userName}! I am your interactive AI Guide. Tell me what you'd like to explore!`;
      if (voiceLang === "hi") {
        greeting = `नमस्ते ${userName}! मैं आपका एआई टूर गाइड हूँ। बताइए आप कहाँ जाना चाहते हैं!`;
      }
      setAssistantText(greeting);
      speakGuideResponse(greeting, voiceLang);
      setTimeout(() => {
        startListening();
      }, 1200);
    } else {
      stopAudio();
      if (recognitionRef.current) recognitionRef.current.stop();
      setIsOpen(false);
    }
  };

  if (!token) return null;

  const isMobile = typeof window !== "undefined" && window.innerWidth < 640;
  const panelWidth = isMobile ? Math.min(340, window.innerWidth - 24) : 340;
  const panelHeight = 360;

  let panelLeft = position.x + BTN_SIZE - panelWidth;
  if (typeof window !== "undefined") {
    if (panelLeft < 12) panelLeft = 12;
    if (panelLeft + panelWidth > window.innerWidth - 12) {
      panelLeft = window.innerWidth - panelWidth - 12;
    }
  }

  let panelTop = position.y - panelHeight - 12;
  if (typeof window !== "undefined") {
    if (panelTop < 12) panelTop = position.y + BTN_SIZE + 12;
    if (panelTop + panelHeight > window.innerHeight - 12) {
      panelTop = Math.max(12, window.innerHeight - panelHeight - (isMobile ? 76 : 12));
    }
  }

  return (
    <>
      {isOpen && (
        <div
          style={{
            position: "fixed",
            left: `${panelLeft}px`,
            top: `${panelTop}px`,
            width: `${panelWidth}px`,
            height: `${panelHeight}px`,
          }}
          className="z-[55] glass dark:glass-dark rounded-3xl shadow-[0_20px_50px_rgba(79,70,229,0.25)] dark:shadow-[0_20px_50px_rgba(0,0,0,0.7)] border border-indigo-200/50 dark:border-indigo-500/30 overflow-hidden flex flex-col transition-all animate-scale-in"
        >
          <div className="bg-gradient-to-r from-indigo-600 via-purple-600 to-brand-600 text-white p-3.5 flex justify-between items-center z-10 border-b border-white/10 shrink-0">
            <div className="flex items-center gap-2.5">
              <div className="w-8 h-8 bg-white/20 rounded-full flex items-center justify-center text-lg shadow-inner">
                🎙️
              </div>
              <div>
                <h3 className="font-bold text-sm tracking-wide leading-tight">AI Voice Assistant</h3>
                <p className="text-[10px] text-indigo-100 uppercase tracking-wider font-semibold">
                  Live Interactive Guide
                </p>
              </div>
            </div>
            <div className="flex items-center gap-2">
              <select
                value={voiceLang}
                onChange={(e) => {
                  setVoiceLang(e.target.value);
                  stopAudio();
                }}
                className="bg-indigo-800/60 text-white text-[11px] font-bold rounded-lg px-2 py-1 outline-none border border-white/20 hover:bg-indigo-700/80 cursor-pointer"
              >
                <option value="en">EN</option>
                <option value="hi">HI (हिंदी)</option>
                <option value="kn">KN (ಕನ್ನಡ)</option>
                <option value="ta">TA (தமிழ்)</option>
                <option value="ml">ML (മലയാളം)</option>
              </select>
              <button
                onClick={() => {
                  stopAudio();
                  if (recognitionRef.current) recognitionRef.current.stop();
                  setIsOpen(false);
                }}
                aria-label="Close AI Voice Assistant"
                className="text-white hover:bg-white/20 p-1.5 rounded-lg transition-colors focus:outline-none"
              >
                ✕
              </button>
            </div>
          </div>

          <div className="flex-1 p-4 flex flex-col items-center justify-between bg-gradient-to-b from-indigo-50/40 to-white dark:from-slate-900/60 dark:to-slate-950 overflow-hidden text-center">
            <div className="w-full flex items-center justify-center pt-2">
              <div className="relative flex items-center justify-center">
                <div
                  className={`w-20 h-20 rounded-full flex items-center justify-center transition-all duration-300 ${
                    isListening
                      ? "bg-red-500 shadow-[0_0_35px_rgba(239,68,68,0.7)] animate-pulse"
                      : isSpeaking
                      ? "bg-indigo-600 shadow-[0_0_35px_rgba(99,102,241,0.7)] animate-bounce"
                      : isProcessing
                      ? "bg-amber-500 shadow-[0_0_30px_rgba(245,158,11,0.6)] animate-spin"
                      : "bg-indigo-500/90 shadow-md"
                  }`}
                >
                  <span className="text-3xl text-white">
                    {isListening ? "🎙️" : isSpeaking ? "🔊" : isProcessing ? "⏳" : "✨"}
                  </span>
                </div>

                {(isListening || isSpeaking) && (
                  <>
                    <span className="absolute w-28 h-28 rounded-full border-2 border-indigo-400 dark:border-indigo-300 opacity-60 animate-ping pointer-events-none"></span>
                    <span className="absolute w-36 h-36 rounded-full border border-purple-400 dark:border-purple-300 opacity-40 animate-pulse pointer-events-none"></span>
                  </>
                )}
              </div>
            </div>

            <div className="text-xs font-semibold uppercase tracking-wider my-1">
              {isListening ? (
                <span className="text-red-600 dark:text-red-400 flex items-center gap-1 justify-center animate-pulse">
                  Listening to you...
                </span>
              ) : isSpeaking ? (
                <span className="text-indigo-600 dark:text-indigo-400 flex items-center gap-1 justify-center">
                  Speaking guidance aloud...
                </span>
              ) : isProcessing ? (
                <span className="text-amber-600 dark:text-amber-400 flex items-center gap-1 justify-center">
                  Finding best recommendations...
                </span>
              ) : (
                <span className="text-gray-500 dark:text-gray-400">Tap Speak below to talk to AI</span>
              )}
            </div>

            <div className="w-full max-h-28 overflow-y-auto px-2 py-1.5 rounded-xl bg-white/70 dark:bg-slate-800/80 border border-gray-100 dark:border-slate-700/60 shadow-inner text-left text-xs leading-relaxed text-gray-700 dark:text-slate-200 custom-scrollbar">
              {transcript && (
                <p className="italic text-gray-500 dark:text-slate-400 mb-1">
                  You: "{transcript}"
                </p>
              )}
              {assistantText && (
                <p className="font-medium text-gray-800 dark:text-slate-100">
                  {assistantText}
                </p>
              )}
              {errorMessage && (
                <p className="text-red-500 font-semibold">{errorMessage}</p>
              )}
            </div>

            <div className="w-full flex items-center justify-center gap-3 pt-2">
              <button
                type="button"
                onClick={isListening ? () => recognitionRef.current?.stop() : startListening}
                disabled={isProcessing}
                aria-label={isListening ? "Stop listening" : "Start talking to AI"}
                className={`flex-1 py-2.5 px-4 rounded-2xl font-bold text-xs flex items-center justify-center gap-2 transition-all shadow-md active:scale-95 text-white ${
                  isListening
                    ? "bg-red-500 hover:bg-red-600 shadow-red-500/40 animate-pulse"
                    : "bg-gradient-to-r from-indigo-600 to-purple-600 hover:from-indigo-700 hover:to-purple-700 shadow-indigo-500/30"
                }`}
              >
                <span>{isListening ? "⏹ Stop Listening" : "🎙 Speak to Guide"}</span>
              </button>

              {isSpeaking && (
                <button
                  type="button"
                  onClick={stopAudio}
                  aria-label="Stop audio"
                  className="py-2.5 px-3 rounded-2xl bg-gray-200 dark:bg-slate-700 hover:bg-gray-300 dark:hover:bg-slate-600 text-gray-700 dark:text-slate-200 font-semibold text-xs transition"
                  title="Mute spoken response"
                >
                  🔇 Mute
                </button>
              )}
            </div>
          </div>
        </div>
      )}

      {/* Separate Floating Button for AI Voice Assistant */}
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
          onClick={handleOpenAssistant}
          onPointerDown={handlePointerDown}
          aria-label={isOpen ? "Close AI Voice Assistant" : "Open AI Voice Assistant"}
          aria-expanded={isOpen}
          title="AI Voice Assistant - Tap to speak directly with your AI Guide"
          className={`w-14 h-14 rounded-full bg-gradient-to-tr from-indigo-600 via-purple-600 to-pink-500 hover:from-indigo-700 hover:to-pink-600 text-white flex items-center justify-center shadow-xl dark:shadow-2xl hover:shadow-indigo-500/50 transition-all select-none cursor-grab active:cursor-grabbing focus:outline-none focus-visible:ring-4 focus-visible:ring-indigo-300 ${
            isDragging ? "scale-105 opacity-90 shadow-2xl" : "hover:-translate-y-0.5"
          }`}
        >
          <span className="text-2xl pointer-events-none" aria-hidden="true">
            {isOpen ? "✕" : "🎙️"}
          </span>
          {!isOpen && (
            <span
              className="absolute -top-1 -right-1 bg-indigo-400 text-white w-4 h-4 rounded-full border-2 border-white dark:border-slate-900 flex items-center justify-center text-[9px] font-bold animate-pulse pointer-events-none"
              aria-hidden="true"
            >
              AI
            </span>
          )}
        </button>
      </div>
    </>
  );
}
