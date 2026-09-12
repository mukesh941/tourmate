import { useState, useEffect } from "react";
import { useParams, Link } from "react-router-dom";
import { getPlaces, getCategories, getDestinations } from "../api/places";

const HERO_IMAGES = {
  nature: "https://images.unsplash.com/photo-1501854140801-50d01698950b?ixlib=rb-4.0.3&auto=format&fit=crop&w=2070&q=80",
  history: "https://images.unsplash.com/photo-1599661046289-e31897846e41?ixlib=rb-4.0.3&auto=format&fit=crop&w=2070&q=80", 
  culture: "https://images.unsplash.com/photo-1561361513-2d000a50f0dc?ixlib=rb-4.0.3&auto=format&fit=crop&w=2076&q=80",
  adventure: "https://images.unsplash.com/photo-1533692328991-08159ff19fca?ixlib=rb-4.0.3&auto=format&fit=crop&w=2069&q=80",
  food: "https://images.unsplash.com/photo-1504674900247-0877df9cc836?ixlib=rb-4.0.3&auto=format&fit=crop&w=2070&q=80",
  shopping: "https://images.unsplash.com/photo-1542051812871-700940331006?ixlib=rb-4.0.3&auto=format&fit=crop&w=2070&q=80",
  architecture: "https://images.unsplash.com/photo-1564507592333-c60657eea523?ixlib=rb-4.0.3&auto=format&fit=crop&w=2071&q=80", 
  default: "https://images.unsplash.com/photo-1469854523086-cc02fe5d8800?ixlib=rb-4.0.3&auto=format&fit=crop&w=2021&q=80"
};

const CATEGORY_DESCRIPTIONS = {
  nature: "Discover the breathtaking landscapes, serene backwaters, and majestic mountains.",
  history: "Step back in time and explore ancient ruins, majestic forts, and historical monuments.",
  culture: "Immerse yourself in rich traditions, vibrant festivals, and local artistry.",
  adventure: "Experience the thrill of a lifetime with exciting outdoor activities.",
  food: "Savor the authentic flavors and culinary masterpieces from around the world.",
  shopping: "Explore bustling markets and modern malls for the perfect souvenir.",
  architecture: "Marvel at stunning structures and architectural wonders."
};

