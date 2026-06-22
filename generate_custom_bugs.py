#!/usr/bin/env python3
"""
Generate synthetic bug YAML files with specific file names and bug types.
=======================================================================

This script creates a series of bug reports in YAML format for testing
your debugging assistant.  Each bug is assigned a unique ID and
randomly combines one of the specified file names (e.g. a.cpp, b.cpp,
c.pp, xcelium) with one of several bug types (crash, SIGSEGV, SIGABORT,
hang) and randomly selected root causes and fixes.  Additional tags
include the bug type and file name so they are searchable.

Usage:
    python3 generate_custom_bugs.py

This will generate 100 bugs (BUG-001 to BUG-100) in the `bugs` directory
relative to this script.  You can adjust the number of bugs generated
by modifying the `NUM_BUGS` constant below.

Note: Running this script multiple times will overwrite existing files
with the same names.
"""
import datetime
import random
from pathlib import Path
import yaml


NUM_BUGS = 100  # Change this value if you want more or fewer bugs

FILE_NAMES = [
    "a.cpp",
    "b.cpp",
    "c.pp",  # intentionally left as provided (assuming it might be a typo)
    "xcelium",  # representing the executable name
]

BUG_TYPES = [
    "crash",
    "SIGSEGV",
    "SIGABORT",
    "hang",
]

ROOT_CAUSES = [
    "Null pointer dereference",
    "Out of memory error",
    "Deadlock due to mutex ordering",
    "Stack overflow caused by infinite recursion",
    "Uncaught exception in library call",
    "Buffer overflow due to unchecked bounds",
    "Race condition on shared resource",
    "Use-after-free bug in memory allocator",
    "Corrupted state due to uninitialized variables",
    "Invalid free on dangling pointer",
]

FIX_SUMMARIES = [
    "Added null check and handled error gracefully",
    "Implemented memory cleanup and error handling",
    "Reordered mutex acquisition to prevent deadlock",
    "Added recursion limit and fixed base case",
    "Added try/catch around risky operation",
    "Checked array bounds before access",
    "Added atomic operations to synchronize threads",
    "Delayed freeing memory until after use",
    "Initialized variables before usage",
    "Removed double-free and added ownership checks",
]


def generate_bug_yaml(bug_id: int, out_dir: Path) -> None:
    """Generate a single bug YAML file with random data.

    Args:
        bug_id: numeric identifier for the bug (1-based).
        out_dir: directory to write the YAML file to.
    """
    bug_code = f"BUG-{bug_id:03d}"
    file_name = random.choice(FILE_NAMES)
    bug_type = random.choice(BUG_TYPES)
    symptom = f"{bug_type} detected in {file_name} during test run."
    root_cause = random.choice(ROOT_CAUSES)
    fix = random.choice(FIX_SUMMARIES)
    # Tags include the bug type and file name for better searchability
    tags = [bug_type.lower(), file_name.replace('.', '-').lower()] + random.sample(BUG_TYPES, k=1)
    data = {
        "id": bug_code,
        "title": f"{bug_type} in {file_name}",
        "symptom": symptom,
        "file": file_name,
        "function": "main",  # generic placeholder function name
        "root_cause": root_cause,
        "fix_summary": fix,
        "tags": tags,
    }
    out_dir.mkdir(parents=True, exist_ok=True)
    file_path = out_dir / f"{bug_code}.yaml"
    with file_path.open("w", encoding="utf-8") as fh:
        yaml.safe_dump(data, fh, sort_keys=False)


def main():
    repo_root = Path(__file__).resolve().parent
    bug_dir = repo_root / "bugs"
    for bug_id in range(1, NUM_BUGS + 1):
        generate_bug_yaml(bug_id, bug_dir)
    print(f"Generated {NUM_BUGS} synthetic bugs in {bug_dir}")


if __name__ == "__main__":
    start = datetime.datetime.now()
    print(f"Start time: {start.strftime('%Y-%m-%d %H:%M:%S')}")
    main()
    end = datetime.datetime.now()
    print(f"End time: {end.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Elapsed: {end - start}")
