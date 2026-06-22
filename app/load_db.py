import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import POSTGRES_URL

import yaml
from pathlib import Path
import psycopg

conn = psycopg.connect(POSTGRES_URL)

cur = conn.cursor()

cur.execute("DELETE FROM chunks")

for f in Path("/data/bugs").glob("*.yaml"):
    bug = yaml.safe_load(open(f))

    text = f"""
{bug['title']}
{bug['symptom']}
{bug['root_cause']}
{bug['fix_summary']}
{' '.join(bug['tags'])}
"""

    cur.execute(
        """
        INSERT INTO chunks
        (
            id,
            project,
            source_type,
            source_id,
            chunk_index,
            chunk_text
        )
        VALUES (%s,%s,%s,%s,%s,%s)
        """,
        (
            bug["id"],
            "xcelium-demo",
            "bug",
            bug["id"],
            0,
            text
        )
    ) 
conn.commit()

print("loaded")
