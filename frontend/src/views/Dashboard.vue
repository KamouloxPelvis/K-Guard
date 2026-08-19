<script setup lang="ts">
  import { ref, computed, onMounted, onUnmounted } from 'vue';
  import { useRoute, useRouter } from 'vue-router';
  import api, { isDemoMode } from '@/services/api';

  interface SystemInfo {
    cluster_version: string;
    vps_os: string;
    uptime: string;
    status: string;
  }
  
  const systemData = ref<SystemInfo | null>(null);
  const systemLatency = ref<number>(0);
  const username = ref<string>(localStorage.getItem('admin_username') || 'Authorized User');
  const isMenuOpen = ref(false);
  const route = useRoute();
  const router = useRouter();
  let statsInterval: any = null;

  /**
   * Health check heartbeat and latency measurement.
   * Calculates the round-trip time (RTT) to the backend health endpoint.
   */
  const updateSystemStats = async () => {
    const start = Date.now();
    try {
      /**
       * The api.get method returns both data and status code.
       * 200 OK confirms backend reachability.
       */
      const response = await api.get('/health');
      if (response.status === 200) {
        systemLatency.value = Date.now() - start;
      }
    } catch (e) {
      systemLatency.value = 0;
      console.warn("[K-Guard] Connectivity lost with backend heartbeat service");
    }
  };

  /**
   * Data retrieval for core infrastructure status.
   * Fetches K3s cluster version and host OS details.
   */
  const fetchSystemInfo = async () => {
    try {
      const { data } = await api.get<SystemInfo>('/k3s/status');
      systemData.value = data;
    } catch (error) {
      /**
       * Errors are logged to the console for infrastructure monitoring.
       * The UI handles null systemData gracefully via templates.
       */
      console.error("Dashboard Service: Failed to retrieve cluster status", error);
    }
  };

  /**
   * Session termination logic.
   * Clears security tokens and user metadata from local storage before redirecting.
   */
  const handleLogout = () => {
    localStorage.removeItem('user_token');
    localStorage.removeItem('admin_username'); 
    router.push({ name: 'Login' });
  };

  onMounted(async () => {
  await fetchSystemInfo();
  
  // Recursive function to prevent call stacking
  const pollStats = async () => {
    await updateSystemStats();
    statsInterval = setTimeout(pollStats, 20000);
  };
  
  pollStats();
  });

  onUnmounted(() => {
    if (statsInterval) clearTimeout(statsInterval);
  });

  /**
   * Dynamic view title mapping.
   * Maps internal routes to human-readable system module names.
   */
  const pageTitle = computed(() => {
    const titles: Record<string, string> = {
      '/': 'System Overview',
      '/security': 'Runtime Security',
      '/wazuh': 'Endpoint & Compliance',
      '/sentinel': 'Network Sentinel',
      '/settings': 'Settings'
    };
    return titles[route.path] || 'K-Guard Dashboard';
  });
</script>

