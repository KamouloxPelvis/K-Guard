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
    const response = await fetch('/api/k3s/deployments/all', {
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
      const response = await fetch(`/api/k3s/restart/${namespace}/${appName.toLowerCase()}`, {
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
          class="bg-[#111217] border border-slate-800/40 p-0 transition-all duration-300 hover:border-slate-700 group relative">
        
        <div class="h-[2px] w-full bg-slate-800 group-hover:bg-blue-600 transition-colors duration-500"></div>

        <div class="p-8">
          <div class="flex justify-between items-center mb-10">
            <h3 class="text-lg font-medium text-slate-200 tracking-widest uppercase">{{ app.name }}</h3>
            <span :class="getAppStatus(app.id).class" 
              class="text-[8px] font-bold px-2 py-1 tracking-[0.2em] uppercase border transition-all duration-500">
              STATUS: {{ getAppStatus(app.id).text }}
            </span>
          </div>

          <div :class="[
              getAppStatus(app.id).text === 'UPDATE REQUIRED' ? 'bg-red-600' : 
              getAppStatus(app.id).text === 'WATCH OUT' ? 'bg-orange-500' : 
              'bg-slate-800 group-hover:bg-blue-600'
            ]" 
            class="h-[2px] w-full mb-10 transition-colors duration-500">
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
              :class="loadingApp === app.id ? 'bg-slate-800 text-slate-600' : 'bg-blue-600 text-white hover:bg-blue-700'"
            >
              {{ loadingApp === app.id ? 'Running Analysis...' : 'Launch Scan' }}
            </button>

            <button 
              v-if="scanResults[app.id]?.summary?.critical > 0" 
              @click="patchApplication(app.namespace, app.name, app.id)"
              :disabled="patchingApp === app.id"
              class="w-full py-4 text-[10px] font-bold uppercase tracking-[0.4em] bg-orange-600 text-white hover:bg-orange-700 transition-all cursor-pointer block text-center"
            >
              {{ patchingApp === app.id ? 'Updating Cluster...' : '⚠ Patch & Pull Latest' }}
            </button>

            <button v-if="scanResults[app.id]" @click="openVulnerabilityDetails(app)" 
                    class="w-full py-3 text-[9px] text-slate-500 hover:text-white border border-transparent hover:border-slate-800 uppercase font-bold tracking-[0.3em] transition-all cursor-pointer">
              [ Open Report ]
            </button>
          </div>
        </div>
      </div>
    </div>
    
    <div v-else class="text-center py-20 border border-dashed border-slate-800">
       <p class="text-slate-500 font-mono text-xs uppercase tracking-[0.3em]">No Deployments Found in Namespace</p>
    </div>
  </div>
</template>