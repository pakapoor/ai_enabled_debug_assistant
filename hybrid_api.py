from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from FlagEmbedding import FlagModel
import psycopg
import logging
import json
import time
from pathlib import Path
from config import POSTGRES_URL

# Logs outside Google Drive sync
LOG_DIR = Path.home() / "rag_logs"
LOG_DIR.mkdir(parents=True, exist_ok=True)

log_file = LOG_DIR / "hybrid_api.log"

logging.basicConfig(
    level=logging.INFO,
    format="%(message)s",
    handlers=[
        logging.FileHandler(log_file),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


def log_request(endpoint: str, query: str, response_time: float, status: str, extra: dict = {}):
    entry = {
        "timestamp": __import__("datetime").datetime.utcnow().isoformat(),
        "endpoint": endpoint,
        "query": query,
        "response_time_seconds": round(response_time, 3),
        "status": status,
        **extra
    }
    logger.info(json.dumps(entry))

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

model = FlagModel("BAAI/bge-small-en-v1.5")

BUG_BOOST = 50
DOC_PENALTY = 30
RRF_K = 60  # standard RRF constant
TOP_N = 5   # number of results returned to the LLM


def is_bug_chunk(metadata):
    if not metadata:
        return False
    return metadata.get("is_bug", False) is True


def is_doc_chunk(metadata):
    if not metadata:
        return False
    file = metadata.get("file", "")
    return (
        file.endswith(".rst")
        or file.endswith(".md")
        or "whatsnew" in file
        or file.endswith(".txt")
    )


def rrf_score(token_rank, vector_rank):
    """Reciprocal Rank Fusion: 1/(k+rank) summed across retrievers."""
    score = 0.0
    if token_rank is not None:
        score += 1.0 / (RRF_K + token_rank)
    if vector_rank is not None:
        score += 1.0 / (RRF_K + vector_rank)
    return score


def apply_boosts(base_score, metadata):
    bug_boost = BUG_BOOST * 0.01 if is_bug_chunk(metadata) else 0
    doc_penalty = DOC_PENALTY * 0.01 if is_doc_chunk(metadata) else 0
    return base_score + bug_boost - doc_penalty


@app.get("/search_hybrid")
def search_hybrid(q: str):
    start_time = time.time()

    query_emb = model.encode([q])[0].tolist()

    conn = psycopg.connect(POSTGRES_URL)
    try:
        cur = conn.cursor()

        cur.execute("""
            SELECT id, source_id, chunk_text, metadata
            FROM chunks
            WHERE to_tsvector('english', chunk_text) @@ plainto_tsquery('english', %s)
            ORDER BY ts_rank_cd(to_tsvector('english', chunk_text), plainto_tsquery('english', %s)) DESC
            LIMIT 10;
        """, (q, q))
        token_rows = cur.fetchall()

        cur.execute("""
            SELECT id, source_id, chunk_text, metadata
            FROM chunks
            WHERE embedding IS NOT NULL
            ORDER BY embedding <=> %s::vector
            LIMIT 10;
        """, (query_emb,))
        vector_rows = cur.fetchall()
    finally:
        conn.close()

    merged = {}

    for rank, (chunk_id, source_id, text, metadata) in enumerate(token_rows):
        merged[chunk_id] = {
            "id": chunk_id,
            "source_id": source_id,
            "text": text,
            "token_rank": rank + 1,
            "vector_rank": None,
            "metadata": metadata,
            "is_bug": is_bug_chunk(metadata),
            "is_doc": is_doc_chunk(metadata),
        }

    for rank, (chunk_id, source_id, text, metadata) in enumerate(vector_rows):
        if chunk_id not in merged:
            merged[chunk_id] = {
                "id": chunk_id,
                "source_id": source_id,
                "text": text,
                "token_rank": None,
                "vector_rank": rank + 1,
                "metadata": metadata,
                "is_bug": is_bug_chunk(metadata),
                "is_doc": is_doc_chunk(metadata),
            }
        else:
            merged[chunk_id]["vector_rank"] = rank + 1

    for entry in merged.values():
        base = rrf_score(entry["token_rank"], entry["vector_rank"])
        entry["score"] = apply_boosts(base, entry["metadata"])
        del entry["metadata"]

    results = sorted(merged.values(), key=lambda x: x["score"], reverse=True)[:TOP_N]

    log_request("/search_hybrid", q, time.time() - start_time, "ok", {
        "results_returned": len(results),
        "token_hits": len(token_rows),
        "vector_hits": len(vector_rows),
    })

    return results