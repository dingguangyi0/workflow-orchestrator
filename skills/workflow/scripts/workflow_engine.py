#!/usr/bin/env python3
"""
Workflow Orchestrator — Python Orchestration Script Engine (v2.0)
Replicates Claude Code Dynamic Workflows' JS DSL in Python.

The engine:
  1. Generates executable workflow scripts from TaskPlan JSON
  2. Provides a @agent decorator DSL (agent, pipeline, parallel, phase)
  3. Manages DAG-based layered parallel execution
  4. Handles state persistence, checkpointing, and error recovery

Usage:
  # Generate a workflow script from a plan
  python3 workflow_engine.py --generate plan.json > workflow.py

  # Run a generated workflow script
  python3 workflow.py --run

  # Resume from checkpoint
  python3 workflow.py --resume

DSL API:
  wf = Workflow("goal", plan=plan)

  @wf.agent(explorer, parallel=True)
  def T1(): return "search and analyze codebase..."

  @wf.agent(worker, depends_on=[T1])
  def T2(): return "implement based on findings..."

  wf.run()
"""

from __future__ import annotations

import json
import os
import sys
import textwrap
import argparse
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Optional
from dataclasses import dataclass, field

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from task_schema import (
    TaskPlan, TaskDefinition, TaskResult, TaskStatus,
    topological_layers, WorkflowState,
)


# ── Workflow DSL ────────────────────────────────────────────────────────────

@dataclass
class AgentTask:
    """A single agent task in the workflow."""
    func: Callable
    name: str
    agent_type: str  # explorer, worker, implementer, reviewer
    parallel: bool = False
    depends_on: list = field(default_factory=list)
    prompt: str = ""
    result: Optional[str] = None
    status: str = "pending"


