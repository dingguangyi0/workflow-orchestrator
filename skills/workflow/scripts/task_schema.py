#!/usr/bin/env python3
"""
Workflow Orchestrator — Task Schema & Data Structures

Defines the canonical JSON schemas for:
  1. Task Plan (output of orchestrator agent)
  2. Task Result (tracked via TaskCreate/TaskUpdate)
  3. Workflow State (aggregate view for monitoring)

All other scripts (dag.py, reporter.py, monitor.py) import from this module.
"""

from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Optional
from dataclasses import dataclass, field, asdict


# ── Enums ────────────────────────────────────────────────────────────────────

class TaskStatus(str, Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"
    BLOCKED = "blocked"


class AgentType(str, Enum):
    EXPLORER = "explorer"
    WORKER = "worker"
    IMPLEMENTER = "implementer"
    REVIEWER = "reviewer"
    ORCHESTRATOR = "orchestrator"


class Priority(str, Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class GoalType(str, Enum):
    DEVELOPMENT = "development"
    RESEARCH = "research"
    REFACTORING = "refactoring"
    DOCUMENTATION = "documentation"
    DEPLOYMENT = "deployment"
    DEBUGGING = "debugging"
    TESTING = "testing"
    OTHER = "other"


# ── Data Classes ──────────────────────────────────────────────────────────────

@dataclass
class TaskDefinition:
    """A single task in the orchestration plan (from orchestrator agent)."""
    id: str
    title: str
    description: str
    agent: str  # AgentType value
    dependencies: list[str] = field(default_factory=list)
    expected_output: str = ""
    file_patterns: list[str] = field(default_factory=list)
    priority: str = "medium"  # Priority value

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, d: dict) -> "TaskDefinition":
        return cls(
            id=d["id"],
            title=d.get("title", d["id"]),
            description=d.get("description", ""),
            agent=d.get("agent", "worker"),
            dependencies=d.get("dependencies", []),
            expected_output=d.get("expected_output", ""),
            file_patterns=d.get("file_patterns", []),
            priority=d.get("priority", "medium"),
        )


@dataclass
class TaskPlan:
    """Full orchestration plan."""
    goal: str
    goal_type: str = "other"
    estimated_layers: int = 1
    tasks: list[TaskDefinition] = field(default_factory=list)
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def to_dict(self) -> dict:
        return {
            "goal": self.goal,
            "goal_type": self.goal_type,
            "estimated_layers": self.estimated_layers,
            "tasks": [t.to_dict() for t in self.tasks],
            "created_at": self.created_at,
        }

    @classmethod
    def from_dict(cls, d: dict) -> "TaskPlan":
        return cls(
            goal=d.get("goal", ""),
            goal_type=d.get("goal_type", "other"),
            estimated_layers=d.get("estimated_layers", 1),
            tasks=[TaskDefinition.from_dict(t) for t in d.get("tasks", [])],
            created_at=d.get("created_at", ""),
        )

    def get_task(self, task_id: str) -> Optional[TaskDefinition]:
        for t in self.tasks:
            if t.id == task_id:
                return t
        return None

    def validate(self) -> list[str]:
        """Validate the plan and return list of errors (empty = valid)."""
        errors = []
        task_ids = {t.id for t in self.tasks}

        if not self.goal:
            errors.append("Goal is empty")
        if not self.tasks:
            errors.append("No tasks defined")
        if len(self.tasks) > 20:
            errors.append(f"Too many tasks ({len(self.tasks)}), max 20")

        for t in self.tasks:
            # Validate agent type
            valid_agents = {a.value for a in AgentType}
            if t.agent not in valid_agents:
                errors.append(f"Task {t.id}: invalid agent '{t.agent}', must be one of {valid_agents}")

            # Validate priority
            valid_priorities = {p.value for p in Priority}
            if t.priority not in valid_priorities:
                errors.append(f"Task {t.id}: invalid priority '{t.priority}'")

            # Validate dependencies
            for dep in t.dependencies:
                if dep not in task_ids:
                    errors.append(f"Task {t.id}: depends on non-existent task '{dep}'")
                if dep == t.id:
                    errors.append(f"Task {t.id}: cannot depend on itself")

        # Check for cycles
        cycle_error = _detect_cycle(self.tasks)
        if cycle_error:
            errors.append(cycle_error)

        return errors


@dataclass
class TaskResult:
    """Runtime result of a single task."""
    task_id: str
    status: str = "pending"  # TaskStatus value
    agent_type: str = ""
    started_at: str = ""
    completed_at: str = ""
    output_summary: str = ""
    error_message: str = ""
    retry_count: int = 0
    max_retries: int = 1

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, d: dict) -> "TaskResult":
        return cls(
            task_id=d.get("task_id", ""),
            status=d.get("status", "pending"),
            agent_type=d.get("agent_type", ""),
            started_at=d.get("started_at", ""),
            completed_at=d.get("completed_at", ""),
            output_summary=d.get("output_summary", ""),
            error_message=d.get("error_message", ""),
            retry_count=d.get("retry_count", 0),
            max_retries=d.get("max_retries", 1),
        )


