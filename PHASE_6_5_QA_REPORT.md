# PHASE 6.5 QA & PRODUCT ACCEPTANCE REPORT

## Executive Summary
This report documents the findings from the real-user product acceptance and end-to-end quality audit for TourMate AI (Phase 6.5). The baseline consisted of 160 backend tests passing, 0 build errors, and verified live endpoints on Render and Vercel.

---

## Issues Discovered

### ISSUE-6.5-01
- **Severity**: 🟠 P1 — HIGH
- **Page**: Landing Page (`/`) & Dashboard (`/dashboard`)
- **Steps to Reproduce**:
  1. Open a browser in private/incognito mode (unauthenticated guest).
  2. Navigate to root URL `https://frontend-delta-six-hf0z79dpo8.vercel.app/`.
- **Expected Behavior**: The root URL `/` serves the public Landing Page (Hero section, search bar, popular destinations, hotels, places) without forcing an immediate redirect to `/login`.
- **Actual Behavior**: The application immediately redirects `/` to `/dashboard`, and `ProtectedRoute` redirects unauthenticated users to `/login`. Furthermore, in `Dashboard.jsx`, `fetchData()` aborted early if `!token`, preventing public data from being fetched.
- **Evidence**: `App.jsx` line 68 (`<Route path="/" element={<Navigate to="/dashboard" replace />} />`), `ProtectedRoute.jsx` line 7 (`if (!user) return <Navigate to="/login" replace />;`), and `Dashboard.jsx` line 24 (`if (!token) return;`).
- **Likely Root Cause**: Root route was linked to `/dashboard` which was wrapped in `<ProtectedRoute>`.
- **Proposed Fix**:
  - In `App.jsx`, render `<Dashboard />` at `/` for public access.
  - In `Dashboard.jsx`, allow `fetchData()` to query public destinations, hotels, and places for unauthenticated visitors, while gating user-specific preference fetching and `OnboardingModal` on `token`.
- **Status**: Confirmed.

---

### ISSUE-6.5-02
- **Severity**: 🟠 P1 — HIGH
- **Page**: Landing Page / Dashboard (`RecommendationCard.jsx` under "Taste India" and "Things To Do")
- **Steps to Reproduce**:
  1. Go to the home page / dashboard and scroll to "Taste India" or "Things To Do".
  2. Click on any restaurant or activity recommendation card.
- **Expected Behavior**: Navigates to `/places/:id` to view full details, ratings, opening hours, and location.
- **Actual Behavior**: Constructs `linkTarget = /${type}s/${item.id}` $\to$ `/restaurants/:id` or `/activitys/:id`, routes which do not exist in `App.jsx`, rendering a blank unhandled page.
- **Evidence**: `RecommendationCard.jsx` line 47: `linkTarget = ... : /${type}s/${item.id}`. `App.jsx` only registers `/places/:id`.
- **Likely Root Cause**: Component assumed separate routes existed for restaurants and activities, but both are canonical POIs/places in PostgreSQL and React.
- **Proposed Fix**: In `RecommendationCard.jsx`, map `type === 'restaurant'` and `type === 'activity'` directly to `/places/${item.id}`.
- **Status**: Confirmed.

---

### ISSUE-6.5-03
- **Severity**: 🟢 P3 — LOW
- **Page**: Location Search Component (`LocationSearch.jsx`)
- **Steps to Reproduce**:
  1. View the main hero search bar on the Landing Page.
  2. Observe the placeholder text.
- **Expected Behavior**: Relevant destination examples within India (e.g., `Where do you want to go? (e.g. Jaipur, Agra, Goa)`).
- **Actual Behavior**: Displays `Where do you want to go? (e.g. Pokhara)` (legacy non-India placeholder).
- **Evidence**: `LocationSearch.jsx` line 69.
- **Likely Root Cause**: Outdated template string.
- **Proposed Fix**: Update placeholder string to reference Indian destinations.
- **Status**: Confirmed.

---

### ISSUE-6.5-04
- **Severity**: 🟡 P2 — MEDIUM
- **Page**: Mobile Bottom Navigation Bar (`Navbar.jsx`)
- **Steps to Reproduce**:
  1. Open website on a mobile viewport ($<768$px).
  2. Click "Home" on the fixed bottom navigation bar.
- **Expected Behavior**: Highlights active when on `/` or `/dashboard`, and navigates to `/`.
- **Actual Behavior**: Hardcoded to `/dashboard` which was guarded by login.
- **Evidence**: `Navbar.jsx` lines 262-265.
- **Likely Root Cause**: Route link hardcoded to `/dashboard`.
- **Proposed Fix**: Link to `/` and match active state on both `/` and `/dashboard`.
- **Status**: Confirmed.
