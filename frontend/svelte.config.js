import adapter from '@sveltejs/adapter-static';
import { vitePreprocess } from '@sveltejs/vite-plugin-svelte';

/** @type {import('@sveltejs/kit').Config} */
const config = {
  preprocess: vitePreprocess(),
  kit: {
    // SPA mode: prerender a single shell + client-side routing. FastAPI serves
    // build/ and falls back to index.html so /ask works on refresh.
    adapter: adapter({ fallback: 'index.html', strict: false })
  }
};

export default config;
