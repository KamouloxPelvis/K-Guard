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

interface WazuhAlert {
  id: string
  timestamp: string
  level: number
  rule_id: string
  description: string
  firedtimes: number
  groups: string[]
  agent: {
    id: string
    name: string
    ip: string
  }
  manager: {
    name: string
  }
  mitre: {
    ids: string[]
    techniques: string[]
    tactics: string[]
  }
  location: string
  decoder: Record<string, unknown>
  predecoder: Record<string, unknown>
  data: Record<string, unknown>
  syscheck: Record<string, unknown>
  full_log: string
}

interface WazuhOverview {
  connected: boolean
  inventory: {
    connected: boolean
    summary: {
      total: number
      active: number
      disconnected: number
      never_connected: number
    }
    agents: WazuhAgent[]
  }
  alerts: {
    available: boolean
    total: number
    critical: number
    high: number
    medium: number
    low: number
  }
  posture: {
    sca_available: boolean
    vulnerabilities_available: boolean
    message: string
  }
}

interface WazuhAlertResponse {
  available: boolean
  total: number
  alerts: WazuhAlert[]
}

type Tab = 'endpoints' | 'posture' | 'alerts'

const activeTab = ref<Tab>('endpoints')
const overview = ref<WazuhOverview | null>(null)
const alerts = ref<WazuhAlert[]>([])
const selectedAgent = ref<WazuhAgent | null>(null)
const selectedAlert = ref<WazuhAlert | null>(null)
const loading = ref(true)
const refreshing = ref(false)
const errorMessage = ref('')
const endpointSearch = ref('')
const alertSearch = ref('')
const levelFilter = ref('all')
const refreshedAt = ref('')
let refreshTimer: number | undefined

const inventory = computed(() => overview.value?.inventory ?? null)

