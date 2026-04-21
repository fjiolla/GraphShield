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
    let detail = "An unexpected error occurred";
    
    if (error.response?.data) {
      const data = error.response.data;
      if (Array.isArray(data.detail)) {
        interface ValidationError { loc?: string[]; msg?: string }
        detail = data.detail.map((err: ValidationError) => `${err.loc?.join(".")}: ${err.msg}`).join(", ");
      } else if (typeof data.detail === "string") {
        detail = data.detail;
      } else if (Array.isArray(data.errors) && data.errors.length > 0) {
        detail = data.errors.join(", ");
      } else if (error.message) {
        detail = error.message;
      }
    } else if (error.message) {
      detail = error.message;
    }
    
    return Promise.reject(new Error(detail));
  }
);

export default api;
