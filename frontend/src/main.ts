import { createApp } from 'vue'
import App from './App.vue'
import router from './router' // Importe la config du router [cite: 2026-02-07]
import './style.css'

const app = createApp(App)

app.use(router) // On dit à Vue d'utiliser le système de navigation [cite: 2026-02-07]
app.mount('#app')