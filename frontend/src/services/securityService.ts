import api from './api';

/**
 * Déclenche un scan de vulnérabilité Trivy via le backend K-Guard.
 * L'instance 'api' injecte déjà le token et gère le préfixe /k-guard/api.
 */
export const triggerScan = async (image: string) => {
  try {
    // La route correcte est maintenant /scan/scan suite à nos modifs backend
    const { data } = await api.post('/scan/scan', { image });
    return data;
  } catch (error: any) {
    console.error("🚨 K-Guard Scan Error:", error.response?.data || error.message);
    return { 
      status: 'error', 
      message: error.response?.data?.detail || error.message 
    };
  }
};