@dataclass
class WorkflowState:
    """Full workflow execution state (for monitoring)."""
    plan: Optional[TaskPlan] = None
    results: dict[str, TaskResult] = field(default_factory=dict)
    current_layer: int = 0
    total_layers: int = 0
    phase: str = "init"  # init | planning | executing | handling_failures | aggregating | done

    @property
    def completed_count(self) -> int:
        return sum(1 for r in self.results.values() if r.status == TaskStatus.COMPLETED.value)

    @property
    def failed_count(self) -> int:
        return sum(1 for r in self.results.values() if r.status == TaskStatus.FAILED.value)

    @property
    def in_progress_count(self) -> int:
        return sum(1 for r in self.results.values() if r.status == TaskStatus.IN_PROGRESS.value)

    @property
    def pending_count(self) -> int:
        return sum(1 for r in self.results.values() if r.status == TaskStatus.PENDING.value)

    @property
    def total_count(self) -> int:
        return len(self.results)

    @property
    def progress_pct(self) -> float:
        if self.total_count == 0:
            return 0.0
        # Completed + Skipped count as "done"
        done = self.completed_count + sum(
            1 for r in self.results.values() if r.status == TaskStatus.SKIPPED.value
        )
        return (done / self.total_count) * 100

    @property
    def is_complete(self) -> bool:
        return all(
            r.status in (TaskStatus.COMPLETED.value, TaskStatus.SKIPPED.value, TaskStatus.FAILED.value)
            for r in self.results.values()
        )

    def to_dict(self) -> dict:
        return {
            "plan": self.plan.to_dict() if self.plan else None,
            "results": {k: v.to_dict() for k, v in self.results.items()},
            "current_layer": self.current_layer,
            "total_layers": self.total_layers,
            "phase": self.phase,
            "stats": {
                "total": self.total_count,
                "completed": self.completed_count,
                "failed": self.failed_count,
                "in_progress": self.in_progress_count,
                "pending": self.pending_count,
                "progress_pct": round(self.progress_pct, 1),
            },
        }


# ── Status & Agent Icons ─────────────────────────────────────────────────────

STATUS_ICONS = {
    TaskStatus.PENDING.value: "⬜",
    TaskStatus.IN_PROGRESS.value: "🔄",
    TaskStatus.COMPLETED.value: "✅",
    TaskStatus.FAILED.value: "❌",
    TaskStatus.SKIPPED.value: "⏭️",
    TaskStatus.BLOCKED.value: "🚫",
}

AGENT_ICONS = {
    "explorer": "🔍",
    "worker": "🔧",
    "implementer": "🛠️",
    "reviewer": "📋",
    "orchestrator": "🧠",
}

# ── Helpers ──────────────────────────────────────────────────────────────────

def _detect_cycle(tasks: list[TaskDefinition]) -> Optional[str]:
    """Detect cycles in the dependency graph using DFS. Returns error message or None."""
    task_map = {t.id: t for t in tasks}
    WHITE, GRAY, BLACK = 0, 1, 2
    color = {t.id: WHITE for t in tasks}

    def dfs(task_id: str, path: list[str]) -> Optional[str]:
        color[task_id] = GRAY
        task = task_map.get(task_id)
        if task:
            for dep in task.dependencies:
                if color.get(dep) == GRAY:
                    cycle = " → ".join(path[path.index(dep):] + [dep])
                    return f"Circular dependency detected: {cycle}"
                if color.get(dep) == WHITE:
                    result = dfs(dep, path + [dep])
                    if result:
                        return result
        color[task_id] = BLACK
        return None

    for t in tasks:
        if color[t.id] == WHITE:
            result = dfs(t.id, [t.id])
            if result:
                return result
    return None


