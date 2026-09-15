# TourMate AI - Implementation Phases

This document outlines the detailed implementation phases for the TourMate AI project, following the 15-phase roadmap defined in Phase 0.

## Phase 1: Foundation + JWT auth, protected dashboard
- **Objective:** Scaffold the monorepo, set up the database connection, and implement secure user authentication.
- **Frontend:**
  - Initialize React + Vite + Tailwind CSS project.
  - Set up React Router.
  - Build Login and Registration pages.
  - Implement a protected dashboard route.
  - Implement JWT storage and interceptors using Axios.
- **Backend:**
  - Initialize FastAPI project with structured routing.
  - Configure MongoDB connection (Motor/PyMongo).
  - Implement custom JWT authentication (bcrypt hashing, token generation/verification).
  - Create Auth and User endpoints.

## Phase 2: Destination & place browsing + admin CRUD
- **Objective:** Build the core database structures for destinations, categories, and places, and the APIs to manage and view them.
- **Frontend:**
  - Destinations listing page and detail page.
  - Places browsing page with filters (category, rating, etc.).
  - Admin UI for CRUD operations on destinations, categories, and tourist places.
- **Backend:**
  - Create Pydantic models for Destinations, Categories, and Places.
  - Implement endpoints for fetching destinations and places.
  - Implement Admin-only CRUD endpoints (role-based access control).

## Phase 3: Interactive map + geo search
- **Objective:** Integrate mapping capabilities for users to view and search places geographically.
- **Frontend:**
  - Integrate Google Maps JavaScript API (or alternative).
  - Display places on the map with custom markers.
  - Implement geo-search (find places near a specific location).
- **Backend:**
  - Ensure coordinates are indexed (2dsphere in MongoDB).
  - Implement geo-spatial queries to return places within a radius.

## Phase 4: KNN recommendation engine
- **Objective:** Provide personalized place recommendations based on user preferences.
- **Frontend:**
  - User onboarding/preferences form (interests, budget, travel style).
  - Display "Recommended for You" section on the dashboard with reasons.
- **Backend:**
  - User preferences endpoint.
  - Implement scikit-learn based K-Nearest Neighbors (KNN) algorithm.
  - Match user profile features against place features (history, nature, etc.).
  - Return top N recommended places.

## Phase 5: K-Means clustering + map overlay
- **Objective:** Group nearby or similar tourist places to help users plan focused area visits.
- **Frontend:**
  - Map overlay displaying distinct clusters of places (color-coded).
  - Cluster summary UI.
- **Backend:**
  - Implement K-Means clustering algorithm using scikit-learn.
  - Endpoint to return clustered places based on a given destination or criteria.

## Phase 6: A* route optimization
- **Objective:** Allow users to build an optimized multi-stop route between selected places.
- **Frontend:**
  - Route planning UI (select places to visit).
  - Display optimized route on the interactive map.
- **Backend:**
  - Implement A* (A-Star) search algorithm for route optimization.
  - Define static distance/time-cost graphs between places.
  - Endpoint to compute and return the optimized sequence of stops.

## Phase 7: AI tour-guide chatbot
- **Objective:** Provide an intelligent, context-aware virtual assistant for users.
- **Frontend:**
  - Chat interface accessible from the dashboard and place detail pages.
- **Backend:**
  - Integrate a hosted LLM API (e.g., OpenAI or Anthropic).
  - Implement RAG (Retrieval-Augmented Generation) style context injection (pass relevant place details to the LLM).
  - Store and manage chat session history.

## Phase 8: AI itinerary generator
- **Objective:** Automatically generate day-wise itineraries based on selected places and user constraints.
- **Frontend:**
  - Itinerary builder UI (select days, start/end times).
  - Display, edit, and save generated itineraries.
- **Backend:**
  - Logic to distribute selected places across days (using clustering/routing data).
  - Use LLM or algorithmic approach to create a structured, day-wise schedule.
  - Endpoints to generate, save, update, and delete itineraries.

## Phase 9: CNN landmark recognition
- **Objective:** Allow users to upload an image to identify a tourist landmark.
- **Frontend:**
  - Image upload interface with preview and loading states.
  - Display prediction results (identified landmark name, description).
- **Backend:**
  - Set up a TensorFlow/Keras image classification pipeline using Transfer Learning (e.g., MobileNetV2).
  - Implement the prediction endpoint.
  - (Assumption: A pre-trained or small labeled dataset model is used).

## Phase 10: i18n (English/Hindi) + audio guide
- **Objective:** Make the platform accessible in multiple languages and provide audio descriptions.
- **Frontend:**
  - Integrate `react-i18next` for English and Hindi support.
  - Language switcher in the UI.
  - Integrate Web SpeechSynthesis API for text-to-speech audio guides on place detail pages.
- **Backend:**
  - Ensure dynamic content (like AI chat responses) can respect the user's preferred language if applicable.

## Phase 11: Favorites, reviews, trip history
- **Objective:** Enhance user engagement through saved items, feedback, and history.
- **Frontend:**
  - "Save to Favorites" button on places.
  - Review and rating submission forms.
  - "My Trips" and "Favorites" sections in the user profile.
- **Backend:**
  - Endpoints for creating/deleting favorites.
  - Endpoints for submitting and fetching reviews/ratings.
  - Endpoints for retrieving trip history.

## Phase 12: Admin dashboard
- **Objective:** Provide administrators with an overview of system usage and content management.
- **Frontend:**
  - Admin overview page with key metrics and charts.
  - User management interface.
- **Backend:**
  - Endpoints for system statistics (user count, top places, etc.).
  - Endpoints to view and manage registered users.

