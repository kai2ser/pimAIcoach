# PIM AI Coach — Setup & Deployment Guide

## Architecture

```
[User Browser]
      │
      ▼
[Vercel — Next.js Frontend]  ──rewrites──▶  [Railway — FastAPI Backend]
                                                     │
                                                     ▼
                                            [Neon PostgreSQL + pgvector]
                                                     │
                                              ┌──────┴──────┐
                                              │             │
                                        policy_records  vector embeddings
                                        + documents     (langchain_pg_*)
                                        (pimrepository)
```

Both the pimrepository app and the AI Coach share the **same Neon database**.
The AI Coach adds pgvector tables alongside the existing pimrepository tables.

---

## Step 1: Prerequisites

- Python 3.12+
- Node.js 20+
- A Neon database (reuse the one from pimrepository)
- An OpenAI API key (for embeddings) or alternative provider
- An Anthropic API key (for Claude LLM) or alternative provider

---

## Step 2: Push to GitHub

```bash
# If gh CLI is installed:
gh repo create kai2ser/pimAIcoach --public --source . --push

# Otherwise, create repo at github.com/new, then:
git remote add origin git@github.com:kai2ser/pimAIcoach.git
git push -u origin main
```

---

## Step 3: Set Up the Backend Locally

```bash
cd backend

# Create virtual environment
python -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your actual values:
#   PIM_DATABASE_URL=postgresql://...  (your Neon connection string)
#   PIM_OPENAI_API_KEY=sk-...
#   PIM_ANTHROPIC_API_KEY=sk-ant-...
```

---

## Step 4: Enable pgvector on Neon

```bash
cd backend
python -m scripts.setup_pgvector
```

This runs `CREATE EXTENSION IF NOT EXISTS vector` on your Neon database.
Neon supports pgvector natively — no additional setup required.

---

## Step 5: Ingest Documents

The ingestion script reads from the pimrepository database (policy_records +
documents tables), downloads PDFs from Vercel Blob, chunks them, and stores
embeddings in pgvector.

```bash
cd backend

# Preview what will be ingested (no changes made)
python -m scripts.ingest_from_pimrepo --dry-run

# Ingest all documents
python -m scripts.ingest_from_pimrepo

# Ingest a specific country
python -m scripts.ingest_from_pimrepo --country COL

# Use a different chunking strategy
python -m scripts.ingest_from_pimrepo --chunker semantic
```

**Note**: Documents must be uploaded in the pimrepository app first.
The ingestion script only processes records that have PDF files attached.

---

## Step 6: Test Locally

```bash
# Terminal 1 — Start the backend
cd backend
source .venv/bin/activate
uvicorn app.main:app --reload --port 8000

# Terminal 2 — Start the frontend
cd frontend
npm install
npm run dev
```

Open http://localhost:3000/coach and try asking a question.

### Verify the API directly:

```bash
# Check config
curl http://localhost:8000/api/config | python -m json.tool

# Ask a question
curl -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{"question": "What are best practices for project appraisal?"}'
```

---

## Step 7: Deploy Backend to Railway

1. Go to [railway.app](https://railway.app) and create a new project
2. Connect your GitHub repo (`kai2ser/pimAIcoach`)
3. Set the **root directory** to `backend`
4. Railway will detect the Dockerfile automatically
5. Add environment variables in Railway dashboard:
   - `PIM_DATABASE_URL` — your Neon connection string
   - `PIM_OPENAI_API_KEY` — your OpenAI key
   - `PIM_ANTHROPIC_API_KEY` — your Anthropic key
   - `PORT` — Railway sets this automatically
6. Deploy. Note the public URL (e.g., `https://pimaicoach-backend-production.up.railway.app`)

---

## Step 8: Deploy Frontend to Vercel

1. Go to [vercel.com](https://vercel.com) and import `kai2ser/pimAIcoach`
2. Set the **root directory** to `frontend`
3. Framework preset: **Next.js**
4. Add environment variable:
   - `NEXT_PUBLIC_BACKEND_URL` = your Railway URL (e.g., `https://pimaicoach-backend-production.up.railway.app`)
5. Deploy

The Next.js rewrites will proxy `/api/coach/*` requests to the Railway backend.

---

## Step 9: Tweak RAG Parameters

### Via the admin API (runtime, no redeploy needed):

```bash
# View current config
curl https://YOUR_RAILWAY_URL/api/config

# Switch to MMR retrieval with more documents
curl -X PUT https://YOUR_RAILWAY_URL/api/config \
  -H "Content-Type: application/json" \
  -d '{"retriever_type": "mmr", "retriever_k": 8}'

# Switch to Claude Opus for generation
curl -X PUT https://YOUR_RAILWAY_URL/api/config \
  -H "Content-Type: application/json" \
  -d '{"llm_model": "claude-opus-4-20250514"}'

# Try larger chunks
curl -X PUT https://YOUR_RAILWAY_URL/api/config \
  -H "Content-Type: application/json" \
  -d '{"chunk_size": 1500, "chunk_overlap": 300}'
```

**Note**: Changing `chunk_size` or `embedding_model` requires re-ingesting
documents for the changes to take effect on stored vectors.

### Via environment variables (requires redeploy):

Update `PIM_*` vars in Railway dashboard and redeploy.

---

## Swappable Components Reference

| Component | Config Key | Options |
|---|---|---|
| Chunker | `PIM_CHUNKER` | `recursive`, `semantic`, `by_section` |
| Embeddings | `PIM_EMBEDDING_MODEL` | `openai`, `cohere`, `huggingface` |
| Vector Store | `PIM_VECTOR_STORE` | `pgvector`, `chroma`, `faiss` |
| Retriever | `PIM_RETRIEVER_TYPE` | `similarity`, `mmr`, `self_query` |
| Reranker | `PIM_RERANKER` | (none), `cohere`, `cross_encoder` |
| LLM | `PIM_LLM_PROVIDER` | `anthropic`, `openai`, `ollama` |
| Chain | `PIM_CHAIN_TYPE` | `stuff`, `map_reduce`, `refine` |
