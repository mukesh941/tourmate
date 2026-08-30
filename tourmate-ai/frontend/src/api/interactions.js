import api from "./axios";

export const toggleFavorite = async (placeId) => {
  const res = await api.post(`/interactions/favorites/${placeId}`);
  return res.data;
};

export const getFavorites = async () => {
  const res = await api.get("/interactions/favorites");
  return res.data.data; // array of places
};

export const addReview = async (placeId, review) => {
  const res = await api.post(`/interactions/reviews/${placeId}`, review);
  return res.data;
};

export const getReviews = async (placeId) => {
  const res = await api.get(`/interactions/reviews/${placeId}`);
  return res.data.data;
};
