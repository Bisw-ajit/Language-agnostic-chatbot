import axios from 'axios';

const client = axios.create({
  baseURL: import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1',
});

// ── Helper: Normalized Error Extraction ─────────────────────────────────────
export function getErrorMessage(error, defaultMsg = 'An unexpected error occurred. Please try again.') {
  if (!error) return defaultMsg;
  // 1. Structured backend error schema: error.response.data.error.message
  if (error.response?.data?.error?.message) {
    return error.response.data.error.message;
  }
  // 2. Direct string detail
  if (typeof error.response?.data?.detail === 'string') {
    return error.response.data.detail;
  }
  // 3. FastAPI validation error list: [{ loc, msg, type }]
  if (Array.isArray(error.response?.data?.detail)) {
    return error.response.data.detail
      .map((d) => `${d.loc?.slice(-1)[0] || 'parameter'}: ${d.msg}`)
      .join(', ');
  }
  // 4. Fallback message keys
  if (error.response?.data?.message) {
    return error.response.data.message;
  }
  if (error.message) {
    return error.message;
  }
  return defaultMsg;
}

// ── Request Interceptor: Attach JWT and Tracing Headers ─────────────────────
client.interceptors.request.use((config) => {
  const token = localStorage.getItem('token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  config.headers['X-Client-Version'] = '2.0.0';
  return config;
});

// ── Response Interceptor: Handle 401 (token expired / invalid) ───────────────
client.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      // Clear stale credentials
      localStorage.removeItem('token');
      localStorage.removeItem('role');
      localStorage.removeItem('user');

      // Redirect to login unless already there (prevents redirect loops)
      if (window.location.pathname !== '/login') {
        window.location.href = '/login?reason=session_expired';
      }
    }
    return Promise.reject(error);
  }
);

export default client;
