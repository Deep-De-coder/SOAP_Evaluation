// API configuration
// In Docker, this will be set via environment variable
// In development, defaults to localhost:8000
export const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || import.meta.env.API_BASE_URL || 'http://localhost:8000';

