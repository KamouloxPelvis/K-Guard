<script setup lang="ts">
  import { ref, computed, onMounted, onUnmounted } from 'vue';
  import { useRoute } from 'vue-router';
  import axios from 'axios';

  interface SystemInfo {
    cluster_version: string;
    vps_os: string;
    uptime: string;
    latency: string;
  }
  
  const systemData = ref<SystemInfo | null>(null);
  const systemLatency = ref<number>(0);
  const vpsProvider = ref<string>("Detecting...");
  const clusterInfo = ref<string>("Fetching...");
  const pseudo = ref<string>(localStorage.getItem('admin_pseudo') || 'Admin');
  const isMenuOpen = ref(false);
  const route = useRoute();
  let statsInterval: any = null;

  const API_CONFIG = {
    baseURL: import.meta.env.VITE_API_URL || 'http://localhost:8000',
    getHeaders: () => ({
      Authorization: `Bearer ${localStorage.getItem('user_token')}`,
      'Content-Type': 'application/json'
    })
  };

  const updateSystemStats = async () => {
    const start = Date.now();
    try {
      
      const response = await fetch(`${API_CONFIG.baseURL}/api/k3s/health`, {
        headers: API_CONFIG.getHeaders()
      });
      
      if (response.ok) {
        const data = await response.json();
        systemLatency.value = Date.now() - start;
        // 'health' renvoie une liste, on prend le premier élément pour le provider
        vpsProvider.value = data[0]?.namespace || "K3s Node";
        clusterInfo.value = "v1.28+k3s"; 
      }
    } catch (e) {
      console.error("Dashboard: Connection Link Down");
      systemLatency.value = 0;
    }
  };

  const fetchSystemInfo = async () => {
  try {
    const token = localStorage.getItem('user_token');
    if (!token) return;

    const response = await axios.get(`${API_CONFIG.baseURL}/api/k3s/status`, {
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json'
      }
    });
    
    // On peuple systemData avec les clés renvoyées par main.py
    systemData.value = response.data; 
    console.log("✅ System Stats Loaded:", systemData.value);
  } catch (error) {
    console.error("Dashboard: Cluster Status Error", error);
  }
};

  onMounted(async () => {
    await fetchSystemInfo();
    await updateSystemStats();
    statsInterval = setInterval(updateSystemStats, 30000);
  });

  onUnmounted(() => {
    if (statsInterval) {
      clearInterval(statsInterval);
    }
  });

  const pageTitle = computed(() => {
    if (route.path === '/') return 'System Monitoring';
    if (route.path === '/security') return 'Vulnerability Audit';
    return 'Dashboard';
  });

  const handleLogout = () => {
    localStorage.removeItem('user_token'); // On utilise la même clé partout
    localStorage.removeItem('admin_pseudo'); 
    // On force le rechargement pour nettoyer les états axios/mémoire
    window.location.href = '/login'; 
  };
</script>

