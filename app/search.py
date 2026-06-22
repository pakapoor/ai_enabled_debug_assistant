import yaml
from pathlib import Path

def search(query):
    query = query.lower()

    results = []

    for f in Path("/data/bugs").glob("*.yaml"):
        bug = yaml.safe_load(open(f))

        text = " ".join([
            bug["title"],
            bug["symptom"],
            bug["root_cause"],
            bug["fix_summary"],
            " ".join(bug["tags"])
        ]).lower()

        score = 0

        for word in query.split():
            if word in text:
                score += 1

        results.append((score, bug["id"], bug["title"]))

    results.sort(reverse=True)

    return results
