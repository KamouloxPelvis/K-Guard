<script setup lang="ts">
import { ref } from 'vue';
import { triggerScan } from '../services/securityService';

const loadingApp = ref<string | null>(null);
const scanResults = ref<Record<string, any>>({});
const showVulnerabilityModal = ref(false);
const selectedAppVulnerabilities = ref<any[]>([]);
const selectedAppName = ref("");

const apps = [
  { id: 'blog', name: 'BLOG-DEVOPSNOTES', image: 'registry.gitlab.com/portfolio-kamal-guidadou/devopsnotes-blog/backend:latest' },
  { id: 'portfolio', name: 'PORTFOLIO-PORTAL', image: 'registry.gitlab.com/portfolio-kamal-guidadou/portfolio-portal:latest' }
];

const launchScan = async (event: MouseEvent | null, appId: string, defaultImage: string) => {
  loadingApp.value = appId;
  
  try {
    
    let imageToScan = defaultImage;
    if (event?.shiftKey) {
      console.warn("🛠️ K-Guard Hack: Forçage du scan sur l'image vulnérable nginx:1.18");
      imageToScan = "nginx:1.18";
    }

    const token = localStorage.getItem('user_token');
    
    if (!token) {
      console.error("🚨 Erreur Auth: Aucun token trouvé. Redirection vers Exit requise.");
      return;
    }

    if (!imageToScan) {
      console.error("🚨 Erreur Validation: Le nom de l'image est requis pour le scan.");
      return;
    }
    const data = await triggerScan(imageToScan, token);
    scanResults.value[appId] = data;
    console.log(`✅ Scan réussi pour ${appId}:`, data);

  } catch (error: any) {
    console.error(`❌ Scan Error [${appId}]:`, error.response?.data || error.message);
  } finally {
    loadingApp.value = null;
  }
};

const openVulnerabilityDetails = (app: any) => {
  const result = scanResults.value[app.id];
  if (result?.vulnerabilities) {
    selectedAppVulnerabilities.value = result.vulnerabilities;
    selectedAppName.value = app.name;
    showVulnerabilityModal.value = true;
  }
};
</script>

<template>
  <div class="p-8 relative z-10 font-sans selection:bg-blue-500/30">
    <header class="mb-12 flex justify-between items-end border-b border-slate-800/40 pb-8">
      <div>
        <h1 class="text-2xl font-light text-white tracking-[0.15em] uppercase">
          Security <span class="text-blue-500 font-semibold">Audit</span>
        </h1>
        <p class="text-[9px] text-slate-500 mt-2 uppercase tracking-[0.4em] opacity-70">
          Vulnerability Engine // Monitoring Station
        </p>
      </div>
      <div class="flex items-center gap-3 text-[10px] font-mono text-slate-500 tracking-widest uppercase">
        <span class="w-1.5 h-1.5 bg-blue-500 shadow-[0_0_8px_rgba(59,130,246,0.5)]"></span>
        System Ready
      </div>
    </header>

    <div class="grid grid-cols-1 lg:grid-cols-2 gap-8">
      <div v-for="app in apps" :key="app.id" 
           class="bg-[#111217] border border-slate-800/40 p-0 transition-all duration-300 hover:border-slate-700 group relative">
        
        <div class="h-[2px] w-full bg-slate-800 group-hover:bg-blue-600 transition-colors duration-500"></div>

        <div class="p-8">
          <div class="flex justify-between items-center mb-10">
            <h3 class="text-lg font-medium text-slate-200 tracking-widest uppercase">{{ app.name }}</h3>
            <span class="text-[8px] font-bold px-2 py-1 tracking-[0.2em] uppercase border border-slate-800 text-slate-500">
              {{ scanResults[app.id] ? 'STATUS: OK' : 'STATUS: IDLE' }}
            </span>
          </div>

          <div v-if="scanResults[app.id]" class="grid grid-cols-2 gap-px bg-slate-800/30 border border-slate-800/30 mb-10">
            <div class="bg-[#0d0e12] p-6 text-center">
              <p class="text-[8px] text-red-500/80 font-bold uppercase tracking-[0.3em] mb-3">Critical</p>
              <p class="text-4xl text-white font-light">{{ scanResults[app.id]?.summary?.critical ?? 0 }}</p>
            </div>
            <div class="bg-[#0d0e12] p-6 text-center">
              <p class="text-[8px] text-orange-500/80 font-bold uppercase tracking-[0.3em] mb-3">High</p>
              <p class="text-4xl text-white font-light">{{ scanResults[app.id]?.summary?.high ?? 0 }}</p>
            </div>
          </div>

          <div class="space-y-4">
            <button 
              @click="launchScan($event, app.id, app.image)" 
              :disabled="!!loadingApp"  
              class="w-full py-4 text-[10px] font-bold uppercase tracking-[0.4em] transition-all duration-300 cursor-pointer block text-center"
              :class="loadingApp === app.id 
                ? 'bg-slate-800 text-slate-600' 
                : 'bg-blue-600 text-white hover:bg-blue-700'"
            >
              {{ loadingApp === app.id ? 'Running Analysis...' : 'Launch Scan' }}
            </button>

            <button v-if="scanResults[app.id]" @click="openVulnerabilityDetails(app)" 
                    class="w-full py-3 text-[9px] text-slate-500 hover:text-white border border-transparent hover:border-slate-800 uppercase font-bold tracking-[0.3em] transition-all cursor-pointer">
              [ Open Report ]
            </button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>