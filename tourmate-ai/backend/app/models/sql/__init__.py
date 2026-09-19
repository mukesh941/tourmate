"""
TourMate AI PostgreSQL Domain Models.
Exports all 23 core domain models and Declarative Base for Alembic migrations.
"""
from app.models.sql.base import Base, UUIDPrimaryKeyMixin, TimestampMixin
from app.models.sql.user import User, UserInterest, Preference
from app.models.sql.category import Category
from app.models.sql.location import Location
from app.models.sql.poi import POI, OpeningHours
from app.models.sql.knowledge import KnowledgeChunk
from app.models.sql.accommodation import Accommodation
from app.models.sql.transport import TransportOption
from app.models.sql.trip import Trip, TripAccommodation, TripTransport, POICluster
from app.models.sql.itinerary import Itinerary, ItineraryStop, Route, AlternativeRoute
from app.models.sql.media import Image, POIImage, AccommodationImage
from app.models.sql.interaction import Feedback, Offer

__all__ = [
    "Base",
    "UUIDPrimaryKeyMixin",
    "TimestampMixin",
    # 1. users
    "User",
    # 2. categories
    "Category",
    # 3. user_interests
    "UserInterest",
    # 4. preferences
    "Preference",
    # 5. locations
    "Location",
    # 6. pois
    "POI",
    # 7. opening_hours
    "OpeningHours",
    # 8. knowledge_chunks
    "KnowledgeChunk",
    # 9. accommodations
    "Accommodation",
    # 10. transport_options
    "TransportOption",
    # 11. trips
    "Trip",
    # 12. trip_accommodations
    "TripAccommodation",
    # 13. trip_transports
    "TripTransport",
    # 14. poi_clusters
    "POICluster",
    # 15. itineraries
    "Itinerary",
    # 16. itinerary_stops
    "ItineraryStop",
    # 17. routes
    "Route",
    # 18. alternative_routes
    "AlternativeRoute",
    # 19. images
    "Image",
    # 20. poi_images
    "POIImage",
    # 21. accommodation_images
    "AccommodationImage",
    # 22. feedback
    "Feedback",
    # 23. offers
    "Offer",
]
