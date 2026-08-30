# TourMate AI – Intelligent Virtual Tour Guide
## PHASE 0 — Project Planning

---

## 1. Project Requirements

### 1.1 Functional Requirements
| ID | Requirement |
|----|-------------|
| FR1 | Users can register/login (JWT-based) |
| FR2 | Users complete an onboarding flow capturing interests, budget, travel style |
| FR3 | Users can search/filter tourist destinations and places |
| FR4 | System returns KNN-based personalized recommendations with a reason |
| FR5 | System clusters places with K-Means and shows clusters on a map |
| FR6 | Users can view places on an interactive map |
| FR7 | System computes an optimized multi-stop route using A* |
| FR8 | Users can chat with an AI tour guide (context-aware) |
| FR9 | Users can generate, save, edit, delete a day-wise itinerary |
| FR10 | Users can upload an image and get a CNN-based landmark prediction |
| FR11 | UI supports English/Hindi with an i18n architecture |
| FR12 | Users can save favorites and view trip history |
| FR13 | Admins can manage places, destinations, categories, users |

### 1.2 Non-Functional Requirements
- Responsive (mobile-first), accessible, secure, maintainable
- Modular ML services (recommendation, clustering, routing, chatbot, vision) kept independent and swappable
- No secrets in source code — all via environment variables
- Graceful degradation: every external/AI/ML call has a defined loading / empty / error state
- Designed to scale to more destinations/users later (pagination, indexes, caching)

### 1.3 Explicit Non-Goals (student-project scope)
- No training of a large language model from scratch — chatbot uses a hosted LLM API (Anthropic/OpenAI) with retrieved place-context (RAG-style), not fine-tuning
- CNN uses transfer learning (e.g., MobileNetV2/ResNet backbone) on a small labeled landmark dataset — not trained from scratch
- "Real-time" traffic-aware routing is out of scope; A* uses static distance/time-cost graphs between selected places

---

## 2. Feature List (Grouped by Phase)
See §10 Development Roadmap — every feature below maps to exactly one phase so nothing is built out of order:
Auth → Destinations/Places → Map → KNN Recommendations → K-Means Clustering → A* Routing → AI Chat → Itinerary → Landmark CNN → i18n/Audio → Favorites/Reviews/History → Admin → Testing/Security → Deployment.

---

## 3. User Roles & Use Cases

### USER
Register/Login → Onboard (interests, budget, style) → Explore destinations → View place details → Get KNN recommendations → Browse map & clusters → Ask AI guide → Build a route (A*) → Generate itinerary → Upload image for landmark ID → Switch language → Listen to audio guide → Save favorites → View past trips.

### ADMIN
Login → CRUD tourist places → CRUD destinations → Manage categories → Manage landmark reference data → View users → View system statistics (usage, top places, recommendation hit-rate).

### Use-Case Diagram (textual)
```
                 ┌────────────────────┐
                 │       USER          │
                 └─────────┬───────────┘
        ┌───────────┬──────┼──────┬───────────┬────────────┐
     Register    Search   Get Rec  AI Chat   Plan Route   Upload
     /Login      Places   (KNN)   (LLM)      (A*)         Image (CNN)
                                                              
                 ┌────────────────────┐
                 │      ADMIN          │
                 └─────────┬───────────┘
        ┌───────────┬──────┼──────┬────────────┐
     Manage      Manage   Manage  View Users   View Stats
     Places      Dest.    Categ.
```

---

## 4. System Architecture

```
                         USER (Browser)
                              │
                    React Frontend (Vite + Tailwind)
                              │  Axios / REST + JWT
                    ──────────┴──────────
                    FastAPI Backend (Python)
                              │
        ┌───────────┬─────────┼─────────┬───────────────┐
        │           │         │         │               │
    Auth/Core   MongoDB   ML Services  External APIs   Static/Media
   (JWT, RBAC)  (Atlas)   ┌─────────┐  (Google Maps,     (images,
                          │ KNN     │   LLM API)          audio TTS)
                          │ K-Means │
                          │ A*      │
                          │ Chatbot │
                          │ CNN     │
                          └─────────┘
                              │
                       JSON Response
                              │
                       React UI (state/cache)
```

