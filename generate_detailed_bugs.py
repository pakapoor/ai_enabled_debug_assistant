#!/usr/bin/env python3
"""
Generate richly detailed synthetic bug reports for testing.
========================================================

This script produces a set of YAML files representing bug reports with
varied and realistic details.  Each bug entry includes a random Jira
ID, file name and nested folder path, bug type (e.g. crash, SIGSEGV,
SIGABORT, hang), line number, stack trace, function names, and tags
reflecting synonyms and context.  The purpose is to create a more
diverse dataset that can challenge retrieval and semantic search
systems.

Key features:
  * Random Jira ID (e.g. JIRA-1234).
  * Random folder path built from specified directory names (e.g. src/curl/verilog).
  * Random file name chosen from a list (a.cpp, b.cpp, c.pp, xcelium).
  * Random bug type selected from [crash, SIGSEGV, SIGABORT, hang].
  * Random line number in the file.
  * Random stack trace with multiple frames referencing functions and files.
  * Function name randomly chosen from func1..func10 or optional custom list.
  * Tags include bug type synonyms, file names, folder names, and languages.

The script writes YAML files to a `bugs` directory relative to this
script.  You can adjust the number of bugs by modifying the NUM_BUGS
constant.

Usage:
  python3 generate_detailed_bugs.py

Note: Running this script multiple times will overwrite existing YAML
files with the same IDs.
"""
import datetime
import random
import string
from pathlib import Path
import yaml


# Number of bugs to generate
NUM_BUGS = 100

# Possible file names (executables and source files)
FILE_NAMES = [
    "a.cpp",
    "b.cpp",
    "c.pp",  # as provided
    "xcelium",  # treat as executable name
]

# Possible directory names to form folder paths
TOP_DIRS = ["src", "rtl", "test", "examples", "docs", "tb"]
MID_DIRS = ["curl", "verilog", "vhdl", "utils", "module", "common"]
LANGUAGES = ["c", "cpp", "verilog", "vhdl"]

# Bug types and synonyms mapping (for tags)
BUG_TYPES = ["crash", "SIGSEGV", "SIGABORT", "hang"]
BUG_SYNONYMS = {
    "crash": ["sigsegv", "sigabort", "hang"],
    "SIGSEGV": ["crash", "sigabort", "hang"],
    "SIGABORT": ["sigsegv", "crash", "hang"],
    "hang": ["crash", "sigsegv", "sigabort"],
}

# Function name pool (func1..func10 plus optional real names)
FUNCTION_NAMES = [f"func{i}" for i in range(1, 11)] + [
    "process_events",
    "dispatch_ready_events",
    "elaborate_generate_block",
    "cleanup_event_queue",
    "build_nets",
]

# Root causes and fix summaries (expanded lists for variety)
ROOT_CAUSES = [
    "Null pointer dereference in code path",
    "Out of memory condition triggered during allocation",
    "Deadlock due to improper mutex ordering",
    "Stack overflow from infinite recursion",
    "Unhandled exception thrown by third-party library",
    "Buffer overflow caused by unchecked index",
    "Race condition on shared resource",
    "Use-after-free in custom memory allocator",
    "Corrupted state due to uninitialized variables",
    "Invalid free on dangling pointer",
    "Mismatched new/delete operators",
    "Divide by zero in arithmetic operation",
    "Concurrent modification without synchronization",
    "Memory leak causing progressive slowdown",
]
FIX_SUMMARIES = [
    "Added null pointer check and fallback logic",
    "Implemented memory cleanup and robust error handling",
    "Reordered mutex acquisition to prevent deadlock",
    "Introduced recursion limit and base case",
    "Wrapped risky call in try/except with recovery",
    "Added proper boundary check before accessing buffer",
    "Replaced unsynchronized access with atomic operations",
    "Deferred freeing memory until safe point",
    "Initialized variables prior to usage",
    "Removed double free and enforced ownership policy",
    "Used consistent allocator/deallocator pair",
    "Added zero division guard and default value",
    "Introduced thread-safe data structure",
    "Implemented leak detection and fixed allocation path",
]


