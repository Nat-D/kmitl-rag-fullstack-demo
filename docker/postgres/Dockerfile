# Postgres 16 with the pgvector extension preinstalled.
#
# We build our own image (instead of using pgvector/pgvector directly) so the
# `vector` extension is enabled automatically the first time the database
# initialises — see init/01-enable-vector.sql, copied into the image's
# docker-entrypoint-initdb.d. That directory is run once, on an empty data
# volume, by the official Postgres entrypoint.
FROM pgvector/pgvector:pg16

# Runs only on first initialisation of an empty data directory.
COPY init/01-enable-vector.sql /docker-entrypoint-initdb.d/01-enable-vector.sql
