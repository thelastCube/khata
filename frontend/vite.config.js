import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// Frontend talks to the FastAPI backend at VITE_API_BASE (default localhost:8000).
// localhost:5173 and localhost:8000 are same-site, so the session cookie flows.
export default defineConfig({
  plugins: [react()],
  server: { port: 5173 },
})
