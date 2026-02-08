<script setup lang="ts">
import { ref, onMounted, onUnmounted } from 'vue';
import { useRouter } from 'vue-router';
import axios from 'axios';

// --- Interfaces & Types ---
interface PodStatus {
  name: string;      
  pod_name: string;  
  status: string;    
  ip: string;        
  type: string;
  namespace: string;      
}

const router = useRouter();
const apps = ref<PodStatus[]>([]);
const loading = ref(false);
const isInitialLoad = ref(true);
const selectedPod = ref<PodStatus | null>(null);
const podLogs = ref("");
const showModal = ref(false);

// Configuration centralisée
const API_CONFIG = {
  baseURL: import.meta.env.VITE_API_URL || 'http://localhost:8000',
  getHeaders: () => ({
    Authorization: `Bearer ${localStorage.getItem('user_token')}`,
    'Content-Type': 'application/json'
  })
};

const fetchClusterData = async () => {
  if (isInitialLoad.value) loading.value = true;
  try {
    const { data } = await axios.get(`${API_CONFIG.baseURL}/api/k3s/health`, {
      headers: API_CONFIG.getHeaders(),
      timeout: 8000
    });
    apps.value = data;
  } catch (error: any) {
    console.error("K-Guard Health Link Down:", error);
    if (error.response?.status === 401) handleLogout();
  } finally {
    loading.value = false;
    isInitialLoad.value = false;
  }
};

const openDetails = async (pod: PodStatus) => {
  selectedPod.value = pod;
  showModal.value = true;
  podLogs.value = ">> ESTABLISHING SECURE CONNECTION...\n>> DECRYPTING LOG STREAM...";
  try {
    const { data } = await axios.get(
      `${API_CONFIG.baseURL}/api/k3s/logs/${pod.namespace}/${pod.pod_name}`,
      { headers: API_CONFIG.getHeaders() }
    );
    podLogs.value = data.logs || "SYSTEM: No logs available.";
  } catch (error) {
    podLogs.value = "CRITICAL ERROR: Connection lost.";
  }
};

const restartPod = async (event: Event, pod: PodStatus) => {
  event.stopPropagation(); 
  if (!confirm(`CAUTION: Restart ${pod.pod_name}?`)) return;
  try {
    await axios.delete(
      `${API_CONFIG.baseURL}/api/k3s/restart/${pod.namespace}/${pod.pod_name}`,
      { headers: API_CONFIG.getHeaders() }
    );
    await fetchClusterData(); 
  } catch (error) {
    alert("Unauthorized: Check CI_CD_SSH_KEY permissions.");
  }
};

const handleLogout = () => {
  localStorage.clear();
  router.push('/login');
};

let refreshInterval: any = null;
onMounted(() => {
  fetchClusterData();
  refreshInterval = setInterval(fetchClusterData, 10000);
});
onUnmounted(() => { if (refreshInterval) clearInterval(refreshInterval); });

const getStatusClass = (status: string) => {
  const s = status.toUpperCase();
  if (s === 'SECURE' || s === 'RUNNING') return 'text-green-500 bg-green-500/10 border-green-500/20';
  if (s === 'PENDING') return 'text-orange-500 bg-orange-500/10 border-orange-500/20';
  return 'text-red-500 bg-red-500/10 border-red-500/20';
};
</script>

<template>
  <div class="p-8 relative z-10">
    <header class="mb-12 flex justify-between items-end border-b border-slate-800 pb-7">
      <div>
        <p class="text-[12px] text-slate-500 mt-6 uppercase tracking-[0.5em]">K3s Cluster</p>
      </div>
      <button @click="fetchClusterData" class="bg-slate-800/40 hover:bg-blue-600 border border-slate-700 px-5 py-2 rounded-sm transition-all">
        <span class="text-[10px] font-bold text-slate-400 hover:text-white uppercase tracking-widest">ReSync</span>
      </button>
    </header>

    <div v-if="loading && isInitialLoad" class="flex flex-col items-center justify-center py-40">
      <div class="w-10 h-10 border-2 border-blue-500 border-t-transparent rounded-full animate-spin mb-6"></div>
      <span class="text-[9px] uppercase tracking-[0.5em] text-blue-500">Scanning Nodes...</span>
    </div>

    <div v-else class="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-6">
      <div v-for="pod in apps" :key="pod.pod_name" @click="openDetails(pod)"
           class="group relative bg-[#181b1f]/60 backdrop-blur-sm border border-slate-800 p-6 rounded-sm hover:border-blue-500/40 transition-all cursor-pointer overflow-hidden">
        <div class="absolute top-0 left-0 w-1 h-full" :class="pod.status === 'SECURE' ? 'bg-green-500' : 'bg-red-500'"></div>
        <div class="flex justify-between items-start mb-8">
          <h3 class="text-lg font-bold text-white uppercase">{{ pod.name }}</h3>
          <span :class="getStatusClass(pod.status)" class="text-[8px] font-black px-2 py-1 border rounded-sm uppercase">{{ pod.status }}</span>
        </div>
        <div class="flex justify-between items-center bg-black/20 p-2 border border-slate-800/50">
          <span class="text-[1px] text-slate-500 uppercase font-bold">IP</span>
          <span class="text-[12px] font-mono text-blue-300">{{ pod.ip }}</span>
        </div>
        <button @click="(e) => restartPod(e, pod)" class="text-xs text-red-500 group-hover:text-red-400 font-bold uppercase tracking-tighter cursor-pointer">
          Force Restart
        </button>
      </div>
    </div>

    <Teleport to="body">
      <div v-if="showModal" class="fixed inset-0 z-[100] flex items-center justify-center p-6 bg-black/95 backdrop-blur-md">
        <div class="bg-[#0d0e12] border border-slate-800 w-full max-w-5xl h-[85vh] flex flex-col rounded-sm shadow-2xl">
          <div class="p-4 border-b border-slate-800 flex justify-between items-center bg-[#181b1f]">
            <span class="text-[10px] font-mono text-blue-400 uppercase tracking-widest">Console // {{ selectedPod?.pod_name }}</span>
            <button @click="showModal = false" class="text-slate-500 hover:text-white text-2xl">&times;</button>
          </div>
          <div class="flex-1 p-6 overflow-y-auto font-mono text-[12px] text-blue-100/80 bg-black/40">
            <pre class="whitespace-pre-wrap">{{ podLogs }}</pre>
          </div>
          <div class="p-3 border-t border-slate-900 bg-black/40 flex justify-between items-center">
             <span class="text-[8px] text-slate-600 uppercase font-bold">K-Guard Terminal v2.0</span>
             <span class="text-[8px] text-blue-900 font-mono">Kamal @ VPS-Master</span>
          </div>
        </div>
      </div>
    </Teleport>
  </div>
</template>