<template>
  <div class="h-screen w-screen bg-[#0b0c10] text-slate-300 font-sans flex overflow-hidden">
    
    <Transition name="fade">
      <div v-if="isMenuOpen" 
           @click="isMenuOpen = false" 
           class="fixed inset-0 bg-black/80 z-40 lg:hidden backdrop-blur-md">
      </div>
    </Transition>

    <aside :class="[
      isMenuOpen ? 'translate-x-0' : '-translate-x-full',
      'fixed lg:sticky top-0 z-50 h-screen bg-[#0d0e12] border-r border-slate-800/60 flex flex-col shrink-0 transition-all duration-500 ease-in-out w-64 lg:translate-x-0'
    ]">
      <button @click="isMenuOpen = false" 
            class="lg:hidden absolute top-5 right-5 text-slate-400 hover:text-white p-2 transition-colors cursor-pointer">
        <span class="text-2xl font-light">✕</span>
      </button>
      
      <div class="h-14 px-6 md:px-0 md:justify-center lg:px-6 flex items-center gap-3 border-b border-slate-800/50 bg-[#111217]">
        <span class="hidden lg:block text-white font-valorant text-lg tracking-[0.2em] mt-1">
          K-<span class="text-[#f05a28]">GUARD</span>
        </span>
      </div>
      
      <nav class="flex-1 flex flex-col p-4 md:p-2 lg:p-4 space-y-2 mt-2">
        <router-link to="/" @click="isMenuOpen = false" class="nav-link py-2.5 px-3 rounded-sm flex items-center transition-all" :class="route.path === '/' ? 'nav-active' : 'nav-inactive text-slate-400 hover:text-slate-200 hover:bg-slate-800/20'">
          <svg class="w-[18px] h-[18px] shrink-0 transition-colors" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
            <rect x="3" y="3" width="7" height="7" rx="1"></rect>
            <rect x="14" y="3" width="7" height="7" rx="1"></rect>
            <rect x="14" y="14" width="7" height="7" rx="1"></rect>
            <rect x="3" y="14" width="7" height="7" rx="1"></rect>
          </svg>
          <div class="flex flex-col md:hidden lg:flex ml-3.5">
            <span class="text-[11.5px] font-bold uppercase tracking-wider text-slate-200">System Overview</span>
            <span class="text-[8.5px] text-slate-400 font-mono mt-0.5 uppercase tracking-wide">K3s Status & Logs</span>
          </div>
        </router-link>

        <router-link to="/security" @click="isMenuOpen = false" class="nav-link py-2.5 px-3 rounded-sm flex items-center transition-all" :class="route.path === '/security' ? 'nav-active' : 'nav-inactive text-slate-400 hover:text-slate-200 hover:bg-slate-800/20'">
          <svg class="w-[18px] h-[18px] shrink-0 transition-colors" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
            <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"></path>
            <path d="m9 12 2 2 4-4"></path>
          </svg>
          <div class="flex flex-col md:hidden lg:flex ml-3.5">
            <span class="text-[11.5px] font-bold uppercase tracking-wider text-slate-200">Runtime Security</span>
            <span class="text-[8.5px] text-slate-400 font-mono mt-0.5 uppercase tracking-wide">AI-Enriched Falco Alerts</span>
          </div>
        </router-link>

        <router-link
          to="/wazuh"
          @click="isMenuOpen = false"
          class="nav-link py-2.5 px-3 rounded-sm flex items-center transition-all"
          :class="route.path === '/wazuh' ? 'nav-active' : 'nav-inactive text-slate-400 hover:text-slate-200 hover:bg-slate-800/20'"
        >
          <svg class="w-[18px] h-[18px] shrink-0 transition-colors" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
            <rect x="2" y="3" width="20" height="14" rx="2" ry="2"></rect>
            <line x1="8" y1="21" x2="16" y2="21"></line>
            <line x1="12" y1="17" x2="12" y2="21"></line>
          </svg>
          <div class="flex flex-col md:hidden lg:flex ml-3.5">
            <span class="text-[11.5px] font-bold uppercase tracking-wider text-slate-200">Endpoint & Compliance</span>
            <span class="text-[8.5px] text-slate-400 font-mono mt-0.5 uppercase tracking-wide">Wazuh Posture & Insights</span>
          </div>
        </router-link>

        <router-link to="/sentinel" @click="isMenuOpen = false" class="nav-link py-2.5 px-3 rounded-sm flex items-center transition-all" :class="route.path === '/sentinel' ? 'nav-active' : 'nav-inactive text-slate-400 hover:text-slate-200 hover:bg-slate-800/20'">
          <svg class="w-[18px] h-[18px] shrink-0 transition-colors" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
            <circle cx="18" cy="5" r="3"></circle>
            <circle cx="6" cy="12" r="3"></circle>
            <circle cx="18" cy="19" r="3"></circle>
            <line x1="8.59" y1="13.51" x2="15.42" y2="17.49"></line>
            <line x1="15.41" y1="6.51" x2="8.59" y2="10.49"></line>
          </svg>
          <div class="flex flex-col md:hidden lg:flex ml-3.5">
            <span class="text-[11.5px] font-bold uppercase tracking-wider text-slate-200">Network Map</span>
            <span class="text-[8.5px] text-slate-400 font-mono mt-0.5 uppercase tracking-wide">Sentinel Topology</span>
          </div>
        </router-link>
        
        <router-link to="/settings" @click="isMenuOpen = false" class="nav-link py-2.5 px-3 rounded-sm flex items-center transition-all" :class="route.path === '/settings' ? 'nav-active' : 'nav-inactive text-slate-400 hover:text-slate-200 hover:bg-slate-800/20'">
          <svg class="w-[18px] h-[18px] shrink-0 transition-colors" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
            <circle cx="12" cy="12" r="3"></circle>
            <path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1 0 2.83 2 2 0 0 1-2.83 0l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-2 2 2 2 0 0 1-2-2v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83 0 2 2 0 0 1 0-2.83l.06-.06a1.65 1.65 0 0 0 .33-1.82 1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1-2-2 2 2 0 0 1 2-2h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 0-2.83 2 2 0 0 1 2.83 0l.06.06a1.65 1.65 0 0 0 1.82.33H9a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 2-2 2 2 0 0 1 2 2v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 0 2 2 0 0 1 0 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82V9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 2 2 2 2 0 0 1-2 2h-.09a1.65 1.65 0 0 0-1.51 1z"></path>
          </svg>
          <div class="flex flex-col md:hidden lg:flex ml-3.5">
            <span class="text-[11.5px] font-bold uppercase tracking-wider text-slate-200">Settings</span>
            <span class="text-[8.5px] text-slate-400 font-mono mt-0.5 uppercase tracking-wide">Infra & Storage</span>
          </div>
        </router-link>

        <div class="flex-1"></div>  
      </nav>

      <div class="hidden lg:block p-4 border-t border-slate-800/80 bg-[#0e1117]">
        <div class="flex items-center gap-2 mb-2.5">
          <span class="w-2 h-2 bg-emerald-400 rounded-full animate-pulse shrink-0"></span>
          <span class="text-[9.5px] text-slate-400 font-mono uppercase tracking-wider">USER:</span>
          <span class="text-[11px] text-[#f05a28] font-bold tracking-wide truncate">{{ username }}</span>
        </div>
        
        <div class="space-y-1.5 pt-2 border-t border-slate-800/50">
          <div class="flex items-center justify-between text-[9.5px] font-mono">
            <span class="text-slate-500 uppercase">Cluster</span>
            <span class="text-slate-300 font-medium">{{ systemData ? systemData.cluster_version : 'v1.31.2+k3s1' }}</span>
          </div>
          <div class="flex items-center justify-between text-[9.5px] font-mono">
            <span class="text-slate-500 uppercase">OS</span>
            <span class="text-slate-300 font-medium">{{ systemData ? systemData.vps_os : 'Debian GNU/Linux 12' }}</span>
          </div>
        </div>
      </div>
    </aside>

    <main class="flex-1 flex flex-col min-h-0 overflow-y-auto">
      <div v-if="isDemoMode" class="bg-gradient-to-r from-[#f05a28]/20 via-amber-500/10 to-[#f05a28]/20 border-b border-[#f05a28]/40 px-4 py-1.5 flex items-center justify-between text-xs text-slate-200 z-[60] backdrop-blur-md shrink-0">
        <div class="flex items-center gap-2">
          <span class="inline-flex items-center gap-1.5 px-2 py-0.5 rounded-full bg-[#f05a28]/30 border border-[#f05a28]/50 text-[10px] font-bold text-[#f05a28] uppercase tracking-wider">
            <span class="w-1.5 h-1.5 rounded-full bg-green-400 animate-pulse"></span>
            Interactive Demo
          </span>
          <span class="text-slate-300 text-[11px] hidden sm:inline">
            K-Guard v1.7.0 live demo mode (simulated Falco eBPF, Wazuh & Network Sentinel telemetry — read-only)
          </span>
        </div>
        <div class="flex items-center gap-3">
          <a href="https://devopsnotes.org" target="_blank" class="text-[11px] text-[#f05a28] hover:underline flex items-center gap-1 font-semibold">
            ← Portfolio
          </a>
        </div>
      </div>

      <div class="absolute inset-0 pointer-events-none flex items-center justify-center z-0">
        <div class="w-[400px] h-[400px] border border-blue-500/5 rounded-full absolute"></div>
        <img src="/logo_background.png" alt="K-Guard" class="w-[350px] opacity-[0.05] pointer-events-none select-none" />
      </div>

      <header class="h-14 shrink-0 border-b border-slate-800/60 bg-[#111217]/80 flex items-center justify-between px-6 lg:px-8 z-[45] backdrop-blur-xl">
        <div class="flex items-center gap-4">
          <button @click="isMenuOpen = !isMenuOpen" class="lg:hidden text-slate-400 hover:text-white p-2 transition-colors cursor-pointer bg-slate-800/30 rounded-sm">
            <span class="text-xl">{{ isMenuOpen ? '✕' : '☰' }}</span>
          </button>
          <h2 class="text-sm font-bold text-white tracking-widest uppercase">{{ pageTitle }}</h2>
        </div>
        
        <div class="flex items-center gap-4">
            <div class="hidden md:flex flex-col items-end">
                <span class="text-[8px] text-green-500 font-bold tracking-[0.2em] uppercase flex items-center gap-2">
                    <span class="relative flex h-1.5 w-1.5">
                        <span class="animate-ping absolute inline-flex h-full w-full rounded-full bg-green-400 opacity-75"></span>
                        <span class="relative inline-flex rounded-full h-1.5 w-1.5 bg-green-500"></span>
                    </span>
                    K3s Cloud online
                </span>
                <span class="text-[9px] text-slate-600 font-mono mt-0.5 uppercase">Latency: {{ isDemoMode ? '12' : systemLatency }}ms</span>
            </div>
            <button v-if="!isDemoMode" @click="handleLogout" class="group flex items-center gap-2 bg-red-500/10 hover:bg-red-500/20 border border-[#f05a28] px-3 py-1.5 rounded-sm transition-all duration-300 cursor-pointer">
              <span class="text-[10px] text-[#f05a28] font-bold uppercase tracking-tighter">LogOut</span>
            </button>
            <div v-else class="flex items-center gap-2 bg-emerald-500/10 border border-emerald-500/30 px-3 py-1 rounded-sm">
              <span class="text-[10px] text-emerald-400 font-bold uppercase tracking-wider">Mode Invité</span>
            </div>
        </div>
      </header>

      <div class="flex-1 flex flex-col relative z-20" custom-scrollbar>
        <router-view v-slot="{ Component, route }">
          <transition name="page" mode="default">
            <component :is="Component" :key="route.fullPath" class="h-full"/>
          </transition>
        </router-view>
      </div>
    </main>
  </div>
</template>