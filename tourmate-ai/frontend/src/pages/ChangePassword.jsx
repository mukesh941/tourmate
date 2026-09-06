import { useState } from "react";
import { useNavigate, Link } from "react-router-dom";
import { Eye, EyeOff, Lock, ShieldCheck, ArrowLeft, CheckCircle2, XCircle } from "lucide-react";
import api from "../api/axios";

function StrengthBar({ password }) {
  const checks = [
    { label: "At least 6 characters", pass: password.length >= 6 },
    { label: "Contains a number", pass: /\d/.test(password) },
    { label: "Contains uppercase", pass: /[A-Z]/.test(password) },
    { label: "Contains special character", pass: /[^a-zA-Z0-9]/.test(password) },
  ];
  const score = checks.filter((c) => c.pass).length;
  const colors = ["bg-red-500", "bg-orange-500", "bg-yellow-500", "bg-green-500"];
  const labels = ["Weak", "Fair", "Good", "Strong"];

  if (!password) return null;

  return (
    <div className="mt-3 space-y-2">
      <div className="flex gap-1">
        {[0, 1, 2, 3].map((i) => (
          <div
            key={i}
            className={`h-1.5 flex-1 rounded-full transition-all duration-300 ${
              i < score ? colors[score - 1] : "bg-white/10"
            }`}
          />
        ))}
      </div>
      <p className={`text-xs font-bold ${score > 0 ? `text-${["red","orange","yellow","green"][score-1]}-400` : "text-gray-400"}`}>
        {score > 0 ? labels[score - 1] : ""}
      </p>
      <ul className="space-y-1">
        {checks.map((c) => (
          <li key={c.label} className={`flex items-center gap-1.5 text-xs ${c.pass ? "text-green-400" : "text-gray-400"}`}>
            {c.pass ? <CheckCircle2 className="w-3.5 h-3.5 flex-shrink-0" /> : <XCircle className="w-3.5 h-3.5 flex-shrink-0" />}
            {c.label}
          </li>
        ))}
      </ul>
    </div>
  );
}

