/**
 * Single Axios instance. Attaches the JWT access token to every request
 * and redirects to /login on a 401 (expired/invalid token).
 */
import axios from "axios";

const rawBase =
  import.meta.env.VITE_API_BASE_URL ||
  (import.meta.env.PROD
    ? "https://tourmate-backend-cfcv.onrender.com/api"
    : "http://localhost:8000/api");

export const API_BASE_URL = rawBase.trim().replace(/\/+$/, "").replace(/(?<!\/api)$/, "/api");

const api = axios.create({
  baseURL: API_BASE_URL,
});

api.interceptors.request.use((config) => {
  const token = localStorage.getItem("access_token");
  if (token) config.headers.Authorization = `Bearer ${token}`;
  return config;
});

api.interceptors.response.use(
  (res) => res,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem("access_token");
      localStorage.removeItem("refresh_token");
      if (window.location.pathname !== "/login") {
        window.location.href = "/login";
      }
    }
    return Promise.reject(error);
  }
);

export default api;
