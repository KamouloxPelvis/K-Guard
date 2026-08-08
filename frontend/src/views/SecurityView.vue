<script setup lang="ts">
import { ref, onMounted, onUnmounted, computed } from 'vue'
import api from '@/services/api'

interface SecurityAlert {
  id: string
  source: string
  severity: string
  level: number
  message: string
  created_at: string
}

const alerts = ref<SecurityAlert[]>([])
const isLoading = ref(true)
const selectedRange = ref('now-15m')
const activeTab = ref<'dashboard' | 'alerts'>('dashboard')

let interval: ReturnType<typeof setInterval>

const rangeLabel = computed(() => {
  if (selectedRange.value === 'now-15m') return 'Last 15m'
  if (selectedRange.value === 'now-1h') return 'Last 1h'
  return 'Last 24h'
})

const summary = computed(() => {
  const critical = alerts.value.filter((a) => a.level >= 15).length
  const high = alerts.value.filter((a) => a.level >= 12 && a.level <= 14).length
  const medium = alerts.value.filter((a) => a.level >= 7 && a.level <= 11).length
  const low = alerts.value.filter((a) => a.level <= 6).length

  return {
    total: alerts.value.length,
    critical,
    high,
    medium,
    low,
  }
})

const chartBars = computed(() => {
  const max = Math.max(
    summary.value.critical,
    summary.value.high,
    summary.value.medium,
    summary.value.low,
    1,
  )

  return [
    { label: 'Critical', value: summary.value.critical, color: 'bg-red-500/80', width: `${(summary.value.critical / max) * 100}%` },
    { label: 'High', value: summary.value.high, color: 'bg-orange-500/80', width: `${(summary.value.high / max) * 100}%` },
    { label: 'Medium', value: summary.value.medium, color: 'bg-amber-500/80', width: `${(summary.value.medium / max) * 100}%` },
    { label: 'Low', value: summary.value.low, color: 'bg-cyan-500/80', width: `${(summary.value.low / max) * 100}%` },
  ]
})

const fetchAlerts = async () => {
  try {
    const response = await api.get('/security/alerts?limit=50')

    const rawAlerts = Array.isArray(response.data)
      ? response.data
      : []

    const severityLevel = (alert: any): number => {
      const severity = String(
        alert.priority || alert.severity || 'info',
      ).toLowerCase()

      if (['critical', 'emergency', 'alert'].includes(severity)) return 15
      if (['high', 'error'].includes(severity)) return 12
      if (['medium', 'warning', 'warn'].includes(severity)) return 7
      return 3
    }

    alerts.value = rawAlerts.map((alert: any, index: number) => {
      const level = severityLevel(alert)

      return {
        id: alert.event_id || alert.id || `alert-${index}`,
        source: alert.source || 'unknown',
        severity: `${String(
          alert.priority || alert.severity || 'INFO',
        ).toUpperCase()}`,
        level,
        message:
          alert.rule_name ||
          alert.message ||
          alert.output ||
          'No description available',
        created_at: alert.created_at || '',
      }
    })
  } catch (error) {
    console.error('[K-Guard] Runtime Security Fetch Error:', error)
    alerts.value = []
  } finally {
    isLoading.value = false
  }
}

onMounted(() => {
  fetchAlerts()
  interval = setInterval(fetchAlerts, 30000)
})

onUnmounted(() => {
  clearInterval(interval)
})
</script>

