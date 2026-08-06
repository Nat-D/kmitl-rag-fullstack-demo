// Tiny fetch wrapper around the backend API. Every call hits /api/* on the same
// origin (served by FastAPI in prod; Vite-proxied in dev).

async function jsonOrThrow(res) {
  if (!res.ok) {
    let detail = res.statusText;
    try {
      const body = await res.json();
      detail = body.detail ?? detail;
    } catch {
      /* non-JSON error body */
    }
    throw new Error(typeof detail === 'string' ? detail : JSON.stringify(detail));
  }
  return res.status === 204 ? null : res.json();
}

export const api = {
  config: () => fetch('/api/config').then(jsonOrThrow),

  listDocuments: () => fetch('/api/documents').then(jsonOrThrow),

  ingest: (file) => {
    const form = new FormData();
    form.append('file', file);
    return fetch('/api/ingest', { method: 'POST', body: form }).then(jsonOrThrow);
  },

  deleteDocument: (id) =>
    fetch(`/api/documents/${id}`, { method: 'DELETE' }).then(jsonOrThrow),

  ask: (question) =>
    fetch('/api/ask', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ question })
    }).then(jsonOrThrow)
};
