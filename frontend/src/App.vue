<script setup lang="ts">
import { ref, onMounted } from 'vue';
import axios from 'axios';

interface SystemStatus {
  status: string;
  k3s_health: string;
  vps_storage: string;
  last_check: string;
}

const data = ref<SystemStatus | null>(null);
const loading = ref(true);

const fetchStatus = async () => {
  try {
    const response = await axios.get('/api/v1/status');
    data.value = response.data;
  } catch (error) {
    console.error("Erreur K-Guard API:", error);
  } finally {
    loading.value = false;
  }
};

onMounted(() => {
  fetchStatus();
  setInterval(fetchStatus, 30000); // Refresh toutes les 30s
});
</script>

<template>
  <div class="grafana-container">
    <aside class="sidebar">
      <div class="logo">🛡️ K-GUARD</div>
      <nav>
        <div class="nav-item active">📊 Dashboard</div>
        <div class="nav-item">🔒 Security Logs</div>
        <div class="nav-item">⚙️ Settings</div>
      </nav>
    </aside>

    <main class="content">
      <header class="header">
        <h1>Smart Maintenance Operator</h1>
        <div class="user-profile">Kamal @ DevOpsNotes</div>
      </header>

      <div class="grid">
        <div class="panel">
          <div class="panel-header">System Health</div>
          <div class="panel-body">
            <div v-if="loading" class="loader">Scanning...</div>
            <div v-else class="status-value" :class="data?.status">
              {{ data?.status === 'ok' ? 'ONLINE' : 'ISSUE' }}
            </div>
          </div>
        </div>

        <div class="panel">
          <div class="panel-header">K3s Cluster & Storage</div>
          <div class="panel-body">
            <p>Node Status: <span class="highlight">Ready</span></p>
            <p>Storage: <span class="highlight">76%</span></p>
          </div>
        </div>
      </div>
    </main>
  </div>
</template>

<style scoped>
.grafana-container {
  display: flex;
  height: 100vh;
  background-color: #111217; /* Dark Grafana BG */
  color: #d8d9da;
  font-family: 'Inter', sans-serif;
}

.sidebar {
  width: 200px;
  background-color: #181b1f;
  border-right: 1px solid #2c3235;
  padding: 20px;
}

.logo {
  font-weight: bold;
  color: #f05a28; /* Orange K-Guard */
  margin-bottom: 30px;
}

.content {
  flex: 1;
  padding: 20px;
  background: linear-gradient(180deg, #181b1f 0%, #111217 100%);
}

.grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
  gap: 20px;
  margin-top: 20px;
}

.panel {
  background-color: #181b1f;
  border: 1px solid #2c3235;
  border-radius: 2px;
}

.panel-header {
  background-color: #222529;
  padding: 8px 12px;
  font-size: 12px;
  font-weight: bold;
  border-bottom: 1px solid #2c3235;
}

.panel-body {
  padding: 20px;
  text-align: center;
}

.status-value.ok { color: #73bf69; font-size: 2rem; font-weight: bold; }
.highlight { color: #5794f2; }
</style>