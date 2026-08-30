import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext";

export default function Login() {
  const { login } = useAuth();
  const navigate = useNavigate();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [submitting, setSubmitting] = useState(false);

  const onSubmit = async (e) => {
    e.preventDefault();
    setError("");
    setSubmitting(true);
    try {
      await login(email, password);
      navigate("/dashboard");
    } catch (err) {
      setError(err.response?.data?.error || err.response?.data?.detail || "Login failed. Check your credentials.");
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div 
      className="min-h-screen flex items-center justify-center p-4 bg-cover bg-center relative overflow-hidden"
      style={{ backgroundImage: 'url("https://images.unsplash.com/photo-1476514525535-07fb3b4ae5f1?ixlib=rb-4.0.3&auto=format&fit=crop&w=2000&q=80")' }}
    >
      <div className="absolute inset-0 bg-[#0f172a]/60 backdrop-blur-md"></div>
      
      {/* Animated blobs */}
      <div className="absolute top-1/4 left-1/4 w-96 h-96 bg-brand-500 rounded-full mix-blend-multiply filter blur-[100px] opacity-40 animate-blob"></div>
      <div className="absolute bottom-1/4 right-1/4 w-96 h-96 bg-accent-500 rounded-full mix-blend-multiply filter blur-[100px] opacity-40 animate-blob animation-delay-2000"></div>
      
      <div className="relative w-full max-w-md glass bg-white/10 dark:bg-slate-900/40 border border-white/20 shadow-2xl rounded-3xl p-8 sm:p-10 z-10 animate-fade-in-up">
        {/* Decorative elements */}
        <div className="absolute top-0 left-0 w-full h-1.5 bg-gradient-to-r from-brand-400 via-accent-500 to-brand-600 rounded-t-3xl"></div>
        
        <div className="text-center mb-8">
          <h1 className="text-4xl font-display font-extrabold text-white tracking-tight mb-3">Welcome Back</h1>
          <p className="text-brand-100 text-sm font-light">Ready for your next adventure with TourMate AI?</p>
        </div>

        <form onSubmit={onSubmit} className="space-y-5">
          {error && (
            <div className="bg-red-500/20 backdrop-blur-sm border border-red-500/50 text-red-100 px-4 py-3 rounded-xl text-sm flex items-center animate-fade-in-up">
              <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5 mr-2 flex-shrink-0 text-red-400" viewBox="0 0 20 20" fill="currentColor">
                <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7 4a1 1 0 11-2 0 1 1 0 012 0zm-1-9a1 1 0 00-1 1v4a1 1 0 102 0V6a1 1 0 00-1-1z" clipRule="evenodd" />
              </svg>
              {error}
            </div>
          )}

          <div className="animate-fade-in-up-delay-1">
            <label className="block text-xs font-bold text-brand-200 uppercase tracking-widest mb-1.5" htmlFor="email">Email</label>
            <input
              id="email"
              type="email"
              required
              placeholder="explorer@example.com"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              className="w-full bg-black/20 backdrop-blur-sm border border-white/10 rounded-xl px-4 py-3.5 text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-brand-400 focus:bg-black/40 transition-all font-medium"
            />
          </div>

          <div className="animate-fade-in-up-delay-1">
            <label className="block text-xs font-bold text-brand-200 uppercase tracking-widest mb-1.5" htmlFor="password">Password</label>
            <input
              id="password"
              type="password"
              required
              placeholder="••••••••"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className="w-full bg-black/20 backdrop-blur-sm border border-white/10 rounded-xl px-4 py-3.5 text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-brand-400 focus:bg-black/40 transition-all font-medium"
            />
          </div>

          <div className="animate-fade-in-up-delay-2 pt-2">
            <button
              type="submit"
              disabled={submitting}
              className="w-full bg-gradient-to-r from-brand-600 to-accent-600 hover:from-brand-500 hover:to-accent-500 text-white shadow-xl shadow-brand-500/20 rounded-xl py-3.5 font-bold transition-all transform hover:-translate-y-0.5 active:translate-y-0 disabled:opacity-70 disabled:transform-none disabled:shadow-none"
            >
              {submitting ? (
                <span className="flex items-center justify-center gap-2">
                  <svg className="animate-spin h-5 w-5 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                  </svg>
                  Logging in...
                </span>
              ) : "Log in to TourMate"}
            </button>
          </div>

          <div className="pt-6 text-center animate-fade-in-up-delay-2 border-t border-white/10 mt-6">
            <p className="text-sm text-gray-300 font-light">
              Don't have an account?{" "}
              <Link to="/register" className="text-brand-300 font-bold hover:text-white transition-colors relative after:absolute after:bottom-0 after:left-0 after:w-0 after:h-px after:bg-white hover:after:w-full after:transition-all after:duration-300 pb-0.5">
                Sign up today
              </Link>
            </p>
          </div>
        </form>
      </div>
    </div>
  );
}
