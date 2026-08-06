<script>
  import { onMount } from 'svelte';
  import { api } from '$lib/api';

  let cfg = $state(null);
  let question = $state('What models does the course use, and what are the embedding dimensions?');
  let busy = $state(false);
  let error = $state('');
  let result = $state(null);
  let showPrompt = $state(false);

  onMount(async () => {
    try {
      cfg = await api.config();
    } catch { /* ignore */ }
  });

  async function ask() {
    if (!question.trim() || busy) return;
    busy = true;
    error = '';
    result = null;
    showPrompt = false;
    try {
      result = await api.ask(question);
    } catch (e) {
      error = e.message;
    } finally {
      busy = false;
    }
  }

  const pct = (score) => Math.round(Math.max(0, Math.min(1, score)) * 100);
</script>

<h1>2 · Ask (retrieve → augment → answer)</h1>
<p class="lead">
  Your question is embedded, the store is searched for the most similar chunks,
  those chunks are pasted into the system prompt, and the model answers using only
  that context. Every step below is what the backend actually did.
</p>

<div class="card">
  <textarea bind:value={question} placeholder="Ask something about your ingested documents…"
    onkeydown={(e) => (e.key === 'Enter' && (e.metaKey || e.ctrlKey)) && ask()}></textarea>
  <div style="display:flex; align-items:center; gap:14px; margin-top:12px; flex-wrap:wrap">
    <button onclick={ask} disabled={busy || !question.trim()}>
      {busy ? 'Thinking…' : 'Ask'}
    </button>
    <span class="muted mono" style="font-size:12px">⌘/Ctrl+Enter</span>
    {#if cfg}
      <span class="muted mono" style="font-size:12px; margin-left:auto">
        top_k={cfg.top_k} · min_score={cfg.min_score}
      </span>
    {/if}
  </div>
  {#if error}<p class="error" style="margin:12px 0 0">⚠ {error}</p>{/if}
</div>

{#if result}
  <!-- STEP 1: retrieval -->
  <h2>① Retrieved {result.retrieved.length} chunk{result.retrieved.length === 1 ? '' : 's'} (ranked by cosine similarity)</h2>
  {#if result.retrieved.length === 0}
    <div class="card">
      <p class="muted" style="margin:0">
        Nothing cleared the <span class="mono">min_score</span> floor — the store has
        no passage relevant to this question. The model is told to say it doesn't
        know rather than answer from general knowledge. (Ingest a relevant document,
        or ask about one you've uploaded.)
      </p>
    </div>
  {:else}
    {#each result.retrieved as c, i (c.chunk_id)}
      <div class="hit">
        <div class="hit-hd">
          <span class="pill" style="border-color:var(--accent); color:var(--accent)">[{i + 1}]</span>
          <span class="muted mono">{c.filename} · chunk {c.ordinal}</span>
          <div class="score">
            <div class="score-bar"><div class="score-fill" style="width:{pct(c.score)}%"></div></div>
            <span class="mono" style="color:var(--accent)">{c.score.toFixed(3)}</span>
          </div>
        </div>
        <div class="hit-body">{c.content}</div>
      </div>
    {/each}
  {/if}

  <!-- STEP 2: augmentation -->
  <h2>② Augmented system prompt</h2>
  <div class="card" style="padding:14px 16px">
    <button class="ghost" onclick={() => (showPrompt = !showPrompt)}>
      {showPrompt ? 'Hide' : 'Show'} the exact prompt sent to the model
    </button>
    {#if showPrompt}
      <pre style="margin-top:12px">{result.system_prompt}</pre>
    {/if}
  </div>

  <!-- STEP 3: answer -->
  <h2>③ Answer
    <span class="pill" style="margin-left:8px; {result.used_context ? 'color:var(--good); border-color:var(--good)' : 'color:var(--accent2); border-color:var(--accent2)'}">
      {result.used_context ? 'grounded in context' : 'no context found'}
    </span>
  </h2>
  <div class="card answer">{result.answer}</div>
{/if}

<style>
  .hit { margin-top: 12px; border: 1px solid var(--border); border-radius: 12px; overflow: hidden; }
  .hit-hd { display: flex; gap: 14px; align-items: center; padding: 9px 14px; background: var(--panel-2); font-size: 13px; }
  .hit-hd .score { margin-left: auto; display: flex; align-items: center; gap: 8px; font-size: 13px; }
  .score-bar { width: 90px; height: 7px; background: var(--border); border-radius: 999px; overflow: hidden; }
  .score-fill { height: 100%; background: var(--accent); }
  .hit-body {
    padding: 12px 14px; font-family: var(--mono); font-size: 12.5px;
    white-space: pre-wrap; word-break: break-word; max-height: 160px; overflow: auto;
  }
  .answer { white-space: pre-wrap; line-height: 1.6; }
</style>