const filteredAgents = computed(() => {
  const query = endpointSearch.value.trim().toLowerCase()
  const agents = inventory.value?.agents ?? []

  if (!query) return agents

  return agents.filter((agent) =>
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

const filteredAlerts = computed(() => {
  const query = alertSearch.value.trim().toLowerCase()

  return alerts.value.filter((alert) => {
    const levelMatches =
      levelFilter.value === 'all' ||
      (levelFilter.value === 'critical' && alert.level >= 15) ||
      (levelFilter.value === 'high' && alert.level >= 12 && alert.level <= 14) ||
      (levelFilter.value === 'medium' && alert.level >= 7 && alert.level <= 11) ||
      (levelFilter.value === 'low' && alert.level <= 6)

    if (!levelMatches) return false
    if (!query) return true

    return [
      alert.id,
      alert.rule_id,
      alert.description,
      alert.agent.name,
      alert.agent.ip,
      alert.location,
      ...alert.groups,
      ...alert.mitre.ids,
      ...alert.mitre.techniques,
      ...alert.mitre.tactics,
    ]
      .join(' ')
      .toLowerCase()
      .includes(query)
  })
})

const formatDate = (value: string) => {
  if (!value || value === 'Never') return 'Never'

  const date = new Date(value)
  return Number.isNaN(date.getTime())
    ? value
    : date.toLocaleString('fr-FR', { dateStyle: 'short', timeStyle: 'short' })
}

const relativeDate = (value: string) => {
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) return 'N/A'

  const seconds = Math.max(0, Math.floor((Date.now() - date.getTime()) / 1000))
  if (seconds < 60) return `${seconds}s ago`
  if (seconds < 3600) return `${Math.floor(seconds / 60)}m ago`
  if (seconds < 86400) return `${Math.floor(seconds / 3600)}h ago`
  return `${Math.floor(seconds / 86400)}d ago`
}

const statusClass = (status: string) => {
  if (status === 'active') return 'text-emerald-400 border-emerald-500/30 bg-emerald-500/10'
  if (status === 'disconnected') return 'text-amber-400 border-amber-500/30 bg-amber-500/10'
  return 'text-slate-400 border-slate-700 bg-slate-800/50'
}

const severityClass = (level: number) => {
  if (level >= 15) return 'text-red-300 border-red-500/30 bg-red-500/10'
  if (level >= 12) return 'text-orange-300 border-orange-500/30 bg-orange-500/10'
  if (level >= 7) return 'text-amber-300 border-amber-500/30 bg-amber-500/10'
  return 'text-cyan-300 border-cyan-500/30 bg-cyan-500/10'
}

const severityName = (level: number) => {
  if (level >= 15) return 'Critical'
  if (level >= 12) return 'High'
  if (level >= 7) return 'Medium'
  return 'Low'
}

const fetchData = async (silent = false) => {
  if (silent) refreshing.value = true
  else loading.value = true

  errorMessage.value = ''

  const emptyOverview: WazuhOverview = {
    connected: false,
    inventory: {
      connected: false,
      summary: {
        total: 0,
        active: 0,
        disconnected: 0,
        never_connected: 0,
      },
      agents: [],
    },
    alerts: {
      available: false,
      total: 0,
      critical: 0,
      high: 0,
      medium: 0,
      low: 0,
    },
    posture: {
      sca_available: false,
      vulnerabilities_available: false,
      message: 'Wazuh posture data is temporarily unavailable.',
    },
  }

  try {
    const [overviewResult, alertsResult] = await Promise.allSettled([
      api.get<WazuhOverview>('/wazuh/overview'),
      api.get<WazuhAlertResponse>('/wazuh/alerts?limit=50'),
    ])

    let nextOverview: WazuhOverview = overview.value ?? emptyOverview
    let nextAlerts: WazuhAlert[] = alerts.value ?? []
    const issues: string[] = []

    if (overviewResult.status === 'fulfilled') {
      nextOverview = overviewResult.value.data
    } else {
      issues.push('overview')
    }

    if (alertsResult.status === 'fulfilled') {
      nextAlerts = Array.isArray(alertsResult.value.data?.alerts)
        ? alertsResult.value.data.alerts
        : []

      if (overviewResult.status !== 'fulfilled') {
        const total = nextAlerts.length
        const critical = nextAlerts.filter((a) => a.level >= 15).length
        const high = nextAlerts.filter((a) => a.level >= 12 && a.level <= 14).length
        const medium = nextAlerts.filter((a) => a.level >= 7 && a.level <= 11).length
        const low = nextAlerts.filter((a) => a.level <= 6).length

        nextOverview = {
          ...emptyOverview,
          alerts: {
            available: true,
            total,
            critical,
            high,
            medium,
            low,
          },
          posture: {
            ...emptyOverview.posture,
            message: 'Inventory unavailable, alert stream still available from Wazuh.',
          },
        }
      } else {
        nextOverview = {
          ...nextOverview,
          alerts: {
            ...nextOverview.alerts,
            available: true,
            total: nextOverview.alerts.total || nextAlerts.length,
          },
        }
      }
    } else {
      issues.push('alerts')
      nextAlerts = []
      nextOverview = {
        ...nextOverview,
        alerts: {
          ...nextOverview.alerts,
          available: false,
          total: 0,
          critical: 0,
          high: 0,
          medium: 0,
          low: 0,
        },
      }
    }

    overview.value = nextOverview
    alerts.value = nextAlerts
    refreshedAt.value = new Date().toLocaleTimeString('fr-FR')

    if (issues.length === 2) {
      errorMessage.value = 'Wazuh security data is temporarily unavailable.'
    } else if (issues.length === 1) {
      errorMessage.value =
        issues[0] === 'overview'
          ? 'Partial Wazuh degradation: endpoint inventory is unavailable, but alerts remain visible.'
          : 'Partial Wazuh degradation: alert stream is unavailable, but inventory remains visible.'
    }
  } finally {
    loading.value = false
    refreshing.value = false
  }
}

onMounted(async () => {
  await fetchData()
  refreshTimer = window.setInterval(() => fetchData(true), 60_000)
})

onUnmounted(() => {
  if (refreshTimer) window.clearInterval(refreshTimer)
})
</script>

<template>
  <div class="p-4 lg:p-6 relative z-10 font-sans h-full overflow-y-auto custom-scrollbar">
    <header class="mb-5 flex flex-col xl:flex-row xl:items-end justify-between gap-4 border-b border-slate-800/40 pb-3">
      <div>
        <p class="text-[10px] text-slate-500 mt-2 uppercase tracking-[0.35em]">
          Wazuh Endpoint Inventory, Posture & Alert Investigation
        </p>
        <p class="text-[8px] text-slate-600 uppercase tracking-widest mt-2">
          Read-only security integration · Last synchronization: {{ refreshedAt || 'N/A' }}
        </p>
      </div>

      <div class="flex items-center gap-2">
        <span
          class="text-[8px] px-2 py-1 border font-bold uppercase tracking-wider"
          :class="overview?.connected ? 'text-emerald-400 border-emerald-500/30 bg-emerald-500/10' : 'text-slate-500 border-slate-800'"
        >
          {{ overview?.connected ? '● Wazuh API + Indexer Connected' : '● Wazuh Status Unknown' }}
        </span>
        
        <button
          @click="fetchData(true)"
          :disabled="loading || refreshing"
          class="bg-blue-600/10 hover:bg-blue-600/20 disabled:opacity-40 border border-blue-500/30 px-3 py-1.5 rounded-sm text-[9px] font-bold text-blue-400 transition-all uppercase cursor-pointer"
        >
          {{ refreshing ? 'Syncing...' : 'Refresh' }}
        </button>
      </div>
    </header>

    <div
      v-if="errorMessage && overview"
      class="mb-4 max-w-7xl mx-auto border border-amber-900/40 bg-amber-950/20 p-4 rounded-sm"
    >
      <h3 class="text-[9px] font-bold uppercase tracking-[0.18em] text-amber-400">
        Wazuh degraded mode
      </h3>
      <p class="mt-2 text-[10px] text-slate-400 font-mono">{{ errorMessage }}</p>
    </div>

    <div v-if="loading && !overview" class="flex flex-col items-center justify-center py-24">
      <div class="w-8 h-8 border-2 border-[#f05a28] border-t-transparent rounded-full animate-spin mb-4"></div>
      <span class="text-[8px] uppercase tracking-[0.4em] text-[#f05a28]">Synchronizing Wazuh security data...</span>
    </div>

    <div v-else-if="errorMessage && !overview" class="max-w-6xl mx-auto border border-red-900/40 bg-red-950/20 p-5 rounded-sm">      <h3 class="text-xs font-bold uppercase tracking-[0.18em] text-red-400">Wazuh integration unavailable</h3>
      <p class="mt-2 text-[10px] text-slate-400 font-mono">{{ errorMessage }}</p>
      <button
        @click="fetchData()"
        class="mt-4 text-[9px] font-bold uppercase tracking-widest text-red-300 border border-red-800 px-3 py-1.5 hover:bg-red-900/30 cursor-pointer"
      >
        Retry connection
      </button>
    </div>

    <div v-else-if="overview && inventory" class="max-w-7xl mx-auto space-y-4 pb-10">
      <section class="grid grid-cols-2 xl:grid-cols-4 gap-3">
        <div class="bg-[#111217]/80 border border-slate-800 p-4 rounded-sm">
          <p class="text-[8px] text-slate-500 uppercase font-bold tracking-[0.18em]">Managed endpoints</p>
          <p class="mt-2 text-3xl font-light text-white">{{ inventory.summary.total }}</p>
          <p class="mt-1 text-[8px] text-slate-600 uppercase">Coverage inventory</p>
        </div>

        <div class="bg-[#111217]/80 border border-emerald-900/30 p-4 rounded-sm">
          <p class="text-[8px] text-emerald-500 uppercase font-bold tracking-[0.18em]">Active agents</p>
          <p class="mt-2 text-3xl font-light text-emerald-400">{{ inventory.summary.active }}</p>
          <p class="mt-1 text-[8px] text-slate-600 uppercase">{{ inventory.summary.total ? Math.round((inventory.summary.active / inventory.summary.total) * 100) : 0 }}% coverage online</p>
        </div>

        <div class="bg-[#111217]/80 border border-amber-900/30 p-4 rounded-sm">
          <p class="text-[8px] text-amber-500 uppercase font-bold tracking-[0.18em]">High / Critical alerts</p>
          <p class="mt-2 text-3xl font-light text-amber-400">{{ overview.alerts.high + overview.alerts.critical }}</p>
          <p class="mt-1 text-[8px] text-slate-600 uppercase">{{ overview.alerts.total }} alerts retained</p>
        </div>

        <div class="bg-[#111217]/80 border border-cyan-900/30 p-4 rounded-sm">
          <p class="text-[8px] text-cyan-500 uppercase font-bold tracking-[0.18em]">Alert stream</p>
          <p class="mt-2 text-3xl font-light text-cyan-400">{{ overview.alerts.available ? 'Live' : 'N/A' }}</p>
          <p class="mt-1 text-[8px] text-slate-600 uppercase">Indexer read-only query</p>
        </div>
      </section>

      <section class="bg-[#111217]/80 border border-slate-800 rounded-sm p-1 flex flex-wrap gap-1">
        <button
          v-for="tab in [
            { id: 'endpoints', label: 'Endpoints' },
            { id: 'posture', label: 'Security posture' },
            { id: 'alerts', label: 'Alerts & incidents' },
          ]"
          :key="tab.id"
          @click="activeTab = tab.id as Tab"
          class="px-4 py-2 text-[9px] font-bold uppercase tracking-widest transition-colors cursor-pointer"
          :class="activeTab === tab.id ? 'bg-cyan-500/15 text-cyan-300 border border-cyan-500/30' : 'text-slate-500 hover:text-slate-300'"
        >
          {{ tab.label }}
        </button>
      </section>

      <section v-if="activeTab === 'endpoints'" class="bg-[#111217]/80 border border-slate-800 rounded-sm shadow-xl overflow-hidden">
        <div class="p-4 border-b border-slate-800 flex flex-col md:flex-row gap-3 md:items-center justify-between">
          <div>
            <h3 class="text-[10px] text-slate-300 uppercase font-black tracking-[0.2em]">Endpoint inventory</h3>
            <p class="text-[8px] text-slate-600 uppercase mt-1">Select an endpoint to inspect its Wazuh identity and coverage state</p>
          </div>

          <input
            v-model="endpointSearch"
            type="search"
            placeholder="Search endpoint, IP, OS, group..."
            class="w-full md:w-72 bg-black border border-slate-800 p-2 text-[10px] text-cyan-400 font-mono focus:border-cyan-500 outline-none"
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
                @click="selectedAgent = agent"
                class="border-b border-slate-800/70 hover:bg-cyan-500/[0.04] cursor-pointer transition-colors"
              >
                <td class="px-4 py-3">
                  <p class="text-[11px] text-white font-bold">{{ agent.name }}</p>
                  <p class="text-[8px] text-slate-600 font-mono mt-0.5">ID: {{ agent.id }} · {{ agent.version }}</p>
                </td>
                <td class="px-4 py-3">
                  <span class="inline-block border px-2 py-0.5 rounded-sm text-[8px] font-bold uppercase" :class="statusClass(agent.status)">
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

      <section v-else-if="activeTab === 'posture'" class="space-y-4">
        <div class="grid grid-cols-1 lg:grid-cols-3 gap-4">
          <article class="bg-[#111217]/80 border border-slate-800 rounded-sm p-5">
            <p class="text-[8px] text-cyan-500 uppercase font-bold tracking-[0.18em]">Endpoint coverage</p>
            <p class="mt-3 text-4xl font-light text-white">
              {{ inventory.summary.active }}/{{ inventory.summary.total }}
            </p>
            <p class="mt-2 text-[9px] text-slate-500 uppercase">Agents actively reporting to Wazuh</p>
          </article>

          <article class="bg-[#111217]/80 border border-slate-800 rounded-sm p-5">
            <p class="text-[8px] text-amber-500 uppercase font-bold tracking-[0.18em]">Observed alert posture</p>
            <p class="mt-3 text-4xl font-light text-amber-400">
              {{ overview.alerts.high + overview.alerts.critical }}
            </p>
            <p class="mt-2 text-[9px] text-slate-500 uppercase">High and critical alerts in retained Wazuh indices</p>
          </article>

          <article class="bg-[#111217]/80 border border-slate-800 rounded-sm p-5">
            <p class="text-[8px] text-emerald-500 uppercase font-bold tracking-[0.18em]">Runtime-safe design</p>
            <p class="mt-3 text-xl font-light text-emerald-400">Read only</p>
            <p class="mt-2 text-[9px] text-slate-500 uppercase">No agent, rule, index or Kubernetes mutation</p>
          </article>
        </div>

        <div class="grid grid-cols-1 lg:grid-cols-2 gap-4">
          <article class="border border-slate-800 bg-[#111217]/80 rounded-sm p-5">
            <div class="flex items-center justify-between gap-4">
              <div>
                <h3 class="text-[10px] text-slate-200 uppercase font-black tracking-[0.2em]">Security Configuration Assessment</h3>
                <p class="mt-2 text-[9px] text-slate-500 leading-relaxed">{{ overview.posture.message }}</p>
              </div>
              <span class="border border-slate-700 text-slate-500 text-[8px] uppercase font-bold px-2 py-1">Pending data</span>
            </div>
          </article>

          <article class="border border-slate-800 bg-[#111217]/80 rounded-sm p-5">
            <div class="flex items-center justify-between gap-4">
              <div>
                <h3 class="text-[10px] text-slate-200 uppercase font-black tracking-[0.2em]">Vulnerability Detection</h3>
                <p class="mt-2 text-[9px] text-slate-500 leading-relaxed">No vulnerability state index is available yet. This module will remain explicitly unavailable until Wazuh publishes inventory-backed CVE data.</p>
              </div>
              <span class="border border-slate-700 text-slate-500 text-[8px] uppercase font-bold px-2 py-1">Pending data</span>
            </div>
          </article>
        </div>
      </section>

      <section v-else class="bg-[#111217]/80 border border-slate-800 rounded-sm shadow-xl overflow-hidden">
        <div class="p-4 border-b border-slate-800 flex flex-col xl:flex-row gap-3 xl:items-center justify-between">
          <div>
            <h3 class="text-[10px] text-slate-300 uppercase font-black tracking-[0.2em]">Wazuh alerts & investigation queue</h3>
            <p class="text-[8px] text-slate-600 uppercase mt-1">Live read-only stream from Wazuh Indexer · Select an alert to inspect evidence</p>
          </div>

          <div class="flex flex-col sm:flex-row gap-2">
            <select v-model="levelFilter" class="bg-black border border-slate-800 px-2 py-2 text-[10px] text-slate-300 outline-none focus:border-cyan-500">
              <option value="all">All severities</option>
              <option value="critical">Critical (15+)</option>
              <option value="high">High (12-14)</option>
              <option value="medium">Medium (7-11)</option>
              <option value="low">Low (0-6)</option>
            </select>

            <input
              v-model="alertSearch"
              type="search"
              placeholder="Rule, endpoint, MITRE, IP..."
              class="w-full sm:w-72 bg-black border border-slate-800 p-2 text-[10px] text-cyan-400 font-mono focus:border-cyan-500 outline-none"
            >
          </div>
        </div>

        <div class="overflow-x-auto">
          <table class="min-w-full text-left">
            <thead class="bg-black/20 border-b border-slate-800">
              <tr class="text-[8px] text-slate-500 uppercase tracking-widest">
                <th class="px-4 py-3 font-bold">Severity</th>
                <th class="px-4 py-3 font-bold">Alert</th>
                <th class="px-4 py-3 font-bold">Endpoint</th>
                <th class="px-4 py-3 font-bold">MITRE ATT&CK</th>
                <th class="px-4 py-3 font-bold">Observed</th>
              </tr>
            </thead>

            <tbody>
              <tr
                v-for="alert in filteredAlerts"
                :key="alert.id"
                @click="selectedAlert = alert"
                class="border-b border-slate-800/70 hover:bg-cyan-500/[0.04] cursor-pointer transition-colors"
              >
                <td class="px-4 py-3">
                  <span class="inline-block border px-2 py-0.5 rounded-sm text-[8px] font-bold uppercase" :class="severityClass(alert.level)">
                    L{{ alert.level }} · {{ severityName(alert.level) }}
                  </span>
                </td>
                <td class="px-4 py-3">
                  <p class="text-[10px] text-slate-200 font-semibold">{{ alert.description }}</p>
                  <p class="mt-1 text-[8px] text-slate-600 font-mono">Rule {{ alert.rule_id }} · {{ alert.groups.join(', ') || 'uncategorized' }}</p>
                </td>
                <td class="px-4 py-3">
                  <p class="text-[10px] text-cyan-400 font-mono">{{ alert.agent.name }}</p>
                  <p class="mt-1 text-[8px] text-slate-600 font-mono">{{ alert.agent.ip }}</p>
                </td>
                <td class="px-4 py-3">
                  <p class="text-[9px] text-violet-300 font-mono">{{ alert.mitre.ids.join(', ') || 'N/A' }}</p>
                  <p class="mt-1 text-[8px] text-slate-600">{{ alert.mitre.techniques.join(', ') || 'No mapping' }}</p>
                </td>
                <td class="px-4 py-3">
                  <p class="text-[9px] text-slate-400 font-mono">{{ relativeDate(alert.timestamp) }}</p>
                  <p class="mt-1 text-[8px] text-slate-600">{{ formatDate(alert.timestamp) }}</p>
                </td>
              </tr>

              <tr v-if="filteredAlerts.length === 0">
                <td colspan="5" class="px-4 py-10 text-center text-[10px] text-slate-600 uppercase tracking-widest">
                  No Wazuh alert matches the current filters
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </section>
    </div>

    <div v-if="selectedAgent" class="fixed inset-0 z-50 bg-black/70 flex justify-end" @click.self="selectedAgent = null">
      <aside class="h-full w-full max-w-md bg-[#111217] border-l border-slate-700 shadow-2xl p-6 overflow-y-auto">
        <div class="flex items-start justify-between gap-4 border-b border-slate-800 pb-4">
          <div class="min-w-0 flex-1">
            <p class="text-[8px] text-cyan-500 uppercase font-bold tracking-[0.2em]">
              Endpoint detail
            </p>

            <h3 class="mt-2 break-words pr-2 text-lg text-white font-semibold leading-snug">
              {{ selectedAgent.name }}
            </h3>
          </div>

          <button
            type="button"
            aria-label="Fermer la fenêtre Endpoint detail"
            title="Fermer"
            @click="selectedAgent = null"
            class="shrink-0 inline-flex h-8 w-8 items-center justify-center border border-slate-700 text-lg leading-none text-slate-400 hover:border-cyan-500 hover:bg-cyan-500/10 hover:text-white cursor-pointer transition-colors"
          >
            ×
          </button>
        </div>

        <dl class="mt-5 space-y-4 text-[10px]">
          <div class="flex justify-between gap-4"><dt class="text-slate-500 uppercase">Agent ID</dt><dd class="text-slate-200 font-mono">{{ selectedAgent.id }}</dd></div>
          <div class="flex justify-between gap-4"><dt class="text-slate-500 uppercase">Status</dt><dd><span class="border px-2 py-0.5 text-[8px] uppercase" :class="statusClass(selectedAgent.status)">{{ selectedAgent.status }}</span></dd></div>
          <div class="flex justify-between gap-4"><dt class="text-slate-500 uppercase">Address</dt><dd class="text-cyan-400 font-mono">{{ selectedAgent.ip }}</dd></div>
          <div class="flex justify-between gap-4"><dt class="text-slate-500 uppercase">Group</dt><dd class="text-slate-200 font-mono">{{ selectedAgent.group }}</dd></div>
          <div class="flex justify-between gap-4"><dt class="text-slate-500 uppercase">Version</dt><dd class="text-slate-200 font-mono">{{ selectedAgent.version }}</dd></div>
          <div class="flex justify-between gap-4"><dt class="text-slate-500 uppercase">Operating system</dt><dd class="text-slate-200 text-right">{{ selectedAgent.os.name }} {{ selectedAgent.os.version }}</dd></div>
          <div class="flex justify-between gap-4"><dt class="text-slate-500 uppercase">Architecture</dt><dd class="text-slate-200 font-mono">{{ selectedAgent.os.architecture }}</dd></div>
          <div class="flex justify-between gap-4"><dt class="text-slate-500 uppercase">Last activity</dt><dd class="text-slate-200 font-mono">{{ formatDate(selectedAgent.last_keep_alive) }}</dd></div>
        </dl>

        <div class="mt-8 border border-cyan-900/30 bg-cyan-950/10 p-4">
          <p class="text-[8px] text-cyan-400 uppercase font-bold tracking-widest">Read-only boundary</p>
          <p class="mt-2 text-[9px] text-slate-500 leading-relaxed">K-Guard exposes endpoint context for investigation only. Agent enrollment, configuration and remediation remain unavailable from this interface.</p>
        </div>
      </aside>
    </div>

    <div v-if="selectedAlert" class="fixed inset-0 z-50 bg-black/70 flex justify-end" @click.self="selectedAlert = null">
      <aside class="h-full w-full max-w-2xl bg-[#111217] border-l border-slate-700 shadow-2xl p-6 overflow-y-auto">
        <div class="flex items-start justify-between gap-4 border-b border-slate-800 pb-4">
          <div class="min-w-0 flex-1">
            <p class="text-[8px] text-cyan-500 uppercase font-bold tracking-[0.2em]">
              Alert evidence
            </p>

            <h3 class="mt-2 break-words pr-2 text-lg text-white font-semibold leading-snug">
              {{ selectedAlert.description }}
            </h3>

            <p class="mt-2 break-words text-[9px] text-slate-500 font-mono">
              {{ formatDate(selectedAlert.timestamp) }} · {{ selectedAlert.agent.name }}
            </p>
          </div>

          <button
            type="button"
            aria-label="Fermer la fenêtre Alert evidence"
            title="Fermer"
            @click="selectedAlert = null"
            class="shrink-0 inline-flex h-8 w-8 items-center justify-center border border-slate-700 text-lg leading-none text-slate-400 hover:border-cyan-500 hover:bg-cyan-500/10 hover:text-white cursor-pointer transition-colors"
          >
            ×
          </button>
        </div>

        <div class="mt-5 grid grid-cols-1 sm:grid-cols-2 gap-3">
          <div class="border border-slate-800 p-3"><p class="text-[8px] text-slate-500 uppercase">Rule</p><p class="mt-1 text-[10px] text-white font-mono">{{ selectedAlert.rule_id }}</p></div>
          <div class="border border-slate-800 p-3"><p class="text-[8px] text-slate-500 uppercase">Severity</p><p class="mt-1 text-[10px] font-mono" :class="severityClass(selectedAlert.level)">{{ severityName(selectedAlert.level) }} · Level {{ selectedAlert.level }}</p></div>
          <div class="border border-slate-800 p-3"><p class="text-[8px] text-slate-500 uppercase">Endpoint</p><p class="mt-1 text-[10px] text-cyan-400 font-mono">{{ selectedAlert.agent.name }} · {{ selectedAlert.agent.ip }}</p></div>
          <div class="border border-slate-800 p-3"><p class="text-[8px] text-slate-500 uppercase">Location</p><p class="mt-1 text-[10px] text-slate-300 font-mono break-all">{{ selectedAlert.location }}</p></div>
          <div class="border border-slate-800 p-3"><p class="text-[8px] text-slate-500 uppercase">Rule fired</p><p class="mt-1 text-[10px] text-slate-300 font-mono">{{ selectedAlert.firedtimes }}</p></div>
          <div class="border border-slate-800 p-3"><p class="text-[8px] text-slate-500 uppercase">Manager</p><p class="mt-1 text-[10px] text-slate-300 font-mono break-all">{{ selectedAlert.manager.name }}</p></div>
        </div>

        <section class="mt-5">
          <h4 class="text-[9px] text-slate-400 uppercase font-bold tracking-widest">MITRE ATT&CK context</h4>
          <div class="mt-2 border border-slate-800 p-3 text-[10px] text-slate-300">
            <p><span class="text-slate-500">IDs:</span> {{ selectedAlert.mitre.ids.join(', ') || 'No mapping' }}</p>
            <p class="mt-2"><span class="text-slate-500">Techniques:</span> {{ selectedAlert.mitre.techniques.join(', ') || 'No mapping' }}</p>
            <p class="mt-2"><span class="text-slate-500">Tactics:</span> {{ selectedAlert.mitre.tactics.join(', ') || 'No mapping' }}</p>
          </div>
        </section>

        <section class="mt-5">
          <h4 class="text-[9px] text-slate-400 uppercase font-bold tracking-widest">Event fields</h4>
          <pre class="mt-2 bg-black border border-slate-800 p-3 text-[9px] text-cyan-300 font-mono whitespace-pre-wrap break-words">{{ JSON.stringify({
            decoder: selectedAlert.decoder,
            predecoder: selectedAlert.predecoder,
            data: selectedAlert.data,
            syscheck: selectedAlert.syscheck,
          }, null, 2) }}</pre>
        </section>

        <section class="mt-5">
          <h4 class="text-[9px] text-slate-400 uppercase font-bold tracking-widest">Raw evidence</h4>
          <pre class="mt-2 bg-black border border-slate-800 p-3 text-[9px] text-slate-400 font-mono whitespace-pre-wrap break-words">{{ selectedAlert.full_log || 'No raw log available' }}</pre>
        </section>

        <div class="mt-6 border border-emerald-900/30 bg-emerald-950/10 p-4">
          <p class="text-[8px] text-emerald-400 uppercase font-bold tracking-widest">Investigation-safe workflow</p>
          <p class="mt-2 text-[9px] text-slate-500 leading-relaxed">This alert is visible for triage and evidence collection. Notification and remediation actions will be introduced only through explicit, audited confirmation workflows.</p>
        </div>
      </aside>
    </div>
  </div>
</template>
