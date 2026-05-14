import pytest
from pathlib import Path
from src.tools.filesystem_tool import FileReadTool, FileListTool, FileWriteTool


@pytest.fixture
def workspace(tmp_path):
    (tmp_path / "test.py").write_text("print('hello')\nprint('world')\n")
    (tmp_path / "subdir").mkdir()
    (tmp_path / "subdir" / "data.txt").write_text("data")
    return str(tmp_path)


@pytest.mark.asyncio
async def test_read_file(workspace):
    tool = FileReadTool(workspace)
    result = await tool.execute("test.py")
    assert result.success
    assert "print('hello')" in result.content


@pytest.mark.asyncio
async def test_read_file_with_lines(workspace):
    tool = FileReadTool(workspace)
    result = await tool.execute("test.py", start_line=1, end_line=1)
    assert result.success
    assert "print('hello')" in result.content
    assert "print('world')" not in result.content


@pytest.mark.asyncio
async def test_read_missing_file(workspace):
    tool = FileReadTool(workspace)
    result = await tool.execute("nope.txt")
    assert not result.success


@pytest.mark.asyncio
async def test_list_directory(workspace):
    tool = FileListTool(workspace)
    result = await tool.execute(".")
    assert result.success
    assert "test.py" in result.content
    assert "subdir/" in result.content


@pytest.mark.asyncio
async def test_write_file(workspace):
    tool = FileWriteTool(workspace)
    result = await tool.execute("new.txt", "content here")
    assert result.success
    assert Path(workspace, "new.txt").read_text() == "content here"
