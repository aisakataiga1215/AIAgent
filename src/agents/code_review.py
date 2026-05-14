from pathlib import Path
from src.agents.base import ReActAgent, AgentResult
from src.tools.registry import ToolRegistry
from src.tools.git_tool import GitDiffTool, GitLogTool, GitStatusTool
from src.tools.filesystem_tool import FileReadTool
from src.tools.ast_tool import ASTAnalyzerTool


CODE_REVIEW_SYSTEM_EXTRA = """
## Your Role (Code Review Agent)
You are an expert code reviewer. Your job is to analyze code changes and provide actionable feedback.

## Review Checklist (follow these in order):
1. **Security** — SQL injection, XSS, hardcoded secrets, unsafe deserialization, path traversal
2. **Correctness** — Logic errors, edge cases, null/None handling, off-by-one errors
3. **Performance** — N+1 queries, unnecessary allocations, blocking I/O in async code
4. **Code Style** — Naming conventions, function length (>50 lines is a smell), DRY violations
5. **Error Handling** — Missing try/except, swallowed exceptions, bare excepts

## Output Format
Structure your review as:

### Summary
(2-3 sentences about the overall quality)

### Issues Found
For each issue:
- **Severity**: 🔴 Critical | 🟠 Major | 🟡 Minor
- **File**: path:line
- **Problem**: what's wrong
- **Fix**: concrete suggestion with code example if helpful

### Recommendations
(Optional broader suggestions — refactoring, test coverage, architectural concerns)

## Important
- Every finding must reference a specific file path and line number.
- If using git_diff tool, reference files from the diff output.
- If you cannot determine something (e.g., whether a function exists), use read_file or ast_analyze to verify.
"""


class CodeReviewAgent(ReActAgent):
    role = "Code Review Agent"
    role_description = (
        "You review code changes for security, correctness, performance, style, and error handling. "
        "You produce structured, actionable review reports with specific file paths and line numbers."
    )
    system_prompt_extra = CODE_REVIEW_SYSTEM_EXTRA


def build_review_agent(workspace: str = ".") -> CodeReviewAgent:
    """Factory: create a CodeReviewAgent with the standard tool set."""
    registry = ToolRegistry()
    ws = Path(workspace).resolve()
    registry.register(GitDiffTool(str(ws)))
    registry.register(GitLogTool(str(ws)))
    registry.register(GitStatusTool(str(ws)))
    registry.register(FileReadTool(str(ws)))
    registry.register(ASTAnalyzerTool(str(ws)))
    return CodeReviewAgent(registry)


async def review_repository(workspace: str = ".", target: str = "HEAD~1") -> AgentResult:
    """Run code review on a repository against a git target."""
    agent = build_review_agent(workspace)
    task = f"""Review the code changes in this repository.

First, run `git_diff` with target="{target}" to see what changed.
Then, for each changed file that looks suspicious or important:
1. Read the file with `read_file` to understand context
2. Use `ast_analyze` for Python files to check structure
3. Report any issues you find

Focus especially on security vulnerabilities and correctness bugs. Be specific about file paths and line numbers."""
    return await agent.run(task)
