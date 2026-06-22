import ast
from pathlib import Path


REPO = Path("repos/pandas")


def find_enclosing_symbols(file_path, target_line):
    full_path = REPO / file_path

    source = full_path.read_text(encoding="utf-8", errors="ignore")
    tree = ast.parse(source)

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

    return {
        "file": file_path,
        "line": target_line,
        "class": class_name,
        "function": function_name,
        "matches": matches,
    }


if __name__ == "__main__":
    result = find_enclosing_symbols("pandas/core/frame.py", 4400)

    print("File:", result["file"])
    print("Line:", result["line"])
    print("Class:", result["class"])
    print("Function:", result["function"])

    print("\nAll matches:")
    for kind, name, start, end, parents in result["matches"]:
        print(f"{kind}: {name} lines {start}-{end}, parents={parents}")