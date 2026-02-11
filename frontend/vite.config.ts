import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

export default defineConfig({
  // Crucial : définit le chemin de base pour tous les assets (JS, CSS, Images)
  base: '/k-guard/', 
  
  server: {
    proxy: {
      // En local, on redirige /k-guard/api vers le backend FastAPI
      '/k-guard/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
        secure: false,
        rewrite: (path) => path.replace(/^\/k-guard\/api/, '/api')
      }
    }
  },
  plugins: [vue()],
})