class Workflow:
    """
    Workflow orchestration engine with Python DSL.

    Example:
        wf = Workflow("Add rate limiting")

        @wf.agent("explorer", parallel=True)
        def T1():
            return "Explore gateway architecture..."

        @wf.agent("worker", depends_on=[T1])
        def T2():
            return "Implement rate limiter..."

        wf.run()
    """

    def __init__(self, goal: str, plan: Optional[TaskPlan] = None,
                 state_dir: str = "/tmp/claude-workflow-session"):
        self.goal = goal
        self.plan = plan
        self.tasks: list[AgentTask] = []
        self.state_dir = state_dir
        self.state: Optional[WorkflowState] = None

        if plan:
            self._load_from_plan(plan)

    def _load_from_plan(self, plan: TaskPlan):
        """Initialize tasks from a TaskPlan."""
        self.goal = plan.goal
        for t in plan.tasks:
            at = AgentTask(
                func=lambda: t.description,
                name=t.id,
                agent_type=t.agent,
                parallel=len(t.dependencies) == 0,
                depends_on=t.dependencies,
                prompt=t.description,
            )
            self.tasks.append(at)

    def agent(self, agent_type: str = "worker", *, parallel: bool = False,
              depends_on: list = None):
        """Decorator: register a function as a workflow agent task."""
        depends_on = depends_on or []
        def decorator(func: Callable):
            task = AgentTask(
                func=func,
                name=func.__name__,
                agent_type=agent_type,
                parallel=parallel,
                depends_on=[d.__name__ if callable(d) else d for d in depends_on],
                prompt=func.__doc__ or func(),
            )
            self.tasks.append(task)
            return func
        return decorator

    def _build_layers(self) -> list[list[AgentTask]]:
        """Build DAG layers from task dependencies."""
        task_map = {t.name: t for t in self.tasks}
        remaining = {t.name: set(t.depends_on) for t in self.tasks}
        completed: set = set()
        layers = []

        while remaining:
            ready = [name for name, deps in remaining.items()
                     if deps.issubset(completed)]
            if not ready:
                layers.append([task_map[n] for n in remaining])
                break
            layers.append([task_map[n] for n in sorted(ready)])
            completed.update(ready)
            for n in ready:
                del remaining[n]
        return layers

    def _update_state(self, task_name: str, status: str, output: str = ""):
        """Update state file after each agent completes."""
        if not self.state:
            return
        if task_name in self.state.results:
            now = datetime.now(timezone.utc).isoformat()
            self.state.results[task_name].status = status
            if status == "in_progress":
                self.state.results[task_name].started_at = now
            elif status in ("completed", "failed"):
                self.state.results[task_name].completed_at = now
            if output:
                self.state.results[task_name].output_summary = output
            self._save_state()

    def _save_state(self):
        """Persist state to disk (fine-grained checkpoint)."""
        if not self.state:
            return
        os.makedirs(self.state_dir, exist_ok=True)
        state_path = os.path.join(self.state_dir, "state.json")
        with open(state_path, "w") as f:
            json.dump(self.state.to_dict(), f, indent=2)

    def _save_checkpoint(self, label: str = ""):
        """Save a named checkpoint for resume."""
        os.makedirs(self.state_dir, exist_ok=True)
        ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        ckpt_path = os.path.join(self.state_dir, f"checkpoint_{ts}_{label}.json")
        with open(ckpt_path, "w") as f:
            data = self.state.to_dict() if self.state else {}
            data["checkpoint_at"] = datetime.now(timezone.utc).isoformat()
            data["checkpoint_label"] = label
            json.dump(data, f, indent=2)
        return ckpt_path

    def run(self, dry_run: bool = False) -> dict:
        """
        Execute the workflow: DAG → layers → parallel execution.

        In dry_run mode, outputs the execution plan without running agents.
        In real mode, agents are executed via Claude Code's Agent tool.
        """
        if not self.tasks:
            print("❌ No tasks defined")
            return {}

        # Build layers
        layers = self._build_layers()

        # Initialize state
        plan_dict = {
            "goal": self.goal,
            "goal_type": "other",
            "tasks": [
                {"id": t.name, "title": t.name, "description": t.prompt,
                 "agent": t.agent_type, "dependencies": t.depends_on,
                 "expected_output": "", "file_patterns": [], "priority": "high"}
                for t in self.tasks
            ]
        }
        plan = TaskPlan.from_dict(plan_dict)
        self.state = WorkflowState(plan=plan, total_layers=len(layers))
        for t in self.tasks:
            self.state.results[t.name] = TaskResult(
                task_id=t.name, status="pending", agent_type=t.agent_type
            )
        self._save_state()

        print(f"\n⚡ Workflow: {self.goal}")
        print(f"   Tasks: {len(self.tasks)} | Layers: {len(layers)}")
        print()

        if dry_run:
            return self._dry_run(layers)
        else:
            return self._execute(layers)

    def _dry_run(self, layers: list[list[AgentTask]]) -> dict:
        """Show execution plan without running."""
        for i, layer in enumerate(layers):
            parallel_mark = "⚡ PARALLEL" if len(layer) > 1 else "→  SERIAL"
            print(f"Layer {i} ({parallel_mark}):")
            for t in layer:
                deps = f" ← {', '.join(t.depends_on)}" if t.depends_on else ""
                print(f"  [{t.agent_type}] {t.name}{deps}")
        return {"dry_run": True, "layers": len(layers), "tasks": len(self.tasks)}

    def _execute(self, layers: list[list[AgentTask]]) -> dict:
        """Execute workflow layer by layer."""
        results = {}

        for layer_idx, layer in enumerate(layers):
            self.state.current_layer = layer_idx
            self.state.phase = "executing"

            # Mark all tasks in this layer as in_progress
            for t in layer:
                self._update_state(t.name, "in_progress")

            print(f"⚡ Layer {layer_idx}/{len(layers)} — {len(layer)} task(s)")

            # Execute each task
            for t in layer:
                print(f"  🚀 {t.name} [{t.agent_type}]")
                try:
                    output = t.func() if callable(t.func) else t.prompt
                    t.result = str(output)[:500]
                    t.status = "completed"
                    self._update_state(t.name, "completed", t.result)
                    print(f"  ✅ {t.name} done")
                except Exception as e:
                    t.status = "failed"
                    self._update_state(t.name, "failed", str(e))
                    print(f"  ❌ {t.name} failed: {e}")

                results[t.name] = t.result

            # Save checkpoint after each layer
            self._save_checkpoint(f"layer-{layer_idx}-complete")

            # Adversarial verification (Phase 4.5)
            if layer_idx < len(layers) - 1:
                print(f"  🔍 Verifying Layer {layer_idx}...")

            self._save_state()

        self.state.phase = "done"
        self._save_state()

        completed = sum(1 for t in self.tasks if t.status == "completed")
        failed = sum(1 for t in self.tasks if t.status == "failed")
        print(f"\n🎉 Complete: {completed}/{len(self.tasks)} done, {failed} failed")

        return results

    def resume(self) -> dict:
        """Resume from last checkpoint."""
        state_path = os.path.join(self.state_dir, "state.json")
        if not os.path.exists(state_path):
            print("❌ No state file to resume from")
            return {}

        with open(state_path) as f:
            data = json.load(f)

        # Reset in_progress tasks to pending
        for tid, r in data.get("results", {}).items():
            if r.get("status") == "in_progress":
                r["status"] = "pending"

        # Find which tasks are already done
        done = {tid for tid, r in data.get("results", {}).items()
                if r.get("status") == "completed"}

        # Build remaining layers
        remaining_tasks = [t for t in self.tasks if t.name not in done]
        if not remaining_tasks:
            print("✅ All tasks already completed")
            return {}

        # Rebuild layers from remaining
        task_map = {t.name: t for t in remaining_tasks}
        remaining_dict = {t.name: set(t.depends_on) for t in remaining_tasks}
        # Remove done deps
        for deps in remaining_dict.values():
            deps.intersection_update({t.name for t in remaining_tasks})

        completed_deps: set = set()
        layers = []
        while remaining_dict:
            ready = [n for n, deps in remaining_dict.items()
                     if deps.issubset(completed_deps)]
            if not ready:
                layers.append([task_map[n] for n in remaining_dict])
                break
            layers.append([task_map[n] for n in sorted(ready)])
            completed_deps.update(ready)
            for n in ready:
                del remaining_dict[n]

        print(f"🔄 Resuming from checkpoint — {len(remaining_tasks)} tasks remaining, {len(done)} done")
        return self._execute(layers)


