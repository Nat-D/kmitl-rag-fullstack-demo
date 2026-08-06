-- Enable pgvector so columns can use the `vector` type. Runs once, when the
-- database is first created. The Alembic migration also guards this with a
-- CREATE EXTENSION IF NOT EXISTS, so the app is safe even against a stock
-- Postgres image — but doing it here keeps the migration focused on tables.
CREATE EXTENSION IF NOT EXISTS vector;
