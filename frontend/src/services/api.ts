import axios from 'axios';

const api = axios.create({
  baseURL: 'http://113.30.191.17/k-guard' 
});

// 1. INTERCEPTEUR DE REQUÊTE
// Injecte le token automatiquement dans chaque appel
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('user_token'); // On utilise la bonne clé
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// 2. INTERCEPTEUR DE RÉPONSE
// Gère l'expiration de session
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response && error.response.status === 401) {
      console.warn("Session expirée, déconnexion...");
      localStorage.removeItem('user_token'); // On nettoie la bonne clé
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);

export default api;