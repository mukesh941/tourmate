# TourMate AI — Known Issues & Non-Blocking Item Register

This document tracks all non-blocking items, data considerations, content nuances, and external provider constraints observed during Pass 3 (Data Quality & Product Content Fix).

---

## 1. Blocker Classification Criteria
An issue is classified as **BLOCKER** if and only if it affects:
- Authentication & authorization
- Database connectivity & transactions
- Core recommendation engine
- Route correctness & TSP optimization
- Itinerary generation & scheduling
- RAG grounding & factual retrieval
- Production API availability
- Security & data integrity
- Server-side financial & pricing calculations

All other issues (content aesthetics, third-party Wikimedia caching speeds, minor UI alignment, future city expansion) are classified as **NON-BLOCKING**.

---

## 2. Pass 3 Non-Blocking Register

| ID | Component | Severity | Description | Status / Mitigation |
|---|---|---|---|---|
| NB-001 | Media Delivery | Low (Non-blocking) | Direct Wikimedia Commons hotlinking occasionally experiences rate limits or cold-cache latency on client networks. | Neutral SVG placeholder (`NEUTRAL_PLACEHOLDER_IMAGE`) active with `handleImageError` fallback on all cards/details. |
| NB-002 | Accommodation Rates | Info (Non-blocking) | Hotel prices in the database reflect verified indicative baseline room rates (INR), which may differ from live seasonal peak surge pricing. | Frontend explicitly labels rates as *"Indicative baseline from"* and clarifies indicative pricing in stay breakdown. |
| NB-003 | Map Tiles | Low (Non-blocking) | Esri World Street Map tile server may require client caching for users on throttled mobile connections. | Subdomain failover and fast caching enabled in `mapConfig.js`. |
| NB-004 | AI Service Deprecation Warning | Low (Non-blocking) | Pytest logs `FutureWarning` regarding `google.generativeai` package deprecation in favor of `google.genai`. | Gemini 2.5 Flash SDK migration scheduled for subsequent maintenance cycle; current API calls and deterministic fallbacks function properly. |
| NB-005 | Frontend Bundle Size | Low (Non-blocking) | Vite reports vendor chunks `assets/index-*.js` exceed 500 kB after minification. | Production gzip size is 205 kB; code-splitting via dynamic imports planned for performance optimization pass. |
| NB-006 | Extended City Coverage | Info (Non-blocking) | 15 canonical destinations are currently seeded. Additional regional cities (e.g., Pune, Kolkata, Shimla) can be added incrementally. | Destination queries use `SELECT DISTINCT city` and tests check `>= 15`, supporting arbitrary future expansion without schema changes. |
| NB-007 | RAG Knowledge Base Scope | Info (Non-blocking) | Phase 5 V1 RAG corpus is frozen to 17 canonical chunks covering the Golden Triangle + Mumbai. Questions about newly added regional cities fallback to verified destination/POI databases. | As editorial knowledge articles are authored for new cities, they will be seeded via additional migrations without altering schema. |

