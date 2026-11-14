import ast
import json
import sys
from pathlib import Path

MAX_LINES = 60  # max lines per chunk
OVERLAP = 10    # overlap between windows when a unit is too long


def split_long(lines, start, end):
    """Split lines[start:end] (0-based, end exclusive) into windows of MAX_LINES."""
    if end - start <= MAX_LINES:
        return [(start, end)]
    windows = []
    s = start
    while s < end:
        e = min(s + MAX_LINES, end)
        windows.append((s, e))
        if e == end:
            break
        s = e - OVERLAP
    return windows


def node_start(node):
    """Start line including decorators (0-based)."""
    lines = [node.lineno] + [d.lineno for d in getattr(node, "decorator_list", [])]
    return min(lines) - 1


def python_units(source, lines):
    """Return list of (name, kind, start, end) units for a Python file."""
    tree = ast.parse(source)
    units = []
    module_lines = set(range(len(lines)))

    for node in tree.body:
        start, end = node_start(node), node.end_lineno
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            units.append((node.name, "function", start, end))
            module_lines -= set(range(start, end))
        elif isinstance(node, ast.ClassDef):
            methods = [n for n in node.body
                       if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))]
            if not methods:
                units.append((node.name, "class", start, end))
            else:
                # class header (signature, docstring, class attributes)
                header_end = node_start(methods[0])
                units.append((node.name, "class_header", start, header_end))
                for m in methods:
                    units.append((f"{node.name}.{m.name}", "method",
                                  node_start(m), m.end_lineno))
            module_lines -= set(range(start, end))

    # remaining module-level code (imports, constants, ...) grouped into
    # contiguous blocks, so it never overlaps with functions/classes
    rest = sorted(i for i in module_lines if lines[i].strip())
    blocks = []
    for i in rest:
        if blocks and all(not lines[j].strip() for j in range(blocks[-1][1], i)):
            blocks[-1][1] = i + 1
        else:
            blocks.append([i, i + 1])
    module_units = [("<module>", "module", s, e) for s, e in blocks]
    return sorted(module_units + units, key=lambda u: u[2])


def chunk_file(path, repo_root):
    source = path.read_text(encoding="utf-8")
    lines = source.splitlines()
    rel = path.relative_to(repo_root).as_posix()

    if path.suffix == ".py":
        try:
            units = python_units(source, lines)
        except SyntaxError:
            units = [("<file>", "text", 0, len(lines))]
    else:
        units = [("<file>", "text", 0, len(lines))]

    # merge consecutive small units of the same parent (class or module level)
    # until the chunk would exceed MAX_LINES
    merged = []
    for name, kind, start, end in units:
        parent = name.split(".")[0] if kind in ("method", "class_header") else "<top>"
        if merged:
            p_names, p_parent, p_start, p_end = merged[-1]
            if p_parent == parent and end - p_start <= MAX_LINES:
                merged[-1] = (p_names + [name], parent, p_start, end)
                continue
        merged.append(([name], parent, start, end))

    chunks = []
    for names, parent, start, end in merged:
        name = ", ".join(names)
        kind = "class" if parent != "<top>" else "top_level"
        for s, e in split_long(lines, start, end):
            text = "\n".join(lines[s:e])
            if not text.strip():
                continue
            chunks.append({
                "id": f"{rel}:{s + 1}-{e}",
                "file": rel,
                "class": parent if parent != "<top>" else None,
                "symbols": names,
                "type": kind,
                "start_line": s + 1,
                "end_line": e,
                "content": text,
            })
    return chunks


def main():
    repo = Path(sys.argv[1] if len(sys.argv) > 1 else "AI4SE_Playground")
    out = Path(sys.argv[2] if len(sys.argv) > 2 else "chunks.json")

    chunks = []
    for path in sorted(repo.rglob("*")):
        if path.is_file() and ".git" not in path.parts and path.suffix == ".py":
            chunks.extend(chunk_file(path, repo))

    out.write_text(json.dumps(chunks, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"{len(chunks)} chunks written to {out}")


if __name__ == "__main__":
    main()
