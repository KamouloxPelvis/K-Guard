import axios from 'axios';

const API_BASE = '/k-guard/api';

export const triggerScan = async (image: string, token: string) => {
  try {
    const response = await axios.post(
      `${API_BASE}/security/scan`,
      { image },
      { 
        headers: { 
          Authorization: `Bearer ${token}`
        } 
      }
    );
    return response.data;
  } catch (error: any) {
    console.error("🚨 Scan API Error:", error.response?.data || error.message);
    return { status: 'error', message: error.message };
  }
};