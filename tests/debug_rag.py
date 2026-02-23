"""
debug.py — Run this to isolate exactly where the RAG pipeline breaks.

Usage:
    python debug.py
"""
import asyncio
import aiohttp
import httpx


GATEWAY_URL = "http://localhost:8080"
VLLM_URL    = "http://localhost:8000"
QDRANT_URL  = "http://localhost:6333"


# ── 1. Check which ports are actually open ───────────────────────────────────
def check_ports():
    import socket
    print("\n── Port checks ─────────────────────────────────────────────────")
    for name, host, port in [
        ("vLLM     ", "localhost", 8000),
        ("Gateway  ", "localhost", 8080),
        ("Qdrant   ", "localhost", 6333),
    ]:
        s = socket.socket()
        s.settimeout(1)
        try:
            s.connect((host, port))
            print(f"  ✅ {name} :{port} — reachable")
        except Exception:
            print(f"  ❌ {name} :{port} — CONNECTION REFUSED")
        finally:
            s.close()


# ── 2. Hit the gateway /chat/completions directly ────────────────────────────
def check_gateway():
    print("\n── Gateway /chat/completions (httpx) ───────────────────────────")
    try:
        r = httpx.post(
            f"{GATEWAY_URL}/chat/completions",
            json={"messages": [{"role": "user", "content": "ping"}], "max_tokens": 10},
            timeout=10,
        )
        print(f"  ✅ Status: {r.status_code}")
        print(f"  Response: {r.json()}")
    except Exception as e:
        print(f"  ❌ {e}")


# ── 3. Hit vLLM directly ─────────────────────────────────────────────────────
def check_vllm():
    print("\n── vLLM /v1/chat/completions (httpx) ───────────────────────────")
    try:
        r = httpx.post(
            f"{VLLM_URL}/v1/chat/completions",
            json={
                "model": "llama-3b",
                "messages": [{"role": "user", "content": "ping"}],
                "max_tokens": 10,
            },
            timeout=10,
        )
        print(f"  ✅ Status: {r.status_code}")
        print(f"  Response: {r.json()}")
    except Exception as e:
        print(f"  ❌ {e}")


# ── 4. Check what VLLM_API_URL is set to in settings ─────────────────────────
def check_settings():
    print("\n── Gateway settings ────────────────────────────────────────────")
    try:
        from gateway.core.config import settings
        print(f"  VLLM_API_URL  : {settings.VLLM_API_URL}")
        print(f"  SERVED_MODEL  : {settings.SERVED_MODEL}")
        print(f"  MAX_TOKENS    : {settings.MAX_TOKENS}")
    except Exception as e:
        print(f"  ❌ Could not load settings: {e}")


# ── 5. Simulate send_chat_request directly ───────────────────────────────────
async def check_vllm_client():
    print("\n── send_chat_request() (aiohttp, same as RAGService) ───────────")
    try:
        from gateway.services.vllm_client import send_chat_request
        from gateway.core.config import settings

        print(f"  Hitting: {settings.VLLM_API_URL}")
        payload = {
            "model": settings.SERVED_MODEL,
            "messages": [{"role": "user", "content": "ping"}],
            "max_tokens": 10,
            "temperature": 0.0,
            "stream": False,
        }
        data = await send_chat_request(payload)
        print(f"  ✅ Response: {data}")
    except Exception as e:
        print(f"  ❌ {type(e).__name__}: {e}")


# ── 6. Check Qdrant ──────────────────────────────────────────────────────────
def check_qdrant():
    print("\n── Qdrant ──────────────────────────────────────────────────────")
    try:
        r = httpx.get(f"{QDRANT_URL}/collections", timeout=5)
        collections = r.json().get("result", {}).get("collections", [])
        print(f"  ✅ Reachable — collections: {[c['name'] for c in collections]}")
    except Exception as e:
        print(f"  ❌ {e}")


# ── 7. Full RAG query dry run ─────────────────────────────────────────────────
async def check_rag():
    print("\n── Full RAG query ──────────────────────────────────────────────")
    try:
        from gateway.services.rag.embedder import Embedder
        from gateway.services.rag.vector_store import VectorStore
        from gateway.services.rag.retriever import Retriever
        from gateway.services.rag.rag_service import RAGService

        embedder  = Embedder()
        store     = VectorStore(url=QDRANT_URL, collection="legal_docs")
        retriever = Retriever(embedder, store, top_k=3)
        rag       = RAGService(retriever, max_tokens=50)

        result = await rag.query("What is the termination clause?")
        print(f"  ✅ Answer: {result['answer'][:200]}")
        print(f"  Citations: {result['citations']}")
    except Exception as e:
        print(f"  ❌ {type(e).__name__}: {e}")


# ─────────────────────────────────────────────────────────────────────────────

async def main():
    print("=" * 60)
    print("  RAG Pipeline Debug")
    print("=" * 60)

    check_ports()
    check_settings()
    check_gateway()
    check_vllm()
    await check_vllm_client()
    check_qdrant()
    await check_rag()

    print("\n" + "=" * 60)
    print("  Done. Fix any ❌ above before retrying chat_cli.py")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())