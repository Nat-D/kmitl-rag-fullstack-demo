<script>
  import '../app.css';
  import { page } from '$app/stores';
  import { onMount } from 'svelte';
  import { api } from '$lib/api';

  let { children } = $props();
  let cfg = $state(null);

  onMount(async () => {
    try {
      cfg = await api.config();
    } catch {
      /* backend not up yet — the pages handle their own errors */
    }
  });

  const isActive = (path) => $page.url.pathname === path;
</script>

<nav class="nav">
  <span class="brand">RAG<span class="dot">·</span>demo</span>
  <a href="/" class:active={isActive('/')}>1 · Ingest</a>
  <a href="/ask" class:active={isActive('/ask')}>2 · Ask</a>
  <span class="spacer"></span>
  {#if cfg}
    <span class="cfg">embed: {cfg.embed_model} ({cfg.embed_dim}d) · chat: {cfg.chat_model}</span>
  {/if}
</nav>

<main class="page">
  {@render children()}
</main>
