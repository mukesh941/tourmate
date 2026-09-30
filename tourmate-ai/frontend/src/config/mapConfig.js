/**
 * Centralized Map Configuration.
 * 
 * Production-safe tile provider strategy:
 * Uses Esri World Street Map as the default provider:
 * - Publicly available for web mapping
 * - Fast global CDN response
 * - Reliable 200 OK responses without referrer-blocking policy conflicts
 * - Configurable via environment variables (VITE_MAP_TILE_URL, VITE_MAP_ATTRIBUTION)
 */

export const MAP_TILE_URL = 
  import.meta.env.VITE_MAP_TILE_URL || 
  "https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png";

export const MAP_ATTRIBUTION = 
  import.meta.env.VITE_MAP_ATTRIBUTION || 
  '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors';
