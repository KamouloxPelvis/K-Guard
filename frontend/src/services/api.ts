// frontend/src/services/api.ts
import axios from 'axios';

// On récupère l'URL injectée par le deploy.sh (ex: http://IP/k-guard)
const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL
});

// --- INTERCEPTEUR DE REQUÊTE ---
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('user_token');
    if (token) {
      // Aligné sur le backend FastAPI (OAuth2)
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

// --- INTERCEPTEUR DE RÉPONSE ---
api.interceptors.response.use(
  (response) => response,
  (error) => {
    // Si le backend renvoie 401 (Token expiré ou invalide)
    if (error.response && error.response.status === 401) {
      console.warn("🔒 Session invalide ou expirée, redirection...");
      localStorage.removeItem('user_token');
      
      // On redirige vers /k-guard/login pour matcher avec l'Ingress
      // Note: On utilise window.location pour un "hard reset" de l'état
      if (!window.location.pathname.endsWith('/login')) {
        window.location.href = '/k-guard/login';
      }
    }
    return Promise.reject(error);
  }
);

export default api;