function PasswordInput({ id, label, value, onChange, show, onToggle, placeholder }) {
  return (
    <div>
      <label className="block text-xs font-bold text-brand-200 uppercase tracking-widest mb-1.5" htmlFor={id}>
        {label}
      </label>
      <div className="relative">
        <div className="absolute left-4 top-1/2 -translate-y-1/2 text-gray-400">
          <Lock className="w-4 h-4" />
        </div>
        <input
          id={id}
          type={show ? "text" : "password"}
          required
          placeholder={placeholder}
          value={value}
          onChange={onChange}
          className="w-full bg-black/20 backdrop-blur-sm border border-white/10 rounded-xl pl-10 pr-12 py-3.5 text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-brand-400 focus:bg-black/40 transition-all font-medium"
        />
        <button
          type="button"
          onClick={onToggle}
          className="absolute right-4 top-1/2 -translate-y-1/2 text-gray-400 hover:text-white transition-colors"
        >
          {show ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
        </button>
      </div>
    </div>
  );
}

export default function ChangePassword() {
  const navigate = useNavigate();
  const [currentPassword, setCurrentPassword] = useState("");
  const [newPassword, setNewPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [showCurrent, setShowCurrent] = useState(false);
  const [showNew, setShowNew] = useState(false);
  const [showConfirm, setShowConfirm] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState("");
  const [success, setSuccess] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError("");

    if (newPassword !== confirmPassword) {
      setError("New passwords do not match.");
      return;
    }
    if (newPassword.length < 6) {
      setError("New password must be at least 6 characters.");
      return;
    }

    setSubmitting(true);
    try {
      await api.put("/users/change-password", {
        current_password: currentPassword,
        new_password: newPassword,
      });
      setSuccess(true);
      setTimeout(() => navigate("/dashboard"), 2500);
    } catch (err) {
      setError(
        err.response?.data?.detail || err.response?.data?.error || "Failed to change password."
      );
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div
      className="min-h-screen flex items-center justify-center p-4 bg-cover bg-center relative overflow-hidden"
      style={{
        backgroundImage:
          'url("https://images.unsplash.com/photo-1507608616759-54f48f0af0ee?ixlib=rb-4.0.3&auto=format&fit=crop&w=2000&q=80")',
      }}
    >
      <div className="absolute inset-0 bg-[#0f172a]/65 backdrop-blur-md" />

      {/* Animated blobs */}
      <div className="absolute top-1/4 left-1/3 w-96 h-96 bg-brand-500 rounded-full mix-blend-multiply filter blur-[120px] opacity-30 animate-blob" />
      <div className="absolute bottom-1/4 right-1/4 w-96 h-96 bg-accent-500 rounded-full mix-blend-multiply filter blur-[120px] opacity-30 animate-blob animation-delay-2000" />

      <div className="relative w-full max-w-md z-10 animate-fade-in-up">
        {/* Back link */}
        <Link
          to="/dashboard"
          className="inline-flex items-center gap-2 text-sm text-brand-200 hover:text-white transition-colors mb-6 font-medium"
        >
          <ArrowLeft className="w-4 h-4" />
          Back to Dashboard
        </Link>

        <div className="glass bg-white/10 dark:bg-slate-900/40 border border-white/20 shadow-2xl rounded-3xl p-8 sm:p-10">
          {/* Top gradient bar */}
          <div className="absolute top-0 left-0 w-full h-1.5 bg-gradient-to-r from-brand-400 via-accent-500 to-brand-600 rounded-t-3xl" />

          {/* Header */}
          <div className="text-center mb-8">
            <div className="inline-flex items-center justify-center w-16 h-16 rounded-2xl bg-brand-500/20 border border-brand-400/30 mb-4">
              <ShieldCheck className="w-8 h-8 text-brand-400" />
            </div>
            <h1 className="text-3xl font-display font-extrabold text-white tracking-tight mb-2">
              Change Password
            </h1>
            <p className="text-brand-100 text-sm font-light">
              Keep your TourMate account secure
            </p>
          </div>

          {/* Success state */}
          {success ? (
            <div className="flex flex-col items-center gap-4 py-6 animate-fade-in-up">
              <div className="w-16 h-16 rounded-full bg-green-500/20 border border-green-400/40 flex items-center justify-center">
                <CheckCircle2 className="w-8 h-8 text-green-400" />
              </div>
              <h2 className="text-xl font-bold text-white">Password Updated!</h2>
              <p className="text-gray-300 text-sm text-center">
                Your password has been changed successfully. Redirecting you to the dashboard…
              </p>
            </div>
          ) : (
            <form onSubmit={handleSubmit} className="space-y-5">
              {/* Error alert */}
              {error && (
                <div className="bg-red-500/20 backdrop-blur-sm border border-red-500/50 text-red-100 px-4 py-3 rounded-xl text-sm flex items-center gap-2 animate-fade-in-up">
                  <XCircle className="w-5 h-5 flex-shrink-0 text-red-400" />
                  {error}
                </div>
              )}

              <PasswordInput
                id="current-password"
                label="Current Password"
                value={currentPassword}
                onChange={(e) => setCurrentPassword(e.target.value)}
                show={showCurrent}
                onToggle={() => setShowCurrent((v) => !v)}
                placeholder="Enter current password"
              />

              <div>
                <PasswordInput
                  id="new-password"
                  label="New Password"
                  value={newPassword}
                  onChange={(e) => setNewPassword(e.target.value)}
                  show={showNew}
                  onToggle={() => setShowNew((v) => !v)}
                  placeholder="Enter new password"
                />
                <StrengthBar password={newPassword} />
              </div>

              <PasswordInput
                id="confirm-password"
                label="Confirm New Password"
                value={confirmPassword}
                onChange={(e) => setConfirmPassword(e.target.value)}
                show={showConfirm}
                onToggle={() => setShowConfirm((v) => !v)}
                placeholder="Re-enter new password"
              />

              {/* Match indicator */}
              {confirmPassword && (
                <p
                  className={`text-xs font-semibold flex items-center gap-1.5 ${
                    newPassword === confirmPassword ? "text-green-400" : "text-red-400"
                  }`}
                >
                  {newPassword === confirmPassword ? (
                    <><CheckCircle2 className="w-3.5 h-3.5" /> Passwords match</>
                  ) : (
                    <><XCircle className="w-3.5 h-3.5" /> Passwords do not match</>
                  )}
                </p>
              )}

              <div className="pt-2">
                <button
                  id="change-password-submit"
                  type="submit"
                  disabled={submitting}
                  className="w-full bg-gradient-to-r from-brand-600 to-accent-600 hover:from-brand-500 hover:to-accent-500 text-white shadow-xl shadow-brand-500/20 rounded-xl py-3.5 font-bold transition-all transform hover:-translate-y-0.5 active:translate-y-0 disabled:opacity-70 disabled:transform-none disabled:shadow-none"
                >
                  {submitting ? (
                    <span className="flex items-center justify-center gap-2">
                      <svg className="animate-spin h-5 w-5 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                        <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                        <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
                      </svg>
                      Updating Password…
                    </span>
                  ) : (
                    "Update Password"
                  )}
                </button>
              </div>
            </form>
          )}
        </div>
      </div>
    </div>
  );
}