def random_jira_id() -> str:
    """Generate a random JIRA-like ID (e.g. JIRA-AB12)."""
    prefix = "JIRA-"
    suffix = ''.join(random.choices(string.ascii_uppercase + string.digits, k=4))
    return prefix + suffix


def random_folder_path() -> str:
    """Generate a random nested folder path using TOP_DIRS and MID_DIRS."""
    top = random.choice(TOP_DIRS)
    mid = random.choice(MID_DIRS)
    # Randomly include a third level with 50% chance
    if random.random() < 0.5:
        third_level = random.choice(MID_DIRS + LANGUAGES)
        return f"{top}/{mid}/{third_level}"
    return f"{top}/{mid}"


def random_stack_trace(file_path: str, func: str, line: int) -> str:
    """Create a synthetic stack trace string with three frames."""
    frames = []
    # First frame is the crash location
    frames.append(f"#0  {func} at {file_path}:{line}")
    # Additional frames with other functions and files
    for i in range(1, 3):
        frame_func = random.choice(FUNCTION_NAMES)
        frame_file = random.choice(FILE_NAMES)
        frame_line = random.randint(10, 2000)
        frames.append(f"#{i}  {frame_func} at {frame_file}:{frame_line}")
    return '\n'.join(frames)


def generate_bug_yaml(bug_id: int, out_dir: Path) -> None:
    """Create a single bug YAML with detailed random data."""
    bug_code = f"BUG-{bug_id:03d}"
    jira_id = random_jira_id()
    # Build folder and file path
    folder = random_folder_path()
    file_name = random.choice(FILE_NAMES)
    file_path = f"{folder}/{file_name}"
    # Pick bug type and synonyms for tags
    bug_type = random.choice(BUG_TYPES)
    synonyms = BUG_SYNONYMS.get(bug_type, [])
    # Random function name and line number
    func_name = random.choice(FUNCTION_NAMES)
    line_number = random.randint(10, 2000)
    # Stack trace
    stack = random_stack_trace(file_path, func_name, line_number)
    # Root cause and fix
    root_cause = random.choice(ROOT_CAUSES)
    fix = random.choice(FIX_SUMMARIES)
    # Choose a language associated with the mid-level directory or randomly from LANGUAGES
    language = random.choice(LANGUAGES)
    # Compose the symptom text
    symptom = (
        f"{bug_type} detected in file {file_path} at line {line_number} "
        f"within function {func_name}."
    )
    # Compose tags: lower-case bug type, synonyms, file name base, folder parts, language
    base_file = file_name.split('.')[0].lower()
    folder_parts = [part.lower().replace('.', '-') for part in folder.split('/')]
    tags = [bug_type.lower(), base_file] + [syn.lower() for syn in synonyms] + folder_parts + [language.lower()]
    # Deduplicate tags
    tags = list(dict.fromkeys(tags))
    # Assemble the YAML data
    data = {
        "id": bug_code,
        "jira_id": jira_id,
        "title": f"{bug_type} in {file_name} (ID: {jira_id})",
        "symptom": symptom,
        "file": file_name,
        "folder": folder,
        "function": func_name,
        "line_number": line_number,
        "stack_trace": stack,
        "root_cause": root_cause,
        "fix_summary": fix,
        "language": language,
        "tags": tags,
    }
    out_dir.mkdir(parents=True, exist_ok=True)
    file_path_out = out_dir / f"{bug_code}.yaml"
    with file_path_out.open("w", encoding="utf-8") as fh:
        yaml.safe_dump(data, fh, sort_keys=False)


def main():
    repo_root = Path(__file__).resolve().parent
    bug_dir = repo_root / "bugs"
    for i in range(1, NUM_BUGS + 1):
        generate_bug_yaml(i, bug_dir)
    print(f"Generated {NUM_BUGS} detailed bug reports in {bug_dir}")


if __name__ == "__main__":
    start = datetime.datetime.now()
    print(f"Start time: {start.strftime('%Y-%m-%d %H:%M:%S')}")
    main()
    end = datetime.datetime.now()
    print(f"End time: {end.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Elapsed: {end - start}")
