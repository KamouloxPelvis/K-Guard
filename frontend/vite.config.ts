import { defineConfig, loadEnv } from 'vite'
import vue from '@vitejs/plugin-vue'
import { fileURLToPath, URL } from 'node:url'

export default defineConfig(({ mode }) => {
  
  const env = loadEnv(mode, process.cwd(), '');

  return {
    base: '/k-guard/', 

    plugins: [vue()],
    
    resolve: {
      alias: {
        '@': fileURLToPath(new URL('./src', import.meta.url)),
        'crypto': 'crypto-js',
      }
    },

    server: {
      port: 5173,
      proxy: {
        // On aligne le proxy sur le chemin de l'Ingress
        '/k-guard/api': {
          target: env.VITE_API_URL || 'http://localhost:8000',
          changeOrigin: true,
          secure: false,
          // On ne réécrit rien pour que FastAPI reçoive le chemin complet
        }
      }
    },

    define: {
      // Évite les erreurs avec certaines libs qui cherchent 'global'
      'global': 'window', 
    }
  }
})