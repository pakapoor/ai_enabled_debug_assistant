import datetime


def build_prompt(query, results):
    sections = []

    sections.append(
        """
You are an engineering debugging assistant.

RULES:
- Use ONLY the context provided below.
- For each relevant fix found, state: what the bug was, which file was changed, and what the fix was.
- Quote key changed lines from any patch shown in the context.
- At the end, list commits referenced as: [commit: <hash>] <description>
- If no relevant fix exists in the context, say "I don't know based on the available context."
""".strip()
    )

    sections.append("")
    sections.append(f"USER QUESTION:\n{query}")

    for i, r in enumerate(results[:5], start=1):
        commit = r.get("source_id", "unknown")
        sections.append("")
        sections.append(f"CONTEXT {i} [commit: {commit}]")
        sections.append("-" * 40)
        sections.append(r.get("text", ""))

    return "\n".join(sections)

if __name__ == "__main__":
    start = datetime.datetime.now()
    print(f"Start time: {start.strftime('%Y-%m-%d %H:%M:%S')}")
    query = "DataFrame duplicated loses index"

    fake_results = [
        {
            "text": "BUG: DataFrame.duplicated() loses index when DataFrame has no columns"
        }
    ]

    prompt = build_prompt(query, fake_results)
    print(prompt)
    end = datetime.datetime.now()
    print(f"End time: {end.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Elapsed: {end - start}")