# pgvector notes

pgvector is an open-source extension for PostgreSQL that adds vector similarity
search. After `CREATE EXTENSION vector`, a table can have a column of type
`vector(N)`, where N is the embedding dimension.

## Distance operators

pgvector provides three distance operators for the ORDER BY clause:

- `<->` is L2 (Euclidean) distance.
- `<#>` is negative inner product.
- `<=>` is cosine distance, which equals 1 minus cosine similarity.

For text embeddings that are normalized, cosine distance is the usual choice. To
find the ten nearest chunks to a query vector `q`, you write
`ORDER BY embedding <=> q LIMIT 10`.

## Indexes

An exact search scans every row, which is fine for thousands of vectors but slow
for millions. pgvector offers two approximate indexes: IVFFlat and HNSW. HNSW
usually gives better recall for the same speed, at the cost of more memory and
slower index build. You create one with `USING hnsw (embedding vector_cosine_ops)`.
