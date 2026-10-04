import { createContext, useContext, useEffect, useState } from "react";
import api from "../api/axios";

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  const getLocalUsers = () => {
    try {
      return JSON.parse(localStorage.getItem("tourmate_registered_users") || "[]");
    } catch {
      return [];
    }
  };

  const saveLocalUsers = (users) => {
    try {
      localStorage.setItem("tourmate_registered_users", JSON.stringify(users));
    } catch (e) {
      console.error("Failed to save local users:", e);
    }
  };

  const loadMe = async () => {
    const token = localStorage.getItem("access_token");
    if (!token) {
      setUser(null);
      setLoading(false);
      return;
    }

    // Try backend if reachable
    try {
      const { data } = await api.get("/auth/me");
      if (data?.data) {
        setUser(data.data);
        localStorage.setItem("tourmate_current_user", JSON.stringify(data.data));
        setLoading(false);
        return;
      }
    } catch {
      // Backend not running / offline - fallback to saved local session
    }

    const savedUserJson = localStorage.getItem("tourmate_current_user");
    if (savedUserJson) {
      try {
        setUser(JSON.parse(savedUserJson));
      } catch {
        setUser(null);
      }
    } else {
      setUser(null);
    }
    setLoading(false);
  };

  useEffect(() => {
    loadMe();
  }, []);

  const login = async (email, password) => {
    try {
      const { data } = await api.post("/auth/login", { email, password });
      if (data?.data?.access_token) {
        localStorage.setItem("access_token", data.data.access_token);
        if (data.data.refresh_token) {
          localStorage.setItem("refresh_token", data.data.refresh_token);
        }
        await loadMe();
        return;
      }
    } catch (apiErr) {
      // Check if user exists in local registered accounts
      const users = getLocalUsers();
      const existing = users.find((u) => u.email.toLowerCase() === email.toLowerCase());

      if (existing) {
        if (existing.password && existing.password !== password) {
          throw new Error("Invalid password. Please check your credentials.");
        }
        const sessionUser = {
          id: existing.id,
          name: existing.name,
          email: existing.email,
          role: existing.role || "user",
          preferred_language: existing.preferred_language || "en",
          is_verified: true,
        };
        const token = "local_token_" + btoa(email) + "_" + Date.now();
        localStorage.setItem("access_token", token);
        localStorage.setItem("tourmate_current_user", JSON.stringify(sessionUser));
        setUser(sessionUser);
        return;
      }

      // If backend network is offline/unreachable, create and log in as local user
      if (apiErr.code === "ERR_NETWORK" || !apiErr.response || apiErr.response?.status >= 500) {
        const newUser = {
          id: "usr_" + Math.random().toString(36).substring(2, 9),
          name: email.split("@")[0],
          email: email.toLowerCase(),
          password,
          role: email.toLowerCase().includes("admin") ? "admin" : "user",
          preferred_language: "en",
          is_verified: true,
        };
        users.push(newUser);
        saveLocalUsers(users);

        const sessionUser = {
          id: newUser.id,
          name: newUser.name,
          email: newUser.email,
          role: newUser.role,
          preferred_language: newUser.preferred_language,
          is_verified: true,
        };
        const token = "local_token_" + btoa(email) + "_" + Date.now();
        localStorage.setItem("access_token", token);
        localStorage.setItem("tourmate_current_user", JSON.stringify(sessionUser));
        setUser(sessionUser);
        return;
      }

      // Re-throw if backend provided an explicit business validation error
      throw apiErr;
    }
  };

  const register = async (name, email, password) => {
    try {
      await api.post("/auth/register", { name, email, password });
    } catch (apiErr) {
      // If backend is offline or network error, save user locally
      if (apiErr.code === "ERR_NETWORK" || !apiErr.response || apiErr.response?.status >= 500) {
        const users = getLocalUsers();
        if (users.some((u) => u.email.toLowerCase() === email.toLowerCase())) {
          throw new Error("An account with this email already exists.");
        }
        const newUser = {
          id: "usr_" + Math.random().toString(36).substring(2, 9),
          name: name || email.split("@")[0],
          email: email.toLowerCase(),
          password,
          role: email.toLowerCase().includes("admin") ? "admin" : "user",
          preferred_language: "en",
          is_verified: true,
        };
        users.push(newUser);
        saveLocalUsers(users);
        return;
      }
      throw apiErr;
    }
  };

  const logout = () => {
    localStorage.removeItem("access_token");
    localStorage.removeItem("refresh_token");
    localStorage.removeItem("tourmate_current_user");
    setUser(null);
  };

  const token = localStorage.getItem("access_token");

  return (
    <AuthContext.Provider value={{ user, loading, token, login, register, logout }}>
      {children}
    </AuthContext.Provider>
  );
}

export const useAuth = () => useContext(AuthContext);
