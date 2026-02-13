<script setup lang="ts">
  import { ref, onMounted } from 'vue';
  import { triggerScan } from '../services/securityService';

  interface AppDeployment {
  id: string;
  name: string;
  namespace: string;
  image: string;
}
  // États pour la découverte dynamique
  const apps = ref<AppDeployment[]>([]); 
  const isLoadingApps = ref(true);
  const patchingApp = ref<string | null>(null);

  // États pour les résultats
  const loadingApp = ref<string | null>(null);
  const scanResults = ref<Record<string, any>>({});
  const showVulnerabilityModal = ref(false);
  const selectedAppVulnerabilities = ref<any[]>([]);
  const selectedAppName = ref("");

  // Fonction de découverte dynamique
  const fetchApps = async () => {
  try {
    const token = localStorage.getItem('user_token');
    const response = await fetch('/k-guard/api/k3s/deployments/all', {
      headers: { 'Authorization': `Bearer ${token}` }
    }); 
    
    if (response.status === 401) {
      console.warn("Session expirée !");
      localStorage.removeItem('user_token');
      window.location.href = '/login';
      return;
    }
    
    if (!response.ok) {
      // Si on a une erreur 500, on essaie de lire le message d'erreur
      const errorDetail = await response.text();
      throw new Error(`Erreur Serveur ${response.status}: ${errorDetail}`);
    }

    const contentType = response.headers.get("content-type");
    if (!contentType || !contentType.includes("application/json")) {
      throw new TypeError("🚨 Le serveur a renvoyé du HTML (Vérifie le proxy Vite)");
    }

    const data = await response.json();
    apps.value = data;
    console.log("✅ Apps chargées :", data);
  } catch (error) {
    console.error("🚨 K-Guard Discovery Error:", error);
  } finally {
    isLoadingApps.value = false;
  }
};

  onMounted(fetchApps);

  const launchScan = async (event: MouseEvent | null, appId: string, defaultImage: string) => {
    loadingApp.value = appId;
    
    try {
      
      let imageToScan = defaultImage;
      if (event?.shiftKey) {
        console.log("🛠️ K-Guard Hack: Forçage du scan sur l'image vulnérable nginx:1.18");
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
      if (data.status === 'error') {
          console.error("❌ Erreur moteur Trivy:", data.message);
          alert("Le moteur de scan est injoignable sur le VPS.");
      } else {
          scanResults.value[appId] = data;
      }

      } catch (error: any) {
        console.error(`❌ Scan Error [${appId}]:`, error.response?.data || error.message);
      } finally {
        loadingApp.value = null;
      }
    };

  const getAppStatus = (appId: string) => {
    const result = scanResults.value[appId];
    if (!result) return { text: 'IDLE', class: 'text-slate-500 border-slate-800' };

    const critical = result.summary?.critical || 0;
    const high = result.summary?.high || 0;

    if (critical > 0) {
      return { text: 'UPDATE REQUIRED', class: 'text-red-500 border-red-500/50 bg-red-500/5' };
    } 
    if (high > 10) {
      return { text: 'WATCH OUT', class: 'text-orange-500 border-orange-500/50 bg-orange-500/5' };
    }
    return { text: 'SECURE', class: 'text-green-500 border-green-500/50 bg-green-500/5' };
  };

  const openVulnerabilityDetails = (app: any) => {
    const result = scanResults.value[app.id];
    if (result?.vulnerabilities) {
      selectedAppVulnerabilities.value = result.vulnerabilities;
      selectedAppName.value = app.name;
      showVulnerabilityModal.value = true;
    }
  };

  const patchApplication = async (namespace: string, appName: string, appId: string) => {
    if (!confirm(`🚀 Lancer le Rolling Update pour ${appName} ?`)) return;  
    patchingApp.value = appId;
    try {
      const response = await fetch(`/k-guard/api/k3s/restart/${namespace}/${appName.toLowerCase()}`, {
        method: 'POST'
      });
      if (response.ok) alert("✅ Update lancé !");
    } catch (error) {
      console.error("Erreur patch:", error);
    } finally {
      patchingApp.value = null;
    }
  };

  onMounted(fetchApps);
</script>

<template>
  <div class="p-8 relative z-10 font-sans selection:bg-blue-500/30">
    <header class="mb-12 flex justify-between items-end border-b border-slate-800/40 pb-8">
      <div>
        <p class="text-[12px] text-slate-500 mt-6 uppercase tracking-[0.5em]">Vulnerability Engine // Monitoring Station</p>
      </div>
    </header>

    <div class="astuce mb-8 p-4 border border-blue-500/20 bg-blue-500/5 text-xs text-slate-400 italic">
      Astuce : Shift + clic gauche force le scan de vulnérabilités sur Nginx 1.18 pour contrôler la 
      réactivité du système face à une image conteneur obsolète et prouver l'efficacité de notre moteur d'audit Trivy.
    </div>

    <Teleport to="body">
      <div v-if="showVulnerabilityModal" 
          class="fixed inset-0 z-[100] flex items-center justify-center p-4 bg-black/90 backdrop-blur-md">
        
        <div class="bg-[#1c2532] border border-slate-700 w-full max-w-4xl max-h-[80vh] flex flex-col shadow-2xl">
          
          <div class="p-6 border-b border-slate-700 flex justify-between items-center bg-[#121822]">
            <div>
              <h2 class="text-white font-valorant text-lg tracking-widest">{{ selectedAppName }}</h2>
              <p class="text-[10px] text-slate-500 uppercase mt-1">Security Audit Report // Trivy v0.48</p>
            </div>
            <button @click="showVulnerabilityModal = false" class="text-slate-500 hover:text-white transition-colors cursor-pointer text-xl">✕</button>
          </div>

          <div class="flex-1 overflow-y-auto p-6 custom-scrollbar bg-[#0d1117]">
            <table class="w-full text-left border-collapse">
              <thead>
                <tr class="text-[10px] text-slate-500 uppercase tracking-tighter border-b border-slate-800">
                  <th class="pb-4">ID</th>
                  <th class="pb-4">Package</th>
                  <th class="pb-4 text-right">Severity</th>
                </tr>
              </thead>
              <tbody class="divide-y divide-slate-800/50">
                <tr v-for="vuln in selectedAppVulnerabilities" :key="vuln.id" class="group">
                  <td class="py-4 text-xs font-mono text-blue-400">{{ vuln.id }}</td>
                  <td class="py-4 text-xs text-slate-300">{{ vuln.pkg }}</td>
                  <td class="py-4 text-right">
                    <span :class="vuln.severity === 'CRITICAL' ? 'text-red-500 bg-red-500/10' : 'text-orange-500 bg-orange-500/10'"
                          class="text-[9px] font-bold px-2 py-0.5 border border-current rounded-sm uppercase">
                      {{ vuln.severity }}
                    </span>
                  </td>
                </tr>
              </tbody>
            </table>
            
            <div v-if="selectedAppVulnerabilities.length === 0" class="py-20 text-center">
              <p class="text-green-500 font-mono text-sm uppercase tracking-widest">✅ No High or Critical Vulnerabilities Found</p>
            </div>
          </div>

          <div class="p-4 border-t border-slate-700 bg-[#121822] text-right">
            <button @click="showVulnerabilityModal = false" class="bg-slate-700 hover:bg-slate-600 text-white px-4 py-2 rounded uppercase text-[10px] font-bold tracking-widest transition-all">Fermer</button>
          </div>
        </div>
      </div>
    </Teleport>

     <div v-if="apps.length > 0" class="grid grid-cols-1 lg:grid-cols-2 gap-8">
      <div v-for="app in apps" :key="app.id" 
          class="group relative bg-[#181b1f]/60 backdrop-blur-sm border border-slate-800 rounded-sm hover:border-blue-500/40 transition-all flex flex-col h-[520px]">
        
        <div v-if="loadingApp === app.id" 
            class="absolute inset-0 z-20 bg-[#0b0c10]/90 backdrop-blur-sm flex flex-col items-center justify-center">
          <div class="radar-loader mb-4"></div>
          <p class="text-[10px] font-mono text-blue-500 animate-pulse tracking-[0.2em]">TRIVY ENGINE : SCANNING</p>
        </div>

        <div class="h-[2px] w-full bg-slate-800 group-hover:bg-blue-600 transition-colors duration-500"></div>

        <div class="p-8 flex flex-col h-full">
          <div class="flex justify-between items-start mb-6 h-12">
            <h3 class="text-md font-bold text-slate-200 tracking-widest uppercase leading-tight">{{ app.name }}</h3>
            <span :class="getAppStatus(app.id).class" 
              class="text-[8px] font-black px-2 py-1 tracking-[0.2em] uppercase border whitespace-nowrap">
              {{ getAppStatus(app.id).text }}
            </span>
          </div>

          <div :class="[
              getAppStatus(app.id).text === 'UPDATE REQUIRED' ? 'bg-red-600' : 
              getAppStatus(app.id).text === 'WATCH OUT' ? 'bg-orange-500' : 
              'bg-slate-800'
            ]" class="h-[1px] w-full mb-8"></div>

          <div class="flex-1">
            <div v-if="scanResults[app.id]" class="grid grid-cols-2 gap-px bg-slate-800/30 border border-slate-800/30 mb-6">
              <div class="bg-black/40 p-4 text-center">
                <p class="text-[8px] text-red-500/80 font-bold uppercase mb-1">Critical</p>
                <p class="text-3xl text-white font-light">{{ scanResults[app.id]?.summary?.critical ?? 0 }}</p>
              </div>
              <div class="bg-black/40 p-4 text-center">
                <p class="text-[8px] text-orange-500/80 font-bold uppercase mb-1">High</p>
                <p class="text-3xl text-white font-light">{{ scanResults[app.id]?.summary?.high ?? 0 }}</p>
              </div>
            </div>
            <div v-else class="flex items-center justify-center h-[100px] border border-dashed border-slate-800/50 mb-6 bg-black/10">
              <p class="text-[9px] text-slate-600 uppercase tracking-widest italic">Awaiting Security Audit</p>
            </div>
          </div>

          <div class="space-y-3 mt-auto">
            <button 
              @click="launchScan($event, app.id, app.image)" 
              :disabled="!!loadingApp"  
              class="w-full py-3 text-[10px] font-bold uppercase tracking-[0.3em] transition-all bg-blue-600 text-white hover:bg-blue-700 disabled:opacity-50 cursor-pointer"
            >
              Launch Scan
            </button>

            <div class="h-10"> 
              <div class="flex gap-3 mt-4 items-center justify-between">
                <button 
                  v-if="scanResults[app.id]" 
                  @click="openVulnerabilityDetails(app)" 
                  class="flex-1 py-2 text-[10px] font-bold uppercase tracking-widest border border-slate-700 bg-slate-800/30 text-slate-400 hover:border-blue-500/50 hover:text-blue-400 transition-all duration-300 rounded-sm cursor-pointer"
                >
                  Full Report
                </button>

                <button 
                  v-if="scanResults[app.id]?.summary?.critical > 0" 
                  @click="patchApplication(app.namespace, app.name, app.id)"
                  class="flex-1 py-2 text-[10px] font-bold uppercase tracking-widest border border-orange-500/40 bg-orange-500/5 text-orange-500 hover:bg-orange-600 hover:text-white transition-all duration-300 rounded-sm cursor-pointer"
                >
                  Patch
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
    
    <div v-else class="text-center py-20 border border-dashed border-slate-800">
       <p class="text-slate-500 font-mono text-xs uppercase tracking-[0.3em]">No Deployments Found in Namespace</p>
    </div>
  </div>
</template>

<style scoped>
  /* L'animation Radar pour le scan */
  .radar-loader {
    width: 40px;
    height: 40px;
    border: 1px solid #3b82f6; /* Bleu comme tes boutons */
    border-radius: 50%;
    position: relative;
    animation: pulse-radar 1.5s infinite;
  }

  .radar-loader::after {
    content: '';
    position: absolute;
    top: 50%; left: 50%;
    width: 100%; height: 100%;
    background: #3b82f6;
    border-radius: 50%;
    transform: translate(-50%, -50%) scale(0);
    opacity: 0.5;
    animation: inner-pulse 1.5s infinite;
  }

  @keyframes pulse-radar {
    0% { transform: scale(0.9); opacity: 1; }
    100% { transform: scale(1.3); opacity: 0; }
  }

  @keyframes inner-pulse {
    0% { transform: translate(-50%, -50%) scale(0); opacity: 0.8; }
    100% { transform: translate(-50%, -50%) scale(1); opacity: 0; }
  }
  </style>