**Layering rules**
- `app/api/` — route handlers only (thin controllers)
- `app/services/` — business logic, orchestrates ML + DB
- `app/ml/*` — pure ML modules, no FastAPI/DB imports (unit-testable in isolation)
- `app/models/` + `app/schemas/` — Mongo document models (Pydantic) vs. API request/response schemas kept separate

---

## 5. Technology Stack (confirmed)

| Layer | Choice | Why |
|---|---|---|
| Frontend | React + Vite + Tailwind + React Router + Axios | Fast dev loop, ubiquitous, easy to grade/demo |
| Backend | FastAPI (Python) | Async, auto-generated OpenAPI docs (great for viva), same language as ML stack |
| Database | MongoDB Atlas | Flexible schema fits place documents with nested arrays (images, nearby places); free tier for students |
| Auth | **JWT-based (custom)**, not Firebase | Keeps the whole stack Python/Mongo (no vendor lock-in), easier to explain/demonstrate password hashing + token flow in a viva, avoids a second external dependency and its cost/quota surprises. Trade-off: Claude/we must implement refresh tokens, password reset, and hashing (bcrypt/passlib) ourselves — acceptable extra work for the learning value. |
| Maps | Google Maps JavaScript API (key restricted, loaded via env var, never in git) | Best documentation, widely graded/understood; OpenStreetMap+Leaflet is the documented fallback if quota/key becomes an issue |
| AI/ML | scikit-learn (KNN, K-Means), NetworkX-style custom A*, TensorFlow/Keras (transfer learning CNN), hosted LLM API for chat | Standard, explainable, appropriate for a student project |
| i18n | `react-i18next` | Standard, avoids app duplication |
| TTS | Browser `SpeechSynthesis` Web API first (zero cost/infra); swappable for a cloud TTS API later | Modular, works fully offline for a demo |
| Deployment | Frontend: Vercel · Backend: Render · DB: MongoDB Atlas | Free tiers sufficient for an academic deployment |

---

## 6. Database Design (MongoDB collections)

### `users`
| field | type | notes |
|---|---|---|
| _id | ObjectId | |
| name | string | required |
| email | string | required, unique, indexed |
| password_hash | string | required |
| role | enum(user, admin) | default "user" |
| preferred_language | string | default "en" |
| created_at | datetime | |

### `user_preferences`
| field | type | notes |
|---|---|---|
| _id | ObjectId | |
| user_id | ObjectId → users | indexed, unique |
| interests | [string] | e.g. history, nature, food |
| budget_range | string | low / medium / high |
| travel_style | string | relaxed / packed / balanced |
| available_time | string | e.g. "3 days" |
| preferred_activities | [string] | |

### `destinations`
| field | type | notes |
|---|---|---|
| _id | ObjectId | |
| name | string | e.g. "Jaipur" |
| state | string | |
| country | string | |
| description | string | |
| cover_image | string (url) | |
| popularity_score | float | |

### `categories`
| field | type | notes |
|---|---|---|
| _id | ObjectId | |
| name | string | unique |
| icon | string | |

### `tourist_places`
| field | type | notes |
|---|---|---|
| _id | ObjectId | |
| destination_id | ObjectId → destinations | indexed |
| name | string | required, indexed (text) |
| category_id | ObjectId → categories | indexed |
| description | string | |
| history | string | |
| cultural_significance | string | |
| coordinates | {lat: float, lng: float} | geospatial index (2dsphere) |
| images | [string] | |
| rating | float | 0–5 |
| price_level | int | 1–4 |
| visit_duration_minutes | int | |
| feature_scores | {history, nature, culture, adventure, food, shopping, architecture: float} | used by KNN |
| nearby_place_ids | [ObjectId] | precomputed or derived |

### `recommendations` (cache/log of generated results)
| field | type | notes |
|---|---|---|
| _id | ObjectId | |
| user_id | ObjectId → users | indexed |
| place_id | ObjectId → tourist_places | |
| score | float | |
| reason | string | |
| generated_at | datetime | |

### `favorites`
| user_id, place_id, created_at | indexed on (user_id, place_id) unique |

### `trips`
| _id, user_id, title, destination_id, start_date, end_date, place_ids[], status |

