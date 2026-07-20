import axios from "axios";

import { toApiError } from "./apiError";
import { clearStoredToken, getStoredToken } from "../utils/tokenStorage";

const apiBaseUrl =
  import.meta.env.DEV && import.meta.env.VITE_API_BASE_URL
    ? "/__api"
    : import.meta.env.VITE_API_BASE_URL ?? "";
const publicAuthPaths = ["/login", "/register"];

export const apiClient = axios.create({
  baseURL: apiBaseUrl,
  headers: {
    "Content-Type": "application/json"
  }
});

apiClient.interceptors.request.use((config) => {
  const token = getStoredToken();

  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }

  return config;
});

apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    const apiError = toApiError(error);

    if (apiError.status === 401) {
      clearStoredToken();
      window.dispatchEvent(new Event("marketmind:auth-expired"));

      if (!publicAuthPaths.includes(window.location.pathname)) {
        window.location.assign("/login");
      }
    }

    return Promise.reject(apiError);
  }
);
