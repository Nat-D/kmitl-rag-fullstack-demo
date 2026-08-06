import { sveltekit } from '@sveltejs/kit/vite';
import { defineConfig } from 'vite';

export default defineConfig({
  plugins: [sveltekit()],
  server: {
    // In dev (`npm run dev`), proxy API calls to the FastAPI backend so the
    // frontend can run on :5173 with hot reload while the backend runs on :8000.
    proxy: {
      '/api': 'http://localhost:8000'
    }
  }
});
