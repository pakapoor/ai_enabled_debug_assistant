import subprocess
import psycopg
from psycopg.types.json import Jsonb
from pathlib import Path
from config import POSTGRES_URL

PROJECT = "your-project"          # change to your repo name
REPO = Path.home() / "rag_data" / PROJECT
LIMIT = 500

conn = psycopg.connect(POSTGRES_URL)
cur = conn.cursor()

# Get commit hashes cleanly first
hashes = subprocess.check_output(
    ["git", "-C", str(REPO), "log", f"-{LIMIT}", "--pretty=format:%H"],
    text=True,
).splitlines()

inserted = 0

for idx, commit_hash in enumerate(hashes):
    subject = subprocess.check_output(
        ["git", "-C", str(REPO), "log", "-1", "--pretty=format:%s", commit_hash],
        text=True,
        errors="ignore",
    ).strip()

    body = subprocess.check_output(
        ["git", "-C", str(REPO), "log", "-1", "--pretty=format:%b", commit_hash],
        text=True,
        errors="ignore",
    ).strip()

    author = subprocess.check_output(
        ["git", "-C", str(REPO), "log", "-1", "--pretty=format:%an", commit_hash],
        text=True,
        errors="ignore",
    ).strip()

    date = subprocess.check_output(
        ["git", "-C", str(REPO), "log", "-1", "--pretty=format:%ad", "--date=short", commit_hash],
        text=True,
        errors="ignore",
    ).strip()

    files_raw = subprocess.check_output(
        ["git", "-C", str(REPO), "show", "--pretty=format:", "--name-only", commit_hash],
        text=True,
        errors="ignore",
    )

    files = [line.strip() for line in files_raw.splitlines() if line.strip()]

    text = f"""
SOURCE: {PROJECT} git commit
COMMIT: {commit_hash}
AUTHOR: {author}
DATE: {date}
SUBJECT: {subject}

BODY:
{body}

FILES CHANGED:
{' '.join(files)}
"""

    chunk_id = f"{PROJECT}-commit-{commit_hash[:12]}"

    metadata = {
        "commit": commit_hash,
        "author": author,
        "date": date,
        "subject": subject,
        "files": files[:100],
    }

    cur.execute(
        """
        INSERT INTO chunks
        (id, project, source_type, source_id, chunk_index, chunk_text, metadata)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT (id) DO UPDATE
        SET chunk_text = EXCLUDED.chunk_text,
            metadata = EXCLUDED.metadata,
            embedding = NULL
        """,
        (
            chunk_id,
            PROJECT,
            "git_commit",
            commit_hash,
            idx,
            text,
            Jsonb(metadata),
        ),
    )

    inserted += 1

conn.commit()
conn.close()

print(f"Inserted/updated {inserted} commits")