export default function CategoryPage() {
  const { categoryName } = useParams();
  const [places, setPlaces] = useState([]);
  const [destinations, setDestinations] = useState([]);
  const [loading, setLoading] = useState(true);

  const normalizedCategory = categoryName?.toLowerCase() || "";
  
  useEffect(() => {
    const fetchData = async () => {
      setLoading(true);
      try {
        const dests = await getDestinations();
        setDestinations(dests);

        const cats = await getCategories();
        const matchedCat = cats.find(c => c.name.toLowerCase() === normalizedCategory);
        
        let fetchedPlaces = [];
        if (matchedCat) {
          fetchedPlaces = await getPlaces({ category_id: matchedCat.id });
        } else {
          fetchedPlaces = await getPlaces({ q: categoryName });
        }
        
        // Prioritize places in India
        const indiaDestIds = dests.filter(d => d.country === 'India').map(d => d.id);
        const indianPlaces = fetchedPlaces.filter(p => indiaDestIds.includes(p.destination_id));
        
        if (indianPlaces.length > 0) {
          setPlaces(indianPlaces);
        } else {
          setPlaces(fetchedPlaces);
        }
        
      } catch (error) {
        console.error("Error fetching category places:", error);
      } finally {
        setLoading(false);
      }
    };
    
    fetchData();
  }, [categoryName, normalizedCategory]);

  const heroImage = HERO_IMAGES[normalizedCategory] || HERO_IMAGES.default;
  const description = CATEGORY_DESCRIPTIONS[normalizedCategory] || "Explore amazing places curated just for you.";
  
  return (
    <div className="min-h-screen bg-gray-50 dark:bg-[#0f172a]">
      {/* Dynamic Hero Section */}
      <div className="relative h-[400px] md:h-[500px] flex items-center justify-center overflow-hidden">
        <div className="absolute inset-0 z-0">
          <img 
            src={heroImage} 
            alt={categoryName} 
            className="w-full h-full object-cover transform scale-105 animate-slow-zoom"
          />
          <div className="absolute inset-0 bg-black/50 backdrop-blur-[2px]"></div>
        </div>
        
        <div className="relative z-10 text-center px-4 max-w-4xl mx-auto animate-fade-in-up">
          <span className="text-brand-300 font-bold tracking-[0.2em] uppercase text-sm mb-4 block">Curated Collection</span>
          <h1 className="text-5xl md:text-7xl font-display font-black text-white capitalize drop-shadow-lg mb-6">
            {categoryName} Places
          </h1>
          <p className="text-lg md:text-xl text-gray-200 font-light max-w-2xl mx-auto drop-shadow-md">
            {description}
          </p>
        </div>
      </div>
      
      {/* Places Grid */}
      <div className="max-w-7xl mx-auto px-6 py-16">
        <div className="flex justify-between items-end mb-8">
          <h2 className="text-3xl font-display font-bold text-gray-900 dark:text-white capitalize">
            Top {categoryName} Destinations
          </h2>
          <span className="text-gray-500 dark:text-gray-400 font-medium">{places.length} places found</span>
        </div>
        
        {loading ? (
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
            {[1, 2, 3, 4, 5, 6, 7, 8].map(i => (
              <div key={i} className="animate-pulse bg-white dark:bg-slate-800 rounded-2xl h-80 shadow-sm border border-gray-100 dark:border-slate-700"></div>
            ))}
          </div>
        ) : places.length > 0 ? (
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
            {places.map(place => (
              <Link to={`/places/${place.id}`} key={place.id} className="group bg-white dark:bg-slate-800 rounded-2xl overflow-hidden shadow-sm hover:shadow-xl hover:-translate-y-1 transition-all duration-300 flex flex-col h-full border border-gray-200 dark:border-slate-700">
                <div className="relative h-56 overflow-hidden bg-gray-200 dark:bg-slate-700">
                  <img 
                    src={place.images?.[0] || HERO_IMAGES[normalizedCategory] || HERO_IMAGES.default} 
                    alt={place.name} 
                    className="w-full h-full object-cover group-hover:scale-110 transition duration-700 ease-out"
                    onError={(e) => {
                      e.target.src = HERO_IMAGES[normalizedCategory] || HERO_IMAGES.default;
                    }}
                  />
                  <div className="absolute top-3 right-3 bg-white/90 backdrop-blur-md px-2 py-1 rounded-lg text-xs font-bold text-gray-900 shadow-sm">
                    ⭐ {place.rating?.toFixed(1) || "0.0"}
                  </div>
                </div>
                
                <div className="p-5 flex flex-col flex-1">
                  <h3 className="font-bold font-display text-xl text-gray-900 dark:text-white group-hover:text-brand-600 transition-colors duration-300 line-clamp-1 mb-1">{place.name}</h3>
                  <p className="text-xs text-brand-600 dark:text-brand-400 font-bold uppercase tracking-wider mb-3">
                    📍 {destinations.find(d => d.id === place.destination_id)?.name || 'Unknown Location'}
                  </p>
                  <p className="text-sm text-gray-600 dark:text-slate-300 line-clamp-2 mb-4 flex-1">{place.description}</p>
                  
                  <div className="flex justify-between items-center mt-auto pt-4 border-t border-gray-100 dark:border-slate-700">
                     <span className="text-brand-600 font-medium text-sm">View Details &rarr;</span>
                     <div className="flex items-center gap-2">
                       <a
                         href={`https://www.google.com/maps/search/?api=1&query=${encodeURIComponent(place.name)}`}
                         target="_blank"
                         rel="noopener noreferrer"
                         onClick={e => e.stopPropagation()}
                         className="text-xs bg-blue-50 dark:bg-blue-900/30 text-blue-600 dark:text-blue-400 font-bold px-2 py-1 rounded-lg hover:bg-blue-100 dark:hover:bg-blue-900/50 transition-colors border border-blue-200 dark:border-blue-800"
                       >
                         📍 Maps
                       </a>
                       <span className="text-gray-400 tracking-widest font-bold bg-gray-100 dark:bg-slate-700 px-2 py-1 rounded-md text-xs">{'💵'.repeat(place.price_level || 1)}</span>
                     </div>
                  </div>
                </div>
              </Link>
            ))}
          </div>
        ) : (
          <div className="flex flex-col items-center justify-center py-20 bg-white dark:bg-slate-800 border border-gray-200 dark:border-slate-700 rounded-3xl shadow-sm text-center">
            <div className="text-5xl mb-4">🌍</div>
            <h3 className="text-2xl font-display font-bold text-gray-800 dark:text-slate-100 mb-2">No {categoryName} places found</h3>
            <p className="text-gray-500 dark:text-slate-400 mb-6">We're still adding more amazing locations to this category.</p>
            <Link to="/places" className="bg-brand-600 hover:bg-brand-700 text-white font-bold px-6 py-3 rounded-xl transition-all">
              Explore All Places
            </Link>
          </div>
        )}
      </div>
    </div>
  );
}
