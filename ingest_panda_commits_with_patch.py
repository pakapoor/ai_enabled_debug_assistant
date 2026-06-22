import subprocess
import psycopg
from psycopg.types.json import Jsonb
from pathlib import Path
from config import POSTGRES_URL

REPO = Path.home() / "rag_data" / "pandas"
LIMIT = 500
MAX_PATCH_CHARS = 20000

conn = psycopg.connect(POSTGRES_URL)
cur = conn.cursor()

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

    patch = subprocess.check_output(
        ["git", "-C", str(REPO), "show", "--stat", "--patch", "--pretty=format:", commit_hash],
        text=True,
        errors="ignore",
    ).strip()

    patch_truncated = False
    if len(patch) > MAX_PATCH_CHARS:
        patch = patch[:MAX_PATCH_CHARS]
        patch_truncated = True

    text = f"""
SOURCE: pandas git commit
COMMIT: {commit_hash}
AUTHOR: {author}
DATE: {date}
SUBJECT: {subject}

BODY:
{body}

FILES CHANGED:
{' '.join(files)}

PATCH:
{patch}
"""

    chunk_id = f"pandas-commit-{commit_hash[:12]}"

    metadata = {
        "commit": commit_hash,
        "author": author,
        "date": date,
        "subject": subject,
        "is_bug": subject.startswith("BUG:"),
        "files": files[:100],
        "has_patch": True,
        "patch_truncated": patch_truncated,
        "max_patch_chars": MAX_PATCH_CHARS,
    }

    cur.execute(
        """
        INSERT INTO chunks
        (id, project, source_type, source_id, chunk_index, chunk_text, metadata, embedding)
        VALUES (%s, %s, %s, %s, %s, %s, %s, NULL)
        ON CONFLICT (id) DO UPDATE
        SET chunk_text = EXCLUDED.chunk_text,
            metadata = EXCLUDED.metadata,
            embedding = NULL
        """,
        (
            chunk_id,
            "pandas",
            "git_commit",
            commit_hash,
            idx,
            text,
            Jsonb(metadata),
        ),
    )

    inserted += 1

    if inserted % 50 == 0:
        conn.commit()
        print(f"Inserted/updated {inserted} commits...")

conn.commit()
conn.close()

print(f"Done. Inserted/updated {inserted} pandas commits with patches.")
