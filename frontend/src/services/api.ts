import {
  demoSystemInfo,
  demoNodeCapacity,
  demoClusterStatus,
  demoPodMetrics,
  demoPodLogs,
  demoSecurityAlerts,
  demoWazuhOverview,
  demoWazuhAlerts,
  demoSentinelMap,
  demoSentinelStatus,
  demoHardeningPlan,
  demoSettingsData
} from '@/mock/demoData';

const BASE_URL = '/api';

export const isDemoMode = (() => {
  if (typeof window === 'undefined') return false;
  return (
    import.meta.env.VITE_DEMO_MODE === 'true' ||
    window.location.hostname.includes('k-guard') ||
    window.location.hostname.includes('demo') ||
    window.location.search.includes('demo=true')
  );
})();

// Auto-initialize demo credentials in local storage if in demo mode
if (isDemoMode && typeof window !== 'undefined') {
  if (!localStorage.getItem('user_token')) {
    localStorage.setItem('user_token', 'kguard_demo_read_only_token');
  }
  if (!localStorage.getItem('admin_username')) {
    localStorage.setItem('admin_username', 'Recruteur / Démo Publique');
  }
}

/**
 * Handle mock API responses in Demo Mode
 */
function handleDemoRequest<T = any>(endpoint: string, method: string = 'GET', body: any = null): { data: T; status: number } {
  const cleanEndpoint = endpoint.split('?')[0];

  // 1. Health & System
  if (cleanEndpoint === '/health') {
    return { data: { status: 'healthy', timestamp: new Date().toISOString() } as T, status: 200 };
  }
  if (cleanEndpoint === '/k3s/status') {
    return { data: demoSystemInfo as T, status: 200 };
  }
  if (cleanEndpoint === '/k3s/node-capacity') {
    return { data: demoNodeCapacity as T, status: 200 };
  }
  if (cleanEndpoint === '/k3s/cluster-status') {
    return { data: demoClusterStatus as T, status: 200 };
  }
  if (cleanEndpoint.startsWith('/k3s/metrics/')) {
    const ns = cleanEndpoint.replace('/k3s/metrics/', '');
    return { data: (demoPodMetrics[ns] || []) as T, status: 200 };
  }
  if (cleanEndpoint.startsWith('/k3s/logs/')) {
    const parts = cleanEndpoint.split('/');
    const podName = parts[parts.length - 1] || 'pod';
    return { data: { logs: demoPodLogs(podName) } as T, status: 200 };
  }

  // 2. Security & Falco
  if (cleanEndpoint === '/security/alerts') {
    return { data: demoSecurityAlerts as T, status: 200 };
  }

  // 3. Wazuh SIEM/XDR
  if (cleanEndpoint === '/wazuh/overview') {
    return { data: demoWazuhOverview as T, status: 200 };
  }
  if (cleanEndpoint === '/wazuh/alerts') {
    return { data: { available: true, total: demoWazuhAlerts.length, alerts: demoWazuhAlerts } as T, status: 200 };
  }

  // 4. Network Sentinel
  if (cleanEndpoint === '/sentinel/map') {
    return { data: demoSentinelMap as T, status: 200 };
  }
  if (cleanEndpoint === '/sentinel/status') {
    return { data: demoSentinelStatus as T, status: 200 };
  }
  if (cleanEndpoint === '/sentinel/hardening') {
    return { data: demoHardeningPlan as T, status: 200 };
  }

  // 5. Settings & Diagnostics
  if (cleanEndpoint === '/k3s/debug/storage') {
    return { data: demoSettingsData.storage as T, status: 200 };
  }
  if (cleanEndpoint === '/settings/integrations/webex') {
    return { data: demoSettingsData.webex as T, status: 200 };
  }

  // 6. Simulated Mutating Actions (POST / PUT / DELETE)
  if (method === 'POST' || method === 'PUT' || method === 'DELETE') {
    console.info(`[K-Guard Demo] Action simulated for ${method} ${cleanEndpoint}`, body);
    return {
      data: {
        status: 'simulated',
        message: 'Action simulée avec succès (Mode Démo en lecture seule)',
        reclaimed_mb: 240,
        items: [],
        preserved: []
      } as T,
      status: 200
    };
  }

  return { data: {} as T, status: 200 };
}

/**
 * Custom wrapper to mimic Axios behavior using native Fetch API.
 * Standardizing to international DevSecOps norms.
 */
const api = {
  async request<T = any>(endpoint: string, options: RequestInit = {}): Promise<{ data: T; status: number }> {
    if (isDemoMode) {
      // Simulate minor realistic network latency for smooth UI feel (80ms - 150ms)
      await new Promise(resolve => setTimeout(resolve, 80));
      return handleDemoRequest<T>(endpoint, options.method || 'GET', options.body);
    }

    const token = localStorage.getItem('user_token');
    const headers = new Headers(options.headers);
    
    if (!headers.has('Content-Type')) {
      headers.set('Content-Type', 'application/json');
    }

    if (token) {
      headers.set('Authorization', `Bearer ${token}`);
    }

    const config: RequestInit = {
      ...options,
      headers
    };

    try {
      const response = await fetch(`${BASE_URL}${endpoint}`, config);

      if (!response.ok) {
        if (response.status === 401) {
          console.warn("🔒 Session invalid or expired, cleaning up...");
          localStorage.removeItem('user_token');
          if (!window.location.pathname.endsWith('/login')) {
            window.location.href = '/login';
          }
        }

        const errorData = await response.json().catch(() => ({}));
        throw { response: { status: response.status, data: errorData } };
      }

      const data = await response.json();
      return { data, status: response.status };
    } catch (error) {
      throw error;
    }
  },

  get<T = any>(endpoint: string, options: RequestInit = {}) {
    return this.request<T>(endpoint, { ...options, method: 'GET' });
  },

  post<T = any>(endpoint: string, body: any = {}, options: RequestInit = {}) {
    const headers = new Headers(options.headers);
    const contentType = headers.get('Content-Type');

    let finalBody;
    if (contentType === 'application/x-www-form-urlencoded') {
      finalBody = body;
    } else {
      finalBody = JSON.stringify(body);
    }

    return this.request<T>(endpoint, {
      ...options,
      method: 'POST',
      body: finalBody
    });
  },

  put<T = any>(endpoint: string, body: any = {}, options: RequestInit = {}) {
    return this.request<T>(endpoint, {
      ...options,
      method: 'PUT',
      body: JSON.stringify(body)
    });
  },

  delete<T = any>(endpoint: string, options: RequestInit = {}) {
    return this.request<T>(endpoint, { ...options, method: 'DELETE' });
  }
};

export default api;