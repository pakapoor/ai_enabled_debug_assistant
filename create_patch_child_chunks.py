import ast
import re
from pathlib import Path

import psycopg
from psycopg.types.json import Jsonb
from config import POSTGRES_URL


REPO = Path.home() / "rag_data" / "pandas"
MAX_FUNCTION_CONTEXT_LINES = 120


def get_hunk_new_start_lines(file_patch):
    lines = []

    for line in file_patch.splitlines():
        if not line.startswith("@@"):
            continue

        match = re.search(r"\+(\d+)(?:,\d+)?", line)
        if match:
            lines.append(int(match.group(1)))

    return lines


def find_enclosing_symbols(file_path, target_line):
    full_path = REPO / file_path

    if not full_path.exists() or not file_path.endswith(".py"):
        return None, None

    try:
        source = full_path.read_text(encoding="utf-8", errors="ignore")
        tree = ast.parse(source)
    except Exception:
        return None, None

    matches = []

    def visit(node, class_stack):
        start = getattr(node, "lineno", None)
        end = getattr(node, "end_lineno", None)

        if start is not None and end is not None:
            if start <= target_line <= end:
                if isinstance(node, ast.ClassDef):
                    matches.append(("class", node.name, start, end, list(class_stack)))
                    class_stack = class_stack + [node.name]
                elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    matches.append(("function", node.name, start, end, list(class_stack)))

        for child in ast.iter_child_nodes(node):
            visit(child, class_stack)

    visit(tree, [])

    classes = [m for m in matches if m[0] == "class"]
    funcs = [m for m in matches if m[0] == "function"]

    class_name = classes[-1][1] if classes else None
    function_name = funcs[-1][1] if funcs else None

    return class_name, function_name


def get_function_source(file_path, function_name):
    full_path = REPO / file_path

    if not full_path.exists() or not file_path.endswith(".py"):
        return ""

    try:
        source = full_path.read_text(encoding="utf-8", errors="ignore")
        tree = ast.parse(source)
    except Exception:
        return ""

    source_lines = source.splitlines()

    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            if node.name == function_name:
                start = node.lineno
                end = node.end_lineno

                function_lines = source_lines[start - 1:end]

                truncated = False
                if len(function_lines) > MAX_FUNCTION_CONTEXT_LINES:
                    function_lines = function_lines[:MAX_FUNCTION_CONTEXT_LINES]
                    truncated = True

                result = "\n".join(function_lines)

                if truncated:
                    result += (
                        f"\n\n[Function context truncated. "
                        f"Showing {MAX_FUNCTION_CONTEXT_LINES} lines.]"
                    )

                return result

    return ""


def extract_symbols_from_patch(file_name, file_patch):
    hunk_headers = []
    class_names = []
    function_names = []

    for line in file_patch.splitlines():
        if line.startswith("@@"):
            hunk_headers.append(line)

    for line_no in get_hunk_new_start_lines(file_patch):
        class_name, function_name = find_enclosing_symbols(file_name, line_no)

        if class_name:
            class_names.append(class_name)

        if function_name:
            function_names.append(function_name)

    return {
        "hunk_headers": list(dict.fromkeys(hunk_headers)),
        "class_names": list(dict.fromkeys(class_names)),
        "function_names": list(dict.fromkeys(function_names)),
    }


def build_function_context_text(file_name, function_names):
    if not function_names:
        return ""

    blocks = []

    for function_name in function_names[:3]:
        function_source = get_function_source(file_name, function_name)

        if not function_source:
            continue

        blocks.append(
            f"""
FUNCTION: {function_name}
{function_source}
""".strip()
        )

    if not blocks:
        return ""

    return "\n\n".join(blocks)


conn = psycopg.connect(POSTGRES_URL)
cur = conn.cursor()

cur.execute("""
SELECT id, source_id, chunk_text, metadata
FROM chunks
WHERE project = 'pandas'
  AND source_type = 'git_commit'
  AND chunk_text LIKE '%PATCH:%'
ORDER BY chunk_index;
""")

parents = cur.fetchall()

inserted = 0

for parent_id, commit_hash, chunk_text, metadata in parents:
    patch = chunk_text.split("PATCH:", 1)[1].strip()

    file_patches = re.split(r"(?=^diff --git )", patch, flags=re.MULTILINE)

    patch_index = 0

    for fp in file_patches:
        fp = fp.strip()

        if not fp.startswith("diff --git "):
            continue

        match = re.search(r"^diff --git a/(.*?) b/(.*?)$", fp, flags=re.MULTILINE)

        if match:
            old_file = match.group(1)
            new_file = match.group(2)
            file_name = new_file
        else:
            old_file = ""
            new_file = ""
            file_name = ""

        symbols = extract_symbols_from_patch(file_name, fp)

        class_names = symbols["class_names"]
        function_names = symbols["function_names"]
        hunk_headers = symbols["hunk_headers"]

        function_context = build_function_context_text(file_name, function_names)

        patch_index += 1

        child_id = f"{parent_id}-patch-{patch_index:03d}"

        subject = metadata.get("subject", "") if metadata else ""
        author = metadata.get("author", "") if metadata else ""
        date = metadata.get("date", "") if metadata else ""

        symbol_text = ""
        if class_names or function_names or hunk_headers:
            symbol_text = f"""
SYMBOL CONTEXT:
Classes: {", ".join(class_names)}
Functions: {", ".join(function_names)}
Hunk headers:
{chr(10).join(hunk_headers)}
"""

        function_context_text = ""
        if function_context:
            function_context_text = f"""
FUNCTION CONTEXT:
{function_context}
"""

        child_text = f"""
SOURCE: pandas git patch file
COMMIT: {commit_hash}
PARENT_CHUNK: {parent_id}
AUTHOR: {author}
DATE: {date}
SUBJECT: {subject}

FILE:
{file_name}

{symbol_text}
{function_context_text}
PATCH:
{fp}
"""

        child_metadata = {
            "commit": commit_hash,
            "parent_chunk": parent_id,
            "subject": subject,
            "author": author,
            "date": date,
            "file": file_name,
            "old_file": old_file,
            "new_file": new_file,
            "chunk_kind": "patch_file",
            "is_bug": metadata.get("is_bug", False) if metadata else False,
            "class_names": class_names,
            "function_names": function_names,
            "hunk_headers": hunk_headers,
            "has_function_context": bool(function_context),
        }

        cur.execute(
            """
            INSERT INTO chunks
            (id, project, source_type, source_id, parent_id, chunk_index, chunk_text, metadata, embedding)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, NULL)
            ON CONFLICT (id) DO UPDATE
            SET chunk_text = EXCLUDED.chunk_text,
                metadata = EXCLUDED.metadata,
                parent_id = EXCLUDED.parent_id,
                embedding = NULL,
                updated_at = now();
            """,
            (
                child_id,
                "pandas",
                "git_patch_file",
                commit_hash,
                parent_id,
                patch_index,
                child_text,
                Jsonb(child_metadata),
            ),
        )

        inserted += 1

    if inserted % 100 == 0 and inserted > 0:
        conn.commit()
        print(f"Inserted/updated {inserted} patch child chunks...")

conn.commit()
conn.close()

print(
    f"Done. Inserted/updated {inserted} "
    f"function-context patch child chunks from {len(parents)} parent commits."
)