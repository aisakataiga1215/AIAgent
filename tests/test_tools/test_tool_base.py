import pytest
from src.tools.base import BaseTool, ToolResult


def test_tool_result_defaults():
    r = ToolResult(success=True, content="hello")
    assert r.success
    assert r.content == "hello"
    assert r.metadata == {}


def test_tool_to_openai_schema():
    class TestTool(BaseTool):
        name = "test"
        description = "A test tool"
        parameters = {"type": "object", "properties": {}}

        async def execute(self, **kwargs):
            return ToolResult(success=True, content="ok")

    t = TestTool()
    schema = t.to_openai_schema()
    assert schema["type"] == "function"
    assert schema["function"]["name"] == "test"


def test_tool_to_anthropic_schema():
    class TestTool(BaseTool):
        name = "test2"
        description = "Another test"
        parameters = {"type": "object", "properties": {"x": {"type": "string"}}}

        async def execute(self, **kwargs):
            return ToolResult(success=True, content="ok")

    t = TestTool()
    schema = t.to_anthropic_schema()
    assert schema["name"] == "test2"
    assert "x" in schema["input_schema"]["properties"]
