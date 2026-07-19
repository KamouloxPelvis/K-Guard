<script setup lang="ts">
import { computed, onMounted, onUnmounted, ref } from 'vue'
import api from '@/services/api'

interface WazuhAgent {
  id: string
  name: string
  status: string
  ip: string
  group: string
  version: string
  last_keep_alive: string
  os: {
    name: string
    platform: string
    version: string
    architecture: string
  }
}

interface WazuhInventory {
  connected: boolean
  summary: {
    total: number
    active: number
    disconnected: number
    never_connected: number
  }
  agents: WazuhAgent[]
}

const inventory = ref<WazuhInventory | null>(null)
const loading = ref(true)
const errorMessage = ref('')
const search = ref('')
const refreshedAt = ref('')
let refreshTimer: number | undefined

const filteredAgents = computed(() => {
  const query = search.value.trim().toLowerCase()

  if (!query || !inventory.value) {
    return inventory.value?.agents ?? []
  }

  return inventory.value.agents.filter((agent) =>
    [
      agent.id,
      agent.name,
      agent.status,
      agent.ip,
      agent.group,
      agent.os.name,
      agent.os.platform,
    ]
      .join(' ')
      .toLowerCase()
      .includes(query),
  )
})

const formatDate = (value: string) => {
  if (!value || value === 'Never') return 'Never'

  const date = new Date(value)
  return Number.isNaN(date.getTime())
    ? value
    : date.toLocaleString('fr-FR', { dateStyle: 'short', timeStyle: 'short' })
}

const statusClass = (status: string) => {
  if (status === 'active') return 'text-emerald-400 border-emerald-500/30 bg-emerald-500/10'
  if (status === 'disconnected') return 'text-amber-400 border-amber-500/30 bg-amber-500/10'
  return 'text-slate-400 border-slate-700 bg-slate-800/50'
}

const fetchAgents = async () => {
  loading.value = true
  errorMessage.value = ''

  try {
    const { data } = await api.get<WazuhInventory>('/wazuh/agents')
    inventory.value = data
    refreshedAt.value = new Date().toLocaleTimeString('fr-FR')
  } catch (error: any) {
    inventory.value = null
    errorMessage.value =
      error?.response?.data?.detail ||
      'Wazuh endpoint inventory is unavailable.'
  } finally {
    loading.value = false
  }
}

onMounted(async () => {
  await fetchAgents()
  refreshTimer = window.setInterval(fetchAgents, 60_000)
})

onUnmounted(() => {
  if (refreshTimer) window.clearInterval(refreshTimer)
})
</script>

