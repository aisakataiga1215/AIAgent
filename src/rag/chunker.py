import ast
from pathlib import Path
from dataclasses import dataclass, field


@dataclass
class Chunk:
    content: str
    file_path: str
    start_line: int
    end_line: int
    chunk_type: str  # function | class | module | method
    name: str = ""
    metadata: dict = field(default_factory=dict)


def chunk_python_file(file_path: Path, max_chunk_lines: int = 200) -> list[Chunk]:
    """Split a Python file into AST-aware chunks (functions, classes, module-level code)."""
    source = file_path.read_text(encoding="utf-8")
    lines = source.splitlines()
    chunks: list[Chunk] = []

    try:
        tree = ast.parse(source)
    except SyntaxError:
        return [Chunk(
            content=source[:5000],
            file_path=str(file_path),
            start_line=1,
            end_line=len(lines),
            chunk_type="module",
        )]

    # Extract top-level functions and classes
    covered: set[int] = set()

    for node in ast.iter_child_nodes(tree):
        if isinstance(node, ast.FunctionDef):
            chunk = _extract_function_chunk(node, lines, file_path)
            chunks.append(chunk)
            for ln in range(node.lineno, node.end_lineno + 1):
                covered.add(ln)
        elif isinstance(node, ast.ClassDef):
            chunk = _extract_class_chunk(node, lines, file_path)
            chunks.append(chunk)
            for ln in range(node.lineno, node.end_lineno + 1):
                covered.add(ln)

    # Catch module-level code not covered by functions/classes
    uncovered = [
        (i + 1, line)
        for i, line in enumerate(lines)
        if (i + 1) not in covered and line.strip() and not line.strip().startswith("#")
    ]
    if uncovered:
        # Group into chunks
        for i in range(0, len(uncovered), max_chunk_lines):
            group = uncovered[i:i + max_chunk_lines]
            start = group[0][0]
            end = group[-1][0]
            content = "\n".join(l for _, l in group)
            chunks.append(Chunk(
                content=content,
                file_path=str(file_path),
                start_line=start,
                end_line=end,
                chunk_type="module",
            ))

    return chunks


def _extract_function_chunk(node: ast.FunctionDef, lines: list[str], file_path: Path) -> Chunk:
    end = getattr(node, "end_lineno", node.lineno)
    content = "\n".join(lines[node.lineno - 1:end])
    return Chunk(
        content=content,
        file_path=str(file_path),
        start_line=node.lineno,
        end_line=end,
        chunk_type="function",
        name=node.name,
        metadata={"decorators": [d.id if isinstance(d, ast.Name) else "..." for d in node.decorator_list]},
    )


def _extract_class_chunk(node: ast.ClassDef, lines: list[str], file_path: Path) -> Chunk:
    end = getattr(node, "end_lineno", node.lineno)
    content = "\n".join(lines[node.lineno - 1:end])
    methods = [n.name for n in ast.walk(node) if isinstance(n, ast.FunctionDef) and n is not node]
    return Chunk(
        content=content,
        file_path=str(file_path),
        start_line=node.lineno,
        end_line=end,
        chunk_type="class",
        name=node.name,
        metadata={"methods": methods},
    )


def chunk_text_file(file_path: Path, chunk_size: int = 1000, chunk_overlap: int = 200) -> list[Chunk]:
    """Split a generic text file into overlapping chunks."""
    text = file_path.read_text(encoding="utf-8", errors="replace")
    lines = text.splitlines()
    chunks: list[Chunk] = []

    if len(lines) <= chunk_size:
        chunks.append(Chunk(
            content=text,
            file_path=str(file_path),
            start_line=1,
            end_line=len(lines),
            chunk_type="file",
        ))
        return chunks

    i = 0
    while i < len(lines):
        chunk_lines = lines[i:i + chunk_size]
        content = "\n".join(chunk_lines)
        chunks.append(Chunk(
            content=content,
            file_path=str(file_path),
            start_line=i + 1,
            end_line=min(i + chunk_size, len(lines)),
            chunk_type="file",
        ))
        i += chunk_size - chunk_overlap
        if i >= len(lines):
            break

    return chunks


def chunk_file(file_path: Path, max_chunk_lines: int = 200) -> list[Chunk]:
    """Auto-detect file type and chunk accordingly."""
    suffix = file_path.suffix.lower()
    if suffix == ".py":
        return chunk_python_file(file_path, max_chunk_lines)
    elif suffix in (".md", ".txt", ".rst", ".yaml", ".yml", ".toml", ".json"):
        return chunk_text_file(file_path)
    elif suffix in (".ts", ".tsx", ".js", ".jsx", ".go", ".rs", ".java", ".c", ".cpp", ".h"):
        # For non-Python code, use line-based chunking
        return chunk_text_file(file_path, chunk_size=150, chunk_overlap=30)
    else:
        return []  # Skip binary/unrecognized files
