# Building LLM-Powered Applications — course facts

The course "Building LLM-Powered Applications" is taught at KMITL. Students learn
to call chat models, get structured JSON output, build a FastAPI backend, stream
tokens to the browser with Server-Sent Events, and build Retrieval-Augmented
Generation (RAG) applications over their own documents.

## The class model proxy

All model calls go through an OpenAI-compatible proxy at https://llm.nat-d.uk/v1.
The chat model is `gemma-4-E4B-it` and the embedding model is `bge-m3`, which
produces 1024-dimensional vectors. Each student gets a personal API key from the
course portal Profile page, with a rate limit of 150 requests per minute.

## Retrieval-Augmented Generation

RAG has two halves. Indexing (offline): split documents into chunks, embed each
chunk into a vector, and store the vectors in a database. Query time (online):
embed the user's question, find the most similar chunks by cosine similarity,
paste those chunks into the system prompt, and ask the model to answer using only
that context. This grounds the answer in your documents and lets the model cite
its sources.

## Why a vector database

A vector database stores embeddings and answers "which stored vectors are closest
to this query vector?" efficiently. This course uses PostgreSQL with the pgvector
extension, which adds a `vector` column type and cosine-distance search to a
database students may already know.
