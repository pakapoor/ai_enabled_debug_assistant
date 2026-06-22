import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import POSTGRES_URL

import yaml
from pathlib import Path
import psycopg
from FlagEmbedding import FlagModel  # or from sentence_transformers import SentenceTransformer

# 1. Load the BGE-small embedding model
model = FlagModel('BAAI/bge-small-en-v1.5')
# If using sentence-transformers instead:
# model = SentenceTransformer('BAAI/bge-small-en-v1.5')

# 2. Connect to the Postgres database
conn = psycopg.connect(POSTGRES_URL)
cur = conn.cursor()

# 3. Iterate over chunks and compute embeddings
cur.execute("SELECT id, chunk_text FROM chunks WHERE embedding IS NULL;")
rows = cur.fetchall()
for chunk_id, text in rows:
    embedding = model.encode([text])[0].tolist()  # produces a 384‑dimensional vector
    cur.execute(
        "UPDATE chunks SET embedding = %s WHERE id = %s;",
        (embedding, chunk_id)
    )

conn.commit()
conn.close()
print("Embeddings saved to database.")
