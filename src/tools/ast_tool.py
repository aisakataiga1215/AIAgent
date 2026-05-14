import ast
from pathlib import Path
from src.tools.base import BaseTool, ToolResult


class ASTAnalyzerTool(BaseTool):
    name = "ast_analyze"
    description = "Parse and analyze Python source code structure. Returns functions, classes, imports, and complexity metrics."
    parameters = {
        "type": "object",
        "properties": {
            "file_path": {"type": "string", "description": "Path to the Python file to analyze"},
        },
        "required": ["file_path"],
    }

    def __init__(self, workspace: str = ".") -> None:
        self.workspace = Path(workspace).resolve()

    async def execute(self, file_path: str) -> ToolResult:
        full_path = self.workspace / file_path
        if not full_path.exists():
            return ToolResult(success=False, content=f"File not found: {file_path}")
        if full_path.suffix != ".py":
            return ToolResult(success=False, content=f"Not a Python file: {file_path}")

        try:
            source = full_path.read_text(encoding="utf-8")
            tree = ast.parse(source)
        except SyntaxError as e:
            return ToolResult(success=False, content=f"Syntax error in {file_path}: {e}")

        functions: list[str] = []
        classes: list[str] = []
        imports: list[str] = []
        total_lines = len(source.splitlines())

        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                cognitive = self._cognitive_complexity(node)
                functions.append(f"  - {node.name}() at line {node.lineno} (cognitive complexity: {cognitive})")
            elif isinstance(node, ast.ClassDef):
                methods = sum(1 for n in ast.walk(node) if isinstance(n, ast.FunctionDef))
                classes.append(f"  - class {node.name} at line {node.lineno} ({methods} methods)")
            elif isinstance(node, ast.Import):
                for alias in node.names:
                    imports.append(f"  - import {alias.name}")
            elif isinstance(node, ast.ImportFrom):
                names = ", ".join(a.name for a in node.names)
                imports.append(f"  - from {node.module} import {names}")

        sections = []
        sections.append(f"Analysis of {file_path} ({total_lines} lines)")
        if imports:
            sections.append(f"\nImports:\n" + "\n".join(imports[:20]))
        if classes:
            sections.append(f"\nClasses:\n" + "\n".join(classes))
        if functions:
            sections.append(f"\nFunctions:\n" + "\n".join(functions))
        if not functions and not classes:
            sections.append("\n(no functions or classes found)")

        return ToolResult(
            success=True,
            content="\n".join(sections),
            metadata={"functions": len(functions), "classes": len(classes), "lines": total_lines},
        )

    def _cognitive_complexity(self, func_node: ast.FunctionDef) -> int:
        score = 1
        for node in ast.walk(func_node):
            if isinstance(node, (ast.If, ast.For, ast.While, ast.ExceptHandler)):
                score += 1
            elif isinstance(node, ast.BoolOp):
                score += len(node.values) - 1
        return score
