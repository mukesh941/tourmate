import { useState, useRef } from "react";
import { Link } from "react-router-dom";
import { Navigation } from "lucide-react";
import api from "../api/axios";
import { openGoogleMapsNavigation } from "../utils/navigation";

export default function LandmarkRecognition() {
  const [file, setFile] = useState(null);
  const [preview, setPreview] = useState(null);
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);
  const fileInputRef = useRef(null);

  const handleFileSelect = (e) => {
    const selected = e.target.files[0];
    if (selected) {
      setFile(selected);
      setPreview(URL.createObjectURL(selected));
      setResult(null);
      setError(null);
    }
  };

  const handleDragOver = (e) => {
    e.preventDefault();
  };

  const handleDrop = (e) => {
    e.preventDefault();
    const dropped = e.dataTransfer.files[0];
    if (dropped) {
      setFile(dropped);
      setPreview(URL.createObjectURL(dropped));
      setResult(null);
      setError(null);
    }
  };

  const handleAnalyze = async () => {
    if (!file) return;
    
    setLoading(true);
    setError(null);
    
    const formData = new FormData();
    formData.append("file", file);
    
    try {
      const res = await api.post("/ai/recognize-landmark", formData, {
        headers: {
          "Content-Type": "multipart/form-data",
        }
      });
      setResult(res.data.data);
    } catch (err) {
      console.error(err);
      setError("Failed to analyze the image. Please try again.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="max-w-4xl mx-auto px-6 py-12 min-h-screen">
      <div className="text-center mb-10">
        <h1 className="text-4xl font-extrabold text-gray-900 dark:text-white tracking-tight">AI Landmark Recognition</h1>
        <p className="text-gray-500 dark:text-slate-400 mt-3 text-lg">Upload a photo of a landmark and our AI will identify it for you.</p>
      </div>
      
      <div className="grid md:grid-cols-2 gap-8">
        {/* Upload Section */}
        <div className="bg-white dark:bg-slate-800 rounded-3xl shadow-xl dark:shadow-none border border-gray-100 dark:border-slate-700 p-8 flex flex-col items-center justify-center text-center">
          {!preview ? (
            <div 
              onDragOver={handleDragOver}
              onDrop={handleDrop}
              className="w-full border-2 border-dashed border-gray-300 dark:border-slate-600 rounded-2xl p-12 hover:bg-gray-50 dark:bg-slate-900/50 hover:border-brand-400 transition-colors cursor-pointer group"
              onClick={() => fileInputRef.current.click()}
            >
              <div className="text-5xl mb-4 group-hover:scale-110 transition-transform">📸</div>
              <h3 className="text-xl font-bold text-gray-800 dark:text-slate-100">Drag & Drop your photo</h3>
              <p className="text-gray-500 dark:text-slate-400 text-sm mt-2">or click to browse from your device</p>
              <input 
                type="file" 
                ref={fileInputRef}
                className="hidden" 
                accept="image/*"
                onChange={handleFileSelect}
              />
            </div>
          ) : (
            <div className="w-full relative rounded-2xl overflow-hidden group">
              <img src={preview} alt="Preview" className="w-full h-64 object-cover" />
              <div className="absolute inset-0 bg-black/40 opacity-0 group-hover:opacity-100 transition-opacity flex items-center justify-center backdrop-blur-sm">
                <button 
                  onClick={() => { setFile(null); setPreview(null); setResult(null); }}
                  className="bg-white dark:bg-slate-800 text-gray-900 dark:text-white px-4 py-2 rounded-full font-bold shadow-lg dark:shadow-none hover:scale-105 transition-transform"
                >
                  Change Image
                </button>
              </div>
            </div>
          )}

          {preview && (
            <button 
              onClick={handleAnalyze}
              disabled={loading}
              className="mt-6 w-full bg-brand-600 hover:bg-brand-700 text-white font-bold py-4 rounded-xl shadow-lg dark:shadow-none transition-all disabled:opacity-70 disabled:cursor-not-allowed flex items-center justify-center gap-2"
            >
              {loading ? (
                <>
                  <svg className="animate-spin h-5 w-5 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                  </svg>
                  Analyzing Image...
                </>
              ) : "✨ Identify Landmark"}
            </button>
          )}
        </div>

        {/* Results Section */}
        <div className="bg-white dark:bg-slate-800 rounded-3xl shadow-xl dark:shadow-none border border-gray-100 dark:border-slate-700 overflow-hidden flex flex-col">
          <div className="bg-gradient-to-r from-brand-800 to-brand-600 p-6 text-white">
            <h2 className="text-xl font-bold">Analysis Results</h2>
          </div>
          
          <div className="p-8 flex-1 flex flex-col items-center justify-center text-center relative">
            {loading ? (
              <div className="animate-pulse flex flex-col items-center">
                <div className="w-20 h-20 bg-gray-200 dark:bg-slate-700 rounded-full mb-4"></div>
                <div className="h-6 bg-gray-200 dark:bg-slate-700 rounded w-48 mb-2"></div>
                <div className="h-4 bg-gray-200 dark:bg-slate-700 rounded w-64"></div>
              </div>
            ) : result ? (
              result.is_landmark === false || result.confidence === "None" ? (
                <div className="w-full animate-slide-up text-center">
                  <div className="inline-block bg-amber-100 dark:bg-amber-900/40 text-amber-800 dark:text-amber-300 font-bold px-4 py-1.5 rounded-full text-xs mb-4">
                    No Recognizable Landmark
                  </div>
                  <h3 className="text-2xl font-bold text-gray-800 dark:text-white mb-3">{result.name || "Unrecognized Landmark"}</h3>
                  <p className="text-gray-600 dark:text-slate-300 leading-relaxed bg-gray-50 dark:bg-slate-900/50 p-4 rounded-xl border border-gray-100 dark:border-slate-700 text-sm">
                    {result.description}
                  </p>
                </div>
              ) : (
                <div className="w-full animate-slide-up">
                  <div className="flex flex-wrap items-center justify-center gap-2 mb-4">
                    <span className={`font-bold px-3 py-1 rounded-full text-xs ${
                      result.confidence === "High"
                        ? "bg-emerald-100 text-emerald-800 dark:bg-emerald-900/40 dark:text-emerald-300"
                        : "bg-amber-100 text-amber-800 dark:bg-amber-900/40 dark:text-amber-300"
                    }`}>
                      {result.confidence === "High" ? "✓ Verified Landmark (High Confidence)" : "⚠ Probable Match (Moderate Confidence)"}
                    </span>
                    {result.is_grounded && (
                      <span className="bg-blue-100 text-blue-800 dark:bg-blue-900/40 dark:text-blue-300 font-bold px-3 py-1 rounded-full text-xs">
                        TourMate Canonical POI
                      </span>
                    )}
                  </div>
                  <h3 className="text-2xl md:text-3xl font-extrabold text-gray-900 dark:text-white mb-2 text-center">{result.name}</h3>
                  {result.location && (
                    <p className="text-sm font-semibold text-brand-600 dark:text-brand-400 text-center mb-1">
                      📍 {result.location}
                    </p>
                  )}
                  {result.category && (
                    <p className="text-xs text-gray-500 dark:text-slate-400 text-center mb-4">
                      🏷️ {result.category}
                    </p>
                  )}
                  <p className="text-gray-600 dark:text-slate-300 leading-relaxed bg-gray-50 dark:bg-slate-900/50 p-4 rounded-xl border border-gray-100 dark:border-slate-700 text-left text-sm mb-4">
                    {result.description}
                  </p>
                  <div className="flex flex-wrap gap-3 justify-center">
                    <button
                      onClick={() => openGoogleMapsNavigation(result)}
                      className="px-4 py-2 bg-gray-900 dark:bg-white text-white dark:text-gray-900 font-bold rounded-xl text-xs flex items-center gap-2 hover:bg-gray-800 dark:hover:bg-gray-100 transition-colors cursor-pointer"
                    >
                      <Navigation className="w-3.5 h-3.5" /> Get Directions
                    </button>
                    {result.poi_id && (
                      <Link
                        to={`/places/${result.poi_id}`}
                        className="px-4 py-2 bg-brand-600 text-white font-bold rounded-xl text-xs flex items-center gap-2 hover:bg-brand-700 transition-colors"
                      >
                        Explore Attraction ↗
                      </Link>
                    )}
                  </div>
                </div>
              )
            ) : error ? (
              <div className="text-red-500">
                <div className="text-4xl mb-2">⚠️</div>
                <p className="font-semibold">{error}</p>
              </div>
            ) : (
              <div className="text-gray-400 space-y-3">
                <div className="text-6xl">🔍</div>
                <p>Upload an image to see the magic happen.</p>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
