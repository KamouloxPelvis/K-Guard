import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import { fileURLToPath, URL } from 'node:url'

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
  resolve: {
    alias: {
      '@': fileURLToPath(new URL('./src', import.meta.url)),
      // On redirige l'appel vers un polyfill ou on le "nullifie" si non critique
      'crypto': 'crypto-js',
    }
  },
  // Si le problème persiste, on peut aussi définir global
  define: {
    'global': {},
  },
})