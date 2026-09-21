import React, { useState, useEffect } from 'react';
import { Compass } from 'lucide-react';

/**
 * Standard neutral placeholder image SVG encoded as data URL.
 * Renders an elegant neutral geometric background with a subtle TourMate compass emblem.
 */
export const NEUTRAL_TOURMATE_PLACEHOLDER = `data:image/svg+xml;utf8,<svg xmlns="http://www.w3.org/2000/svg" width="600" height="400" viewBox="0 0 600 400" fill="none"><rect width="600" height="400" fill="%230f172a"/><radialGradient id="g" cx="50%25" cy="50%25" r="50%25"><stop offset="0%25" stop-color="%231e293b"/><stop offset="100%25" stop-color="%230f172a"/></radialGradient><rect width="600" height="400" fill="url(%23g)"/><circle cx="300" cy="180" r="44" stroke="%2338bdf8" stroke-width="2.5" stroke-opacity="0.6" stroke-dasharray="4 4"/><circle cx="300" cy="180" r="32" fill="%230284c7" fill-opacity="0.2"/><path d="M300 152 L310 176 L300 208 L290 176 Z" fill="%2338bdf8"/><path d="M272 180 L296 170 L328 180 L296 190 Z" fill="%230ea5e9" fill-opacity="0.8"/><circle cx="300" cy="180" r="4" fill="%23ffffff"/><text x="300" y="250" text-anchor="middle" fill="%2394a3b8" font-family="system-ui, -apple-system, sans-serif" font-size="14" font-weight="600" letter-spacing="1">TOURMATE VERIFIED PLACE</text></svg>`;

export default function SafeImage({
  src,
  alt = "TourMate Place",
  className = "",
  containerClassName = "",
  fallbackSrc = NEUTRAL_TOURMATE_PLACEHOLDER,
  aspectRatio,
  loading = "lazy",
  ...props
}) {
  // Normalize source: handle string, array of strings, or object with url property
  const resolveSrc = (raw) => {
    if (!raw) return null;
    if (typeof raw === 'string') return raw.trim() || null;
    if (Array.isArray(raw) && raw.length > 0) return resolveSrc(raw[0]);
    if (typeof raw === 'object') {
      return raw.url || raw.thumbnail_url || raw.image_url || raw.cover_image || null;
    }
    return null;
  };

  const initialSrc = resolveSrc(src);
  const [currentSrc, setCurrentSrc] = useState(initialSrc);
  const [isLoaded, setIsLoaded] = useState(false);
  const [hasError, setHasError] = useState(!initialSrc);

  useEffect(() => {
    const nextSrc = resolveSrc(src);
    setCurrentSrc(nextSrc);
    setIsLoaded(false);
    setHasError(!nextSrc);
  }, [src]);

  const handleError = () => {
    setHasError(true);
    setCurrentSrc(fallbackSrc);
  };

  const handleLoad = () => {
    setIsLoaded(true);
  };

  const effectiveSrc = hasError ? fallbackSrc : (currentSrc || fallbackSrc);

  return (
    <div
      className={`relative overflow-hidden bg-slate-100 dark:bg-slate-800 ${containerClassName}`}
      style={aspectRatio ? { aspectRatio } : undefined}
    >
      {/* Shimmer skeleton while loading original image */}
      {!isLoaded && !hasError && (
        <div className="absolute inset-0 bg-slate-200 dark:bg-slate-700/60 animate-pulse flex items-center justify-center">
          <Compass className="w-6 h-6 text-slate-400 dark:text-slate-500 animate-spin opacity-40" />
        </div>
      )}

      <img
        src={effectiveSrc}
        alt={alt}
        loading={loading}
        decoding="async"
        onError={handleError}
        onLoad={handleLoad}
        className={`${className} ${
          isLoaded || hasError ? 'opacity-100' : 'opacity-0'
        } transition-opacity duration-300 w-full h-full object-cover`}
        {...props}
      />
    </div>
  );
}
