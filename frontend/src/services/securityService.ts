export interface Vulnerability {
  id: string;
  pkg: string;
  severity: string;
}

export interface ScanResponse {
  image: string;
  critical: number;
  high: number;
  details: Vulnerability[];
  status?: string;
}

import axios from 'axios';

const getBaseURL = () => import.meta.env.VITE_API_URL || 'http://localhost:8000';

export const triggerScan = async (image: string, token: string) => {
  const response = await axios.post(
    `${getBaseURL()}/api/security/scan`,
    { image },
    { 
      headers: { 
        Authorization: `Bearer ${token}`
      } 
    }
  );
  return response.data;
};