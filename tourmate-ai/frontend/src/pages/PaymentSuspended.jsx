import React, { useState } from "react";
import { 
  AlertTriangle, 
  Lock, 
  Send, 
  Copy, 
  Check, 
  ExternalLink, 
  ShieldAlert, 
  Clock, 
  CreditCard,
  MessageCircle
} from "lucide-react";

export default function PaymentSuspended() {
  const [copied, setCopied] = useState(false);
  const telegramHandle = "@unknownman59";
  const telegramUrl = "https://t.me/unknownman59";

  const handleCopy = () => {
    navigator.clipboard?.writeText(telegramHandle);
    setCopied(true);
    setTimeout(() => setCopied(false), 2500);
  };

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 flex flex-col justify-between selection:bg-amber-500/30 selection:text-amber-200">
      {/* Top Banner Warning Bar */}
      <div className="bg-gradient-to-r from-amber-600 via-rose-600 to-amber-600 px-4 py-2.5 text-center text-xs sm:text-sm font-semibold tracking-wide text-white shadow-lg flex items-center justify-center gap-2">
        <AlertTriangle className="w-4 h-4 animate-pulse text-amber-200 flex-shrink-0" />
        <span>CRITICAL NOTICE: Service currently frozen due to outstanding payment settlement</span>
      </div>

      {/* Main Content Area */}
      <main className="flex-1 max-w-4xl w-full mx-auto px-4 sm:px-6 py-12 flex flex-col justify-center items-center">
        <div className="w-full bg-slate-900/80 border border-slate-800 backdrop-blur-xl rounded-3xl p-6 sm:p-10 shadow-2xl relative overflow-hidden">
          {/* Subtle Ambient Glow */}
          <div className="absolute -top-32 -right-32 w-80 h-80 bg-rose-600/10 rounded-full blur-3xl pointer-events-none" />
          <div className="absolute -bottom-32 -left-32 w-80 h-80 bg-amber-600/10 rounded-full blur-3xl pointer-events-none" />

          {/* Icon Badge & Heading */}
          <div className="flex flex-col items-center text-center space-y-4">
            <div className="relative">
              <div className="w-20 h-20 rounded-2xl bg-gradient-to-br from-rose-500/20 via-amber-500/20 to-rose-500/10 border border-rose-500/30 flex items-center justify-center text-rose-400 shadow-inner">
                <Lock className="w-10 h-10 text-rose-400" />
              </div>
              <span className="absolute -top-1 -right-1 flex h-4 w-4">
                <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-rose-400 opacity-75"></span>
                <span className="relative inline-flex rounded-full h-4 w-4 bg-rose-500"></span>
              </span>
            </div>

            <div className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-semibold bg-rose-500/10 border border-rose-500/20 text-rose-400 uppercase tracking-wider">
              <ShieldAlert className="w-3.5 h-3.5" />
              Service Suspended
            </div>

            <h1 className="text-3xl sm:text-4xl lg:text-5xl font-extrabold tracking-tight text-white">
              TourMate is Temporarily On Hold
            </h1>

            <p className="max-w-2xl text-slate-300 text-sm sm:text-base leading-relaxed">
              Access to the TourMate frontend, AI itinerary planner, map APIs, and backend services has been paused pending payment from the client.
            </p>
          </div>

          {/* Details Grid */}
          <div className="mt-8 grid grid-cols-1 sm:grid-cols-2 gap-4 text-left">
            <div className="bg-slate-950/60 border border-slate-800/80 rounded-2xl p-5 space-y-2">
              <div className="flex items-center gap-2 text-rose-400 font-semibold text-sm">
                <CreditCard className="w-4 h-4" />
                <span>Reason for Suspension</span>
              </div>
              <p className="text-xs sm:text-sm text-slate-400 leading-normal">
                Development and maintenance payments for this project have not been cleared by the client. Services are withheld until payment confirmation.
              </p>
            </div>

            <div className="bg-slate-950/60 border border-slate-800/80 rounded-2xl p-5 space-y-2">
              <div className="flex items-center gap-2 text-amber-400 font-semibold text-sm">
                <Clock className="w-4 h-4" />
                <span>How to Resume Service</span>
              </div>
              <p className="text-xs sm:text-sm text-slate-400 leading-normal">
                Once the overdue payment is made, all platform features, routes, databases, and custom AI tools will be immediately restored to normal operation.
              </p>
            </div>
          </div>

          {/* Telegram Action Box */}
          <div className="mt-8 bg-gradient-to-br from-slate-950/90 to-slate-900 border border-amber-500/30 rounded-2xl p-6 sm:p-8 text-center space-y-5">
            <div className="space-y-1">
              <h2 className="text-lg sm:text-xl font-bold text-white flex items-center justify-center gap-2">
                <MessageCircle className="w-5 h-5 text-amber-400" />
                <span>Resolve Payment & Resume Access</span>
              </h2>
              <p className="text-xs sm:text-sm text-slate-400">
                To complete the payment and resume service immediately, please talk to the developer on Telegram:
              </p>
            </div>

            {/* Telegram Username Box & CTA Buttons */}
            <div className="flex flex-col sm:flex-row items-center justify-center gap-3 max-w-md mx-auto">
              <a
                href={telegramUrl}
                target="_blank"
                rel="noopener noreferrer"
                className="w-full sm:w-auto inline-flex items-center justify-center gap-2.5 px-6 py-3.5 rounded-xl bg-gradient-to-r from-sky-500 to-blue-600 hover:from-sky-400 hover:to-blue-500 text-white font-semibold text-sm shadow-lg shadow-sky-500/25 transition-all transform hover:-translate-y-0.5 active:translate-y-0"
              >
                <Send className="w-4 h-4" />
                <span>Open Telegram @unknownman59</span>
                <ExternalLink className="w-3.5 h-3.5 opacity-70" />
              </a>

              <button
                type="button"
                onClick={handleCopy}
                className="w-full sm:w-auto inline-flex items-center justify-center gap-2 px-4 py-3.5 rounded-xl bg-slate-800 hover:bg-slate-700 border border-slate-700 text-slate-200 text-sm font-medium transition-colors"
                title="Copy Telegram Username"
              >
                {copied ? (
                  <>
                    <Check className="w-4 h-4 text-emerald-400" />
                    <span className="text-emerald-400">Copied!</span>
                  </>
                ) : (
                  <>
                    <Copy className="w-4 h-4 text-slate-400" />
                    <span>Copy Username</span>
                  </>
                )}
              </button>
            </div>

            <div className="inline-block px-3 py-1 rounded-md bg-slate-800/80 border border-slate-700/60 text-slate-300 text-xs font-mono">
              Telegram Handle: <span className="text-sky-400 font-semibold">{telegramHandle}</span>
            </div>
          </div>

          {/* Reassurance Footer inside Card */}
          <div className="mt-8 pt-6 border-t border-slate-800/80 flex flex-col sm:flex-row items-center justify-between text-xs text-slate-500 gap-3">
            <span>Platform: TourMate AI Travel Suite</span>
            <span>Status: Paused by Contractor (Payment Overdue)</span>
          </div>
        </div>
      </main>

      {/* Footer Notice */}
      <footer className="text-center py-6 px-4 text-xs text-slate-600 border-t border-slate-900">
        All rights and intellectual property remain reserved by the creator until payment obligations are fully met.
      </footer>
    </div>
  );
}
