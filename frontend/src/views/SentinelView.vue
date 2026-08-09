<script setup lang="ts">
  import { ref, computed, nextTick, onMounted, onUnmounted } from 'vue';
  import api from '@/services/api';

  // --- INTERFACES ---
  interface PodNode {
    id: string;
    name: string;
    namespace: string;
    status: string;
    ip: string;
    role: string;
    labels: Record<string, string>;
    is_hardened: boolean;
    image?: string; 
  }

  interface NetworkEdge {
    source: string;
    target: string;
    label: string;
    sourceIp?: string;
    targetIp?: string;
  }

  interface SecurityFinding {
  id: string
  severity: 'critical' | 'high' | 'medium' | 'low' | 'info'
  namespace?: string
  pod?: string
  resource?: string
  message: string
}

interface SecurityCategory {
  score: number | null
  weight: number
  passed: number
  failed: number
  unknown: number
}

interface SentinelStatusResponse {
  deployed: boolean
  security_score: number | null
  confidence: number
  coverage: number
  assessed_at: string
  summary: {
    passed: number
    failed: number
    unknown: number
  }
  categories: Record<string, SecurityCategory>
  findings: SecurityFinding[]
}

  /**
   * API Response structure for the Sentinel Map.
   */
  interface SentinelMapResponse {
    nodes: PodNode[];
    edges: NetworkEdge[];
    namespaces: string[];
  }

  // --- REACTIVE STATE ---
  const pods = ref<PodNode[]>([]);
  const edges = ref<NetworkEdge[]>([]);
  const selectedNS = ref('all-protected');
  const isLoading = ref(false);
  const namespaces = ref(['all-protected']);

  // --- UI STATES ---
  const showRoleModal = ref(false);
  const selectedPod = ref<PodNode | null>(null);
  const currentViewMode = ref('list');
  const activeAccordion = ref<string | null>(null);
  const isHardened = ref(false); // Track the deployment status

  // --- LOGIC: SECURITY ANALYSIS ---
  const isVulnerable = (pod: PodNode) => {
    if (!pod || !pod.role) return true; 
    return !pod.is_hardened;
  };

  /**
 * Fetches the current Sentinel status to update the UI buttons accordingly.
 */
  const securityScore = ref(0);
  const securityCategories = ref<Record<string, SecurityCategory>>({});
  const securityFindings = ref<SecurityFinding[]>([]);
  const securityCoverage = ref(0);
  const securityConfidence = ref(0);
  const securityAssessedAt = ref('');

  const fetchSentinelStatus = async () => {
    try {
      const response = await api.get<SentinelStatusResponse>(
        '/sentinel/status',
      )

      const data = response.data

      isHardened.value = data.deployed
      securityScore.value = data.security_score ?? 0
      securityCategories.value = data.categories ?? {}
      securityFindings.value = data.findings ?? []
      securityCoverage.value = data.coverage ?? 0
      securityConfidence.value = data.confidence ?? 0
      securityAssessedAt.value = data.assessed_at ?? ''
    } catch (error) {
      console.error('Sentinel security audit unavailable:', error)

      isHardened.value = false
      securityScore.value = 0
      securityCategories.value = {}
      securityFindings.value = []
      securityCoverage.value = 0
      securityConfidence.value = 0
      securityAssessedAt.value = ''
    }
  };

  /**
   * Filters and sorts pods based on the selected namespace.
   * Vulnerable pods are prioritized in the list for visibility.
   */
  const filteredPods = computed(() => {
    const list = selectedNS.value === 'all-protected' 
      ? pods.value 
      : pods.value.filter(pod => pod.namespace === selectedNS.value);
    
    return [...list].sort((a, b) => (isVulnerable(b) ? 1 : 0) - (isVulnerable(a) ? 1 : 0));
  });

  /**
   * Groups filtered pods by their respective Kubernetes namespace.
   */
  const podsByNamespace = computed(() => {
    return filteredPods.value.reduce((acc, pod) => {
      if (!acc[pod.namespace]) acc[pod.namespace] = [];
      acc[pod.namespace]!.push(pod); 
      return acc;
    }, {} as Record<string, PodNode[]>);
  });

  /**
   * Filters network edges to only show connections relevant to the current namespace.
   */
  const filteredEdges = computed(() => {
    if (selectedNS.value === 'all-protected') return edges.value;
    const nsPodIds = filteredPods.value.map(p => p.id);
    return edges.value.filter(edge => nsPodIds.includes(edge.source) && nsPodIds.includes(edge.target));
  });

  // --- DATA FETCHING ---

  /**
   * Synchronizes the network map from the Sentinel backend service.
   */
  /**
   * Fetches the network topology for the Sentinel module.
   * Includes a safety watchdog timer to detect hung requests.
   */
  let abortController: AbortController | null = null;

  /**
   * Synchronizes the network topology from the Sentinel backend.
   * Implements robust error handling and concurrency control to ensure UI stability.
   */

  const fetchNetworkData = async () => {

    if (isLoading.value) return; 

    if (abortController) abortController.abort();
    abortController = new AbortController();
    isLoading.value = true;

    try {
      // API call with AbortSignal for request cancellation
      const response = await api.get<SentinelMapResponse>('/sentinel/map', {
        signal: abortController.signal
      });

      const { data } = response;

      // 3. Wait for DOM to be ready for incoming data
      await nextTick();

      // 4. Atomic state updates
      pods.value = data.nodes || [];
      namespaces.value = data.namespaces 
        ? ['all-protected', ...data.namespaces] 
        : ['all-protected'];

      // 5. Edge mapping with safe lookup for associated IPs
      edges.value = (data.edges || []).map(edge => ({
        ...edge,
        sourceIp: pods.value.find(p => p.id === edge.source)?.ip || '0.0.0.0',
        targetIp: pods.value.find(p => p.id === edge.target)?.ip || '0.0.0.0'
      }));

      console.info("DEBUG: Network topology data successfully applied to state");

    } catch (error: any) {
      // 6. Fine-grained error handling
      if (error.name === 'AbortError' || error.name === 'CanceledError') {
        console.warn("DEBUG: Request aborted due to navigation.");
        return; 
      }
      
      console.error("DEBUG: Critical synchronization error:", error);
      
      // Reset state to prevent UI inconsistency in case of API failure
      pods.value = [];
      edges.value = [];
      namespaces.value = ['all-protected'];
      isLoading.value = false;
      
    } finally {
      // 7. Final Cleanup: Ensure loading state is reset
      if (abortController && !abortController.signal.aborted) {
        isLoading.value = false;
      }
    }
  };
    

  // --- TOPOLOGY HELPERS ---
  const getNodePos = (_id: string, index: number, total: number, side: 'left' | 'right') => {
    const x = side === 'left' ? 150 : 850;
    const y = (index + 1) * (500 / (total + 1));
    return { x, y };
  };

  // --- TOPOLOGY HELPERS ---
  const getEdgePath = (edge: NetworkEdge) => {
    
    if (!pods.value || pods.value.length === 0) return "";
    
    const sourceIdx = filteredPods.value.findIndex(p => p.id === edge.source);
    const targetIdx = filteredPods.value.findIndex(p => p.id === edge.target);

    if (sourceIdx === -1 || targetIdx === -1) return "";

    const total = filteredPods.value.length;
    const start = getNodePos(edge.source, sourceIdx, total, sourceIdx % 2 === 0 ? 'left' : 'right');
    const end = getNodePos(edge.target, targetIdx, total, targetIdx % 2 === 0 ? 'left' : 'right');
    
    return `M ${start.x} ${start.y} C ${(start.x + end.x)/2} ${start.y}, ${(start.x + end.x)/2} ${end.y}, ${end.x} ${end.y}`;
  };

  const toggleAccordion = (id: string) => {
    activeAccordion.value = activeAccordion.value === id ? null : id;
  };

  const openRoleDetails = (pod: PodNode) => {
    selectedPod.value = pod;
    showRoleModal.value = true;
  };
  
  const init = async () => {
    console.log("DEBUG: Chargement frais des données Sentinel...");
    await Promise.all([fetchNetworkData(), fetchSentinelStatus()]);
  };

  onMounted(async () => {
  console.log("DEBUG: SentinelView MONTE");
  await nextTick(); 
  init(); 
});

  onUnmounted(() => {
    console.log("DEBUG: SentinelView en cours de nettoyage...");
    if (abortController) {
      abortController.abort(); 
    }
    
    pods.value = [];
    edges.value = [];
    isLoading.value = false;
    console.log("DEBUG: État nettoyé, prêt pour navigation.");
  });
