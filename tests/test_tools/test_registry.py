import pytest
from src.tools.registry import ToolRegistry
from src.tools.base import BaseTool, ToolResult


class FakeTool(BaseTool):
    name = "fake"
    description = "Fake tool"
    parameters = {}

    async def execute(self, **kwargs):
        return ToolResult(success=True, content="fake result")


class FakeTool2(BaseTool):
    name = "fake2"
    description = "Fake tool 2"
    parameters = {}

    async def execute(self, **kwargs):
        return ToolResult(success=True, content="fake2 result")


@pytest.fixture
def registry():
    r = ToolRegistry()
    r.register(FakeTool())
    r.register(FakeTool2())
    return r


def test_register_and_list(registry):
    names = registry.list_names()
    assert "fake" in names
    assert "fake2" in names


def test_get_tool(registry):
    t = registry.get("fake")
    assert t is not None
    assert t.name == "fake"


def test_get_unknown_tool(registry):
    assert registry.get("unknown") is None


@pytest.mark.asyncio
async def test_execute(registry):
    result = await registry.execute("fake")
    assert result.success
    assert result.content == "fake result"


@pytest.mark.asyncio
async def test_execute_unknown(registry):
    result = await registry.execute("unknown")
    assert not result.success
    assert "not found" in result.content


def test_to_openai_schemas(registry):
    schemas = registry.to_openai_schemas()
    assert len(schemas) == 2


def test_to_anthropic_schemas(registry):
    schemas = registry.to_anthropic_schemas()
    assert len(schemas) == 2
