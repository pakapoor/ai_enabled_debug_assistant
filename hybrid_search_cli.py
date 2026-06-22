from FlagEmbedding import FlagModel
import psycopg
from config import POSTGRES_URL

model = FlagModel("BAAI/bge-small-en-v1.5")

query = input("Enter query: ")

query_emb = model.encode([query])[0].tolist()

conn = psycopg.connect(POSTGRES_URL)
cur = conn.cursor()

# 1. Token search top 10
cur.execute(
    """
    SELECT source_id, chunk_text,
           ts_rank_cd(to_tsvector('english', chunk_text), plainto_tsquery('english', %s)) AS score
    FROM chunks
    WHERE to_tsvector('english', chunk_text) @@ plainto_tsquery('english', %s)
    ORDER BY score DESC
    LIMIT 10;
    """,
    (query, query),
)

token_rows = cur.fetchall()

# 2. Vector search top 10
cur.execute(
    """
    SELECT source_id, chunk_text,
           embedding <=> %s::vector AS distance
    FROM chunks
    WHERE embedding IS NOT NULL
    ORDER BY embedding <=> %s::vector
    LIMIT 10;
    """,
    (query_emb, query_emb),
)

vector_rows = cur.fetchall()

print(f"Token rows: {len(token_rows)}")
print(f"Vector rows: {len(vector_rows)}")


# 3. Merge / dedupe
merged = {}

for rank, row in enumerate(token_rows):
    source_id, text, score = row
    merged[source_id] = {
        "id": source_id,
        "text": text,
        "token_rank": rank + 1,
        "vector_rank": None,
        "score": 100 - rank * 5,
    }

for rank, row in enumerate(vector_rows):
    source_id, text, distance = row
    if source_id not in merged:
        merged[source_id] = {
            "id": source_id,
            "text": text,
            "token_rank": None,
            "vector_rank": rank + 1,
            "score": 100 - rank * 5,
        }
    else:
        merged[source_id]["vector_rank"] = rank + 1
        merged[source_id]["score"] += 100 - rank * 5

# 4. Simple rerank for now: combined rank score
results = sorted(merged.values(), key=lambda x: x["score"], reverse=True)[:3]

print("\nTOP 3 RESULTS\n" + "=" * 60)

for r in results:
    print(f"\nID: {r['id']}")
    print(f"Token rank: {r['token_rank']}")
    print(f"Vector rank: {r['vector_rank']}")
    print(f"Combined score: {r['score']}")
    print(r["text"])
    print("-" * 60)

conn.close()
