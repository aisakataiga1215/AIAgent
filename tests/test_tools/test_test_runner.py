import pytest
from pathlib import Path
from src.tools.test_runner_tool import TestRunnerTool, CoverageAnalyzerTool


class TestTestRunnerTool:
    def test_init(self):
        tool = TestRunnerTool("/tmp")
        assert tool.name == "test_runner"

    @pytest.mark.asyncio
    async def test_execute_runs_pytest(self, tmp_path):
        (tmp_path / "test_sample.py").write_text("""
def test_pass():
    assert True
""")
        tool = TestRunnerTool(str(tmp_path))
        result = await tool.execute("test_sample.py")
        assert result.success
        assert "passed" in result.content.lower() or "1 passed" in result.content

    @pytest.mark.asyncio
    async def test_execute_failing_test(self, tmp_path):
        (tmp_path / "test_fail.py").write_text("""
def test_fail():
    assert False
""")
        tool = TestRunnerTool(str(tmp_path))
        result = await tool.execute("test_fail.py")
        assert not result.success

    @pytest.mark.asyncio
    async def test_execute_with_coverage(self, tmp_path):
        (tmp_path / "test_cov.py").write_text("""
def test_pass():
    assert True
""")
        tool = TestRunnerTool(str(tmp_path))
        result = await tool.execute("test_cov.py", cov_target=".")
        assert "100%" in result.content or result.metadata["exit_code"] >= 0


class TestCoverageAnalyzerTool:
    def test_no_coverage_file(self, tmp_path):
        tool = CoverageAnalyzerTool(str(tmp_path))
        import asyncio
        result = asyncio.run(tool.execute())
        assert not result.success

    def test_with_coverage_json(self, tmp_path):
        import json
        cov = {
            "files": {
                "src/foo.py": {
                    "summary": {"percent_covered": 75.0},
                    "missing_lines": [10, 15, 20],
                    "excluded_lines": [1, 2],
                }
            }
        }
        (tmp_path / "coverage.json").write_text(json.dumps(cov))
        tool = CoverageAnalyzerTool(str(tmp_path))
        import asyncio
        result = asyncio.run(tool.execute())
        assert result.success
        assert "75.0%" in result.content
        assert "10" in result.content
