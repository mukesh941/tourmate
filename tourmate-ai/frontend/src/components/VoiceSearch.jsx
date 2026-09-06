import React, { useState, useEffect } from 'react';
import { Mic, MicOff, Search } from 'lucide-react';
import { useNavigate } from 'react-router-dom';

const VoiceSearch = () => {
  const [isListening, setIsListening] = useState(false);
  const [transcript, setTranscript] = useState('');
  const [error, setError] = useState(null);
  const navigate = useNavigate();

  // Speech Recognition API
  const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
  const recognition = SpeechRecognition ? new SpeechRecognition() : null;

  useEffect(() => {
    if (!recognition) {
      setError("Your browser doesn't support speech recognition.");
      return;
    }

    recognition.continuous = false;
    recognition.interimResults = false;
    recognition.lang = 'en-US';

    recognition.onresult = (event) => {
      const current = event.resultIndex;
      const result = event.results[current][0].transcript;
      setTranscript(result);
      setIsListening(false);
      // Automatically search for the transcribed text
      if (result) {
        navigate(`/places?q=${encodeURIComponent(result)}`);
      }
    };

    recognition.onerror = (event) => {
      console.error(event.error);
      setError("Error recognizing speech.");
      setIsListening(false);
    };

    recognition.onend = () => {
      setIsListening(false);
    };
  }, [recognition, navigate]);

  const toggleListening = () => {
    if (isListening) {
      recognition.stop();
      setIsListening(false);
    } else {
      if (recognition) {
        recognition.start();
        setIsListening(true);
        setError(null);
        setTranscript('');
      }
    }
  };

  if (!recognition) return null;

  return (
    <div className="relative">
      <button 
        onClick={toggleListening}
        className={`flex items-center justify-center p-3.5 rounded-xl transition-all duration-300 ${
          isListening 
            ? 'bg-red-500 text-white shadow-lg animate-pulse' 
            : 'bg-white/10 hover:bg-white/20 text-white border border-white/20 backdrop-blur-sm'
        }`}
        title="Search by Voice"
      >
        {isListening ? <Mic className="w-5 h-5" /> : <MicOff className="w-5 h-5" />}
      </button>
      
      {transcript && !isListening && (
        <div className="absolute top-full mt-2 w-48 left-1/2 -translate-x-1/2 bg-white text-gray-800 text-sm p-2 rounded-lg shadow-lg z-50">
          <p className="font-bold flex items-center gap-1"><Search className="w-3 h-3" /> Searching:</p>
          <p className="italic text-gray-600 truncate">{transcript}</p>
        </div>
      )}
    </div>
  );
};

export default VoiceSearch;
