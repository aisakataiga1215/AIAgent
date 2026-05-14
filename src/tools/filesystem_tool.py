from pathlib import Path
from src.tools.base import BaseTool, ToolResult


class FileReadTool(BaseTool):
    name = "read_file"
    description = "Read the contents of a file at the given path."
    parameters = {
        "type": "object",
        "properties": {
            "path": {"type": "string", "description": "Relative or absolute path to the file"},
            "start_line": {"type": "integer", "description": "Optional start line (1-indexed)"},
            "end_line": {"type": "integer", "description": "Optional end line (1-indexed)"},
        },
        "required": ["path"],
    }

    def __init__(self, workspace: str = ".") -> None:
        self.workspace = Path(workspace).resolve()

    async def execute(self, path: str, start_line: int | None = None, end_line: int | None = None) -> ToolResult:
        file_path = self.workspace / path
        if not file_path.exists():
            return ToolResult(success=False, content=f"File not found: {path}")
        try:
            lines = file_path.read_text(encoding="utf-8").splitlines()
            if start_line is not None or end_line is not None:
                start = (start_line or 1) - 1
                end = end_line if end_line is not None else len(lines)
                lines = lines[start:end]
            return ToolResult(
                success=True,
                content="\n".join(lines),
                metadata={"path": str(file_path), "total_lines": len(lines)},
            )
        except UnicodeDecodeError:
            return ToolResult(success=False, content=f"Cannot read binary file: {path}")


class FileListTool(BaseTool):
    name = "list_directory"
    description = "List files and directories in a given path."
    parameters = {
        "type": "object",
        "properties": {
            "path": {"type": "string", "description": "Directory path relative to workspace"},
            "pattern": {"type": "string", "description": "Optional glob pattern to filter"},
        },
        "required": ["path"],
    }

    def __init__(self, workspace: str = ".") -> None:
        self.workspace = Path(workspace).resolve()

    async def execute(self, path: str, pattern: str = "*") -> ToolResult:
        dir_path = self.workspace / path
        if not dir_path.exists():
            return ToolResult(success=False, content=f"Directory not found: {path}")
        entries = sorted(dir_path.glob(pattern))
        result = []
        for e in entries[:200]:
            suffix = "/" if e.is_dir() else ""
            result.append(f"{e.relative_to(self.workspace)}{suffix}")
        if len(entries) > 200:
            result.append(f"... and {len(entries) - 200} more entries")
        return ToolResult(success=True, content="\n".join(result), metadata={"count": len(entries)})


class FileWriteTool(BaseTool):
    name = "write_file"
    description = "Write content to a file, overwriting if it exists."
    parameters = {
        "type": "object",
        "properties": {
            "path": {"type": "string", "description": "File path relative to workspace"},
            "content": {"type": "string", "description": "Content to write"},
        },
        "required": ["path", "content"],
    }

    def __init__(self, workspace: str = ".") -> None:
        self.workspace = Path(workspace).resolve()

    async def execute(self, path: str, content: str) -> ToolResult:
        file_path = self.workspace / path
        file_path.parent.mkdir(parents=True, exist_ok=True)
        file_path.write_text(content, encoding="utf-8")
        return ToolResult(success=True, content=f"Written {len(content)} bytes to {path}", metadata={"bytes": len(content)})
