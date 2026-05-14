"""Predefined workflow templates."""


def pr_review_workflow(repo: str = ".", target: str = "HEAD~1") -> dict:
    """Template: Full PR review workflow."""
    return {
        "task": "Review the code changes and provide a comprehensive report.",
        "metadata": {"repo": repo, "target": target},
        "plan": [
            {"agent": "code_review", "subtask": "Review code changes for security, correctness, performance, and style", "status": "pending"},
        ],
    }


def full_ci_workflow(repo: str = ".", target: str = "HEAD~1") -> dict:
    """Template: Full CI check (review + test coverage check)."""
    return {
        "task": "Run a full CI check: review code, check test coverage.",
        "metadata": {"repo": repo, "target": target},
        "plan": [
            {"agent": "code_review", "subtask": "Review code changes", "status": "pending"},
        ],
    }


WORKFLOW_TEMPLATES = {
    "pr-review": pr_review_workflow,
    "full-ci": full_ci_workflow,
}