### `itineraries`
| _id, trip_id, user_id, days: [{date, items: [{time, place_id, note}]}], budget, travelers, created_at, updated_at |

### `chat_sessions` / `chat_messages`
| chat_sessions: _id, user_id, place_context_id, created_at
| chat_messages: _id, session_id, role(user/assistant), content, created_at

### `landmarks` (CNN label reference data)
| _id, label, place_id (→ tourist_places), description, model_confidence_threshold |

### `reviews`
| _id, user_id, place_id, rating, comment, created_at |

### `admin_users`
| Same shape as `users` filtered by role=admin, or simply a role flag — no separate collection needed (kept in requirements for clarity only). |

**Indexes:** `users.email` (unique), `tourist_places.name` (text), `tourist_places.coordinates` (2dsphere), `tourist_places.destination_id`, `favorites (user_id, place_id)` (unique compound), `chat_messages.session_id`.

---

## 7. API Specification (v1)

```
AUTH
POST   /api/auth/register
POST   /api/auth/login
GET    /api/auth/me

USERS
GET    /api/users/profile
PUT    /api/users/profile
PUT    /api/users/preferences

DESTINATIONS
GET    /api/destinations
GET    /api/destinations/{id}

PLACES
GET    /api/places?destination_id=&category=&q=&min_rating=
GET    /api/places/{id}
POST   /api/places            (admin)
PUT    /api/places/{id}       (admin)
DELETE /api/places/{id}       (admin)

RECOMMENDATIONS
GET    /api/recommendations
POST   /api/recommendations/generate

CLUSTERING
GET    /api/clusters?destination_id=

CHAT
POST   /api/chat
GET    /api/chat/history?session_id=

ROUTES
POST   /api/routes/optimize   { start, destinations[] }

ITINERARY
POST   /api/itinerary/generate
GET    /api/itinerary
PUT    /api/itinerary/{id}
DELETE /api/itinerary/{id}

LANDMARK
POST   /api/landmark/predict  (multipart image)

FAVORITES
POST   /api/favorites
GET    /api/favorites
DELETE /api/favorites/{id}

ADMIN
GET    /api/admin/users
GET    /api/admin/statistics
```
Every endpoint returns a consistent envelope: `{ success, data, error }` and uses standard HTTP status codes (400/401/403/404/422/500). Full OpenAPI docs are auto-generated by FastAPI at `/docs`.

---

## 8. Folder Structure
Adopting the monorepo layout exactly as specified in the brief (`frontend/`, `backend/app/{api,models,schemas,services,ml/*,core,utils}`, `ml/`, `docs/`, `scripts/`, root `docker-compose.yml`). This will be scaffolded at the start of Phase 1.

---

## 9. Development Roadmap (15 phases)

| Phase | Deliverable |
|---|---|
| 0 | Planning (this document) |
| 1 | Foundation + JWT auth, protected dashboard |
| 2 | Destination & place browsing + admin CRUD |
| 3 | Interactive map + geo search |
| 4 | KNN recommendation engine |
| 5 | K-Means clustering + map overlay |
| 6 | A* route optimization |
| 7 | AI tour-guide chatbot |
| 8 | AI itinerary generator |
| 9 | CNN landmark recognition |
| 10 | i18n (English/Hindi) + audio guide |
| 11 | Favorites, reviews, trip history |
| 12 | Admin dashboard |
| 13 | Testing & security hardening |
| 14 | Deployment |

Each phase will be delivered only when you say "start phase N", following the 19-point response format (objective → …→ next-phase preview), and will not break what was built before it.

---

## Phase 0 Completion Checklist
- [x] Requirements documented (functional + non-functional)
- [x] Feature list mapped to phases
- [x] User roles & use cases defined
- [x] System architecture diagram
- [x] Tech stack finalized with justification (JWT chosen over Firebase)
- [x] Database schema for all 14 collections with indexes
- [x] REST API surface specified
- [x] Folder structure locked
- [x] 15-phase roadmap agreed

## Next Step
Say **"start phase 1"** to scaffold the repo, React+Tailwind frontend, FastAPI backend, MongoDB connection, and JWT authentication with a protected dashboard.
