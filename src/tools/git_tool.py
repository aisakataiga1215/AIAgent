import asyncio
from pathlib import Path
from src.tools.base import BaseTool, ToolResult
from src.observability.logger import get_logger

logger = get_logger(__name__)


class GitDiffTool(BaseTool):
    name = "git_diff"
    description = "Get the git diff for a repository. Shows changes between commits, branches, or working tree."
    parameters = {
        "type": "object",
        "properties": {
            "target": {"type": "string", "description": "Branch, commit, or PR reference to diff against. Defaults to HEAD~1."},
            "path": {"type": "string", "description": "Optional file/directory path to filter diff"},
        },
        "required": [],
    }

    def __init__(self, workspace: str = ".") -> None:
        self.workspace = Path(workspace).resolve()

    async def _run(self, *args: str) -> tuple[int, str, str]:
        cmd = ["git", "-C", str(self.workspace), *args]
        proc = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, stderr = await proc.communicate()
        return proc.returncode or 0, stdout.decode("utf-8", errors="replace"), stderr.decode("utf-8", errors="replace")

    async def execute(self, target: str = "HEAD~1", path: str | None = None) -> ToolResult:
        args = ["diff", "--unified=5", target]
        if path:
            args.extend(["--", path])
        rc, stdout, stderr = await self._run(*args)
        if rc != 0:
            return ToolResult(success=False, content=stderr)
        if not stdout.strip():
            return ToolResult(success=True, content="No changes detected.", metadata={"changed_files": 0})
        changed = [l for l in stdout.splitlines() if l.startswith("diff --git")]
        return ToolResult(
            success=True,
            content=stdout[:15000],
            metadata={"changed_files": len(changed), "truncated": len(stdout) > 15000},
        )


class GitLogTool(BaseTool):
    name = "git_log"
    description = "Get recent git commit history."
    parameters = {
        "type": "object",
        "properties": {
            "count": {"type": "integer", "description": "Number of recent commits to show. Default 10."},
        },
        "required": [],
    }

    def __init__(self, workspace: str = ".") -> None:
        self.workspace = Path(workspace).resolve()

    async def _run(self, *args: str) -> tuple[int, str, str]:
        cmd = ["git", "-C", str(self.workspace), *args]
        proc = await asyncio.create_subprocess_exec(*cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE)
        stdout, stderr = await proc.communicate()
        return proc.returncode or 0, stdout.decode("utf-8", errors="replace"), stderr.decode("utf-8", errors="replace")

    async def execute(self, count: int = 10) -> ToolResult:
        rc, stdout, stderr = await self._run("log", f"-{count}", "--oneline", "--decorate")
        if rc != 0:
            return ToolResult(success=False, content=stderr)
        return ToolResult(success=True, content=stdout.strip(), metadata={"count": count})


class GitStatusTool(BaseTool):
    name = "git_status"
    description = "Show the working tree status of a git repository."
    parameters = {"type": "object", "properties": {}, "required": []}

    def __init__(self, workspace: str = ".") -> None:
        self.workspace = Path(workspace).resolve()

    async def _run(self, *args: str) -> tuple[int, str, str]:
        cmd = ["git", "-C", str(self.workspace), *args]
        proc = await asyncio.create_subprocess_exec(*cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE)
        stdout, stderr = await proc.communicate()
        return proc.returncode or 0, stdout.decode("utf-8", errors="replace"), stderr.decode("utf-8", errors="replace")

    async def execute(self) -> ToolResult:
        rc, stdout, stderr = await self._run("status", "--short")
        if rc != 0:
            return ToolResult(success=False, content=stderr)
        if not stdout.strip():
            return ToolResult(success=True, content="Working tree clean.")
        return ToolResult(success=True, content=stdout.strip())
