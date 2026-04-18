import axios from "axios";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "https://fjiolla-graphshield.hf.space";

const api = axios.create({
  baseURL: API_BASE,
  timeout: 300000, // 5 min — ML endpoints (SHAP, graph traversal) can be slow on HF free tier
  headers: {
    Accept: "application/json",
  },
});

// Response interceptor for error normalization
api.interceptors.response.use(
  (response) => response,
  (error) => {
    const detail =
      error.response?.data?.detail ||
      error.message ||
      "An unexpected error occurred";
    return Promise.reject(new Error(detail));
  }
);

export default api;
