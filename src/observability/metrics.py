from dataclasses import dataclass, field
from typing import Any


@dataclass
class AgentMetrics:
    agent_name: str = ""
    total_runs: int = 0
    successful_runs: int = 0
    failed_runs: int = 0
    total_tokens: int = 0
    total_tool_calls: int = 0
    avg_latency_ms: float = 0.0

    def record_run(self, success: bool, tokens: int, tool_calls: int, latency_ms: float) -> None:
        self.total_runs += 1
        if success:
            self.successful_runs += 1
        else:
            self.failed_runs += 1
        self.total_tokens += tokens
        self.total_tool_calls += tool_calls
        self.avg_latency_ms = (
            (self.avg_latency_ms * (self.total_runs - 1) + latency_ms) / self.total_runs
        )

    @property
    def success_rate(self) -> float:
        if self.total_runs == 0:
            return 0.0
        return self.successful_runs / self.total_runs

    def to_dict(self) -> dict[str, Any]:
        return {
            "agent_name": self.agent_name,
            "total_runs": self.total_runs,
            "success_rate": f"{self.success_rate:.1%}",
            "total_tokens": self.total_tokens,
            "total_tool_calls": self.total_tool_calls,
            "avg_latency_ms": f"{self.avg_latency_ms:.1f}",
        }


class MetricsCollector:
    """Collects and aggregates agent performance metrics."""

    def __init__(self) -> None:
        self._metrics: dict[str, AgentMetrics] = {}

    def get(self, agent_name: str) -> AgentMetrics:
        if agent_name not in self._metrics:
            self._metrics[agent_name] = AgentMetrics(agent_name=agent_name)
        return self._metrics[agent_name]

    def list_all(self) -> list[dict[str, Any]]:
        return [m.to_dict() for m in self._metrics.values()]
