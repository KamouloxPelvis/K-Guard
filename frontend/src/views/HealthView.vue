<script setup lang="ts">
  import { ref, onMounted, onUnmounted } from 'vue';
  import { useRouter } from 'vue-router';
  import axios from 'axios';

  // --- Interfaces ---
  interface PodStatus {
    name: string;      
    pod_name: string;  
    status: string;    
    ip: string;        
    type: string;
    namespace: string;      
  }

  interface PodMetrics {
    pod_name: string;
    cpuUsage: string;    
    memoryUsage: string; 
  }

  // --- Configuration ---
  const router = useRouter();
  const API_CONFIG = {
    baseURL: import.meta.env.VITE_API_URL || 'http://localhost:8000',
    getHeaders: () => ({
      Authorization: `Bearer ${localStorage.getItem('user_token')}`,
      'Content-Type': 'application/json'
    })
  };

  // --- État Réactif ---
  const apps = ref<PodStatus[]>([]);
  const metrics = ref<Record<string, PodMetrics>>(
    JSON.parse(localStorage.getItem('kguard_metrics') || '{}')
  );
  const metricsLoading = ref<Record<string, boolean>>({});
  const loading = ref(false);
  const isInitialLoad = ref(true);
  const selectedPod = ref<PodStatus | null>(null);
  const podLogs = ref("");
  const showModal = ref(false);
  let refreshInterval: any = null;

  const nodeCapacity = ref({ 
    cpu_cores: 2, 
    memory_total_ki: 8388608 
  });

  // --- Logique métier ---
  const fetchNodeCapacity = async () => {
    try {
      const { data } = await axios.get(`${API_CONFIG.baseURL}/api/k3s/node-capacity`, {
        headers: API_CONFIG.getHeaders()
      });
      nodeCapacity.value = data;
    } catch (error) {
      console.warn("⚠️ Utilisation du fallback 2 vCPU/8GB");
    }
  };

  const calculateCpuPercent = (raw: string | undefined): number => {
    if (!raw) return 0;
    const nanocores = parseInt(raw.replace(/\D/g, '')) || 0;
    const totalNanocores = nodeCapacity.value.cpu_cores * 1000000000;
    return (nanocores / totalNanocores) * 100;
  };

  const calculateMemPercent = (raw: string | undefined): number => {
    if (!raw) return 0;
    const kiValue = parseInt(raw.replace(/\D/g, '')) || 0;
    return Math.max((kiValue / nodeCapacity.value.memory_total_ki) * 100, 0.5);
  };

  const formatMemory = (raw: string | undefined): string => {
    if (!raw) return '0 Mo';
    const miValue = (parseInt(raw.replace(/\D/g, '')) || 0) / 1024;
    return miValue < 1024 ? `${miValue.toFixed(0)} Mo` : `${(miValue / 1024).toFixed(2)} Go`;
  };

  const fetchMetrics = async (namespace: string) => {
    if (isInitialLoad.value) metricsLoading.value[namespace] = true;
    try {
      const { data } = await axios.get(`${API_CONFIG.baseURL}/api/k3s/metrics/${namespace}`, {
        headers: API_CONFIG.getHeaders()
      });
      if (Array.isArray(data)) {
        data.forEach((m: PodMetrics) => { metrics.value[m.pod_name] = m; });
        localStorage.setItem('kguard_metrics', JSON.stringify(metrics.value));
      }
    } catch (e) { console.error("Metrics error", e); }
    finally { metricsLoading.value[namespace] = false; }
  };

  const fetchClusterData = async () => {
    if (isInitialLoad.value) loading.value = true;
    try {
      const { data } = await axios.get(`${API_CONFIG.baseURL}/api/k3s/health`, {
        headers: API_CONFIG.getHeaders()
      });
      apps.value = data;
      const namespaces = [...new Set(data.map((p: PodStatus) => p.namespace))];
      namespaces.forEach(ns => fetchMetrics(ns as string));
    } catch (error: any) {
      if (error.response?.status === 401) {
        localStorage.removeItem('user_token');
        router.push('/login');
      }
    } finally {
      loading.value = false;
      isInitialLoad.value = false;
    }
  };

  // --- Actions UI ---
  const openDetails = async (pod: PodStatus) => {
    selectedPod.value = pod;
    showModal.value = true;
    podLogs.value = ">> ESTABLISHING SECURE CONNECTION...";
    try {
      const { data } = await axios.get(`${API_CONFIG.baseURL}/api/k3s/logs/${pod.namespace}/${pod.pod_name}`, {
        headers: API_CONFIG.getHeaders()
      });
      podLogs.value = data.logs || "No logs available.";
    } catch (error) { podLogs.value = "CRITICAL ERROR: Connection lost."; }
  };

  const restartPod = async (event: Event, pod: PodStatus) => {
    event.stopPropagation(); 
    if (!confirm(`CAUTION: Restart ${pod.pod_name}?`)) return;
    try {
      await axios.delete(`${API_CONFIG.baseURL}/api/k3s/restart/${pod.namespace}/${pod.pod_name}`, {
        headers: API_CONFIG.getHeaders()
      });
      fetchClusterData(); 
    } catch (error) { alert("Action failed."); }
  };

  const remediateLoad = async (event: Event, pod: PodStatus) => {
    event.stopPropagation();
    if (!confirm(`ACTIVATE REMEDIATION: Scale down ${pod.name}?`)) return;
    try {
      await axios.post(`${API_CONFIG.baseURL}/api/k3s/remediate/${pod.namespace}/${pod.pod_name}`, {}, {
        headers: API_CONFIG.getHeaders()
      });
      alert("Remediation signal sent.");
    } catch (error) { alert("Remediation failed."); }
  };

  const getStatusClass = (status: string) => {
    const s = status.toUpperCase();
    return (s === 'SECURE' || s === 'RUNNING') 
      ? 'text-green-500 bg-green-500/10 border-green-500/20' 
      : 'text-red-500 bg-red-500/10 border-red-500/20';
  };

  onMounted(() => {
    fetchNodeCapacity();
    fetchClusterData();
    refreshInterval = setInterval(fetchClusterData, 30000);
  });

  onUnmounted(() => { if (refreshInterval) clearInterval(refreshInterval); });