<template>
  <div class="p-4 lg:p-6 relative z-10 font-sans h-full overflow-y-auto custom-scrollbar">
    <header class="max-w-7xl mx-auto w-full mb-5 flex flex-col xl:flex-row xl:items-end justify-between gap-4 border-b border-slate-800/40 pb-3">
      <div>
        <p class="text-[10px] text-slate-500 mt-2 uppercase tracking-[0.35em]">
          Runtime Security
        </p>

        <p class="text-[8px] text-slate-600 uppercase tracking-widest mt-2">
          Read-only runtime observability · Falco, Wazuh and K-Guard AI
        </p>
      </div>

      <nav class="flex gap-6">
        <button
          type="button"
          @click="activeTab = 'dashboard'"
          :class="activeTab === 'dashboard' ? 'text-white border-b border-red-500' : 'text-slate-500'"
          class="text-[10px] uppercase font-bold tracking-widest pb-1 transition-all cursor-pointer"
        >
          Dashboard
        </button>

        <button
          type="button"
          @click="activeTab = 'alerts'"
          :class="activeTab === 'alerts' ? 'text-white border-b border-red-500' : 'text-slate-500'"
          class="text-[10px] uppercase font-bold tracking-widest pb-1 transition-all cursor-pointer"
        >
          Live Feed
        </button>
      </nav>
    </header>

    <main class="max-w-7xl mx-auto w-full flex-1 min-h-0">
      <div v-if="activeTab === 'dashboard'" class="w-full space-y-4 pb-10">
        <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
          <select
            v-model="selectedRange"
            class="bg-[#111217] border border-slate-700 text-[9px] px-2 py-1 rounded uppercase font-bold tracking-widest cursor-pointer text-white hover:border-slate-500 transition-colors"
          >
            <option value="now-15m">Last 15m</option>
            <option value="now-1h">Last 1h</option>
            <option value="now-24h">Last 24h</option>
          </select>

          <span class="text-[9px] text-slate-500 uppercase tracking-[0.18em]">
            Runtime telemetry window · {{ rangeLabel }}
          </span>
        </div>

        <div class="grid grid-cols-2 xl:grid-cols-4 gap-3 mb-4">
          <div class="bg-[#111217]/80 border border-slate-800 p-4 rounded-sm">
            <p class="text-[8px] text-slate-500 uppercase font-bold tracking-[0.18em]">Events loaded</p>
            <p class="mt-2 text-3xl font-light text-white">{{ summary.total }}</p>
            <p class="mt-1 text-[8px] text-slate-600 uppercase">Read-only stream</p>
          </div>

          <div class="bg-[#111217]/80 border border-red-900/30 p-4 rounded-sm">
            <p class="text-[8px] text-red-400 uppercase font-bold tracking-[0.18em]">Critical</p>
            <p class="mt-2 text-3xl font-light text-red-300">{{ summary.critical }}</p>
            <p class="mt-1 text-[8px] text-slate-600 uppercase">Falco / Wazuh severe events</p>
          </div>

          <div class="bg-[#111217]/80 border border-orange-900/30 p-4 rounded-sm">
            <p class="text-[8px] text-orange-400 uppercase font-bold tracking-[0.18em]">High</p>
            <p class="mt-2 text-3xl font-light text-orange-300">{{ summary.high }}</p>
            <p class="mt-1 text-[8px] text-slate-600 uppercase">Priority triage queue</p>
          </div>

          <div class="bg-[#111217]/80 border border-cyan-900/30 p-4 rounded-sm">
            <p class="text-[8px] text-cyan-400 uppercase font-bold tracking-[0.18em]">Mode</p>
            <p class="mt-2 text-xl font-light text-cyan-300">Native UI</p>
            <p class="mt-1 text-[8px] text-slate-600 uppercase">No external iframe dependency</p>
          </div>
        </div>

        <section class="grid grid-cols-1 xl:grid-cols-3 gap-4">
          <article class="xl:col-span-2 bg-[#111217]/80 border border-slate-800 rounded-sm p-5">
            <div class="flex items-start justify-between gap-4">
              <div class="min-w-0">
                <p class="text-[8px] text-cyan-400 uppercase font-bold tracking-[0.18em]">
                  Runtime telemetry
                </p>

                <h3 class="mt-2 text-[11px] text-slate-200 uppercase font-black tracking-[0.2em]">
                  Security event context
                </h3>

                <p class="mt-2 text-[9px] text-slate-500 leading-relaxed">
                  Consolidated runtime events from Falco, Wazuh and Kubernetes telemetry.
                </p>
              </div>

              <span class="shrink-0 border border-cyan-500/30 bg-cyan-500/10 px-2 py-1 text-[8px] text-cyan-400 uppercase font-bold">
                Read only
              </span>
            </div>

            <div class="mt-5 min-h-28 border border-slate-800 bg-black/20 p-4">
              <p class="text-[9px] text-slate-600 uppercase tracking-widest">
                Runtime correlation layer ready
              </p>

              <p class="mt-2 text-[9px] text-slate-500 leading-relaxed">
                This area will display correlated events, affected workloads and investigation context.
              </p>
            </div>
          </article>

          <aside class="bg-[#111217]/80 border border-violet-900/30 rounded-sm p-5">
            <div class="flex items-start justify-between gap-4">
              <div class="min-w-0">
                <p class="text-[8px] text-violet-400 uppercase font-bold tracking-[0.18em]">
                  K-Guard AI
                </p>

                <h3 class="mt-2 text-[11px] text-slate-200 uppercase font-black tracking-[0.2em]">
                  Investigation assistant
                </h3>
              </div>

              <span class="shrink-0 border border-violet-500/30 bg-violet-500/10 px-2 py-1 text-[8px] text-violet-300 uppercase font-bold">
                Preparing
              </span>
            </div>

            <div class="mt-5 min-h-28 border border-violet-900/30 bg-violet-950/10 p-4">
              <p class="text-[9px] text-violet-300 uppercase tracking-widest">
                AI enrichment layer
              </p>

              <p class="mt-2 text-[9px] text-slate-500 leading-relaxed">
                AI-generated summaries, probable impact, MITRE context and investigation recommendations will appear here.
              </p>
            </div>
          </aside>
        </section>

        <div class="bg-[#111217]/80 border border-slate-800 rounded-sm p-5">
          <div class="flex items-center justify-between mb-4">
            <div>
              <h3 class="text-[10px] text-slate-300 uppercase font-black tracking-[0.2em]">
                Alert severity distribution
              </h3>
            </div>
          </div>

          <div class="space-y-3">
            <div v-for="bar in chartBars" :key="bar.label">
              <div class="flex items-center justify-between mb-1">
                <span class="text-[9px] text-slate-400 uppercase tracking-widest">{{ bar.label }}</span>
                <span class="text-[9px] text-slate-500 font-mono">{{ bar.value }}</span>
              </div>
              <div class="h-2 w-full bg-black/40 border border-slate-800 overflow-hidden">
                <div class="h-full" :class="bar.color" :style="{ width: bar.width }"></div>
              </div>
            </div>
          </div>

          <div class="mt-5 border border-cyan-900/30 bg-cyan-950/10 p-4 rounded-sm">
            <p class="text-[8px] text-cyan-400 uppercase font-bold tracking-widest">Portfolio-safe design</p>
            <p class="mt-2 text-[9px] text-slate-500 leading-relaxed">
              This runtime view no longer depends on an embedded Kibana dashboard. K-Guard now renders a native,
              read-only observability layer from backend security events.
            </p>
          </div>
        </div>
      </div>

      <div v-else class="w-full space-y-3 pb-10">
        <header class="bg-[#111217]/80 border border-slate-800 rounded-sm p-5">
          <p class="text-[8px] text-red-400 uppercase font-bold tracking-[0.18em]">
            Runtime events
          </p>

          <h2 class="mt-2 text-[11px] text-slate-200 uppercase font-black tracking-[0.2em]">
            Live Alert Feed
          </h2>

          <p class="mt-2 text-[9px] text-slate-500 leading-relaxed">
            Read-only runtime events collected from Falco, Wazuh and the K-Guard security pipeline.
          </p>
        </header>
        <section class="space-y-2">
          <div
          v-for="alert in alerts"
          :key="alert.id"
          class="bg-[#181b1f] border-l-2 border-red-500 p-4 flex justify-between items-start gap-4 hover:bg-[#1e2329] transition-all"
        >
          <div class="min-w-0 flex-1">
            <h3 class="break-words font-mono text-sm font-bold text-white leading-snug">
              {{ alert.message }}
            </h3>

            <p class="mt-1 break-words text-[10px] text-slate-500 uppercase">
              {{ alert.source }} // {{ alert.created_at }}
            </p>
          </div>

          <span class="shrink-0 text-[9px] font-bold px-2 py-1 bg-red-900/20 text-red-500 border border-red-500/30">
            {{ alert.severity }}
          </span>
        </div>
      </section>
        
        <div v-if="!isLoading && alerts.length === 0" class="p-10 text-center text-slate-600 italic">
          System Secure. No active threats detected.
        </div>
      </div>
    </main>
  </div>
</template>