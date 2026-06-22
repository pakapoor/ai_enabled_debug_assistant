import datetime
import json

from llm_client import ask_llm


EXTRACTION_PROMPT = """
You are a query parser for an engineering debugging assistant.

Extract structured fields from the user's debugging query and return ONLY valid JSON.
No explanation, no markdown, no code blocks. Just the raw JSON object.

CRITICAL RULES:
- Extract keywords ONLY from the actual query text below. Never copy words from this instruction or from any example.
- Correct obvious spelling mistakes in technical terms (e.g. "datafrme" -> "DataFrame", "gruopby" -> "groupby").
- Do NOT invent a file name. Only set "file" if an actual file name with an extension (like .py, .cpp, .pyx) appears in the query.
- "signal" is the type of problem described. If the query contains words like "crash", "hang", "assertion", "segfault", "SIGSEGV", "SIGABORT", "timeout", "error", "bug", "memory leak", "deadlock" -- set "signal" to that word (normalized to lowercase, e.g. "hang", "crash", "error").
- confidence = "high" if the query contains AT LEAST TWO of the following: a signal word (not negated), a file name, a specific function or method name, or specific technical keywords describing the problem. A single vague word like "crash", "hang", "error", or "bug" alone with no other detail is NOT sufficient — set confidence to "low" and ask a focused follow-up question.
- confidence = "low" if the query has fewer than two of the above (e.g. "it broke" or "it crashed" alone with no file, function, or technical detail).
- If confidence is "low", you MUST provide a "follow_up" question. If confidence is "high", "follow_up" must be null.

This is the JSON shape to follow (do not copy these values, they are just the format):
{"signal": null, "file": null, "function": null, "line": null, "stack_trace": false, "keywords": [], "negations": [], "confidence": "high", "follow_up": null}
""".strip()


def extract_query(raw_query: str) -> dict:
    prompt = EXTRACTION_PROMPT + f"\n\nQUERY TO PARSE: {raw_query}\n\nJSON output:"

    raw = ask_llm(prompt).strip()

    if raw.startswith("```"):
        lines = raw.splitlines()
        lines = [l for l in lines if not l.startswith("```")]
        raw = "\n".join(lines).strip()

    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return {
            "signal": None,
            "file": None,
            "function": None,
            "line": None,
            "stack_trace": False,
            "keywords": raw_query.split(),
            "negations": [],
            "confidence": "low",
            "follow_up": "Can you provide more details such as a file name, function, or error signal?"
        }