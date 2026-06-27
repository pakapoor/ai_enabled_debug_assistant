#!/usr/bin/env python3

import json
import time
import urllib.parse
import urllib.request
import tkinter as tk
from tkinter import ttk
from tkinter import scrolledtext
import threading
import requests
from prompt_builder import build_prompt
from query_understanding import extract_query
from llm_client import ask_llm

from config import SEARCH_URL

STRUCTURED_PROMPT_SUFFIX = """

You MUST respond using EXACTLY these three section headers in this exact order.
Do not skip any section. Do not add extra text before TLDR.

TLDR:
<one sentence: what was the bug and how was it fixed>

EXPLANATION:
<2-3 paragraphs: what caused the bug, why it happened, and what the fix does>

CODE:
<the actual diff lines from the patch. Must use diff format with - for removed lines and + for added lines. No markdown fences. Example:
- old line of code
+ new line of code
>
"""


def extract_field(text, label):
    marker = label + ":"
    for line in text.splitlines():
        if line.startswith(marker):
            return line.replace(marker, "", 1).strip()
    return ""


def score_to_confidence(score):
    if score is None:
        return 0
    score = max(0, float(score))
    return int(100 * score / (score + 50))


def score_to_strength(score):
    confidence = score_to_confidence(score)
    if confidence >= 80:
        return "High"
    elif confidence >= 60:
        return "Medium"
    else:
        return "Low"


def format_result(item):
    text = item.get("text", "")

    source = extract_field(text, "SOURCE")
    subject = extract_field(text, "SUBJECT")
    commit = extract_field(text, "COMMIT")
    author = extract_field(text, "AUTHOR")
    date = extract_field(text, "DATE")
    file_name = extract_field(text, "FILE")

    files = ""
    symbol_context = ""
    function_context = ""
    patch = ""

    if "FILES CHANGED:" in text:
        files_part = text.split("FILES CHANGED:", 1)[1]
        if "PATCH:" in files_part:
            files, patch = files_part.split("PATCH:", 1)
            files = files.strip()
            patch = patch.strip()
        else:
            files = files_part.strip()

    elif "FILE:" in text:
        after_file = text.split("FILE:", 1)[1]
        if "SYMBOL CONTEXT:" in after_file:
            file_part, after_symbol = after_file.split("SYMBOL CONTEXT:", 1)
            files = file_part.strip()
            if "FUNCTION CONTEXT:" in after_symbol:
                symbol_context, after_function = after_symbol.split("FUNCTION CONTEXT:", 1)
                symbol_context = symbol_context.strip()
                if "PATCH:" in after_function:
                    function_context, patch = after_function.split("PATCH:", 1)
                    function_context = function_context.strip()
                    patch = patch.strip()
                else:
                    function_context = after_function.strip()
            elif "PATCH:" in after_symbol:
                symbol_context, patch = after_symbol.split("PATCH:", 1)
                symbol_context = symbol_context.strip()
                patch = patch.strip()
            else:
                symbol_context = after_symbol.strip()
        elif "FUNCTION CONTEXT:" in after_file:
            file_part, after_function = after_file.split("FUNCTION CONTEXT:", 1)
            files = file_part.strip()
            if "PATCH:" in after_function:
                function_context, patch = after_function.split("PATCH:", 1)
                function_context = function_context.strip()
                patch = patch.strip()
            else:
                function_context = after_function.strip()
        elif "PATCH:" in after_file:
            files, patch = after_file.split("PATCH:", 1)
            files = files.strip()
            patch = patch.strip()
        else:
            files = file_name

    commit_short = commit[:12] if commit else item.get("id", "")[:12]

    MAX_FUNCTION_LINES = 80
    function_lines = function_context.splitlines()
    if len(function_lines) > MAX_FUNCTION_LINES:
        function_preview = "\n".join(function_lines[:MAX_FUNCTION_LINES])
        function_preview += f"\n\n[Function context truncated. Showing {MAX_FUNCTION_LINES} of {len(function_lines)} lines]"
    else:
        function_preview = function_context

    MAX_PATCH_LINES = 80
    patch_lines = patch.splitlines()
    if len(patch_lines) > MAX_PATCH_LINES:
        patch_preview = "\n".join(patch_lines[:MAX_PATCH_LINES])
        patch_preview += f"\n\n[Patch truncated. Showing {MAX_PATCH_LINES} of {len(patch_lines)} lines]"
    else:
        patch_preview = patch

    output = []
    output.append("=" * 80)
    output.append("BUG / FIX SUMMARY")
    output.append("=" * 80)
    output.append(f"SOURCE: {source}")
    output.append(f"SUBJECT: {subject}")
    output.append(f"COMMIT: {commit_short}")
    output.append(f"AUTHOR: {author}")
    output.append(f"DATE: {date}")
    output.append("")
    output.append("-" * 80)
    output.append("MATCH DETAILS")
    output.append("-" * 80)
    output.append(f"TOKEN RANK: {item.get('token_rank')}")
    output.append(f"VECTOR RANK: {item.get('vector_rank')}")
    score = item.get("score")
    output.append(f"SCORE: {score}")
    output.append(f"MATCH CONFIDENCE: {score_to_confidence(score)}%")
    output.append(f"MATCH STRENGTH: {score_to_strength(score)}")
    output.append("")
    output.append("-" * 80)
    output.append("FILE / FILES")
    output.append("-" * 80)
    output.append(files)

    if symbol_context:
        output.append("")
        output.append("-" * 80)
        output.append("SYMBOL CONTEXT")
        output.append("-" * 80)
        output.append(symbol_context)

    if function_preview:
        output.append("")
        output.append("-" * 80)
        output.append("FUNCTION CONTEXT")
        output.append("-" * 80)
        output.append(function_preview)

    if patch_preview:
        output.append("")
        output.append("-" * 80)
        output.append("PATCH PREVIEW")
        output.append("-" * 80)
        output.append(patch_preview)

    output.append("")
    output.append("=" * 80)
    output.append("")

    return "\n".join(output)


