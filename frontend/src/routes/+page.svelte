<script>
  import { onMount } from 'svelte';
  import { api } from '$lib/api';

  let docs = $state([]);
  let cfg = $state(null);
  let busy = $state(false);
  let error = $state('');
  let lastIngest = $state(null); // the IngestResult of the most recent upload
  let fileInput;

  onMount(refresh);

  async function refresh() {
    try {
      [docs, cfg] = await Promise.all([api.listDocuments(), api.config()]);
    } catch (e) {
      error = e.message;
    }
  }

  async function onPick(e) {
    const file = e.target.files?.[0];
    if (!file) return;
    busy = true;
    error = '';
    lastIngest = null;
    try {
      lastIngest = await api.ingest(file);
      await refresh();
    } catch (e) {
      error = e.message;
    } finally {
      busy = false;
      if (fileInput) fileInput.value = '';
    }
  }

  async function remove(id) {
    try {
      await api.deleteDocument(id);
      if (lastIngest?.document.id === id) lastIngest = null;
      await refresh();
    } catch (e) {
      error = e.message;
    }
  }

  // Split a chunk's text into [overlappingPrefix, rest] so the shared region can
  // be highlighted — this is the part it shares with the previous chunk.
  const splitOverlap = (chunk) => [
    chunk.content.slice(0, chunk.overlap_prev),
    chunk.content.slice(chunk.overlap_prev)
  ];
</script>

<h1>1 · Ingest documents</h1>
<p class="lead">
  Upload a <code>.txt</code> or <code>.md</code> file. It's split into overlapping
  <strong>chunks</strong>, each chunk is turned into a 1024-dim <strong>embedding</strong>,
  and the vectors are stored in Postgres (pgvector). Watch how the chunking works below.
</p>

<div class="card">
  <div style="display:flex; align-items:center; gap:14px; flex-wrap:wrap">
    <button onclick={() => fileInput.click()} disabled={busy}>
      {busy ? 'Ingesting…' : 'Choose a file to ingest'}
    </button>
    <input
      bind:this={fileInput}
      type="file"
      accept=".txt,.md,text/plain,text/markdown"
      onchange={onPick}
      style="display:none"
    />
    {#if cfg}
      <span class="muted mono" style="font-size:13px">
        chunk_size={cfg.chunk_size} · overlap={cfg.chunk_overlap} chars
      </span>
    {/if}
  </div>
  {#if error}<p class="error" style="margin:12px 0 0">⚠ {error}</p>{/if}
</div>

{#if lastIngest}
  <h2>How “{lastIngest.document.filename}” was chunked</h2>
  <p class="lead">
    {lastIngest.document.n_chars.toLocaleString()} characters →
    <strong>{lastIngest.chunks.length} chunks</strong> of up to {lastIngest.chunk_size} chars,
    each overlapping the previous by {lastIngest.chunk_overlap}. The
    <span style="background:var(--accent); color:#04222e; padding:0 4px; border-radius:3px">highlighted</span>
    text is the overlap — it appears in two chunks so a sentence split across a
    boundary still lands whole in at least one.
  </p>

  <!-- overview bar: each chunk as a segment along the document -->
  <div class="card" style="padding:14px 16px">
    <div class="bars">
      {#each lastIngest.chunks as c (c.ordinal)}
        <div
          class="bar"
          style="flex: {c.n_chars}"
          title={`chunk ${c.ordinal}: chars ${c.start}–${c.end}`}
        >
          <span class="bar-label">#{c.ordinal}</span>
        </div>
      {/each}
    </div>
  </div>

  {#each lastIngest.chunks as c (c.ordinal)}
    {@const [pre, rest] = splitOverlap(c)}
    <div class="chunk">
      <div class="chunk-hd">
        <span class="pill">chunk {c.ordinal}</span>
        <span class="muted mono">chars {c.start}–{c.end} · {c.n_chars} chars</span>
        {#if c.overlap_prev > 0}
          <span class="muted mono">↖ overlaps prev by {c.overlap_prev}</span>
        {/if}
      </div>
      <div class="chunk-body">{#if pre}<mark>{pre}</mark>{/if}{rest}</div>
    </div>
  {/each}
{/if}

<h2>Stored documents <span class="muted mono" style="font-size:14px">({docs.length})</span></h2>
{#if docs.length === 0}
  <p class="muted">Nothing ingested yet. Upload a file above to fill the vector store.</p>
{:else}
  <div class="card" style="padding:0">
    <table>
      <thead>
        <tr><th>#</th><th>file</th><th>chars</th><th>chunks</th><th></th></tr>
      </thead>
      <tbody>
        {#each docs as d (d.id)}
          <tr>
            <td class="mono muted">{d.id}</td>
            <td>{d.filename}</td>
            <td class="mono">{d.n_chars.toLocaleString()}</td>
            <td class="mono">{d.n_chunks}</td>
            <td><button class="ghost" onclick={() => remove(d.id)}>delete</button></td>
          </tr>
        {/each}
      </tbody>
    </table>
  </div>
{/if}

<style>
  .bars { display: flex; gap: 2px; height: 34px; }
  .bar {
    position: relative;
    min-width: 8px;
    background: var(--panel-2);
    border: 1px solid var(--accent);
    border-radius: 5px;
    display: flex;
    align-items: center;
    justify-content: center;
    overflow: hidden;
  }
  .bar-label { font-family: var(--mono); font-size: 11px; color: var(--accent); }
  .chunk { margin-top: 12px; border: 1px solid var(--border); border-radius: 12px; overflow: hidden; }
  .chunk-hd {
    display: flex; gap: 14px; align-items: center; flex-wrap: wrap;
    padding: 9px 14px; background: var(--panel-2); font-size: 13px;
  }
  .chunk-body {
    padding: 12px 14px; font-family: var(--mono); font-size: 12.5px;
    white-space: pre-wrap; word-break: break-word; max-height: 180px; overflow: auto;
  }
  mark { background: var(--accent); color: #04222e; border-radius: 2px; }
  table { width: 100%; border-collapse: collapse; }
  th, td { text-align: left; padding: 11px 16px; border-bottom: 1px solid var(--border); }
  th { font-size: 12px; text-transform: uppercase; letter-spacing: 0.05em; color: var(--muted); }
  tr:last-child td { border-bottom: none; }
</style>
