import { useState, useRef } from "react";
import api from "../api/axios";

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
              <div className="w-full animate-slide-up">
                <div className="inline-block bg-green-100 text-green-700 font-bold px-4 py-1.5 rounded-full text-sm mb-4">
                  Match Found!
                </div>
                <h3 className="text-3xl font-extrabold text-gray-900 dark:text-white mb-4">{result.name}</h3>
                <p className="text-gray-600 dark:text-slate-300 leading-relaxed bg-gray-50 dark:bg-slate-900/50 p-4 rounded-xl border border-gray-100 dark:border-slate-700 text-left text-sm">
                  {result.description}
                </p>
              </div>
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
