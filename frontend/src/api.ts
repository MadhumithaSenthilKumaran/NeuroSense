import axios from "axios";

const API_BASE = import.meta.env.VITE_API_BASE || "http://localhost:5000/api";

const api = axios.create({
  baseURL: API_BASE,
  withCredentials: true,
});

api.interceptors.response.use(
  response => response,
  error => {
    const message = error?.response?.data?.msg || error?.response?.data?.error;
    if (error?.response?.status === 422 && message === 'Signature verification failed') {
      localStorage.removeItem('ns_token');
      delete api.defaults.headers.common['Authorization'];
      window.location.assign('/login');
    }
    return Promise.reject(error);
  },
);

export function setAuthToken(token: string | null) {
  if (token) {
    api.defaults.headers.common["Authorization"] = `Bearer ${token}`;
  } else {
    delete api.defaults.headers.common["Authorization"];
  }
}

export default api;
