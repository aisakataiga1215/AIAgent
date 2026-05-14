from src.agents.code_review import build_review_agent
from src.tools.registry import ToolRegistry


def get_tool_registry() -> ToolRegistry:
    from src.tools.filesystem_tool import FileReadTool, FileListTool
    from src.tools.git_tool import GitDiffTool, GitLogTool
    from src.tools.ast_tool import ASTAnalyzerTool

    registry = ToolRegistry()
    registry.register(GitDiffTool())
    registry.register(GitLogTool())
    registry.register(FileReadTool())
    registry.register(FileListTool())
    registry.register(ASTAnalyzerTool())
    return registry
