import pytest
from src.workflow.state import WorkflowState
from src.workflow.templates import pr_review_workflow, full_ci_workflow, WORKFLOW_TEMPLATES
from src.workflow.engine import build_workflow


class TestWorkflowState:
    def test_initial_state(self):
        state: WorkflowState = {
            "messages": [],
            "task": "test",
            "plan": [],
            "agent_outputs": {},
            "errors": [],
            "status": "pending",
            "metadata": {},
        }
        assert state["status"] == "pending"
        assert state["task"] == "test"


class TestWorkflowTemplates:
    def test_pr_review_template(self):
        tmpl = pr_review_workflow()
        assert tmpl["task"]
        assert len(tmpl["plan"]) >= 1
        assert any(p["agent"] == "code_review" for p in tmpl["plan"])

    def test_full_ci_template(self):
        tmpl = full_ci_workflow()
        assert tmpl["task"]
        assert len(tmpl["plan"]) >= 1

    def test_all_templates_registered(self):
        assert "pr-review" in WORKFLOW_TEMPLATES
        assert "full-ci" in WORKFLOW_TEMPLATES


class TestWorkflowEngine:
    def test_build_workflow(self):
        graph = build_workflow()
        assert graph is not None

    def test_route_after_plan_empty(self):
        from src.workflow.engine import _route_after_plan
        state: WorkflowState = {
            "messages": [], "task": "", "plan": [],
            "agent_outputs": {}, "errors": [], "status": "pending", "metadata": {},
        }
        result = _route_after_plan(state)
        assert result == "aggregate"

    def test_route_after_plan_with_pending_review(self):
        from src.workflow.engine import _route_after_plan
        state: WorkflowState = {
            "messages": [], "task": "",
            "plan": [{"agent": "code_review", "subtask": "review", "status": "pending"}],
            "agent_outputs": {}, "errors": [], "status": "pending", "metadata": {},
        }
        result = _route_after_plan(state)
        assert result == "review"
