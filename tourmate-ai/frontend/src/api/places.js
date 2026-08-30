import api from "./axios";

export const getDestinations = async () => (await api.get("/destinations")).data.data;
export const getDestination = async (id) => (await api.get(`/destinations/${id}`)).data.data;
export const getCategories = async () => (await api.get("/categories")).data.data;
export const getPlaces = async (params = {}) => {
  const query = new URLSearchParams();
  if (params.destination_id) query.append("destination_id", params.destination_id);
  if (params.category_id) query.append("category_id", params.category_id);
  if (params.q) query.append("q", params.q);
  if (params.min_rating) query.append("min_rating", params.min_rating);
  if (params.lat) query.append("lat", params.lat);
  if (params.lng) query.append("lng", params.lng);
  if (params.radius_km) query.append("radius_km", params.radius_km);
  return (await api.get(`/places?${query.toString()}`)).data.data;
};
export const getPlace = async (id) => (await api.get(`/places/${id}`)).data.data;
