import psycopg
from config import POSTGRES_URL

conn = psycopg.connect(POSTGRES_URL)
cur = conn.cursor()

cur.execute("DELETE FROM chunks")

print("Deleted:", cur.rowcount)

conn.commit()
conn.close()
