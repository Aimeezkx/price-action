import { defineConfig, loadEnv } from 'vite'
import react from '@vitejs/plugin-react'

// https://vitejs.dev/config/
export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, process.cwd(), 'VITE_')
  const configuredApiUrl = env.VITE_API_BASE_URL || 'http://localhost:8000'
  const apiTarget = new URL(configuredApiUrl).origin
  
  return {
    plugins: [react()],
    server: {
      host: '0.0.0.0',
      port: 3000,
      hmr: {
        overlay: false
      },
      proxy: {
        '/api': {
          target: apiTarget,
          changeOrigin: true,
          secure: false
        }
      }
    },
    build: {
      outDir: 'dist',
      sourcemap: true,
    },
    css: {
      postcss: {
        plugins: []
      }
    }
  }
})
