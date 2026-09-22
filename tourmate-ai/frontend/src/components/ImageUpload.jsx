import React, { useState, useRef } from 'react';
import { Camera, Upload, X, MapPin, Loader2 } from 'lucide-react';
import axios from 'axios';
import { useAuth } from '../context/AuthContext';
import { API_BASE_URL } from '../api/axios';

const ImageUpload = () => {
  const [isUploading, setIsUploading] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);
  const fileInputRef = useRef(null);
  const { token } = useAuth();

  const handleFileChange = async (e) => {
    const file = e.target.files[0];
    if (!file) return;

    // Reset state
    setResult(null);
    setError(null);
    setIsUploading(true);

    const formData = new FormData();
    formData.append('file', file);

    try {
      const res = await axios.post(`${API_BASE_URL}/ai/recognize-landmark`, formData, {
        headers: { 
          'Content-Type': 'multipart/form-data',
          Authorization: `Bearer ${token}`
        }
      });
      
      if (res.data.success) {
        setResult(res.data.data);
      } else {
        setError(res.data.error || "Could not recognize landmark.");
      }
    } catch (err) {
      console.error(err);
      setError("An error occurred while analyzing the image.");
    } finally {
      setIsUploading(false);
      // Reset file input
      if (fileInputRef.current) {
        fileInputRef.current.value = '';
      }
    }
  };

  const triggerUpload = () => {
    if (fileInputRef.current) {
      fileInputRef.current.click();
    }
  };

  return (
    <div className="relative">
      <input 
        type="file" 
        accept="image/*" 
        className="hidden" 
        ref={fileInputRef} 
        onChange={handleFileChange} 
      />
      
      <button 
        onClick={triggerUpload}
        disabled={isUploading}
        className="flex items-center justify-center p-3.5 bg-white/10 hover:bg-white/20 text-white border border-white/20 backdrop-blur-sm rounded-xl transition-all duration-300 disabled:opacity-50"
        title="Search by Image"
      >
        {isUploading ? <Loader2 className="w-5 h-5 animate-spin" /> : <Camera className="w-5 h-5" />}
      </button>

      {/* Result Popover */}
      {result && (
        <div className="absolute top-full mt-4 w-72 md:w-80 right-0 md:left-1/2 md:-translate-x-1/2 bg-white text-gray-800 p-5 rounded-2xl shadow-2xl z-50 animate-fade-in-up">
          <button 
            onClick={() => setResult(null)} 
            className="absolute top-3 right-3 text-gray-400 hover:text-gray-600"
          >
            <X className="w-5 h-5" />
          </button>
          
          <div className="flex items-center gap-2 mb-3 text-brand-600">
            <MapPin className="w-6 h-6" />
            <h3 className="font-display font-bold text-xl leading-tight">{result.name}</h3>
          </div>
          
          <p className="text-sm text-gray-600 leading-relaxed mb-4">
            {result.description}
          </p>
          
          <a 
            href={`/places?q=${encodeURIComponent(result.name)}`}
            className="block text-center bg-brand-50 text-brand-700 font-bold py-2 rounded-lg hover:bg-brand-100 transition-colors"
          >
            Find Places Here
          </a>
        </div>
      )}

      {/* Error Popover */}
      {error && (
        <div className="absolute top-full mt-4 w-64 left-1/2 -translate-x-1/2 bg-red-50 border border-red-200 text-red-700 p-4 rounded-xl shadow-lg z-50">
          <button 
            onClick={() => setError(null)} 
            className="absolute top-2 right-2 text-red-400 hover:text-red-600"
          >
            <X className="w-4 h-4" />
          </button>
          <p className="text-sm font-medium pr-4">{error}</p>
        </div>
      )}
    </div>
  );
};

export default ImageUpload;
