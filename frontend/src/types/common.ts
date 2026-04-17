/** Common types used across the app */

export interface ApiError {
  detail: string;
  status_code?: number;
}

export interface HealthResponse {
  message: string;
}
