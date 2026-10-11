import api from "./axios";

export const getDestinations = async (params = {}) => {
  const query = new URLSearchParams();
  if (params.page) query.append("page", params.page);
  if (params.page_size) query.append("page_size", params.page_size);
  if (params.search) query.append("search", params.search);
  const response = await api.get(`/destinations?${query.toString()}`);
  return response.data.data.results || response.data.data;
};

export const getDestinationsPaginated = async (params = {}) => {
  const query = new URLSearchParams();
  if (params.page) query.append("page", params.page);
  if (params.page_size) query.append("page_size", params.page_size);
  if (params.search) query.append("search", params.search);
  const response = await api.get(`/destinations?${query.toString()}`);
  return response.data.data;
};
export const getDestination = async (id) => (await api.get(`/destinations/${id}`)).data.data;
export const getCategories = async () => (await api.get("/categories")).data.data;
export const getPlaces = async (params = {}, config = {}) => {
  const query = new URLSearchParams();
  if (params.destination_id) query.append("destination_id", params.destination_id);
  if (params.destination) query.append("destination", params.destination);
  if (params.category_id) query.append("category_id", params.category_id);
  if (params.category) query.append("category", params.category);
  if (params.q) query.append("q", params.q);
  if (params.min_rating) query.append("min_rating", params.min_rating);
  if (params.lat) query.append("lat", params.lat);
  if (params.lng) query.append("lng", params.lng);
  if (params.radius_km) query.append("radius_km", params.radius_km);
  return (await api.get(`/places?${query.toString()}`, config)).data.data;
};
export const getPlace = async (id, config = {}) => (await api.get(`/places/${id}`, config)).data.data;
