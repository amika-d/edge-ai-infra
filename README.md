# Edge AI Gateway

> Running quantized LLMs at the edge with a production-grade RAG pipeline.

A portfolio project demonstrating practical AI infrastructure: serving an AWQ-quantized Llama 3.2 3B model with vLLM, wrapping it in a FastAPI gateway with metrics and concurrency control, and layering a legal document RAG system on top — all running in Docker on a single consumer GPU.

---

## What This Demonstrates

- **AWQ quantization** — 4x VRAM reduction, runs Llama 3.2 3B on 4GB+ GPU
- **vLLM** — production inference engine with PagedAttention and async batching
- **RAG pipeline** — Docling (AI PDF parsing) → HybridChunker → Qdrant → cited answers
- **API gateway** — FastAPI with auth, concurrency limiting, Prometheus metrics
- **Observability** — real-time Grafana dashboards for latency, throughput, active requests

---

## Stack

| Layer | Technology |
|---|---|
| Model serving | vLLM + AWQ |
| API gateway | FastAPI + Uvicorn |
| PDF parsing | Docling (AI layout analysis) |
| Chunking | HybridChunker (section-aware) |
| Embeddings | Sentence Transformers (local) |
| Vector store | Qdrant |
| Observability | Prometheus + Grafana |
| Containers | Docker Compose |

---

## Quick Start

**Prerequisites:** Docker, NVIDIA GPU (4GB+ VRAM), nvidia-container-toolkit

```bash
# 1. Clone and configure
git clone <repo>
cd edge_computing
cp .env.example .env
# fill in MODEL_ID and HF_TOKEN

# 2. Start the full stack
docker compose up -d

# 3. Index a document
python gateway/cli/ingest_cli.py gateway/data/docs/lease_agreement.pdf

# 4. Chat
python gateway/cli/chat_cli.py --doc lease_agreement
```

---

## API

```bash
curl -X POST http://localhost:8080/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "messages": [{"role": "user", "content": "What is the termination notice period?"}],
    "max_tokens": 512
  }'
```

Response includes `usage.latency` and `usage.tokens_per_sec` from your hardware.

---

## RAG Pipeline

```
PDF → Docling → HybridChunker → SentenceTransformer → Qdrant
                                                          ↓
Query → embed → similarity search → prompt_builder → vLLM → cited answer
```

Every answer includes structured citations:
```json
{
  "answer": "The tenant must provide 30 days written notice...",
  "citations": [
    { "doc": "lease_agreement.pdf", "page": 12, "section": "Termination Clause", "score": 0.91 }
  ]
}
```

---

## Services

| Service | URL | Purpose |
|---|---|---|
| Gateway | http://localhost:8080 | API endpoint |
| vLLM | http://localhost:8000 | Model inference |
| Qdrant | http://localhost:6333 | Vector store |
| Prometheus | http://localhost:9090 | Metrics |
| Grafana | http://localhost:3030 | Dashboards |

---

## Model

`AMead10/Llama-3.2-3B-Instruct-AWQ` — 4-bit AWQ quantized Llama 3.2 3B.  
vLLM serves it using optimized AWQ CUDA kernels with no runtime quantization step.

---

## Project Structure

```
gateway/
├── routes/          chat + metrics endpoints
├── services/
│   ├── vllm_client.py      async aiohttp client
│   └── rag/
│       ├── chunker.py       Docling-powered chunker
│       ├── embedder.py      local sentence-transformers
│       ├── vector_store.py  Qdrant wrapper
│       ├── retriever.py     embed + search
│       ├── prompt_builder.py  context formatting
│       ├── citation_builder.py  structured citations
│       └── rag_service.py   orchestrates full pipeline
├── middleware/auth.py        API key enforcement
├── metrics/metrics.py        Prometheus metrics
└── cli/
    ├── ingest_cli.py         index a PDF
    └── chat_cli.py           interactive chat
```