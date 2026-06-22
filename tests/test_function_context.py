import ast
from pathlib import Path


REPO = Path("repos/pandas")


def get_function_source(file_path, function_name):
    full_path = REPO / file_path

    source = full_path.read_text(
        encoding="utf-8",
        errors="ignore",
    )

    tree = ast.parse(source)

    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            if node.name == function_name:

                start = node.lineno
                end = node.end_lineno

                lines = source.splitlines()

                return "\n".join(lines[start - 1:end])

    return None


if __name__ == "__main__":

    file_name = "pandas/core/frame.py"
    function_name = "duplicated"

    function_body = get_function_source(
        file_name,
        function_name,
    )

    if function_body:
        print("=" * 80)
        print(f"FILE: {file_name}")
        print(f"FUNCTION: {function_name}")
        print("=" * 80)
        print(function_body)
    else:
        print("Function not found")