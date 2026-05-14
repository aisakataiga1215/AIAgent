import pytest
from unittest.mock import MagicMock
from src.agents.test_gen import TestGenAgent, build_test_gen_agent, generate_tests, TEST_GEN_SYSTEM_EXTRA
from src.tools.registry import ToolRegistry
from src.tools.base import BaseTool, ToolResult


class EchoTool(BaseTool):
    name = "echo"
    description = "Echo"
    parameters = {"type": "object", "properties": {"msg": {"type": "string"}}, "required": ["msg"]}

    async def execute(self, msg: str = "") -> ToolResult:
        return ToolResult(success=True, content=msg)


@pytest.fixture
def agent():
    registry = ToolRegistry()
    registry.register(EchoTool())
    agent = TestGenAgent(registry, model="claude-haiku-4-5-20251001")
    agent.client = MagicMock()
    return agent


def test_agent_role(agent):
    assert "Test Generation Agent" in agent.role


def test_system_prompt_extra():
    assert "pytest" in TEST_GEN_SYSTEM_EXTRA
    assert "parametrize" in TEST_GEN_SYSTEM_EXTRA


def test_build_agent(tmp_path):
    agent = build_test_gen_agent(str(tmp_path))
    assert isinstance(agent, TestGenAgent)
    names = agent.registry.list_names()
    assert "read_file" in names
    assert "ast_analyze" in names
    assert "test_runner" in names
    assert "codebase_search" in names


@pytest.mark.asyncio
async def test_run_agent(agent):
    mock_response = MagicMock()
    mock_response.usage.input_tokens = 10
    mock_response.usage.output_tokens = 5
    text_block = MagicMock()
    text_block.type = "text"
    text_block.text = "Final Answer:\nGenerated test code here..."
    mock_response.content = [text_block]
    agent.client.messages.create.return_value = mock_response

    result = await agent.run("Generate tests for foo.py")
    assert result.success
    assert "Generated test" in result.content
