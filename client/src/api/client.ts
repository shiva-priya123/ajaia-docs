import axios from 'axios';
import { TOKEN_KEY } from '../utils/constants';

// Same-origin '/api' works in dev (Vite proxy) and in production (FastAPI serves the SPA).
const client = axios.create({
  baseURL: import.meta.env.VITE_API_URL || '/api',
  timeout: 20_000,
});

client.interceptors.request.use((config) => {
  const token = localStorage.getItem(TOKEN_KEY);
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

client.interceptors.response.use(
  (response) => response,
  (error) => {
    const isLoginCall = axios.isAxiosError(error) && error.config?.url?.includes('/auth/login');
    // An expired/invalid session anywhere except the login form itself:
    // drop the token and send the user back to sign in.
    if (axios.isAxiosError(error) && error.response?.status === 401 && !isLoginCall) {
      localStorage.removeItem(TOKEN_KEY);
      if (!window.location.pathname.startsWith('/login')) {
        window.location.assign('/login?expired=1');
      }
    }
    return Promise.reject(error);
  },
);

export default client;
