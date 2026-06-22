# app/app/main.py
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import POSTGRES_URL

from fastapi import FastAPI
import psycopg

app = FastAPI()

@app.get("/health")
def health():
    """Simple health check endpoint."""
    return {"status": "ok"}

@app.get("/search")
def search(q: str):
    """
    Run a keyword search over your bug chunks using PostgreSQL full‑text search.
    Returns up to five matches with basic ranking.
    """
    conn = psycopg.connect(POSTGRES_URL)
    cur = conn.cursor()
    cur.execute(
        """
        SELECT source_id,
               chunk_text,
               ts_rank_cd(
                 to_tsvector(chunk_text),
                 plainto_tsquery(%s)
               ) AS rank
        FROM chunks
        WHERE to_tsvector(chunk_text) @@ plainto_tsquery(%s)
        ORDER BY rank DESC
        LIMIT 5;
        """,
        (q, q),
    )
    rows = cur.fetchall()
    conn.close()
    return [
        {"id": row[0], "text": row[1], "rank": float(row[2])}
        for row in rows
    ]