def topological_layers(tasks: list[TaskDefinition]) -> list[list[str]]:
    """
    Sort tasks into layers for parallel execution.
    Layer 0 = no dependencies, Layer N = depends on tasks from Layer N-1 or earlier.
    Returns list of layers, each layer is a list of task IDs.
    """
    remaining = {t.id: set(t.dependencies) for t in tasks}
    completed: set[str] = set()
    layers: list[list[str]] = []

    while remaining:
        # Find tasks whose dependencies are all completed
        ready = [
            tid for tid, deps in remaining.items()
            if deps.issubset(completed)
        ]
        if not ready:
            # Should not happen if DAG is valid, but handle gracefully
            # Put remaining tasks in a final layer
            layers.append(list(remaining.keys()))
            break
        layers.append(sorted(ready))
        completed.update(ready)
        for tid in ready:
            del remaining[tid]

    return layers


# ── CLI ──────────────────────────────────────────────────────────────────────

def main():
    """Task schema validation, state management, and workflow utilities."""
    import argparse
    parser = argparse.ArgumentParser(description="Workflow Orchestrator — task schema and state utilities")
    parser.add_argument("--validate", action="store_true", help="Validate task plan JSON from stdin")
    parser.add_argument("--layers", action="store_true", help="Compute topological layers from plan JSON")
    parser.add_argument("--init-state", action="store_true", help="Initialize workflow state from plan JSON")
    parser.add_argument("--update-status", action="store_true", help="Update workflow state (use with --task, --layer, --phase)")
    parser.add_argument("--task", action="append", nargs=2, metavar=("ID", "STATUS"), default=[], help="Set task status (repeatable)")
    parser.add_argument("--output", action="append", nargs=2, metavar=("ID", "SUMMARY"), default=[], help="Set task output summary (repeatable)")
    parser.add_argument("--error", action="append", nargs=2, metavar=("ID", "MSG"), default=[], help="Set task error message (repeatable)")
    parser.add_argument("--layer", type=int, help="Set current layer")
    parser.add_argument("--phase", type=str, help="Set workflow phase")
    args = parser.parse_args()

    try:
        raw = sys.stdin.read()
        data = json.loads(raw)
    except json.JSONDecodeError as e:
        print(f"❌ Invalid JSON: {e}", file=sys.stderr)
        sys.exit(1)
    except EOFError:
        print("❌ No input provided", file=sys.stderr)
        sys.exit(1)

    if args.update_status:
        # Update workflow state from CLI flags
        now = datetime.now(timezone.utc).isoformat()
        for task_id, status in args.task:
            if task_id in data.get("results", {}):
                data["results"][task_id]["status"] = status
                if status == "in_progress":
                    data["results"][task_id]["started_at"] = now
                elif status in ("completed", "failed", "skipped"):
                    data["results"][task_id]["completed_at"] = now
        for task_id, summary in args.output:
            if task_id in data.get("results", {}):
                data["results"][task_id]["output_summary"] = summary
        for task_id, msg in args.error:
            if task_id in data.get("results", {}):
                data["results"][task_id]["error_message"] = msg
        if args.layer is not None:
            data["current_layer"] = args.layer
        if args.phase:
            data["phase"] = args.phase
        print(json.dumps(data, indent=2))

    elif args.validate:
        plan = TaskPlan.from_dict(data)
        errors = plan.validate()
        if errors:
            print("❌ Plan validation failed:")
            for err in errors:
                print(f"  - {err}")
            sys.exit(1)
        else:
            print(f"✅ Plan is valid: {len(plan.tasks)} tasks, {plan.estimated_layers} layers")
            layers = topological_layers(plan.tasks)
            print(f"   Computed layers: {len(layers)}")
            for i, layer in enumerate(layers):
                print(f"   Layer {i}: {layer}")

    elif args.layers:
        plan = TaskPlan.from_dict(data)
        layers = topological_layers(plan.tasks)
        print(json.dumps({"layers": [[tid for tid in layer] for layer in layers]}))

    elif args.init_state:
        plan = TaskPlan.from_dict(data)
        state = WorkflowState(plan=plan)
        layers = topological_layers(plan.tasks)
        state.total_layers = len(layers)
        for task in plan.tasks:
            state.results[task.id] = TaskResult(
                task_id=task.id,
                status=TaskStatus.PENDING.value,
                agent_type=task.agent,
            )
        print(json.dumps(state.to_dict(), indent=2))

    else:
        # Default: validate only
        plan = TaskPlan.from_dict(data)
        errors = plan.validate()
        if errors:
            print("❌ Plan validation failed:")
            for err in errors:
                print(f"  - {err}")
            sys.exit(1)
        print("✅ Valid")
        print(json.dumps(plan.to_dict(), indent=2))


if __name__ == "__main__":
    main()
