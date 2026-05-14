import asyncio
from src.tools.base import BaseTool, ToolResult


class ShellTool(BaseTool):
    name = "shell"
    description = "Execute a shell command in a sandboxed environment. Use with caution."
    parameters = {
        "type": "object",
        "properties": {
            "command": {"type": "string", "description": "The shell command to execute"},
            "cwd": {"type": "string", "description": "Working directory for the command"},
        },
        "required": ["command"],
    }

    # Blocklist for dangerous commands
    BLOCKED_PATTERNS = [
        "rm -rf /", "mkfs.", "dd if=", ":(){ :|:& };:", "chmod 777 /",
    ]

    async def execute(self, command: str, cwd: str = ".") -> ToolResult:
        for pattern in self.BLOCKED_PATTERNS:
            if pattern in command:
                return ToolResult(success=False, content=f"Blocked dangerous command pattern: {pattern}")

        try:
            proc = await asyncio.create_subprocess_shell(
                command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=cwd,
            )
            stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=30)
            output = stdout.decode("utf-8", errors="replace")
            if stderr:
                output += "\n[stderr]\n" + stderr.decode("utf-8", errors="replace")
            return ToolResult(
                success=proc.returncode == 0,
                content=output[:5000] or "(no output)",
                metadata={"exit_code": proc.returncode, "truncated": len(output) > 5000},
            )
        except asyncio.TimeoutError:
            return ToolResult(success=False, content="Command timed out after 30 seconds.")
