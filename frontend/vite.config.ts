import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import path from 'path'

export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
    },
  },
  server: {
    host: '0.0.0.0',
    port: 3000,
    proxy: {
      '/biomarkers': 'http://localhost:8000',
      '/protocols': 'http://localhost:8000',
      '/checklist': 'http://localhost:8000',
      '/research': 'http://localhost:8000',
      '/correlation': 'http://localhost:8000',
      '/blood-panel': 'http://localhost:8000',
    },
  },
})