## Phase 13: Testing & security hardening
- **Objective:** Ensure application reliability and security before deployment.
- **Frontend/Backend:**
  - Write unit and integration tests (pytest for backend, Jest/React Testing Library for frontend).
  - Validate ML module outputs independently.
  - Implement rate limiting, input validation, and secure headers.
  - Ensure no sensitive information is exposed.

## Phase 14: Deployment (COMPLETED)
- **Objective:** Make the application live on the web.
- **Infrastructure & Artifacts Delivered:**
  - Frontend: Configured for Vercel deployment with SPA routing (`vercel.json`), Netlify fallback (`netlify.toml`), and production builds validated.
  - Backend: Configured for Render deployment with Infrastructure as Code blueprint (`render.yaml`), root `/health` endpoint, and dynamic `$PORT` compatibility.
  - Containerization: Fixed multi-stage `Dockerfile` and `docker-compose.yml` for unified local/cloud container deployments.
  - Database: MongoDB Atlas production guidelines and seed automation with verified real photography.
  - Complete Deployment Guide: Documented in `docs/deployment_guide.md`.

## Phase 15: All-India Verified Hotels & Stays Module (COMPLETED)
- **Objective:** Enable tourists to discover, filter, and book verified accommodations across 20+ major destinations across all of India.
- **Backend:**
  - Pydantic schema: `app/schemas/hotel.py` with multi-room inventory, amenities, cancellation policies, and booking validation.
  - Service layer: `app/services/hotel_service.py` with Mongo geo-filters, text search, price filters, star ratings, and transactional reservation management.
  - REST endpoints: `app/api/routes/hotels.py` mounted at `/api/hotels` with room inventory calculations and bookings.
  - Seed database: 20 luxury/heritage/boutique stays across Delhi, Mumbai, Goa, Jaipur, Udaipur, Manali, Kerala, Agra, Varanasi, Kashmir, Rishikesh, Shimla, Ladakh, etc. with 100% real Unsplash photography.
- **Frontend:**
  - `Hotels.jsx`: Directory with destination pill filters, price range slider, star rating toggles, amenity badges, and interactive search.
  - `HotelDetail.jsx`: Room type selection, date range calculator with automated night count and total price, amenities grid, verified badge, and instant reservation modal.

## Phase 16: VTU Presentation Specification Alignment (COMPLETED)
- **Objective:** Satisfy all presentation requirements from `G2 VIRTUAL FINAL presentation 11.pptx` (VTU Major Project Synopsis).
- **Implemented Modules:**
  1. **A* (A-Star) Pathfinding Algorithm (Slide 11):**
     - Implemented in `app/services/route_service.py` and `app/services/ml_service.py`.
     - Uses priority queue (`heapq`) and Haversine heuristic cost function: $f(n) = g(n) + h(n)$.
     - Exposes detailed leg-by-leg waypoint distances, directions, and estimated transit times.
     - Frontend UI in `RoutePlannerView.jsx` displays A* heuristic badges, transit times, and turn-by-turn navigation.
  2. **Social Sharing Feature (Slide 19, Functional Requirement #5):**
     - Reusable `ShareModal.jsx` component supporting native Web Share API (`navigator.share`), WhatsApp one-click sharing, X (Twitter) posting, and clipboard copy.
     - Integrated across `MyItineraries.jsx`, `RoutePlannerView.jsx`, `PlaceDetail.jsx`, and `HotelDetail.jsx`.
  3. **Low-Network Offline Mode & Downloadable Tour (Slide 20, Non-Functional Requirement #3):**
     - Built `offlineService.js` utilizing browser `localStorage` for offline itinerary persistence.
     - Mode switcher in `MyItineraries.jsx` ("All Trips" vs "Available Offline") for travelers in remote/mountainous low-network areas.
     - Executive Printable/PDF Travel Pass generator complete with daily schedules and National Emergency/Tourist Police helplines (1363, 112, 102).
     - JSON export for offline data backup.
  4. **Tourist Review Sentiment Analysis (Slide 10 & 15):**
     - NLP Sentiment Service in `app/services/sentiment_service.py` utilizing tourism domain lexicon with valence scoring, negation flipping, and rating calibration.
     - Endpoints in `app/api/routes/interactions.py` automatically classify reviews into `Positive`, `Neutral`, or `Negative` with confidence percentages.
     - Sentiment distribution widget and sentiment badges displayed in `PlaceDetail.jsx`.

## Phase 17: Smart Nearby Tourist Recommendation System (COMPLETED)
- **Objective:** Build a smart location-based recommendation feature for the TourMate application, allowing tourists to plan their complete trip from one location.
- **Implemented Modules:**
  1. **Location Search:** Added an autocomplete search bar on the Dashboard targeting `/api/locations/search` to find cities, landmarks, and destinations.
  2. **Backend API Structure:** Created `/api/places`, `/api/hotels`, `/api/restaurants`, and `/api/activities` endpoints supporting MongoDB `$geoWithin` proximity search based on latitude, longitude, and radius (e.g., 5km, 15km).
  3. **Database Design:** Extended `HotelBase` schema with `GeoJSONPointSchema` location fields, and created brand new `Restaurant` and `Activity` models/schemas with geo-indexing.
  4. **Destination Overview (ExploreDestination.jsx):**
     - Parallel loading of 4 categories: Tourist Places, Hotels, Restaurants, and Things To Do.
     - Reusable `RecommendationCard.jsx` displaying image, rating, dynamic badges, distance, and price/duration details.
     - Interactive **React-Leaflet Map** rendering the center location and plotting all nearby spots with distinct color-coded markers.
     - "Plan Your Visit" summary sidebar guiding users to the Itinerary Builder.
