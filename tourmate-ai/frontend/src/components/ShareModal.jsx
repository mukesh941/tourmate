import React, { useState } from "react";

export default function ShareModal({ isOpen, onClose, title, text, url }) {
  const [copied, setCopied] = useState(false);

  if (!isOpen) return null;

  const shareUrl = url || window.location.href;
  const shareTitle = title || "TourMate - AI-Powered Travel Experience";
  const shareText = text || `Check out ${shareTitle} on TourMate!`;

  const handleCopy = async () => {
    try {
      if (navigator.clipboard && navigator.clipboard.writeText) {
        await navigator.clipboard.writeText(shareUrl);
      } else {
        const input = document.createElement("input");
        input.value = shareUrl;
        document.body.appendChild(input);
        input.select();
        document.execCommand("copy");
        document.body.removeChild(input);
      }
      setCopied(true);
      setTimeout(() => setCopied(false), 2500);
    } catch (err) {
      console.error("Failed to copy link:", err);
    }
  };

  const handleNativeShare = async () => {
    if (navigator.share) {
      try {
        await navigator.share({
          title: shareTitle,
          text: shareText,
          url: shareUrl,
        });
      } catch (err) {
        // User cancelled or share failed
        console.log("Share dismissed");
      }
    } else {
      handleCopy();
    }
  };

  const whatsappUrl = `https://api.whatsapp.com/send?text=${encodeURIComponent(
    `${shareText}\n🔗 Explore details: ${shareUrl}`
  )}`;

  const twitterUrl = `https://twitter.com/intent/tweet?text=${encodeURIComponent(
    shareText
  )}&url=${encodeURIComponent(shareUrl)}`;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-sm animate-fade-in">
      <div 
        className="bg-white dark:bg-slate-800 rounded-2xl shadow-2xl border border-gray-100 dark:border-slate-700 max-w-md w-full p-6 relative overflow-hidden"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Decorative top accent */}
        <div className="absolute top-0 left-0 right-0 h-1.5 bg-gradient-to-r from-brand-500 via-indigo-500 to-purple-500"></div>

        <div className="flex justify-between items-start mb-4">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-brand-50 dark:bg-brand-900/30 text-brand-600 dark:text-brand-400 flex items-center justify-center text-xl">
              📤
            </div>
            <div>
              <h3 className="text-lg font-bold text-gray-900 dark:text-white">Share with Travel Buddies</h3>
              <p className="text-xs text-gray-500 dark:text-slate-400">Collaborate and plan your trip together</p>
            </div>
          </div>
          <button 
            onClick={onClose} 
            className="text-gray-400 hover:text-gray-600 dark:hover:text-slate-200 p-1 rounded-lg hover:bg-gray-100 dark:hover:bg-slate-700 transition"
          >
            ✕
          </button>
        </div>

        {/* Content Preview */}
        <div className="bg-gray-50 dark:bg-slate-700/50 rounded-xl p-3 mb-5 border border-gray-100 dark:border-slate-700">
          <p className="text-sm font-semibold text-gray-800 dark:text-slate-200 truncate">{shareTitle}</p>
          <p className="text-xs text-gray-500 dark:text-slate-400 line-clamp-2 mt-0.5">{shareText}</p>
        </div>

        {/* Action Buttons */}
        <div className="grid grid-cols-2 gap-3 mb-5">
          {/* WhatsApp */}
          <a
            href={whatsappUrl}
            target="_blank"
            rel="noopener noreferrer"
            className="flex items-center justify-center gap-2 py-3 px-4 rounded-xl bg-emerald-500 hover:bg-emerald-600 text-white font-medium text-sm transition shadow-sm hover:shadow"
          >
            <span className="text-base">💬</span>
            <span>WhatsApp</span>
          </a>

          {/* X / Twitter */}
          <a
            href={twitterUrl}
            target="_blank"
            rel="noopener noreferrer"
            className="flex items-center justify-center gap-2 py-3 px-4 rounded-xl bg-black hover:bg-gray-900 text-white font-medium text-sm transition shadow-sm hover:shadow"
          >
            <span className="font-bold">𝕏</span>
            <span>Post on X</span>
          </a>
        </div>

        {/* Native Web Share API if available */}
        {typeof navigator !== "undefined" && navigator.share && (
          <button
            onClick={handleNativeShare}
            className="w-full mb-4 py-2.5 px-4 rounded-xl bg-indigo-50 dark:bg-indigo-900/30 hover:bg-indigo-100 text-indigo-700 dark:text-indigo-300 font-medium text-sm transition flex items-center justify-center gap-2"
          >
            <span>📱</span>
            <span>Open System Share Sheet</span>
          </button>
        )}

        {/* Link Copy Field */}
        <div>
          <label className="block text-xs font-semibold text-gray-500 dark:text-slate-400 uppercase tracking-wider mb-1.5">
            Share Link
          </label>
          <div className="flex gap-2">
            <input 
              type="text" 
              readOnly 
              value={shareUrl}
              className="flex-1 bg-gray-100 dark:bg-slate-700/80 border border-gray-200 dark:border-slate-600 rounded-xl px-3 py-2 text-xs text-gray-700 dark:text-slate-200 outline-none select-all"
            />
            <button
              onClick={handleCopy}
              className={`px-4 py-2 rounded-xl text-xs font-semibold transition flex items-center gap-1.5 shrink-0 shadow-sm ${
                copied 
                  ? "bg-green-600 text-white" 
                  : "bg-brand-600 hover:bg-brand-700 text-white"
              }`}
            >
              {copied ? (
                <>
                  <span>✓</span> Copied!
                </>
              ) : (
                <>
                  <span>📋</span> Copy
                </>
              )}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