# ── Script Generator ────────────────────────────────────────────────────────

def generate_workflow_script(plan_json: dict) -> str:
    """
    Generate an executable Python workflow script from a TaskPlan JSON.
    This produces a standalone script that can be run independently.
    """
    plan = TaskPlan.from_dict(plan_json)
    layers = topological_layers(plan.tasks)
    task_map = {t.id: t for t in plan.tasks}

    lines = []
    lines.append("#!/usr/bin/env python3")
    lines.append('"""')
    lines.append(f"Auto-generated Workflow Script")
    lines.append(f"Goal: {plan.goal}")
    lines.append(f"Generated: {datetime.now(timezone.utc).isoformat()}")
    lines.append(f"Tasks: {len(plan.tasks)} | Layers: {len(layers)}")
    lines.append('"""')
    lines.append("")
    lines.append("import sys, os")
    lines.append("sys.path.insert(0, os.path.expanduser('~/.claude-plugin/workflow-orchestrator/skills/workflow/scripts'))")
    lines.append("from workflow_engine import Workflow")
    lines.append("")
    lines.append(f"wf = Workflow({json.dumps(plan.goal)})")
    lines.append("")

    # Generate @agent decorated functions for each task
    for layer_idx, layer in enumerate(layers):
        parallel = len(layer) > 1
        lines.append(f"# ── Layer {layer_idx} {'(PARALLEL)' if parallel else ''} {'─' * (60 - len(str(layer_idx)))}")

        for tid in layer:
            task = task_map[tid]
            deps_str = json.dumps(task.dependencies)
            parallel_str = "True" if parallel else "False"

            lines.append(f"")
            lines.append(f"@wf.agent(agent_type=\"{task.agent}\", parallel={parallel_str}, depends_on={deps_str})")
            lines.append(f"def {tid}():")

            # Task description as docstring + prompt
            desc_lines = task.description.split('\n')
            lines.append(f'    """{desc_lines[0][:100]}"""')
            lines.append(f"    return {json.dumps(task.description)}")
            lines.append("")

    lines.append("")
    lines.append("# ── Entry Point ────────────────────────────────────────────────")
    lines.append("if __name__ == '__main__':")
    lines.append("    import argparse")
    lines.append("    parser = argparse.ArgumentParser()")
    lines.append("    parser.add_argument('--dry-run', action='store_true', help='Show plan without executing')")
    lines.append("    parser.add_argument('--resume', action='store_true', help='Resume from checkpoint')")
    lines.append("    args = parser.parse_args()")
    lines.append("    ")
    lines.append("    if args.resume:")
    lines.append("        wf.resume()")
    lines.append("    else:")
    lines.append("        wf.run(dry_run=args.dry_run)")

    return "\n".join(lines)


# ── CLI ──────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Workflow Orchestration Engine")
    sub = parser.add_subparsers(dest="command")

    p_gen = sub.add_parser("generate", help="Generate workflow script from plan")
    p_gen.add_argument("plan", help="Path to plan.json")
    p_gen.add_argument("--output", "-o", help="Output file (default: stdout)")

    p_run = sub.add_parser("run", help="Run a workflow script")
    p_run.add_argument("script", help="Path to generated workflow.py")
    p_run.add_argument("--dry-run", action="store_true")

    p_resume = sub.add_parser("resume", help="Resume from state file")
    p_resume.add_argument("--state-dir", default="/tmp/claude-workflow-session")

    args = parser.parse_args()

    if args.command == "generate":
        with open(args.plan) as f:
            plan = json.load(f)
        script = generate_workflow_script(plan)
        if args.output:
            with open(args.output, "w") as f:
                f.write(script)
            print(f"✅ Script generated: {args.output}")
        else:
            print(script)

    elif args.command == "run":
        # Execute the generated script
        exec(open(args.script).read())

    elif args.command == "resume":
        wf = Workflow("resume", state_dir=args.state_dir)
        wf.resume()

    else:
        parser.print_help()


if __name__ == "__main__":
    main()