</script>

  <template>
    <div class="p-4 lg:p-6 space-y-4 relative max-w-[1600px] mx-auto">
      <!-- Header + controls -->
      <div class="grid grid-cols-1 xl:grid-cols-4 gap-4">
        <div class="xl:col-span-3 bg-[#111217] border border-slate-800/60 rounded-sm p-5">
          <div class="flex flex-col lg:flex-row lg:items-center lg:justify-between gap-4">
            <div class="space-y-1">

              <p class="text-[9px] text-slate-500 uppercase tracking-[0.4em]">
                Automated Micro-segmentation
              </p>
              <div class="flex items-center gap-3 flex-wrap">
                <h2 class="text-lg font-black text-white uppercase tracking-tighter">
                  Network Sentinel <span class="text-blue-500">v2.0</span>
                </h2>

                <span
                  v-if="isHardened"
                  class="px-2.5 py-1 text-[8px] font-black uppercase tracking-[0.25em] rounded-sm border border-emerald-500/50 bg-emerald-500/10 text-emerald-400"
                >
                  Policies Active
                </span>

                <span
                  v-else
                  class="px-2.5 py-1 text-[8px] font-black uppercase tracking-[0.25em] rounded-sm border border-amber-500/40 bg-amber-500/10 text-amber-400"
                >
                  Unhardened
                </span>
              </div>
            </div>

            <div class="flex flex-wrap items-center gap-3">
              <div class="inline-flex p-1 bg-[#0b0c10] border border-slate-700 rounded-sm">
                <button
                  @click="currentViewMode = 'list'"
                  :class="currentViewMode === 'list' ? 'bg-blue-600 text-white' : 'text-slate-500 hover:text-slate-300'"
                  class="px-3 py-1 text-[8px] font-black uppercase tracking-widest rounded-sm transition-all"
                >
                  List
                </button>
                <button
                  @click="currentViewMode = 'topology'"
                  :class="currentViewMode === 'topology' ? 'bg-orange-600 text-white' : 'text-slate-500 hover:text-slate-300'"
                  class="px-3 py-1 text-[8px] font-black uppercase tracking-widest rounded-sm transition-all"
                >
                  Topology
                </button>
              </div>

              <select
                v-model="selectedNS"
                class="bg-[#0b0c10] border border-slate-700 text-[9px] text-slate-300 px-3 py-1.5 rounded-sm uppercase font-bold tracking-widest cursor-pointer"
              >
                <option v-for="ns in namespaces" :key="ns" :value="ns">
                  {{ ns }}
                </option>
              </select>

              <button
                @click="init"
                :disabled="isLoading"
                class="bg-slate-800 hover:bg-slate-700 disabled:opacity-50 disabled:cursor-not-allowed border border-slate-600 text-slate-300 px-4 py-1.5 rounded-sm text-[9px] font-bold uppercase tracking-widest transition-all"
              >
                {{ isLoading ? 'Syncing...' : 'Refresh Audit' }}
              </button>
            </div>
          </div>
        </div>

        <!-- Security score -->
        <div class="bg-[#111217] border border-slate-800/60 p-4 rounded-sm flex flex-col justify-between">
          <div>
            <p class="text-[8px] text-slate-500 uppercase font-bold tracking-[0.25em] mb-2">
              Security Score
            </p>

            <div class="relative flex items-center justify-center py-2">
              <svg class="w-20 h-20 transform -rotate-90">
                <circle
                  cx="40"
                  cy="40"
                  r="32"
                  stroke="currentColor"
                  stroke-width="4"
                  fill="transparent"
                  class="text-slate-800"
                />
                <circle
                  cx="40"
                  cy="40"
                  r="32"
                  stroke="currentColor"
                  stroke-width="4"
                  fill="transparent"
                  stroke-linecap="round"
                  :stroke-dasharray="201"
                  :stroke-dashoffset="201 - (201 * securityScore) / 100"
                  :class="securityScore < 50 ? 'text-red-500' : securityScore < 80 ? 'text-amber-400' : 'text-blue-500'"
                />
              </svg>

              <span class="absolute text-lg font-black text-white">
                {{ securityScore }}%
              </span>
            </div>
          </div>

          <div class="grid grid-cols-2 gap-2 pt-3 border-t border-slate-800/50">
            <div class="bg-[#0b0c10] border border-slate-800 rounded-sm p-2">
              <p class="text-[8px] text-slate-500 uppercase font-bold">Pods</p>
              <p class="text-sm font-black text-white mt-1">{{ filteredPods.length }}</p>
            </div>
            <div class="bg-[#0b0c10] border border-slate-800 rounded-sm p-2">
              <p class="text-[8px] text-slate-500 uppercase font-bold">Flows</p>
              <p class="text-sm font-black text-white mt-1">{{ filteredEdges.length }}</p>
            </div>
          </div>
        </div>
      </div>

      <!-- Security posture findings -->
      <section class="bg-[#111217] border border-slate-800/60 rounded-sm p-4">
        <div class="flex flex-col md:flex-row md:items-center md:justify-between gap-3">
          <div>
            <h3 class="text-[10px] text-slate-300 uppercase font-black tracking-[0.2em]">
              Security posture findings
            </h3>
            <p class="mt-1 text-[8px] text-slate-600 uppercase">
              Read-only assessment from Kubernetes API evidence
            </p>
          </div>

          <div class="flex items-center gap-4 text-[8px] uppercase">
            <span class="text-slate-500">
              Coverage:
              <span class="text-cyan-400">{{ securityCoverage }}%</span>
            </span>

            <span class="text-slate-500">
              Confidence:
              <span class="text-violet-400">{{ securityConfidence }}%</span>
            </span>

            <span
              v-if="securityAssessedAt"
              class="text-slate-600 font-mono"
            >
              {{ securityAssessedAt }}
            </span>
          </div>
        </div>

        <div class="mt-4 grid grid-cols-1 md:grid-cols-2 xl:grid-cols-5 gap-2">
          <div
            v-for="(category, name) in securityCategories"
            :key="name"
            class="border border-slate-800 bg-[#0b0c10] p-3"
          >
            <p class="text-[8px] text-slate-500 uppercase font-bold">
              {{ name.replaceAll('_', ' ') }}
            </p>

            <p
              class="mt-2 text-xl font-black"
              :class="
                category.score === null
                  ? 'text-slate-500'
                  : category.score < 50
                    ? 'text-red-400'
                    : category.score < 80
                      ? 'text-amber-400'
                      : 'text-emerald-400'
              "
            >
              {{ category.score === null ? 'N/A' : `${category.score}%` }}
            </p>

            <p class="mt-1 text-[8px] text-slate-600">
              {{ category.passed }} passed ·
              {{ category.failed }} failed ·
              {{ category.unknown }} unknown
            </p>
          </div>
        </div>

        <div
          v-if="securityFindings.length"
          class="mt-4 space-y-2"
        >
          <div
            v-for="finding in securityFindings.slice(0, 12)"
            :key="`${finding.id}-${finding.namespace}-${finding.pod || finding.resource}`"
            class="border border-slate-800 bg-[#0b0c10] p-3"
          >
            <div class="flex items-start justify-between gap-3">
              <p class="text-[9px] text-slate-300">
                {{ finding.message }}
              </p>

              <span class="shrink-0 text-[8px] uppercase text-amber-400">
                {{ finding.severity }}
              </span>
            </div>

            <p
              v-if="finding.namespace || finding.pod"
              class="mt-1 text-[8px] text-slate-600 font-mono"
            >
              {{ finding.namespace || 'cluster' }}
              <span v-if="finding.pod || finding.resource">
                · {{ finding.pod || finding.resource }}
              </span>
            </p>
          </div>
        </div>

        <p
          v-else
          class="mt-4 text-[9px] text-slate-600 uppercase tracking-widest"
        >
          No security findings returned by the audit.
        </p>
      </section>

      <!-- Topology -->
      <div
        v-if="currentViewMode === 'topology'"
        class="bg-[#0b0c10] border border-slate-800/60 p-3 rounded-sm relative min-h-[540px] overflow-hidden"
      >
        <div
          class="absolute inset-0 opacity-5"
          style="background-image: radial-gradient(#3b82f6 1px, transparent 1px); background-size: 20px 20px;"
        ></div>

        <div
          v-if="isLoading"
          class="absolute inset-0 z-20 flex items-center justify-center bg-[#0b0c10]/80 backdrop-blur-[1px]"
        >
          <div class="text-center space-y-2">
            <div class="w-10 h-10 mx-auto rounded-full border-2 border-slate-700 border-t-blue-500 animate-spin"></div>
            <p class="text-[10px] uppercase tracking-[0.3em] font-bold text-slate-400">
              Synchronizing topology
            </p>
          </div>
        </div>

        <div v-if="filteredPods.length > 0" class="relative z-10 w-full h-full flex items-center justify-center">
          <svg viewBox="0 0 1000 500" class="w-full h-full max-w-6xl">
            <!-- edges base -->
            <g v-for="edge in filteredEdges" :key="'base-' + edge.source + '-' + edge.target">
              <path
                v-if="getEdgePath(edge)"
                :d="getEdgePath(edge)"
                fill="none"
                class="stroke-slate-800 stroke-[1]"
              />
            </g>

            <!-- edges animated -->
            <g v-for="edge in filteredEdges" :key="'flow-' + edge.source + '-' + edge.target">
              <path
                v-if="getEdgePath(edge)"
                :d="getEdgePath(edge)"
                fill="none"
                class="stroke-blue-500 stroke-[1.5] opacity-60 animate-dash-flow"
                stroke-dasharray="4 8"
              />
            </g>

            <!-- nodes -->
            <g
              v-for="(pod, idx) in filteredPods"
              :key="pod.id"
              @click="openRoleDetails(pod)"
              class="cursor-pointer group"
            >
              <rect
                :x="getNodePos(pod.id, idx, filteredPods.length, idx % 2 === 0 ? 'left' : 'right').x - 62"
                :y="getNodePos(pod.id, idx, filteredPods.length, idx % 2 === 0 ? 'left' : 'right').y - 26"
                width="124"
                height="52"
                rx="4"
                :class="[
                  isVulnerable(pod)
                    ? 'fill-red-950/90 stroke-red-500'
                    : 'fill-slate-900 stroke-blue-500',
                  'stroke-[1.2] transition-all group-hover:stroke-white'
                ]"
              />

              <text
                :x="getNodePos(pod.id, idx, filteredPods.length, idx % 2 === 0 ? 'left' : 'right').x"
                :y="getNodePos(pod.id, idx, filteredPods.length, idx % 2 === 0 ? 'left' : 'right').y - 2"
                text-anchor="middle"
                class="fill-white text-[9px] font-mono font-bold uppercase"
              >
                {{ pod.role?.length > 16 ? pod.role.substring(0, 16) + '…' : pod.role || 'unknown-role' }}
              </text>

              <text
                :x="getNodePos(pod.id, idx, filteredPods.length, idx % 2 === 0 ? 'left' : 'right').x"
                :y="getNodePos(pod.id, idx, filteredPods.length, idx % 2 === 0 ? 'left' : 'right').y + 12"
                text-anchor="middle"
                class="fill-slate-400 text-[7px] font-mono uppercase"
              >
                {{ pod.namespace }}
              </text>
            </g>
          </svg>
        </div>

        <div
          v-else-if="!isLoading"
          class="relative z-10 min-h-[500px] flex items-center justify-center"
        >
          <div class="text-center space-y-2">
            <p class="text-xs font-bold text-slate-400 uppercase tracking-[0.25em]">
              No topology data
            </p>
            <p class="text-[11px] text-slate-500">
              No pod or flow is currently available for the selected scope.
            </p>
          </div>
        </div>
      </div>

      <!-- List -->
      <div v-if="currentViewMode === 'list'" class="space-y-6">
        <div
          v-if="isLoading"
          class="bg-[#0b0c10] border border-slate-800/60 rounded-sm p-6 flex items-center justify-center"
        >
          <div class="text-center space-y-2">
            <div class="w-10 h-10 mx-auto rounded-full border-2 border-slate-700 border-t-blue-500 animate-spin"></div>
            <p class="text-[10px] uppercase tracking-[0.3em] font-bold text-slate-400">
              Loading Sentinel inventory
            </p>
          </div>
        </div>

        <div
          v-else-if="filteredPods.length === 0"
          class="bg-[#0b0c10] border border-slate-800/60 rounded-sm p-8 text-center"
        >
          <p class="text-[10px] uppercase tracking-[0.3em] font-bold text-slate-400">
            Empty scope
          </p>
          <p class="text-[11px] text-slate-500 mt-2">
            No protected pod found for this namespace filter.
          </p>
        </div>

        <template v-else>
          <div v-for="(nsPods, nsName) in podsByNamespace" :key="nsName" class="space-y-3">
            <div class="flex items-center gap-3">
              <h3 class="text-[10px] font-black text-slate-500 uppercase tracking-[0.25em]">
                {{ nsName }}
              </h3>
              <div class="h-px flex-1 bg-slate-800/40"></div>
              <span class="text-[9px] text-slate-600 font-mono">
                {{ nsPods.length }} pod{{ nsPods.length > 1 ? 's' : '' }}
              </span>
            </div>

            <div class="space-y-2">
              <div
                v-for="pod in nsPods"
                :key="pod.id"
                class="border border-slate-800/60 rounded-sm overflow-hidden"
              >
                <div
                  @click="toggleAccordion(pod.id)"
                  class="bg-[#111217] p-3 flex items-center justify-between gap-3 cursor-pointer hover:bg-[#15171e] transition-colors"
                >
                  <div class="min-w-0 flex items-center gap-3">
                    <div
                      :class="isVulnerable(pod)
                        ? 'bg-red-500 shadow-[0_0_8px_rgba(239,68,68,0.5)]'
                        : 'bg-blue-500 shadow-[0_0_8px_rgba(59,130,246,0.5)]'"
                      class="w-1.5 h-1.5 rounded-full shrink-0"
                    ></div>

                    <div class="min-w-0">
                      <p class="text-[10px] font-bold text-white uppercase truncate">
                        {{ pod.name }}
                      </p>
                      <p class="text-[9px] text-slate-500 font-mono truncate">
                        {{ pod.role || 'unknown-role' }}
                      </p>
                    </div>
                  </div>

                  <div class="flex items-center gap-3 shrink-0">
                    <span
                      :class="isVulnerable(pod)
                        ? 'text-red-400 border-red-500/40 bg-red-500/10'
                        : 'text-emerald-400 border-emerald-500/40 bg-emerald-500/10'"
                      class="px-2 py-1 rounded-sm border text-[8px] font-black uppercase tracking-[0.2em]"
                    >
                      {{ isVulnerable(pod) ? 'Vulnerable' : 'Hardened' }}
                    </span>

                    <span class="text-slate-500 text-[12px] leading-none">
                      {{ activeAccordion === pod.id ? '−' : '+' }}
                    </span>
                  </div>
                </div>

                <div
                  v-if="activeAccordion === pod.id"
                  class="bg-[#0b0c10] p-4 border-t border-slate-800/40 space-y-4"
                >
                  <div class="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-4 gap-4 text-[9px]">
                    <div>
                      <p class="text-slate-500 uppercase font-bold mb-1">Pod Name</p>
                      <p class="text-white font-mono break-all">{{ pod.name }}</p>
                    </div>

                    <div>
                      <p class="text-slate-500 uppercase font-bold mb-1">Namespace</p>
                      <p class="text-blue-400 font-mono">{{ pod.namespace }}</p>
                    </div>

                    <div>
                      <p class="text-slate-500 uppercase font-bold mb-1">IP Address</p>
                      <p class="text-cyan-400 font-mono">{{ pod.ip }}</p>
                    </div>

                    <div>
                      <p class="text-slate-500 uppercase font-bold mb-1">Runtime Status</p>
                      <p
                        :class="pod.status === 'Running' ? 'text-emerald-400' : 'text-amber-400'"
                        class="font-bold"
                      >
                        {{ pod.status }}
                      </p>
                    </div>
                  </div>

                  <div class="grid grid-cols-1 md:grid-cols-3 gap-4 text-[9px]">
                    <div>
                      <p class="text-slate-500 uppercase font-bold mb-1">Role</p>
                      <p class="text-white">{{ pod.role || 'N/A' }}</p>
                    </div>

                    <div>
                      <p class="text-slate-500 uppercase font-bold mb-1">Protection State</p>
                      <p :class="pod.is_hardened ? 'text-emerald-400' : 'text-red-400'" class="font-bold">
                        {{ pod.is_hardened ? 'Sentinel Hardened' : 'Not Hardened' }}
                      </p>
                    </div>

                    <div>
                      <p class="text-slate-500 uppercase font-bold mb-1">Labels</p>
                      <p class="text-slate-300">
                        {{ Object.keys(pod.labels || {}).length }} detected
                      </p>
                    </div>
                  </div>

                  <div v-if="pod.labels && Object.keys(pod.labels).length > 0" class="space-y-2">
                    <p class="text-slate-500 uppercase font-bold text-[9px]">Kubernetes Labels</p>
                    <div class="flex flex-wrap gap-2">
                      <span
                        v-for="(value, key) in pod.labels"
                        :key="`${pod.id}-${key}`"
                        class="px-2 py-1 rounded-sm border border-slate-700 bg-[#111217] text-[8px] font-mono text-slate-300"
                      >
                        {{ key }}={{ value }}
                      </span>
                    </div>
                  </div>

                  <div class="pt-2">
                    <button
                      @click="openRoleDetails(pod)"
                      class="bg-slate-800 hover:bg-slate-700 border border-slate-700 text-slate-200 px-3 py-2 rounded-sm text-[9px] font-bold uppercase tracking-[0.2em] transition-all"
                    >
                      Inspect Role Details
                    </button>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </template>
      </div>

      <!-- Role modal -->
      <div
        v-if="showRoleModal && selectedPod"
        class="fixed inset-0 z-50 bg-black/70 backdrop-blur-[2px] flex items-center justify-center p-4"
        @click.self="showRoleModal = false"
      >
        <div class="w-full max-w-3xl bg-[#0b0c10] border border-slate-800 rounded-sm overflow-hidden shadow-2xl">
          <div class="px-5 py-4 border-b border-slate-800 bg-[#111217] flex items-start justify-between gap-4">
            <div>
              <p class="text-[8px] text-slate-500 uppercase tracking-[0.3em] font-bold mb-1">
                Sentinel Pod Inspection
              </p>
              <h3 class="text-sm font-black text-white uppercase tracking-[0.15em]">
                {{ selectedPod.name }}
              </h3>
              <p class="text-[10px] text-slate-500 font-mono mt-1">
                {{ selectedPod.namespace }} • {{ selectedPod.ip }}
              </p>
            </div>

            <button
              @click="showRoleModal = false"
              class="text-slate-500 hover:text-white text-lg leading-none"
            >
              ×
            </button>
          </div>

          <div class="p-5 space-y-5 max-h-[75vh] overflow-y-auto custom-scrollbar">
            <div class="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-4 gap-4">
              <div class="bg-[#111217] border border-slate-800 rounded-sm p-3">
                <p class="text-[8px] text-slate-500 uppercase font-bold mb-1">Role</p>
                <p class="text-white font-bold break-words">{{ selectedPod.role || 'N/A' }}</p>
              </div>

              <div class="bg-[#111217] border border-slate-800 rounded-sm p-3">
                <p class="text-[8px] text-slate-500 uppercase font-bold mb-1">Namespace</p>
                <p class="text-blue-400 font-mono">{{ selectedPod.namespace }}</p>
              </div>

              <div class="bg-[#111217] border border-slate-800 rounded-sm p-3">
                <p class="text-[8px] text-slate-500 uppercase font-bold mb-1">Runtime</p>
                <p
                  :class="selectedPod.status === 'Running' ? 'text-emerald-400' : 'text-amber-400'"
                  class="font-bold"
                >
                  {{ selectedPod.status }}
                </p>
              </div>

              <div class="bg-[#111217] border border-slate-800 rounded-sm p-3">
                <p class="text-[8px] text-slate-500 uppercase font-bold mb-1">Sentinel State</p>
                <p
                  :class="selectedPod.is_hardened ? 'text-emerald-400' : 'text-red-400'"
                  class="font-bold"
                >
                  {{ selectedPod.is_hardened ? 'Hardened' : 'Vulnerable' }}
                </p>
              </div>
            </div>

            <div class="bg-[#111217] border border-slate-800 rounded-sm p-4 space-y-3">
              <p class="text-[9px] text-slate-500 uppercase font-bold tracking-[0.2em]">
                Identity
              </p>

              <div class="grid grid-cols-1 md:grid-cols-2 gap-4 text-[10px]">
                <div>
                  <p class="text-slate-500 uppercase font-bold mb-1">Pod ID</p>
                  <p class="text-slate-300 font-mono break-all">{{ selectedPod.id }}</p>
                </div>

                <div>
                  <p class="text-slate-500 uppercase font-bold mb-1">Pod IP</p>
                  <p class="text-cyan-400 font-mono">{{ selectedPod.ip }}</p>
                </div>

                <div class="md:col-span-2">
                  <p class="text-slate-500 uppercase font-bold mb-1">Image</p>
                  <p class="text-slate-300 font-mono break-all">
                    {{ selectedPod.image || 'N/A' }}
                  </p>
                </div>
              </div>
            </div>

            <div class="bg-[#111217] border border-slate-800 rounded-sm p-4 space-y-3">
              <p class="text-[9px] text-slate-500 uppercase font-bold tracking-[0.2em]">
                Kubernetes Labels
              </p>

              <div
                v-if="selectedPod.labels && Object.keys(selectedPod.labels).length > 0"
                class="flex flex-wrap gap-2"
              >
                <span
                  v-for="(value, key) in selectedPod.labels"
                  :key="`modal-${key}`"
                  class="px-2 py-1 rounded-sm border border-slate-700 bg-[#0b0c10] text-[8px] font-mono text-slate-300"
                >
                  {{ key }}={{ value }}
                </span>
              </div>

              <p v-else class="text-[10px] text-slate-500">
                No Kubernetes labels available for this pod.
              </p>
            </div>

            <div class="flex justify-end">
              <button
                @click="showRoleModal = false"
                class="bg-slate-800 hover:bg-slate-700 border border-slate-700 text-slate-200 px-4 py-2 rounded-sm text-[9px] font-bold uppercase tracking-[0.2em] transition-all"
              >
                Close Inspection
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  </template>

  <style scoped>
  @keyframes dash-flow {
    from { stroke-dashoffset: 24; }
    to { stroke-dashoffset: 0; }
  }
  .animate-dash-flow {
    animation: dash-flow 1.5s linear infinite;
  }
  .custom-scrollbar::-webkit-scrollbar { width: 4px; }
  .custom-scrollbar::-webkit-scrollbar-thumb { background: #1e293b; border-radius: 2px; }
  </style>