import api from "./axios";

export const createDestination = async (data) => (await api.post("/destinations", data)).data.data;
export const updateDestination = async (id, data) => (await api.put(`/destinations/${id}`, data)).data.data;
export const deleteDestination = async (id) => (await api.delete(`/destinations/${id}`)).data.data;

export const createCategory = async (data) => (await api.post("/categories", data)).data.data;
export const updateCategory = async (id, data) => (await api.put(`/categories/${id}`, data)).data.data;
export const deleteCategory = async (id) => (await api.delete(`/categories/${id}`)).data.data;

export const createPlace = async (data) => (await api.post("/places", data)).data.data;
export const updatePlace = async (id, data) => (await api.put(`/places/${id}`, data)).data.data;
export const deletePlace = async (id) => (await api.delete(`/places/${id}`)).data.data;