</script>

<template>
  <div class="p-8 relative z-10">
    <header class="mb-12 flex justify-between items-end border-b border-slate-800 pb-7">
      <div><p class="text-[12px] text-slate-500 mt-6 uppercase tracking-[0.5em]">K-Guard SRE Monitor</p></div>
      <div class="flex gap-4">
        <button @click="fetchClusterData" class="bg-slate-800/40 hover:bg-blue-600 border border-slate-700 px-5 py-2 rounded-sm transition-all text-[10px] font-bold text-slate-400 hover:text-white uppercase tracking-widest cursor-pointer">ReSync</button>
      </div>
    </header>

    <div v-if="loading && isInitialLoad" class="flex flex-col items-center justify-center py-40">
      <div class="w-10 h-10 border-2 border-blue-500 border-t-transparent rounded-full animate-spin mb-6"></div>
      <span class="text-[9px] uppercase tracking-[0.5em] text-blue-500">Scanning Nodes...</span>
    </div>

    <div v-else class="grid grid-cols-1 xl:grid-cols-2 gap-8 max-w-7xl mx-auto">
      <div v-for="pod in apps" :key="pod.pod_name" @click="openDetails(pod)"
          class="group relative bg-[#181b1f]/60 backdrop-blur-sm border border-slate-800 p-6 rounded-sm hover:border-blue-500/40 transition-all cursor-pointer">
        
        <div class="absolute top-0 left-0 w-1 h-full" 
            :class="pod.status === 'SECURE' || pod.status === 'RUNNING' ? 'bg-green-500' : 'bg-red-500'">
        </div>
        
        <div class="flex justify-between items-start mb-6">
          <div class="flex flex-col">
            <h3 class="text-lg font-bold text-white uppercase leading-tight">{{ pod.name }}</h3>
            <p class="text-[10px] text-slate-400 font-mono mt-0.5 opacity-80">Namespace: {{ pod.namespace }}</p>
          </div>
          <span :class="getStatusClass(pod.status)" class="text-[8px] font-black px-2 py-1 border rounded-sm uppercase">
            {{ pod.status }}
          </span>
        </div>

        <div class="space-y-6 mb-8">
          <div class="flex flex-col gap-2">
            <div class="flex justify-between text-[11px] uppercase font-bold tracking-widest">
              <span class="text-slate-500">CPU</span>
              <span v-if="metricsLoading[pod.namespace]" class="text-blue-500 animate-pulse">[ SCANNING... ]</span>
              <span class="text-blue-400 font-mono">{{ calculateCpuPercent(metrics[pod.pod_name]?.cpuUsage).toFixed(2) }}%</span>
            </div>
            <div class="w-full bg-slate-900 h-1 rounded-full overflow-hidden">
              <div class="h-full transition-all duration-1000"
                :class="calculateCpuPercent(metrics[pod.pod_name]?.cpuUsage) > 60 ? 'bg-red-600' : 'bg-blue-500'"
                :style="{ width: `${calculateCpuPercent(metrics[pod.pod_name]?.cpuUsage)}%` }">
              </div>
            </div>
          </div>

          <div class="flex flex-col gap-2">
            <div class="flex justify-between text-[11px] uppercase font-bold tracking-widest">
              <span class="text-slate-500">RAM</span>
              <span class="text-indigo-400 font-mono">{{ formatMemory(metrics[pod.pod_name]?.memoryUsage) }}</span>
            </div>
            <div class="w-full h-1 bg-slate-900 rounded-full overflow-hidden">
              <div class="h-full bg-indigo-500 transition-all duration-1000" 
                  :style="{ width: calculateMemPercent(metrics[pod.pod_name]?.memoryUsage) + '%' }"></div>
            </div>
          </div>
        </div>

        <div class="flex justify-between items-center bg-black/20 p-2 border border-slate-800/50 mb-4 font-mono">
          <span class="text-[10px] text-slate-500 uppercase font-bold">IP Address</span>
          <span class="text-[12px] text-blue-300">{{ pod.ip }}</span>
        </div>

        <div class="flex justify-between items-center pt-4 border-t border-slate-800/30">
          <button @click.stop="(e) => restartPod(e, pod)" class="px-3 py-1.5 text-[10px] font-bold uppercase border border-red-500/40 text-red-500 hover:bg-red-500 hover:text-white transition-all rounded-sm">
            Restart
          </button>
          <div class="flex gap-2">
            <button @click.stop="openDetails(pod)" class="btn-action btn-logs">Logs</button>
            <button v-if="calculateCpuPercent(metrics[pod.pod_name]?.cpuUsage) > 30" 
                    @click.stop="(e) => remediateLoad(e, pod)" 
                    class="btn-action btn-remediate">
              Remediate
            </button>
          </div>
        </div>
      </div>
    </div>

    <Teleport to="body">
      <div v-if="showModal" class="fixed inset-0 z-[100] flex items-center justify-center p-6 bg-black/95 backdrop-blur-md">
        <div class="bg-[#0d0e12] border border-slate-800 w-full max-w-5xl h-[85vh] flex flex-col rounded-sm">
          <div class="p-4 border-b border-slate-800 flex justify-between items-center bg-[#181b1f]">
            <span class="text-[10px] font-mono text-blue-400 uppercase tracking-widest">Console // {{ selectedPod?.pod_name }}</span>
            <button @click="showModal = false" class="text-slate-500 hover:text-white text-2xl">&times;</button>
          </div>
          <div class="flex-1 p-6 overflow-y-auto font-mono text-[12px] text-blue-100/80 bg-black/40">
            <pre class="whitespace-pre-wrap">{{ podLogs }}</pre>
          </div>
          <div class="p-3 border-t border-slate-900 bg-black/40 flex justify-between items-center">
            <span class="text-[8px] text-slate-600 uppercase font-bold">K-Guard Terminal v2.0</span>
            <span class="text-[8px] text-blue-900 font-mono">Kamal @ VPS-</span>
          </div>
        </div>
      </div>
    </Teleport>
  </div>
</template>