def search():
    q = entry.get().strip()
    if not q:
        return

    btn.config(state=tk.DISABLED)
    ai_btn.config(state=tk.DISABLED)
    results_box.delete("1.0", tk.END)

    try:
        url = f"{SEARCH_URL}?q=" + urllib.parse.quote(q)
        with urllib.request.urlopen(url) as resp:
            data = json.loads(resp.read().decode("utf-8"))

        if not data:
            results_box.insert(tk.END, "No results found for query: " + q)
        else:
            for item in data:
                results_box.insert(tk.END, format_result(item))

    except Exception as e:
        results_box.insert(tk.END, "Error: " + str(e))

    finally:
        btn.config(state=tk.NORMAL)
        ai_btn.config(state=tk.NORMAL)


def ask_ai():
    q = entry.get().strip()
    if not q:
        return

    ai_btn.config(state=tk.DISABLED)
    btn.config(state=tk.DISABLED)
    answer_box.delete("1.0", tk.END)
    answer_box.insert(tk.END, "Understanding your query...")

    def run():
        start_time = time.time()
        try:
            # Step 1: structured extraction + sufficiency check
            parsed = extract_query(q)

            if parsed.get("confidence") == "low":
                follow_up = parsed.get("follow_up", "Can you provide more details?")
                answer_box.delete("1.0", tk.END)
                answer_box.insert(
                    tk.END,
                    f"I need more information:\n\n{follow_up}\n\n"
                    f"(Add more detail to your query above and click Ask AI again.)"
                )

                # Pre-fill the entry box so the user can continue typing
                # right after their original query instead of starting over.
                def prefill():
                    entry.delete(0, tk.END)
                    entry.insert(0, q + " ")
                    entry.icursor(tk.END)
                    entry.focus()

                root.after(0, prefill)
                return

            # Step 2: search
            answer_box.delete("1.0", tk.END)
            answer_box.insert(tk.END, "Searching and generating answer... (this may take 1-3 minutes)")

            resp = requests.get(SEARCH_URL, params={"q": q}, timeout=30)
            resp.raise_for_status()
            results = resp.json()

            negations = [n.lower() for n in parsed.get("negations", [])]
            if negations:
                results = [
                    r for r in results
                    if not any(neg in r.get("text", "").lower() for neg in negations)
                ]

            prompt = build_prompt(q, results) + STRUCTURED_PROMPT_SUFFIX

            answer = ask_llm(prompt, timeout=60)

            # Build citations from search results directly
            citations = "\n\n" + "=" * 40 + "\n"
            citations += "CITATIONS:\n"
            seen = set()
            for r in results:
                commit = r.get("source_id", "unknown")
                if commit in seen:
                    continue
                seen.add(commit)
                text = r.get("text", "")
                subject = ""
                for line in text.splitlines():
                    if line.startswith("SUBJECT:"):
                        subject = line.replace("SUBJECT:", "").strip()
                        break
                citations += f"- [commit: {commit[:12]}] {subject}\n"

            negations = parsed.get("negations", [])
            negation_note = f"\n\n(Excluded per your query: {', '.join(negations)})" if negations else ""

            elapsed = time.time() - start_time
            timing_note = f"\n\nTime taken: {elapsed:.1f} seconds"

            answer_box.delete("1.0", tk.END)
            answer_box.insert(tk.END, answer + negation_note + citations + timing_note)

        except Exception as e:
            answer_box.delete("1.0", tk.END)
            answer_box.insert(tk.END, "Error: " + str(e))

        finally:
            ai_btn.config(state=tk.NORMAL)
            btn.config(state=tk.NORMAL)

    threading.Thread(target=run, daemon=True).start()


# --- UI Layout ---

root = tk.Tk()
root.title("Pandas Debug Assistant")

label = ttk.Label(root, text="Enter search query:")
label.pack(pady=5)

entry = ttk.Entry(root, width=70)
entry.pack(pady=5)

ai_btn = ttk.Button(root, text="Ask AI", command=ask_ai)
ai_btn.pack(pady=5)

ttk.Label(root, text="AI Answer:").pack()

answer_box = scrolledtext.ScrolledText(root, wrap=tk.WORD, width=100, height=12)
answer_box.pack(pady=5, padx=5)

ttk.Separator(root, orient="horizontal").pack(fill="x", padx=10, pady=5)

btn = ttk.Button(root, text="Search (Raw Results)", command=search)
btn.pack(pady=5)

results_box = scrolledtext.ScrolledText(root, wrap=tk.WORD, width=100, height=15)
results_box.pack(pady=5, padx=5)

root.mainloop()