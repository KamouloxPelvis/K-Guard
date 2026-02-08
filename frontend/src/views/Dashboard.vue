<script setup lang="ts">
import { ref, onMounted } from 'vue';
import axios from 'axios';

interface PodStatus {
  name: string;      
  pod_name: string;  
  status: string;    
  ip: string;        
  type: string;
  namespace: string;      
}

const apps = ref<PodStatus[]>([]);
const loading = ref(true);
const selectedPod = ref<PodStatus | null>(null);
const podLogs = ref("");
const showModal = ref(false);

// Récupération dynamique de l'URL et du Token
const getBaseURL = () => import.meta.env.VITE_API_URL || 'http://localhost:8000';
const getAuthHeader = () => {
  const token = localStorage.getItem('user_token');
  return token ? { Authorization: `Bearer ${token}` } : {};
};

const fetchClusterData = async () => {
  if (apps.value.length === 0) loading.value = true; 
  
  try {
    // La route health peut rester publique ou être protégée
    const response = await axios.get(`${getBaseURL()}/api/k3s/health`, {
      headers: getAuthHeader()
    });
    apps.value = response.data;
    console.log("K-Guard Update Success");
  } catch (error: any) {
    console.error("Fetch Error:", error);
    // Optionnel : redirection si 401
    if (error.response?.status === 401) window.location.href = '/login';
  } finally {
    loading.value = false;
  }
};

const openDetails = async (pod: PodStatus) => {
  selectedPod.value = pod;
  showModal.value = true;
  podLogs.value = "FETCHING ENCRYPTED LOGS...";
  
  try {
    const response = await axios.get(
      `${getBaseURL()}/api/k3s/logs/${pod.namespace}/${pod.pod_name}`,
      { headers: getAuthHeader() } // Injection du token indispensable ici
    );
    podLogs.value = response.data.logs || "No logs found in standard output.";
  } catch (error) {
    podLogs.value = "ERROR: Connection to cluster lost.";
  }
};

const restartPod = async (event: Event, pod: PodStatus) => {
  event.stopPropagation(); 
  if (!confirm(`Confirm hard restart for ${pod.pod_name}?`)) return;
  
  try {
    await axios.delete(
      `${getBaseURL()}/api/k3s/restart/${pod.namespace}/${pod.pod_name}`,
      { headers: getAuthHeader() } // Protection de la commande de restart
    );
    alert("Instruction sent to K3s controller.");
    await fetchClusterData(); 
  } catch (error) {
    alert("Command failed : Unauthorized or Network error.");
  }
};

onMounted(() => {
  fetchClusterData();
  // Update toutes les 10s pour garder un œil sur le cluster
  setInterval(fetchClusterData, 10000); 
});
</script>

