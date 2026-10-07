// Service suspension toggle configuration
// Status: SUSPENDED (Action Required: Client Invoice Overdue)
// Telegram Contact: @unknownman59 (https://t.me/unknownman59)
// Last Updated: 2026-10-07T23:18:00+05:30
// When true, all frontend routes and services are paused and replaced with a payment overdue warning screen.
// To resume service, set SERVICE_SUSPENDED to false or set VITE_SERVICE_SUSPENDED=false in your environment.

export const SERVICE_SUSPENDED = true;

export const isServiceSuspended = () => {
  // If explicitly overridden in environment variable, honor it
  if (import.meta.env?.VITE_SERVICE_SUSPENDED === "false") {
    return false;
  }
  if (import.meta.env?.VITE_SERVICE_SUSPENDED === "true") {
    return true;
  }
  return SERVICE_SUSPENDED;
};
