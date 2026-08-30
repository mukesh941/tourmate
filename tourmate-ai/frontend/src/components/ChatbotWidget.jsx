import { useState, useRef, useEffect } from "react";
import axios from "axios";
import { useAuth } from "../context/AuthContext";
import { useLocation } from "react-router-dom";
import { useTranslation } from "react-i18next";

export default function ChatbotWidget() {
  const { token, user } = useAuth();
  const [isOpen, setIsOpen] = useState(false);
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const messagesEndRef = useRef(null);
  const { i18n } = useTranslation();
  
  const location = useLocation();

  // Auto-scroll to bottom of chat
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, isOpen]);

  // Initial greeting
  useEffect(() => {
    if (isOpen && messages.length === 0) {
      setMessages([{
        role: "model",
        content: `Hi ${user?.name?.split(' ')[0] || 'there'}! I'm your TourMate AI guide. What kind of trip are you planning today?`
      }]);
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
      // Check if we are on a specific place detail page to inject context
      let placeId = null;
      if (location.pathname.startsWith('/places/')) {
        placeId = location.pathname.split('/places/')[1];
      }

      // Format history for API
      const history = messages.map(m => ({ role: m.role, content: m.content }));

      const res = await axios.post(
        `${import.meta.env.VITE_API_BASE_URL}/ai/chat`,
        { message: userMessage, history, place_id: placeId, language: i18n.language },
        { headers: { Authorization: `Bearer ${token}` } }
      );

      setMessages([...newMessages, { role: "model", content: res.data.data.response }]);
    } catch (err) {
      console.error(err);
      setMessages([
        ...newMessages, 
        { role: "model", content: "Sorry, I'm having trouble connecting right now. Ensure your API keys are configured correctly!" }
      ]);
    } finally {
      setIsLoading(false);
    }
  };

  // Only show for logged in users
  if (!token) return null;

  return (
    <div className="fixed bottom-6 right-6 z-[1000] flex flex-col items-end">
      
      {/* Chat Window */}
      {isOpen && (
        <div className="bg-white dark:bg-slate-800 w-80 sm:w-96 rounded-2xl shadow-2xl border border-gray-200 dark:border-slate-700 mb-4 overflow-hidden flex flex-col h-[500px] max-h-[70vh] transition-all transform origin-bottom-right">
          
          {/* Header */}
          <div className="bg-gradient-to-r from-brand-600 to-brand-500 text-white p-4 flex justify-between items-center shadow-md dark:shadow-none z-10">
            <div className="flex items-center gap-3">
              <div className="w-8 h-8 bg-white dark:bg-slate-800/20 rounded-full flex items-center justify-center text-xl">
                🤖
              </div>
              <div>
                <h3 className="font-bold text-sm">TourMate Guide</h3>
                <p className="text-[10px] text-brand-100 uppercase tracking-wider">AI Assistant</p>
              </div>
            </div>
            <button 
              onClick={() => setIsOpen(false)}
              className="text-white hover:bg-white dark:bg-slate-800/20 p-1.5 rounded-lg transition-colors"
            >
              ✕
            </button>
          </div>
          
          {/* Messages Area */}
          <div className="flex-1 overflow-y-auto p-4 space-y-4 bg-gray-50 dark:bg-slate-900/50 custom-scrollbar">
            {messages.map((msg, idx) => (
              <div key={idx} className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}>
                <div 
                  className={`max-w-[80%] rounded-2xl p-3 text-sm shadow-sm dark:shadow-none ${
                    msg.role === 'user' 
                      ? 'bg-brand-600 text-white rounded-br-sm' 
                      : 'bg-white dark:bg-slate-800 border border-gray-100 dark:border-slate-700 text-gray-800 dark:text-slate-100 rounded-bl-sm'
                  }`}
                >
                  {/* Extremely basic markdown rendering for bold text */}
                  {msg.content.split('\n').map((line, i) => (
                    <p key={i} className={i > 0 ? "mt-1.5" : ""}>
                      {line.replace(/\*\*(.*?)\*\*/g, '$1')} 
                    </p>
                  ))}
                </div>
              </div>
            ))}
            
            {isLoading && (
              <div className="flex justify-start">
                <div className="bg-white dark:bg-slate-800 border border-gray-100 dark:border-slate-700 rounded-2xl rounded-bl-sm p-4 shadow-sm dark:shadow-none flex gap-1">
                  <div className="w-2 h-2 bg-gray-300 rounded-full animate-bounce"></div>
                  <div className="w-2 h-2 bg-gray-300 rounded-full animate-bounce" style={{ animationDelay: "0.15s" }}></div>
                  <div className="w-2 h-2 bg-gray-300 rounded-full animate-bounce" style={{ animationDelay: "0.3s" }}></div>
                </div>
              </div>
            )}
            <div ref={messagesEndRef} />
          </div>
          
          {/* Input Area */}
          <div className="p-3 bg-white dark:bg-slate-800 border-t">
            <form onSubmit={handleSend} className="flex items-center gap-2">
              <input 
                type="text" 
                value={input}
                onChange={e => setInput(e.target.value)}
                placeholder="Ask about places, tips..."
                className="flex-1 bg-gray-100 dark:bg-slate-800/80 border-transparent focus:bg-white dark:bg-slate-800 focus:border-brand-500 focus:ring-2 focus:ring-brand-200 rounded-full px-4 py-2 text-sm transition-all outline-none"
                disabled={isLoading}
              />
              <button 
                type="submit"
                disabled={!input.trim() || isLoading}
                className="bg-brand-600 hover:bg-brand-700 disabled:opacity-50 text-white rounded-full w-9 h-9 flex items-center justify-center transition-colors shadow-sm dark:shadow-none shrink-0"
              >
                ↑
              </button>
            </form>
          </div>
          
        </div>
      )}

      {/* Floating Button */}
      <button 
        onClick={() => setIsOpen(!isOpen)}
        className={`${isOpen ? 'scale-0 opacity-0' : 'scale-100 opacity-100'} transition-all duration-300 bg-brand-600 hover:bg-brand-700 text-white rounded-full w-14 h-14 flex items-center justify-center shadow-xl dark:shadow-none hover:shadow-brand-500/50 hover:-translate-y-1 relative`}
      >
        <span className="text-2xl">💬</span>
        <span className="absolute -top-1 -right-1 bg-red-500 w-4 h-4 rounded-full border-2 border-white animate-pulse"></span>
      </button>
    </div>
  );
}
