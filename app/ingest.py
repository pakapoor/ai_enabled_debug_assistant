import yaml
from pathlib import Path

for f in Path("/data/bugs").glob("*.yaml"):
    bug = yaml.safe_load(open(f))

    text = f"""
BUG ID: {bug['id']}
TITLE: {bug['title']}
SYMPTOM: {bug['symptom']}
FILE: {bug['file']}
FUNCTION: {bug['function']}
ROOT CAUSE: {bug['root_cause']}
FIX: {bug['fix_summary']}
TAGS: {','.join(bug['tags'])}
"""

    print("=" * 80)
    print(text)
