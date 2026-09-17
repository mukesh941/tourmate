import numpy as np
from sklearn.cluster import KMeans
from app.schemas.place import TouristPlaceResponse

async def generate_place_clusters(places: list[TouristPlaceResponse], k: int) -> dict:
    if not places:
        return {"k": 0, "centroids": [], "clusters": [], "skipped": 0}
        
    valid_places = []
    coords = []
    skipped = 0
    
    for place in places:
        if place.location and place.location.coordinates and len(place.location.coordinates) >= 2:
            lng, lat = place.location.coordinates[0], place.location.coordinates[1]
            if -90 <= lat <= 90 and -180 <= lng <= 180:
                valid_places.append(place)
                coords.append([lat, lng])
            else:
                skipped += 1
        else:
            skipped += 1

    if not valid_places:
        return {"k": 0, "centroids": [], "clusters": [], "skipped": skipped}

    if len(valid_places) < k:
        k = len(valid_places)
        
    # If 1 valid place, handle without KMeans
    if k <= 1:
        return {
            "k": 1,
            "centroids": [coords[0]],
            "clusters": [{
                "cluster_id": 0,
                "centroid": coords[0],
                "places": valid_places
            }],
            "skipped": skipped
        }

    X = np.array(coords)
    
    # Run K-Means
    kmeans = KMeans(n_clusters=k, random_state=42, n_init=10)
    labels = kmeans.fit_predict(X)
    centroids = kmeans.cluster_centers_.tolist()
    
    # Group places by cluster
    clusters = []
    for i in range(k):
        clusters.append({
            "cluster_id": i,
            "centroid": centroids[i], # [lat, lng]
            "places": []
        })
        
    for place, label in zip(valid_places, labels):
        clusters[label]["places"].append(place)
        
    return {
        "k": k,
        "centroids": centroids,
        "clusters": clusters,
        "skipped": skipped
    }

from sklearn.neighbors import NearestNeighbors

async def get_knn_recommendations(places: list[TouristPlaceResponse], user_interests: list[str], k: int = 10) -> list[TouristPlaceResponse]:
    if not places:
        return []
    
    if len(places) < k:
        k = len(places)

    features = ["history", "nature", "culture", "adventure", "food", "shopping", "architecture"]
    
    # Build place vectors
    X = []
    for p in places:
        scores = p.feature_scores
        X.append([
            scores.history,
            scores.nature,
            scores.culture,
            scores.adventure,
            scores.food,
            scores.shopping,
            scores.architecture
        ])
        
    X = np.array(X)
    
    # Build user vector
    user_vec = []
    for f in features:
        if f in user_interests:
            user_vec.append(10.0) # High weight for interested feature
        else:
            user_vec.append(0.0)
            
    user_vec = np.array([user_vec])
    
    # Use KNN to find closest places based on cosine similarity
    # Cosine is good for feature vectors to measure angle/alignment rather than pure magnitude
    knn = NearestNeighbors(n_neighbors=k, metric='cosine')
    
    # Handle edge case where all vectors might be 0
    if not X.any():
        return places[:k]
        
    knn.fit(X)
    
    distances, indices = knn.kneighbors(user_vec)
    
    recommended_places = []
    for idx in indices[0]:
        recommended_places.append(places[idx])
        
    return recommended_places

from app.services.route_service import astar_route_optimization

async def astar_optimize_route(places: list[TouristPlaceResponse]) -> dict:
    """
    Exposes A* Pathfinding route optimization algorithm for VTU ML synopsis requirements.
    Calculates shortest path between attractions considering travel time and distance.
    """
    return astar_route_optimization(places)