<template>
  <div class="min-h-screen bg-[#0b0c10] text-slate-300 font-sans flex overflow-hidden">
    
    <aside class="w-64 bg-[#111217] border-r border-slate-800 flex flex-col shrink-0">
      <div class="h-[64px] px-6 flex items-center gap-3 border-b border-slate-800">
        <img src="/logo_small.png" alt="K-Guard" class="w-8 h-8 object-contain" />
        <span class="text-[#f05a28] font-valorant text-xl tracking-widest mt-1">
          K-GUARD
        </span>
      </div>
      
      <nav class="flex-1 p-4 space-y-2">
        <div class="bg-slate-800 text-white p-3 rounded-sm text-sm font-medium cursor-default flex items-center gap-2">
          <span>📊</span> Health & Logs
        </div>
        <div class="p-3 text-slate-500 text-sm cursor-not-allowed flex items-center gap-2">
          <span>🔒</span> Security
        </div>
      </nav>

      <div class="p-4 border-t border-slate-800 text-[10px] text-slate-500 font-mono text-center uppercase tracking-widest">
        Kamal @ Root / VPS Kamatera (Ubuntu)
      </div>
    </aside>

    <main class="flex-1 overflow-y-auto relative">
      
      <div class="fixed inset-0 pointer-events-none flex items-center justify-center z-0 overflow-hidden">
        <img 
          src="/logo_background.png" 
          alt="Watermark" 
          class="ml-64 p-10 w-[600px] opacity-[0.10] grayscale brightness-50"
        />
      </div>

      <header class="h-16 border-b border-slate-800 bg-[#111217]/50 flex items-center justify-between px-8 sticky top-0 z-10 backdrop-blur-md">
        <h2 class="text-[10px] uppercase tracking-[0.3em] font-bold text-slate-500">Infrastructure Monitoring</h2>
        <div class="text-[10px] text-green-500 font-bold tracking-widest animate-pulse">● CLUSTER ONLINE</div>
      </header>

      <div class="p-8 relative z-10">
        <div class="mb-10 flex justify-between items-center">
          <div>
            <h1 class="text-4xl font-extralight text-white tracking-tight">System Status</h1>
            <p class="text-xs text-slate-500 mt-1 uppercase tracking-wider">K3s Environment: blog & portfolio</p>
          </div>
          <button 
            @click="fetchClusterData" 
            class="cursor-pointer bg-blue-600/10 hover:bg-blue-600 text-blue-500 hover:text-white border border-blue-500/20 px-6 py-2 rounded-sm text-[10px] font-bold transition-all uppercase tracking-widest active:scale-95"
          >
            Refresh Data
          </button>
        </div>

        <div v-if="loading" class="flex flex-col items-center justify-center py-32 space-y-4">
          <div class="w-12 h-12 border-2 border-blue-500 border-t-transparent rounded-full animate-spin"></div>
          <span class="text-[10px] uppercase tracking-[0.4em] text-slate-500">Scanning Nodes...</span>
        </div>

        <div v-else class="grid grid-cols-1 lg:grid-cols-2 xl:grid-cols-3 gap-6">
          <div v-for="pod in apps" :key="pod.pod_name" 
               @click="openDetails(pod)"
               class="group relative bg-[#181b1f] border border-slate-800 p-6 rounded-sm hover:border-blue-500/50 transition-all cursor-pointer">
            
            <div class="flex justify-between items-start mb-8">
              <div>
                <h3 class="text-xl font-bold text-white group-hover:text-blue-400 transition-colors uppercase">{{ pod.name }}</h3>
                <p class="text-[9px] font-mono text-slate-500 mt-1 break-all">{{ pod.pod_name }}</p>
              </div>
              <span :class="pod.status === 'SECURE' ? 'text-green-500 bg-green-500/10' : 'text-red-500 bg-red-500/10'" 
                    class="text-[9px] font-bold px-2 py-1 rounded-full uppercase tracking-tighter">
                {{ pod.status }}
              </span>
            </div>

            <div class="space-y-4">
              <div class="flex justify-between items-end">
                <span class="text-[10px] text-slate-600 uppercase font-bold">Network Intern IP</span>
                <span class="text-xs font-mono text-slate-300">{{ pod.ip }}</span>
              </div>
              <div class="h-1 bg-slate-900 rounded-full overflow-hidden">
                <div class="h-full bg-blue-500 transition-all duration-1000" :style="{ width: pod.status === 'SECURE' ? '100%' : '20%' }"></div>
              </div>
            </div>

            <button 
              @click="(e) => restartPod(e, pod)" 
              class="cursor-pointer absolute top-18 right-6 opacity-0 group-hover:opacity-100 bg-red-900/40 hover:bg-red-700 text-white text-[9px] font-bold px-3 py-1.5 rounded-sm shadow-xl transition-all uppercase tracking-widest z-30"
            >
              Restart
            </button>
          </div>
        </div>
      </div>
    </main>

    <div v-if="showModal" class="fixed inset-0 z-50 flex items-center justify-center p-6 bg-black/95 backdrop-blur-sm">
      <div class="bg-[#111217] border border-slate-800 w-full max-w-5xl h-[80vh] flex flex-col rounded-sm shadow-2xl">
        <div class="p-4 border-b border-slate-800 flex justify-between items-center bg-[#181b1f]">
          <span class="text-[10px] font-mono text-blue-400 uppercase tracking-widest">Log Stream // {{ selectedPod?.name }}</span>
          <button @click="showModal = false" class="text-slate-500 hover:text-white text-2xl">&times;</button>
        </div>
        <div class="flex-1 p-6 overflow-y-auto font-mono text-[11px] text-slate-400 leading-relaxed bg-black/20">
          <pre class="whitespace-pre-wrap">{{ podLogs }}</pre>
        </div>
      </div>
    </div>
  </div>
</template>

<style>
@import "tailwindcss";

@font-face {
  font-family: 'Valorant';
  src: url('./assets/fonts/Valorant.ttf') format('truetype');
  font-weight: normal;
  font-style: normal;
}

:root { color-scheme: dark; }
body { margin: 0; background: #0b0c10; overflow: hidden; }

/* Classe utilitaire pour la police Valorant */
.font-valorant {
  font-family: 'Valorant', sans-serif;
}
</style>