<template>
  <div class="min-h-screen bg-[#0b0c10] text-slate-300 font-sans flex overflow-auto">
    
    <Transition name="fade">
      <div v-if="isMenuOpen" 
           @click="isMenuOpen = false" 
           class="fixed inset-0 bg-black/80 z-40 lg:hidden backdrop-blur-md">
      </div>
    </Transition>

    <aside :class="[
      isMenuOpen ? 'translate-x-0' : '-translate-x-full',
      'fixed lg:relative z-50 h-full bg-[#0d0e12] border-r border-slate-800/60 flex flex-col shrink-0 transition-all duration-500 ease-in-out w-72 lg:translate-x-0 md:w-20 lg:w-72'
    ]">
    <button @click="isMenuOpen = false" 
          class="lg:hidden absolute top-5 right-5 text-slate-400 hover:text-white p-2 transition-colors cursor-pointer">
      <span class="text-2xl font-light">✕</span>
    </button>
      
      <div class="h-20 px-6 md:px-0 md:justify-center lg:px-8 flex items-center gap-4 border-b border-slate-800/50 bg-[#111217]">
        <img 
          src="/logo_small.png" 
          alt="K-Guard" 
          class="w-10 h-10 object-contain"
        />
        
        <span class="hidden lg:block text-white font-valorant text-xl tracking-[0.2em] mt-1">
          K-<span class="text-[#f05a28]">GUARD</span>
        </span>
      </div>
      
      <nav class="flex-1 p-4 md:p-3 lg:p-6 space-y-4 mt-4">
        <router-link to="/" 
          @click="isMenuOpen = false"
          class="nav-link"
          :class="route.path === '/' ? 'nav-active' : 'nav-inactive'">
          <span class="text-xl">📊</span>
          <div class="flex flex-col md:hidden lg:flex">
            <span class="text-[11px] font-bold uppercase tracking-widest">Health</span>
            <span class="text-[8px] text-slate-500 font-mono mt-0.5 uppercase">K3s Cluster Status</span>
          </div>
        </router-link>

        <router-link to="/security" 
          @click="isMenuOpen = false"
          class="nav-link"
          :class="route.path === '/security' ? 'nav-active' : 'nav-inactive'">
          <span class="text-xl">🔒</span>
          <div class="flex flex-col md:hidden lg:flex">
            <span class="text-[11px] font-bold uppercase tracking-widest">Security</span>
            <span class="text-[8px] text-slate-500 font-mono mt-0.5 uppercase">Trivy Image Scan</span>
          </div>
        </router-link>
      </nav>

      <div class="hidden lg:block p-6 border-t border-slate-800/50 bg-[#0a0b0e]">
        <div class="flex items-center gap-3 mb-3">
            <p class="text-[10px] text-slate-500 uppercase tracking-widest flex items-center gap-2">
              <span class="w-1.5 h-1.5 bg-green-500 rounded-full animate-pulse"></span>
              Authenticated as 
              <span class="text-[#f05a28] font-bold">{{ pseudo }}</span>
            </p>
        </div>
        <div class="text-[10px] text-slate-600 font-mono break-all leading-tight uppercase"> Kubernetes & OS Distribution versions : <br />
          {{ systemData ? `${systemData.cluster_version} // ${systemData.vps_os}` : 'Loading system info...' }}
        </div>
      </div>
    </aside>

    <main class="flex-1 flex flex-col min-w-0 relative">
      <div class="absolute inset-0 pointer-events-none flex items-center justify-center z-0">
        <div class="w-[500px] h-[500px] border border-blue-500/5 rounded-full absolute"></div>
        <img src="/logo_background.png" alt="K-Guard" 
             class="w-[450px] opacity-[0.05] pointer-events-none select-none" />
      </div>

      <header class="h-20 border-b border-slate-800/60 bg-[#111217]/80 flex items-center justify-between px-6 lg:px-10 sticky top-0 z-[45] backdrop-blur-xl">
        <div class="flex items-center gap-6">
          <button @click="isMenuOpen = !isMenuOpen" 
                  class="lg:hidden text-slate-400 hover:text-white p-2 transition-colors cursor-pointer bg-slate-800/30 rounded-sm">
            <span class="text-xl">{{ isMenuOpen ? '✕' : '☰' }}</span>
          </button>
          
          <div class="flex flex-col">
            <h2 class="text-xl font-extralight text-white tracking-tight uppercase">{{ pageTitle }}</h2>
          </div>
        </div>
        
        <div class="flex items-center gap-6">
            <div class="hidden md:flex flex-col items-end">
                <span class="text-[9px] text-green-500 font-bold tracking-[0.2em] uppercase flex items-center gap-2">
                    <span class="relative flex h-2 w-2">
                        <span class="animate-ping absolute inline-flex h-full w-full rounded-full bg-green-400 opacity-75"></span>
                        <span class="relative inline-flex rounded-full h-2 w-2 bg-green-500"></span>
                    </span>
                    K3s Cloud online
                </span>
                
                <span class="text-[10px] text-slate-600 font-mono mt-1 uppercase">
                    Latency: {{ systemLatency }}ms
                </span>
            </div>
            <button @click="handleLogout" 
                  class="group flex items-center gap-2 bg-red-500/10 hover:bg-red-500/20 border border-red-500/30 hover:border-red-500/60 px-4 py-2 rounded-sm transition-all duration-300 cursor-pointer">
              <span class="text-xs text-red-500 group-hover:text-red-400 font-bold uppercase tracking-tighter">LogOut</span>
          </button>
        </div>
      </header>

      <div class="flex-1 overflow-y-auto overflow-x-auto relative z-10 custom-scrollbar">
        <router-view v-slot="{ Component }">
          <transition name="page" mode="out-in">
            <component :is="Component" />
          </transition>
        </router-view>
      </div>
    </main>
  </div>
</template>

<style scoped>
/* Navigation Links Styles */
@reference "../style.css";

.nav-link {
  @apply flex items-center gap-4 p-4 rounded-sm text-sm transition-all duration-300 border border-transparent;
}

.nav-active {
  @apply bg-blue-600/10 border-blue-500/30 text-white shadow-[inset_0_0_20px_rgba(59,130,246,0.1)];
}

.nav-inactive {
  @apply text-slate-500 hover:bg-slate-800/30 hover:text-slate-200 hover:border-slate-800;
}

/* Animations */
.animate-ping-slow {
  animation: ping 5s cubic-bezier(0, 0, 0.2, 1) infinite;
}

.fade-enter-active, .fade-leave-active { transition: opacity 0.3s; }
.fade-enter-from, .fade-leave-to { opacity: 0; }

.page-enter-active, .page-leave-active { transition: all 0.2s ease-out; }
.page-enter-from { opacity: 0; transform: translateY(10px); }
.page-leave-to { opacity: 0; transform: translateY(-10px); }

/* Custom Scrollbar */
.custom-scrollbar::-webkit-scrollbar { width: 4px; }
.custom-scrollbar::-webkit-scrollbar-track { background: transparent; }
.custom-scrollbar::-webkit-scrollbar-thumb { background: #1e293b; border-radius: 10px; }
.custom-scrollbar::-webkit-scrollbar-thumb:hover { background: #334155; }
</style>