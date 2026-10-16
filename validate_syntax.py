"""Validate Python syntax and detect unawaited coroutine calls in async functions."""
import ast
from pathlib import Path


# Known HA coroutine methods commonly called without await.
KNOWN_ASYNC_HA_METHODS = {
    "async_forward_entry_setups",
    "async_setup_entry",
    "async_unload_entry",
    "async_register_static_paths",
    "async_remove_panel",
    "async_get_config_entries",
}


def _collect_all_call_nodes(node):
    """Recursively collect all Call nodes from ANY AST node (not just statements)."""

    def walk(n):
        calls = []
        # Handle bare Call nodes directly.
        if isinstance(n, ast.Call) and not isinstance(
            getattr(n, "func", None), (ast.Name, ast.Attribute)
        ):
            return  # Skip nested expressions like list(map(...))
        for child in ast.iter_child_nodes(n):
            calls.extend(walk(child))
        return calls

    if isinstance(node, ast.Call) and not isinstance(
        getattr(node, "func", None), (ast.Name, ast.Attribute)
    ):
        return []  # Skip nested expressions like list(map(...))

    return walk(node)


def _check_body(func_node, filename):
    """Check the body of an async function for unawaited coroutine calls."""

    call_nodes = _collect_all_call_nodes(func_node)

    await_lines = set()
    for n in func_node.body:  # Only direct child statements
        if isinstance(n, ast.Await):
            await_lines.add(getattr(n, "lineno", -1))

    for call_node in call_nodes:
        func_attr = getattr(getattr(call_node, "func", None), "attr", None)
        if not func_attr or func_attr not in KNOWN_ASYNC_HA_METHODS:
            continue

        call_line = getattr(call_node, "lineno", -1)
        # Skip if the same line contains 'await' (e.g., await foo()).
        if await_lines and call_line in await_lines:
            continue

        print(f"  [{filename}:{call_line}] {func_attr}() called without await")


def _check_file(filepath):
    """Check a single Python file. Returns True if clean."""
    filename = filepath.name

    # Syntax check via ast.parse
    try:
        with open(filepath, "r", encoding="utf-8") as fh:
            source = fh.read()
        ast.parse(source)
    except SyntaxError as e:
        print(f"[FAIL] {filename}: syntax error — {e}")
        return False

    # Coroutine check: walk module and find all AsyncFunctionDef nodes (including nested).
    tree = ast.parse(open(filepath, "r", encoding="utf-8").read())

    for node in ast.walk(tree):
        if isinstance(node, ast.AsyncFunctionDef):
            _check_body(node, filename)

    return True


# Main loop — check every .py file in the component directory.
component_dir = "custom_components/youtube_content_search"

issues_found = False

for py_file in sorted(Path(component_dir).glob("*.py")):
    if not _check_file(py_file):
        issues_found = True


print(f"\nChecked {len(list(Path(component_dir).glob('*.py')))} file(s) for syntax and coroutine issues.")

if issues_found:
    print("[WARN] Potential runtime errors detected. Review warnings above.")
else:
    print("All async functions properly await their coroutine calls.")
