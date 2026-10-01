import { useState, useEffect } from "react";
import { useSearchParams, useNavigate, Link } from "react-router-dom";
import api from "../api/axios";

export default function VerifyEmail() {
  const [searchParams] = useSearchParams();
  const token = searchParams.get("token");
  const [status, setStatus] = useState("loading"); // loading, success, error
  const [message, setMessage] = useState("");
  const [resendEmail, setResendEmail] = useState("");
  const [resendStatus, setResendStatus] = useState(""); // idle, sending, success, error

  useEffect(() => {
    if (!token) {
      setStatus("error");
      setMessage("No verification token provided.");
      return;
    }

    const verifyToken = async () => {
      try {
        const response = await api.post("/auth/verify-email", { token });
        setStatus("success");
        setMessage("Email verified successfully. You can now log in to TourMate.");
      } catch (err) {
        setStatus("error");
        const msg = err.response?.data?.detail || "Invalid or expired verification token.";
        setMessage(typeof msg === "string" ? msg : JSON.stringify(msg));
      }
    };

    verifyToken();
  }, [token]);

  const handleResend = async (e) => {
    e.preventDefault();
    if (!resendEmail) return;
    
    setResendStatus("sending");
    try {
      await api.post("/auth/resend-verification", { email: resendEmail });
      setResendStatus("success");
    } catch (err) {
      setResendStatus("error");
    }
  };

  return (
    <div 
      className="min-h-screen flex items-center justify-center p-4 bg-cover bg-center relative overflow-hidden"
      style={{ backgroundImage: 'url("https://images.unsplash.com/photo-1476514525535-07fb3b4ae5f1?ixlib=rb-4.0.3&auto=format&fit=crop&w=2000&q=80")' }}
    >
      <div className="absolute inset-0 bg-[#0f172a]/60 backdrop-blur-md"></div>
      
      <div className="relative w-full max-w-md glass bg-white/10 dark:bg-slate-900/40 border border-white/20 shadow-2xl rounded-3xl p-8 sm:p-10 z-10 animate-fade-in-up">
        <div className="absolute top-0 left-0 w-full h-1.5 bg-gradient-to-r from-brand-400 via-accent-500 to-brand-600 rounded-t-3xl"></div>
        
        <div className="text-center mb-8">
          <h1 className="text-3xl font-display font-extrabold text-white tracking-tight mb-3">Email Verification</h1>
        </div>

        {status === "loading" && (
          <div className="flex flex-col items-center justify-center space-y-4">
            <svg className="animate-spin h-10 w-10 text-brand-400" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
              <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
              <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
            </svg>
            <p className="text-brand-100">Verifying your email...</p>
          </div>
        )}

        {status === "success" && (
          <div className="text-center space-y-6">
            <div className="inline-flex items-center justify-center w-16 h-16 rounded-full bg-green-500/20 text-green-400 mb-2">
              <svg xmlns="http://www.w3.org/2000/svg" className="h-8 w-8" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M5 13l4 4L19 7" />
              </svg>
            </div>
            <p className="text-white font-medium">{message}</p>
            <Link to="/login" className="block w-full bg-gradient-to-r from-brand-600 to-accent-600 hover:from-brand-500 hover:to-accent-500 text-white rounded-xl py-3 font-bold transition-all">
              Go to Login
            </Link>
          </div>
        )}

        {status === "error" && (
          <div className="space-y-6">
            <div className="bg-red-500/20 border border-red-500/50 text-red-100 px-4 py-3 rounded-xl text-sm flex items-center">
              <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5 mr-2 flex-shrink-0 text-red-400" viewBox="0 0 20 20" fill="currentColor">
                <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7 4a1 1 0 11-2 0 1 1 0 012 0zm-1-9a1 1 0 00-1 1v4a1 1 0 102 0V6a1 1 0 00-1-1z" clipRule="evenodd" />
              </svg>
              {message}
            </div>

            <div className="border-t border-white/10 pt-6 mt-6">
              <h3 className="text-white font-medium mb-4 text-center">Need a new link?</h3>
              <form onSubmit={handleResend} className="space-y-4">
                <input
                  type="email"
                  required
                  placeholder="Enter your email"
                  value={resendEmail}
                  onChange={(e) => setResendEmail(e.target.value)}
                  className="w-full bg-black/20 border border-white/10 rounded-xl px-4 py-3 text-white focus:ring-2 focus:ring-brand-400"
                />
                <button
                  type="submit"
                  disabled={resendStatus === "sending"}
                  className="w-full bg-white/10 hover:bg-white/20 text-white rounded-xl py-3 font-bold transition-all"
                >
                  {resendStatus === "sending" ? "Sending..." : "Resend Verification Email"}
                </button>
              </form>
              
              {resendStatus === "success" && (
                <p className="text-green-400 text-sm mt-3 text-center">If the email is registered, a new link has been sent.</p>
              )}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
