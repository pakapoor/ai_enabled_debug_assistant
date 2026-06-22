import os
import yaml
from pathlib import Path


import datetime
import random

def generate_bug_yaml(bug_dir: Path, bug_id: int) -> None:
    """
    Create a synthetic bug YAML file with randomized fields.  Each bug
    receives a unique ID and a mixture of file names, functions, symptoms,
    root causes, fixes, and tags pulled from predefined pools to ensure
    variety.  This helps the vector search differentiate between entries.

    Args:
        bug_dir: Directory where the YAML file should be saved.
        bug_id: Numeric portion of the bug ID (e.g., 5 for BUG-005).
    """
    bug_code = f"BUG-{bug_id:03d}"

    # Pools of example values for random bug generation.  These lists are
    # intentionally varied to emulate different categories of debugging
    # issues (crashes, hangs, assertions, etc.).  You can expand or
    # customize these as needed to better represent your domain.
    file_names = [
        "scheduler.cpp",
        "dispatch.cpp",
        "elaborate.cpp",
        "parser.cpp",
        "license_manager.cpp",
    ]
    functions = [
        "process_events",
        "dispatch_ready_events",
        "elaborate_generate_block",
        "cleanup_event_queue",
        "build_nets",
    ]
    symptoms = [
        "Simulator crashes with SIGSEGV during nightly regression.",
        "Regression test hangs indefinitely due to deadlock.",
        "Assertion failure during elaboration of nested generate blocks.",
        "Segmentation fault when parsing nested if statements.",
        "Hang in event dispatcher after zero-delay loop.",
        "Null pointer dereference triggers a crash in the parser.",
        "Memory leak causes progressive slowdown across runs.",
        "Deadlock occurs when two threads acquire locks in reverse order.",
        "Out-of-bounds array access results in corrupted data.",
        "Infinite recursion causes stack overflow during elaboration.",
    ]
    root_causes = [
        "Missing null pointer check before dereference.",
        "Stale pointer reused after queue cleanup.",
        "Missing parent scope assignment when nested block was cloned.",
        "Dispatcher did not yield when queue was continuously refilled.",
        "Use-after-free on event object during cleanup.",
        "Incorrect boundary check leads to buffer overflow.",
        "Recursive function lacks base case, causing infinite recursion.",
        "Mutex lock not released on error path, causing deadlock.",
        "Uninitialized variable used in computation.",
        "Pointer arithmetic error miscalculates data offset.",
    ]
    fix_summaries = [
        "Added null check and early return.",
        "Added ownership check and cleared stale pointer after cleanup.",
        "Propagated parent scope and added regression coverage.",
        "Added iteration budget and yield point to avoid starvation.",
        "Reverted unsafe assumption and added explicit ownership state.",
        "Added proper boundary checks and updated tests.",
        "Implemented base case and limited recursion depth.",
        "Ensured lock release on error paths.",
        "Initialized variables and added sanity assertions.",
        "Fixed pointer arithmetic and adjusted offset calculations.",
    ]
    tags_pool = [
        "crash",
        "hang",
        "scheduler",
        "parser",
        "deadlock",
        "assertion",
        "segfault",
        "null-pointer",
        "stale-pointer",
        "regression",
        "ownership",
        "memory-leak",
        "overrun",
        "race-condition",
        "recursion",
    ]

    # Randomly select attributes for this bug
    selected_file = random.choice(file_names)
    selected_function = random.choice(functions)
    selected_symptom = random.choice(symptoms)
    selected_root = random.choice(root_causes)
    selected_fix = random.choice(fix_summaries)
    # Randomly choose 2–4 tags from the pool without repetition
    selected_tags = random.sample(tags_pool, k=random.randint(2, 4))

    # Use the first sentence of the symptom (without the trailing period) as the title
    title_sentence = selected_symptom.split(".")[0].strip()

    bug_data = {
        "id": bug_code,
        "title": title_sentence,
        "symptom": selected_symptom,
        "file": selected_file,
        "function": selected_function,
        "root_cause": selected_root,
        "fix_summary": selected_fix,
        "tags": selected_tags,
    }
    bug_dir.mkdir(parents=True, exist_ok=True)
    out_path = bug_dir / f"{bug_code}.yaml"
    with out_path.open("w", encoding="utf-8") as f:
        yaml.safe_dump(bug_data, f, sort_keys=False)


def main():
    # Determine the path to the `bugs` directory relative to this script.
    repo_root = Path(__file__).resolve().parent
    bug_dir = repo_root / "bugs"

    # Generate synthetic bugs from BUG-005 to BUG-100 inclusive
    for bug_id in range(5, 101):
        generate_bug_yaml(bug_dir, bug_id)
    print(f"Generated synthetic bugs in {bug_dir}")


if __name__ == "__main__":
    start = datetime.datetime.now()
    print(f"Start time: {start.strftime('%Y-%m-%d %H:%M:%S')}")
    main()
    end = datetime.datetime.now()
    print(f"End time: {end.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Elapsed: {end - start}")
