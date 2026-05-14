import asyncio
import json
from pathlib import Path
from src.tools.base import BaseTool, ToolResult


class TestRunnerTool(BaseTool):
    __test__ = False
    name = "test_runner"
    description = "Run pytest on a target file or directory. Returns test results and coverage data."
    parameters = {
        "type": "object",
        "properties": {
            "target": {"type": "string", "description": "File or directory to run tests against. Use '.' for all."},
            "cov_target": {"type": "string", "description": "Package to measure coverage for (e.g. 'src.agents')."},
            "extra_args": {"type": "string", "description": "Additional pytest arguments (e.g. '-k test_name')."},
        },
        "required": ["target"],
    }

    def __init__(self, workspace: str = ".") -> None:
        self.workspace = Path(workspace).resolve()

    async def _run(self, *args: str) -> tuple[int, str, str]:
        cmd = ["python", "-m", "pytest", *args, "-q", "--tb=short"]
        proc = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            cwd=str(self.workspace),
        )
        stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=120)
        return proc.returncode or 0, stdout.decode("utf-8", errors="replace"), stderr.decode("utf-8", errors="replace")

    async def execute(self, target: str, cov_target: str = "", extra_args: str = "") -> ToolResult:
        args = [target]
        if cov_target:
            args.extend(["--cov", cov_target, "--cov-report", "json", "--cov-report", "term-missing"])
        if extra_args:
            args.extend(extra_args.split())

        try:
            rc, stdout, stderr = await self._run(*args)
        except asyncio.TimeoutError:
            return ToolResult(success=False, content="Tests timed out after 120 seconds.")

        output = stdout
        if stderr:
            output += "\n[stderr]\n" + stderr
        return ToolResult(
            success=rc == 0,
            content=output[:8000] or "(no output)",
            metadata={"exit_code": rc, "truncated": len(output) > 8000},
        )


class CoverageAnalyzerTool(BaseTool):
    name = "coverage_analyzer"
    description = "Read the JSON coverage report to identify uncovered lines and functions."
    parameters = {
        "type": "object",
        "properties": {
            "file_path": {"type": "string", "description": "Specific source file to check coverage for."},
        },
        "required": [],
    }

    def __init__(self, workspace: str = ".") -> None:
        self.workspace = Path(workspace).resolve()

    async def execute(self, file_path: str = "") -> ToolResult:
        cov_json = self.workspace / "coverage.json"
        if not cov_json.exists():
            return ToolResult(success=False, content="No coverage.json found. Run test_runner with --cov first.")

        try:
            data = json.loads(cov_json.read_text())
        except json.JSONDecodeError:
            return ToolResult(success=False, content="Could not parse coverage.json.")

        result_parts = []
        files = data.get("files", {})

        for fpath, fdata in files.items():
            if file_path and file_path not in fpath:
                continue
            summary = fdata.get("summary", {})
            pct = summary.get("percent_covered", 0)
            result_parts.append(f"### {fpath} — {pct:.1f}% covered")
            missing = fdata.get("missing_lines", [])
            if missing:
                result_parts.append(f"  Uncovered lines: {missing[:20]}")
            excluded = fdata.get("excluded_lines", [])
            if excluded:
                result_parts.append(f"  Excluded: {excluded[:10]}")

        if not result_parts:
            return ToolResult(success=True, content="No coverage data found for the specified file." if file_path else "No files in coverage report.")

        return ToolResult(success=True, content="\n".join(result_parts))