<template>
  <div class="p-4 lg:p-6 relative z-10 font-sans h-full overflow-y-auto custom-scrollbar">
    <header class="mb-5 flex flex-col sm:flex-row sm:items-end justify-between gap-4 border-b border-slate-800/40 pb-3">
      <div>
        <p class="text-[10px] text-slate-500 mt-2 uppercase tracking-[0.35em]">
          Wazuh Endpoint Inventory & Compliance
        </p>
      </div>

      <div class="flex items-center gap-2">
        <span
          class="text-[8px] px-2 py-1 border font-bold uppercase tracking-wider"
          :class="inventory?.connected ? 'text-emerald-400 border-emerald-500/30 bg-emerald-500/10' : 'text-slate-500 border-slate-800'"
        >
          {{ inventory?.connected ? '● Wazuh API Connected' : '● Wazuh API Unknown' }}
        </span>

        <button
          @click="fetchAgents"
          :disabled="loading"
          class="bg-blue-600/10 hover:bg-blue-600/20 disabled:opacity-40 border border-blue-500/30 px-3 py-1.5 rounded-sm text-[9px] font-bold text-blue-400 transition-all uppercase cursor-pointer"
        >
          {{ loading ? 'Syncing...' : 'Refresh' }}
        </button>
      </div>
    </header>

    <div v-if="loading && !inventory" class="flex flex-col items-center justify-center py-24">
      <div class="w-8 h-8 border-2 border-[#f05a28] border-t-transparent rounded-full animate-spin mb-4"></div>
      <span class="text-[8px] uppercase tracking-[0.4em] text-[#f05a28]">Synchronizing Wazuh...</span>
    </div>

    <div v-else-if="errorMessage" class="max-w-4xl mx-auto border border-red-900/40 bg-red-950/20 p-5 rounded-sm">
      <h3 class="text-xs font-bold uppercase tracking-[0.18em] text-red-400">Wazuh unavailable</h3>
      <p class="mt-2 text-[10px] text-slate-400 font-mono">{{ errorMessage }}</p>
      <button
        @click="fetchAgents"
        class="mt-4 text-[9px] font-bold uppercase tracking-widest text-red-300 border border-red-800 px-3 py-1.5 hover:bg-red-900/30 cursor-pointer"
      >
        Retry connection
      </button>
    </div>

    <div v-else-if="inventory" class="max-w-6xl mx-auto space-y-4 pb-10">
      <section class="grid grid-cols-2 lg:grid-cols-4 gap-3">
        <div class="bg-[#111217]/80 border border-slate-800 p-4 rounded-sm">
          <p class="text-[8px] text-slate-500 uppercase font-bold tracking-[0.18em]">Managed endpoints</p>
          <p class="mt-2 text-3xl font-light text-white">{{ inventory.summary.total }}</p>
        </div>

        <div class="bg-[#111217]/80 border border-emerald-900/30 p-4 rounded-sm">
          <p class="text-[8px] text-emerald-500 uppercase font-bold tracking-[0.18em]">Active agents</p>
          <p class="mt-2 text-3xl font-light text-emerald-400">{{ inventory.summary.active }}</p>
        </div>

        <div class="bg-[#111217]/80 border border-amber-900/30 p-4 rounded-sm">
          <p class="text-[8px] text-amber-500 uppercase font-bold tracking-[0.18em]">Disconnected</p>
          <p class="mt-2 text-3xl font-light text-amber-400">{{ inventory.summary.disconnected }}</p>
        </div>

        <div class="bg-[#111217]/80 border border-slate-800 p-4 rounded-sm">
          <p class="text-[8px] text-slate-500 uppercase font-bold tracking-[0.18em]">Never connected</p>
          <p class="mt-2 text-3xl font-light text-slate-300">{{ inventory.summary.never_connected }}</p>
        </div>
      </section>

      <section class="bg-[#111217]/80 border border-slate-800 rounded-sm shadow-xl overflow-hidden">
        <div class="p-4 border-b border-slate-800 flex flex-col md:flex-row gap-3 md:items-center justify-between">
          <div>
            <h3 class="text-[10px] text-slate-300 uppercase font-black tracking-[0.2em]">
              Endpoint inventory
            </h3>
            <p class="text-[8px] text-slate-600 uppercase mt-1">
              Last synchronization: {{ refreshedAt || 'N/A' }}
            </p>
          </div>

          <input
            v-model="search"
            type="search"
            placeholder="Search endpoint, IP, OS..."
            class="w-full md:w-64 bg-black border border-slate-800 p-2 text-[10px] text-cyan-400 font-mono focus:border-cyan-500 outline-none"
          >
        </div>

        <div class="overflow-x-auto">
          <table class="min-w-full text-left">
            <thead class="bg-black/20 border-b border-slate-800">
              <tr class="text-[8px] text-slate-500 uppercase tracking-widest">
                <th class="px-4 py-3 font-bold">Endpoint</th>
                <th class="px-4 py-3 font-bold">Status</th>
                <th class="px-4 py-3 font-bold">Address</th>
                <th class="px-4 py-3 font-bold">Operating system</th>
                <th class="px-4 py-3 font-bold">Group</th>
                <th class="px-4 py-3 font-bold">Last seen</th>
              </tr>
            </thead>

            <tbody>
              <tr
                v-for="agent in filteredAgents"
                :key="agent.id"
                class="border-b border-slate-800/70 hover:bg-white/[0.02]"
              >
                <td class="px-4 py-3">
                  <p class="text-[11px] text-white font-bold">{{ agent.name }}</p>
                  <p class="text-[8px] text-slate-600 font-mono mt-0.5">ID: {{ agent.id }} · {{ agent.version }}</p>
                </td>
                <td class="px-4 py-3">
                  <span
                    class="inline-block border px-2 py-0.5 rounded-sm text-[8px] font-bold uppercase"
                    :class="statusClass(agent.status)"
                  >
                    {{ agent.status.replace('_', ' ') }}
                  </span>
                </td>
                <td class="px-4 py-3 text-[10px] text-cyan-400 font-mono">{{ agent.ip }}</td>
                <td class="px-4 py-3">
                  <p class="text-[10px] text-slate-300">{{ agent.os.name }}</p>
                  <p class="text-[8px] text-slate-600">{{ agent.os.version }} · {{ agent.os.architecture }}</p>
                </td>
                <td class="px-4 py-3 text-[9px] text-slate-400 font-mono">{{ agent.group }}</td>
                <td class="px-4 py-3 text-[9px] text-slate-500 font-mono">{{ formatDate(agent.last_keep_alive) }}</td>
              </tr>

              <tr v-if="filteredAgents.length === 0">
                <td colspan="6" class="px-4 py-10 text-center text-[10px] text-slate-600 uppercase tracking-widest">
                  No Wazuh agent matches this search
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </section>

      <section class="border border-cyan-900/30 bg-cyan-950/5 p-4 rounded-sm">
        <h3 class="text-[10px] text-cyan-400 uppercase font-bold tracking-[0.18em]">
          Read-only Wazuh integration
        </h3>
        <p class="mt-2 text-[9px] leading-relaxed text-slate-500 uppercase">
          This first version exposes endpoint inventory only. Vulnerabilities, SCA posture, FIM and alert investigation will be added through separate, read-only integrations.
        </p>
      </section>
    </div>
  </div>
</template>