<script setup lang="ts">
  import { ref, onMounted, onUnmounted } from 'vue';
  
  import api from '../services/api'; 
  import { triggerScan } from '../services/securityService';

  // --- INTERFACES ---
  interface AppDeployment {
    id: string;
    name: string;
    namespace: string;
    image: string;
  }

  interface StatusResult {
    text: string;
    class: string;
  }

  // --- ÉTATS RÉACTIFS ---
  const apps = ref<AppDeployment[]>([]); 
  const isLoadingApps = ref(true);
  const loadingApp = ref<string | null>(null);
  
  // États Scan & Vulnérabilités
  const scanResults = ref<Record<string, any>>({});
  const showVulnerabilityModal = ref(false);
  const selectedAppVulnerabilities = ref<any[]>([]);
  const selectedAppName = ref("");

  // États Remédiation (Patch & Logs)
  const patchingApp = ref<string | null>(null);
  const showPatchModal = ref(false);
  const patchLogs = ref("");
  const activePatchApp = ref("");
  let logInterval: any = null;

  // --- FONCTIONS UTILITAIRES ---
  const isDemoMode = (appId: string) => {
    return scanResults.value[appId]?.image === 'nginx:1.18';
  };

  // --- 1. CHARGEMENT DES APPS (DRY: Pas de headers manuels) ---
  const fetchApps = async () => {
    try {
      // L'intercepteur api.ts injecte le Bearer Token automatiquement
      const response = await api.get('/api/k3s/deployments/all');
      apps.value = response.data;
    } catch (error) {
      console.error("🚨 K-Guard Discovery Error:", error);
    } finally {
      isLoadingApps.value = false;
    }
  };

  // --- 2. LANCEMENT DU SCAN TRIVY ---
  const launchScan = async (event: MouseEvent | null, appId: string, defaultImage: string) => {
    loadingApp.value = appId;
    try {
      let imageToScan = defaultImage;
      // Cheat code pour la démo
      if (event?.shiftKey) imageToScan = "nginx:1.18"; 

      // Note: triggerScan utilise peut-être encore fetch natif, on passe le token par sécurité
      const token = localStorage.getItem('user_token');
      const data = await triggerScan(imageToScan, token || "");
      
      if (data.status === 'success') {
        scanResults.value[appId] = data;
      }
    } catch (error) {
      console.error("❌ Scan Error:", error);
    } finally {
      loadingApp.value = null;
    }
  };

  // --- 3. LOGIQUE DE REMÉDIATION (PATCH INTELLIGENT) ---
  
  // Fonction de polling pour récupérer les logs en quasi-temps réel
  const fetchPatchLogs = async (namespace: string, appName: string) => {
    try {
      const response = await api.get(`/api/k3s/patch-logs/${namespace}/${appName}`);
      patchLogs.value = response.data.logs;
    } catch (e) {
      patchLogs.value += "\n[SYSTEM] Connexion au flux Kubernetes instable...";
    }
  };

  const patchApplication = async (namespace: string, appName: string, appId: string) => {
    const result = scanResults.value[appId];

    if (isDemoMode(appId)) {
      alert("⚠️ ACTION IMPOSSIBLE\n\nCeci est une démo technique (Stress Test).\nCette image n'existe pas réellement dans votre cluster, le patch ne peut donc pas être appliqué.");
      return; 
    }

    const suggestion = result?.vulnerabilities?.find((v: any) => v.fixed_version)?.fixed_version;
    
    if (!suggestion) {
      alert("Aucune version de correction automatique trouvée dans le rapport Trivy.");
      return;
    }

    if (result.image === 'nginx:1.18') {
      alert("⚠️ ACTION IMPOSSIBLE\n\nCeci est une démo technique (Stress Test).\nCette image n'existe pas réellement dans votre cluster, le patch ne peut donc pas être appliqué.");
      return; 
    }

    if (!confirm(`🚀 K-Guard suggère : ${suggestion}\nLancer la remédiation pour ${appName} ?`)) return;

    // Initialisation UI
    showPatchModal.value = true;
    activePatchApp.value = appName;
    patchLogs.value = "🚀 K-GUARD ENGINE: Initialisation...\n🛰️ Connexion au cluster K3s...\n📦 Préparation du patch d'image...";
    patchingApp.value = appId;

    try {
      // 1. Appel API (DRY: Pas de headers, api.ts gère tout)
      await api.post('/api/k3s/patch-image', {
        namespace: namespace,
        deployment: appName,
        new_image: `${result.image.split(':')[0]}:${suggestion}` 
      });

      // 2. Démarrage du streaming des logs (polling toutes les 2s)
      logInterval = setInterval(() => fetchPatchLogs(namespace, appName), 2000);

    } catch (error) {
      console.error("Patch Error:", error);
      patchLogs.value += "\n❌ ERREUR CRITIQUE: Le backend n'a pas pu appliquer le patch.";
    } finally {
      // On laisse le modal ouvert pour voir les logs, mais on débloque le bouton
      patchingApp.value = null; 
      // On nettoie le résultat du scan car l'image va changer
      delete scanResults.value[appId];
    }
  };

  const closePatchModal = () => {
    showPatchModal.value = false;
    if (logInterval) clearInterval(logInterval);
  };

  // --- UTILITAIRES D'AFFICHAGE ---

  // Retourne le statut avec typage strict pour éviter l'erreur 'void'
  const getAppStatus = (appId: string): StatusResult => {
    const result = scanResults.value[appId];
    if (!result) return { text: 'IDLE', class: 'text-slate-500 border-slate-800' };

    const critical = result.summary?.critical || 0;
    const high = result.summary?.high || 0;

    if (critical > 0) return { text: 'UPDATE REQUIRED', class: 'text-red-500 border-red-500/50 bg-red-500/5' };
    if (high > 10) return { text: 'WATCH OUT', class: 'text-orange-500 border-orange-500/50 bg-orange-500/5' };
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

  // Lifecycle hooks
  onMounted(fetchApps);
  onUnmounted(() => {
    if (logInterval) clearInterval(logInterval);
  });
</script>

<template>
  <div class="p-8 relative z-10 font-sans">
    
    <header class="mb-12 flex justify-between items-end border-b border-slate-800/40 pb-8">
      <p class="text-[12px] text-slate-500 mt-6 uppercase tracking-[0.5em]">Vulnerability Monitor & Smart Patch Station</p>
    </header>

    <div class="mb-8 p-4 border border-blue-500/20 bg-blue-500/5 text-xs text-slate-400 italic">
      Astuce : Shift + clic gauche force le scan sur une image volontairement obsolète Nginx 1.18 pour tester la détection. ( Stress test )
    </div>

    <Teleport to="body">
      <div v-if="showVulnerabilityModal" class="fixed inset-0 z-[100] flex items-center justify-center p-4 bg-black/90 backdrop-blur-md">
        <div class="bg-[#1c2532] border border-slate-700 w-full max-w-4xl max-h-[80vh] flex flex-col shadow-2xl">
          <div class="p-6 border-b border-slate-700 flex justify-between items-center bg-[#121822]">
            <div>
              <h2 class="text-white font-valorant text-lg tracking-widest">{{ selectedAppName }}</h2>
              <p class="text-[10px] text-slate-500 uppercase mt-1">Security Audit Report // Trivy v0.48</p>
            </div>
            <button @click="showVulnerabilityModal = false" class="text-slate-500 hover:text-white transition-colors cursor-pointer text-xl">✕</button>
          </div>
          <div class="flex-1 overflow-y-auto p-6 bg-[#0d1117] custom-scrollbar">
            <table class="w-full text-left border-collapse">
              <thead>
                <tr class="text-[10px] text-slate-500 uppercase tracking-tighter border-b border-slate-800">
                  <th class="pb-4">ID</th>
                  <th class="pb-4">Package</th>
                  <th class="pb-4 text-green-500">Fixed Version</th>
                  <th class="pb-4 text-right">Severity</th>
                </tr>
              </thead>
              <tbody class="divide-y divide-slate-800/50">
                <tr v-for="vuln in selectedAppVulnerabilities" :key="vuln.id">
                  <td class="py-4 text-xs font-mono text-blue-400">{{ vuln.id }}</td>
                  <td class="py-4 text-xs text-slate-300">{{ vuln.pkg }}</td>
                  <td class="py-4 text-xs text-green-400 font-mono">{{ vuln.fixed_version || '-' }}</td>
                  <td class="py-4 text-right">
                    <span :class="vuln.severity === 'CRITICAL' ? 'text-red-500 bg-red-500/10' : 'text-orange-500 bg-orange-500/10'"
                          class="text-[9px] font-bold px-2 py-0.5 border border-current rounded-sm uppercase">
                      {{ vuln.severity }}
                    </span>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
          <div class="p-4 border-t border-slate-700 bg-[#121822] text-right">
            <button @click="showVulnerabilityModal = false" class="bg-slate-700 hover:bg-slate-600 text-white px-4 py-2 rounded uppercase text-[10px] font-bold tracking-widest transition-all">Fermer</button>
          </div>
        </div>
      </div>
    </Teleport>

    <Teleport to="body">
      <div v-if="showPatchModal" class="fixed inset-0 z-[110] flex items-center justify-center p-4 bg-black/80 backdrop-blur-sm">
        <div class="bg-[#0b0f15] border border-orange-500/30 w-full max-w-3xl shadow-[0_0_50px_-12px_rgba(249,115,22,0.2)]">
          
          <div class="p-4 border-b border-slate-800 flex justify-between items-center bg-black/40">
            <div class="flex items-center gap-3">
              <div class="w-2 h-2 bg-orange-500 animate-pulse rounded-full"></div>
              <h2 class="text-orange-500 font-mono text-[10px] uppercase tracking-[0.2em]">Patching Deployment: {{ activePatchApp }}</h2>
            </div>
            <button @click="closePatchModal" class="text-slate-500 hover:text-white transition-colors cursor-pointer">✕</button>
          </div>

          <div class="p-6 h-80 overflow-y-auto font-mono text-[11px] bg-black/60 custom-scrollbar">
            <pre class="text-blue-400/90 whitespace-pre-wrap leading-relaxed">{{ patchLogs }}</pre>
            <div class="mt-4 flex items-center gap-2 text-slate-600">
              <span class="animate-spin inline-block">⚙️</span>
              <span class="italic uppercase text-[9px] tracking-widest">Kubernetes Rolling Update in progress...</span>
            </div>
          </div>

          <div class="p-4 bg-slate-900/20 text-right">
            <button @click="closePatchModal" class="border border-slate-700 text-slate-400 px-4 py-2 text-[10px] hover:bg-white/5 uppercase font-bold tracking-widest transition-all cursor-pointer">
              Fermer la console
            </button>
          </div>
        </div>
      </div>
    </Teleport>

    <div v-if="apps.length > 0" class="grid grid-cols-1 lg:grid-cols-2 gap-8">
      <div v-for="app in apps" :key="app.id" class="relative bg-[#181b1f]/60 backdrop-blur-sm border border-slate-800 rounded-sm hover:border-blue-500/40 transition-all flex flex-col h-[520px]">
        
        <div v-if="loadingApp === app.id" class="absolute inset-0 z-20 bg-[#0b0c10]/90 backdrop-blur-sm flex flex-col items-center justify-center">
          <div class="radar-loader mb-4"></div>
          <p class="text-[10px] font-mono text-blue-500 animate-pulse tracking-[0.2em]">TRIVY ENGINE : SCANNING</p>
        </div>

        <div class="p-8 flex flex-col h-full">
          <div class="flex justify-between items-start mb-6 h-20"><div>
            <h3 class="text-md font-bold text-slate-200 tracking-widest uppercase leading-tight">{{ app.name }}</h3>
            
            <div class="flex flex-col mt-1 gap-1">
              <p class="text-[10px] text-slate-200 font-mono">Namespace: {{ app.namespace }}</p>
              
              <p class="text-[11px] font-mono tracking-wider transition-colors duration-300"
                :class="isDemoMode(app.id) ? 'text-orange-400 font-bold animate-pulse' : 'text-slate-400'">
                Image: {{ isDemoMode(app.id) ? '⚠️ DÉMO : Nginx 1.18' : app.image }}
              </p>
            </div>
          </div>

          <div class="flex flex-col items-end gap-2">
              <span :class="getAppStatus(app.id).class" class="text-[8px] font-black px-2 py-1 tracking-[0.2em] uppercase border whitespace-nowrap transition-all duration-500">
                {{ patchingApp === app.id ? 'PATCHING...' : getAppStatus(app.id).text }}
              </span>
              <div v-if="patchingApp === app.id" class="flex gap-1">
                <span class="w-1 h-1 bg-orange-500 animate-bounce"></span>
                <span class="w-1 h-1 bg-orange-500 animate-bounce [animation-delay:-0.3s]"></span>
                <span class="w-1 h-1 bg-orange-500 animate-bounce [animation-delay:-0.5s]"></span>
              </div>
            </div>
          </div>

          <div :class="[
            patchingApp === app.id ? 'bg-blue-500 animate-pulse' :
            getAppStatus(app.id).text === 'UPDATE REQUIRED' ? 'bg-red-600' : 
            getAppStatus(app.id).text === 'WATCH OUT' ? 'bg-orange-500' : 
            'bg-slate-800'
          ]" class="h-[1px] w-full mb-8 transition-colors duration-700"></div>

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
              :disabled="!!loadingApp || !!patchingApp"  
              class="w-full py-3 text-[10px] font-bold uppercase tracking-[0.3em] transition-all bg-blue-600 text-white hover:bg-blue-700 disabled:opacity-50 cursor-pointer"
            >
              Launch Scan
            </button>

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
                :disabled="!!patchingApp"
                class="flex-1 py-2 text-[10px] font-bold uppercase tracking-widest border border-orange-500/40 bg-orange-500/5 text-orange-500 hover:bg-orange-600 hover:text-white disabled:opacity-30 disabled:cursor-not-allowed transition-all duration-300 rounded-sm cursor-pointer"
              >
                Patch
              </button>
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
  /* Animation Radar */
  .radar-loader {
    width: 40px; height: 40px;
    border: 1px solid #3b82f6; border-radius: 50%;
    position: relative; animation: pulse-radar 1.5s infinite;
  }
  .radar-loader::after {
    content: ''; position: absolute; top: 50%; left: 50%;
    width: 100%; height: 100%;
    background: #3b82f6; border-radius: 50%;
    transform: translate(-50%, -50%) scale(0);
    opacity: 0.5; animation: inner-pulse 1.5s infinite;
  }
  @keyframes pulse-radar { 0% { transform: scale(0.9); opacity: 1; } 100% { transform: scale(1.3); opacity: 0; } }
  @keyframes inner-pulse { 0% { transform: translate(-50%, -50%) scale(0); opacity: 0.8; } 100% { transform: translate(-50%, -50%) scale(1); opacity: 0; } }
</style>