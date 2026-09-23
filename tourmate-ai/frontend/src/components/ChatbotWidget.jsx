import { useState, useRef, useEffect, useCallback } from "react";
import axios from "axios";
import { useAuth } from "../context/AuthContext";
import { API_BASE_URL } from "../api/axios";
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

  // Initial greeting
  useEffect(() => {
    if (isOpen && messages.length === 0) {
      setMessages([
        {
          role: "model",
          content: `Hi ${user?.name?.split(" ")[0] || "there"}! I'm your TourMate AI guide. What kind of trip are you planning today?`,
        },
      ]);
    }
  }, [isOpen, messages.length, user]);

  const handleSend = async (e) => {
    e?.preventDefault();
    if (!input.trim() || !token) return;

    const userMessage = input.trim();
    setInput("");

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

      const res = await axios.post(
        `${API_BASE_URL}/ai/chat`,
        { message: userMessage, history, place_id: placeId, language: i18n.language },
        { headers: { Authorization: `Bearer ${token}` } }
      );

      const data = res.data?.data || {};
      const answerContent =
        data.answer || data.response || "I do not have verified knowledge about that in my database.";
      const sources = Array.isArray(data.sources) ? data.sources : [];

      setMessages([
        ...newMessages,
        {
          role: "model",
          content: answerContent,
          sources: sources,
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
            <button
              onClick={() => setIsOpen(false)}
              aria-label="Close TourMate Guide"
              className="text-white hover:bg-white/20 p-1.5 rounded-lg transition-colors focus:outline-none focus-visible:ring-2 focus-visible:ring-white"
            >
              ✕
            </button>
          </div>

          {/* Messages Area */}
          <div className="flex-1 overflow-y-auto p-3.5 sm:p-4 space-y-3.5 bg-gray-50 dark:bg-slate-900/50 custom-scrollbar">
            {messages.map((msg, idx) => (
              <div key={idx} className={`flex ${msg.role === "user" ? "justify-end" : "justify-start"}`}>
                <div
                  className={`max-w-[85%] rounded-2xl p-3 text-sm shadow-sm dark:shadow-none ${
                    msg.role === "user"
                      ? "bg-brand-600 text-white rounded-br-sm"
                      : msg.isError
                      ? "bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 text-red-800 dark:text-red-300 rounded-bl-sm"
                      : "bg-white dark:bg-slate-800 border border-gray-100 dark:border-slate-700 text-gray-800 dark:text-slate-100 rounded-bl-sm"
                  }`}
                >
                  {/* Basic markdown rendering for paragraphs */}
                  {msg.content.split("\n").map((line, i) => (
                    <p key={i} className={i > 0 ? "mt-1.5" : ""}>
                      {line.replace(/\*\*(.*?)\*\*/g, "$1")}
                    </p>
                  ))}

                  {/* Grounded Source Attribution Metadata */}
                  {msg.sources && msg.sources.length > 0 && (
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
            <form onSubmit={handleSend} className="flex items-center gap-2">
              <input
                type="text"
                value={input}
                onChange={(e) => setInput(e.target.value)}
                placeholder="Ask about places, tips..."
                className="flex-1 bg-gray-100 dark:bg-slate-800/80 border border-transparent focus:bg-white dark:focus:bg-slate-800 focus:border-brand-500 focus:ring-2 focus:ring-brand-200 rounded-full px-4 py-2 text-sm transition-all outline-none text-gray-900 dark:text-slate-100 placeholder-gray-500 dark:placeholder-slate-400"
                disabled={isLoading}
              />
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

