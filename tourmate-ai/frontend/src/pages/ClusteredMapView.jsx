import { useState, useEffect } from "react";
import axios from "axios";
import { useAuth } from "../context/AuthContext";
import { MapContainer, TileLayer, Marker, Popup, CircleMarker, useMap } from "react-leaflet";
import "leaflet/dist/leaflet.css";

function ChangeView({ center, zoom }) {
  const map = useMap();
  map.setView(center, zoom);
  return null;
}

export default function ClusteredMapView() {
  const { token } = useAuth();
  const [k, setK] = useState(3);
  const [clustersData, setClustersData] = useState(null);
  const [loading, setLoading] = useState(true);

  // Distinct colors for clusters
  const clusterColors = ["#ef4444", "#3b82f6", "#10b981", "#f59e0b", "#8b5cf6", "#ec4899", "#14b8a6", "#f97316"];

  useEffect(() => {
    const fetchClusters = async () => {
      setLoading(true);
      try {
        const res = await axios.get(`${import.meta.env.VITE_API_BASE_URL}/places/clusters?k=${k}`, {
          headers: { Authorization: `Bearer ${token}` }
        });
        setClustersData(res.data.data);
      } catch (err) {
        console.error("Failed to fetch clusters:", err);
      } finally {
        setLoading(false);
      }
    };

    if (token) {
      fetchClusters();
    }
  }, [k, token]);

  const defaultCenter = [20.5937, 78.9629]; // Default to India roughly
  
  // Calculate center of map based on centroids if available
  const mapCenter = clustersData && clustersData.centroids && clustersData.centroids.length > 0 
    ? clustersData.centroids[0] 
    : defaultCenter;

  return (
    <div className="flex flex-col h-[calc(100vh-64px)]">
      {/* Header bar */}
      <div className="bg-white dark:bg-slate-800 border-b px-6 py-4 flex flex-col sm:flex-row justify-between items-center z-10 shadow-sm dark:shadow-none">
        <div>
          <h1 className="text-xl font-bold text-gray-800 dark:text-slate-100">AI Cluster Map</h1>
          <p className="text-sm text-gray-500 dark:text-slate-400">Group nearby places to plan focused area visits</p>
        </div>
        
        <div className="flex items-center gap-4 mt-4 sm:mt-0">
          <label className="text-sm font-medium text-gray-700 dark:text-slate-200 whitespace-nowrap">
            Number of Clusters (K): <span className="font-bold text-brand-600">{k}</span>
          </label>
          <input 
            type="range" 
            min="2" 
            max="8" 
            value={k} 
            onChange={(e) => setK(parseInt(e.target.value))}
            className="w-32 sm:w-48 accent-brand-600"
          />
        </div>
      </div>

      {/* Main Content */}
      <div className="flex flex-1 overflow-hidden relative">
        {/* Map Area */}
        <div className="flex-1 bg-gray-100 dark:bg-slate-800/80 relative z-0">
          {loading && (
            <div className="absolute inset-0 bg-white dark:bg-slate-800/50 backdrop-blur-sm z-[400] flex items-center justify-center">
              <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-brand-600"></div>
            </div>
          )}
          
          <MapContainer center={mapCenter} zoom={5} style={{ height: "100%", width: "100%" }}>
            <ChangeView center={mapCenter} zoom={5} />
            <TileLayer
              attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
              url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
            />
            
            {clustersData && clustersData.clusters.map((cluster, idx) => {
              const color = clusterColors[idx % clusterColors.length];
              
              return (
                <div key={`cluster-group-${idx}`}>
                  {/* Centroid Marker */}
                  <CircleMarker 
                    center={cluster.centroid} 
                    radius={15} 
                    pathOptions={{ color: 'black', fillColor: color, fillOpacity: 0.8, weight: 2 }}
                  >
                    <Popup>
                      <div className="font-bold text-center">Cluster {idx + 1} Center</div>
                      <div className="text-xs text-center">{cluster.places.length} places nearby</div>
                    </Popup>
                  </CircleMarker>
                  
                  {/* Place Markers */}
                  {cluster.places.map(place => {
                    if (!place.location || !place.location.coordinates) return null;
                    const pos = [place.location.coordinates[1], place.location.coordinates[0]];
                    return (
                      <CircleMarker 
                        key={place.id}
                        center={pos} 
                        radius={6} 
                        pathOptions={{ color: 'white', fillColor: color, fillOpacity: 1, weight: 1.5 }}
                      >
                        <Popup>
                          <div>
                            <h3 className="font-bold">{place.name}</h3>
                            <p className="text-xs text-gray-500 dark:text-slate-400 line-clamp-1">{place.description}</p>
                            <span className="text-[10px] bg-gray-100 dark:bg-slate-800/80 px-1 py-0.5 rounded mt-1 inline-block border">
                              Cluster {idx + 1}
                            </span>
                          </div>
                        </Popup>
                      </CircleMarker>
                    );
                  })}
                </div>
              );
            })}
          </MapContainer>
        </div>

        {/* Sidebar Summary */}
        <div className="w-80 bg-white dark:bg-slate-800 border-l shadow-xl dark:shadow-none overflow-y-auto z-10 hidden lg:block">
          <div className="p-4 border-b bg-gray-50 dark:bg-slate-900/50 sticky top-0">
            <h2 className="font-bold text-gray-800 dark:text-slate-100 flex items-center gap-2">
              <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5 text-brand-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
              </svg>
              Cluster Summary
            </h2>
          </div>
          
          <div className="p-4 space-y-6">
            {!clustersData ? (
              <div className="text-center text-sm text-gray-500 dark:text-slate-400 mt-10">Loading clustering data...</div>
            ) : clustersData.clusters.length === 0 ? (
              <div className="text-center text-sm text-gray-500 dark:text-slate-400 mt-10">No places to cluster.</div>
            ) : (
              clustersData.clusters.map((cluster, idx) => (
                <div key={idx} className="border border-gray-100 dark:border-slate-700 rounded-xl overflow-hidden shadow-sm dark:shadow-none">
                  <div 
                    className="px-3 py-2 text-white font-semibold text-sm flex justify-between"
                    style={{ backgroundColor: clusterColors[idx % clusterColors.length] }}
                  >
                    <span>Cluster {idx + 1}</span>
                    <span className="bg-white dark:bg-slate-800/30 px-2 rounded-full text-xs">{cluster.places.length}</span>
                  </div>
                  <div className="bg-white dark:bg-slate-800 divide-y divide-gray-50 max-h-48 overflow-y-auto">
                    {cluster.places.map(p => (
                      <div key={p.id} className="p-2 text-sm hover:bg-gray-50 dark:bg-slate-900/50 cursor-default">
                        <div className="font-medium text-gray-800 dark:text-slate-100 truncate">{p.name}</div>
                        <div className="text-xs text-gray-500 dark:text-slate-400">⭐ {p.rating}</div>
                      </div>
                    ))}
                    {cluster.places.length === 0 && (
                      <div className="p-3 text-xs text-gray-400 italic text-center">Empty cluster</div>
                    )}
                  </div>
                </div>
              ))
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
