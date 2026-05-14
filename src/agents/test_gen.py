from pathlib import Path
from src.agents.base import ReActAgent, AgentResult
from src.tools.registry import ToolRegistry
from src.tools.filesystem_tool import FileReadTool, FileWriteTool
from src.tools.ast_tool import ASTAnalyzerTool
from src.tools.test_runner_tool import TestRunnerTool, CoverageAnalyzerTool
from src.tools.codebase_search_tool import CodebaseSearchTool


TEST_GEN_SYSTEM_EXTRA = """
## Your Role (Test Generation Agent)
You are an expert test engineer. Your job is to analyze source code and generate high-quality pytest tests.

## Process (follow in order):
1. Read the target source file with `read_file`
2. Analyze the structure with `ast_analyze` — identify functions, classes, branch points
3. Check existing tests with `codebase_search` (search for existing test files for this module)
4. Run current tests with `test_runner` to see baseline coverage
5. If coverage exists, use `coverage_analyzer` to find gaps
6. Generate pytest test code and output it

## Test Quality Standards
- Use `pytest.mark.parametrize` for multiple input/output pairs
- Use `unittest.mock` or `pytest-mock` for external dependencies
- Cover: happy path, edge cases (None, empty, boundary), error paths
- Follow the project's existing test patterns (check `codebase_search` results)
- Use descriptive test function names: `test_<function>_<scenario>`

## Output Format
Structure your response as:

### Analysis
(What the code does, key functions found, current coverage gaps)

### Generated Tests
For each test file you propose, provide the complete code in a fenced code block:
```python
# tests/test_xxx.py
import pytest
...
```

### Running Results
(If you ran the tests, report pass/fail and any fixes made)

## Important
- Every test must be ready to paste into a file and run.
- If you need to write the test file, use `write_file` tool.
- Run `test_runner` after writing to verify tests pass.
- If tests fail, analyze the error, fix the test, and re-run (max 3 attempts).
"""


class TestGenAgent(ReActAgent):
    __test__ = False
    role = "Test Generation Agent"
    role_description = (
        "You generate pytest test cases by analyzing source code structure, branch logic, and dependencies. "
        "You produce parametrized, mock-aware tests that cover happy paths, edge cases, and error handling."
    )
    system_prompt_extra = TEST_GEN_SYSTEM_EXTRA


def build_test_gen_agent(workspace: str = ".") -> TestGenAgent:
    """Factory: create a TestGenAgent with the standard tool set."""
    registry = ToolRegistry()
    ws = Path(workspace).resolve()
    registry.register(FileReadTool(str(ws)))
    registry.register(FileWriteTool(str(ws)))
    registry.register(ASTAnalyzerTool(str(ws)))
    registry.register(TestRunnerTool(str(ws)))
    registry.register(CoverageAnalyzerTool(str(ws)))
    registry.register(CodebaseSearchTool())
    return TestGenAgent(registry)


async def generate_tests(workspace: str = ".", file_path: str | None = None) -> AgentResult:
    """Generate tests for a target file, or for files changed in the last commit."""
    agent = build_test_gen_agent(workspace)

    if file_path:
        task = f"""Generate tests for the file: {file_path}

1. Read the file with `read_file`
2. Analyze its structure with `ast_analyze`
3. Search for existing test files with `codebase_search` (query: "test_{file_path}")
4. Run existing tests with `test_runner`
5. Generate comprehensive pytest test file
6. Write the test file with `write_file`
7. Run the tests with `test_runner` to verify they pass
8. If tests fail, fix and re-run (max 3 attempts)
9. Report the final test code and run results"""
    else:
        task = """Generate tests for the most recently changed files in this repository.

1. Find changed files by checking diffs or reading key source files
2. For each source file without tests, generate pytest tests
3. Write test files, run them, fix if needed
4. Report all generated tests and their results"""

    return await agent.run(task)
