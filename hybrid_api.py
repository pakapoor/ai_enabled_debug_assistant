from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from FlagEmbedding import FlagModel
import psycopg
from config import POSTGRES_URL

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


def compute_score(base_score, metadata):
    bug_boost = BUG_BOOST if is_bug_chunk(metadata) else 0
    doc_penalty = DOC_PENALTY if is_doc_chunk(metadata) else 0
    return base_score + bug_boost - doc_penalty


@app.get("/search_hybrid")
def search_hybrid(q: str):
    query_emb = model.encode([q])[0].tolist()

    conn = psycopg.connect(POSTGRES_URL)
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

    merged = {}

    for rank, (chunk_id, source_id, text, metadata) in enumerate(token_rows):
        base = 100 - rank * 5
        score = compute_score(base, metadata)

        merged[chunk_id] = {
            "id": chunk_id,
            "source_id": source_id,
            "text": text,
            "token_rank": rank + 1,
            "vector_rank": None,
            "score": score,
            "is_bug": is_bug_chunk(metadata),
            "is_doc": is_doc_chunk(metadata),
        }

    for rank, (chunk_id, source_id, text, metadata) in enumerate(vector_rows):
        base = 100 - rank * 5
        vector_score = compute_score(base, metadata)

        if chunk_id not in merged:
            merged[chunk_id] = {
                "id": chunk_id,
                "source_id": source_id,
                "text": text,
                "token_rank": None,
                "vector_rank": rank + 1,
                "score": vector_score,
                "is_bug": is_bug_chunk(metadata),
                "is_doc": is_doc_chunk(metadata),
            }
        else:
            merged[chunk_id]["vector_rank"] = rank + 1
            merged[chunk_id]["score"] += vector_score

    conn.close()

    results = sorted(merged.values(), key=lambda x: x["score"], reverse=True)[:3]
    return results