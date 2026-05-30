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

    def to_manifest(self) -> dict:
        """
        Generate a structured agent-call manifest for the SKILL.md protocol.

        This is the bridge between the Python DSL and the actual Claude Code
        Agent orchestration. The returned dict describes exactly which agents
        to launch, with their prompts, dependencies, and expected outputs —
        ready for consumption by the Phase 3 execution loop.
        """
        layers = self._build_layers()
        task_map = {t.name: t for t in self.tasks}

        manifest = {
            "goal": self.goal,
            "total_tasks": len(self.tasks),
            "total_layers": len(layers),
            "layers": [],
        }
        for layer_idx, layer in enumerate(layers):
            layer_tasks = []
            for t in layer:
                layer_tasks.append({
                    "id": t.name,
                    "title": t.name,
                    "agent_type": t.agent_type,
                    "depends_on": t.depends_on,
                    "prompt": t.prompt,
                })
            manifest["layers"].append({
                "index": layer_idx,
                "parallel": len(layer) > 1,
                "tasks": layer_tasks,
            })
        return manifest

    def run(self, dry_run: bool = True) -> dict:
        """
        Show the workflow execution plan.

        IMPORTANT: This method does NOT execute Claude Code agents.
        Real orchestration happens through the SKILL.md protocol, which
        reads the plan JSON and spawns Agent() calls per layer.

        Use dry_run=True (default) to visualize the DAG.
        Use to_manifest() to get structured data for the protocol.
        """
        if not self.tasks:
            print("❌ No tasks defined")
            return {}

        layers = self._build_layers()

        print(f"\n⚡ Workflow: {self.goal}")
        print(f"   Tasks: {len(self.tasks)} | Layers: {len(layers)}")
        print(f"   ℹ️  This shows the execution PLAN. Real agent orchestration")
        print(f"      is driven by the SKILL.md protocol + plan.json.")
        print()

        return self._dry_run(layers)

    def _dry_run(self, layers: list[list[AgentTask]]) -> dict:
        """Show execution plan without running."""
        for i, layer in enumerate(layers):
            parallel_mark = "⚡ PARALLEL" if len(layer) > 1 else "→  SERIAL"
            print(f"Layer {i} ({parallel_mark}):")
            for t in layer:
                deps = f" ← {', '.join(t.depends_on)}" if t.depends_on else ""
                print(f"  [{t.agent_type}] {t.name}{deps}")
        return {"dry_run": True, "layers": len(layers), "tasks": len(self.tasks)}

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
        print(f"   ℹ️  Real orchestration is driven by the SKILL.md protocol.")
        return self._dry_run(layers)


# ── Script Generator ────────────────────────────────────────────────────────

def generate_workflow_script(plan_json: dict) -> str:
    """
    Generate a Python workflow script from a TaskPlan JSON.

    The generated script outputs a structured manifest (JSON) describing
    the DAG layers, agent types, and task prompts. This manifest is then
    consumed by the SKILL.md protocol's Phase 3 execution loop.

    NOTE: The script does NOT execute Claude Code agents directly.
    Real orchestration happens through the SKILL.md text protocol.
    """
    plan = TaskPlan.from_dict(plan_json)
    layers = topological_layers(plan.tasks)
    task_map = {t.id: t for t in plan.tasks}

    lines = []
    lines.append("#!/usr/bin/env python3")
    lines.append('"""')
    lines.append(f"Auto-generated Workflow Manifest")
    lines.append(f"Goal: {plan.goal}")
    lines.append(f"Generated: {datetime.now(timezone.utc).isoformat()}")
    lines.append(f"Tasks: {len(plan.tasks)} | Layers: {len(layers)}")
    lines.append("")
    lines.append("This script outputs a structured JSON manifest for the")
    lines.append("SKILL.md workflow protocol. It does NOT execute agents.")
    lines.append("Real orchestration is driven by the Phase 3 execution loop.")
    lines.append('"""')
    lines.append("")
    lines.append("import json, sys, os")
    lines.append("from datetime import datetime, timezone")
    lines.append("")
    lines.append("")
    lines.append(f"GOAL = {json.dumps(plan.goal)}")
    lines.append("")
    lines.append("# ── Task Definitions ──────────────────────────────────────────")
    lines.append("TASKS = [")
    for t in plan.tasks:
        lines.append(f"    {{")
        lines.append(f"        \"id\": {json.dumps(t.id)},")
        lines.append(f"        \"title\": {json.dumps(t.title)},")
        lines.append(f"        \"agent\": {json.dumps(t.agent)},")
        lines.append(f"        \"dependencies\": {json.dumps(t.dependencies)},")
        lines.append(f"        \"description\": {json.dumps(t.description[:200])},")
        lines.append(f"        \"priority\": {json.dumps(t.priority)},")
        lines.append(f"    }},")
    lines.append("]")
    lines.append("")
    lines.append("# ── Layer Computation (topological sort) ──────────────────────")
    lines.append("def compute_layers(tasks):")
    lines.append("    remaining = {t['id']: set(t['dependencies']) for t in tasks}")
    lines.append("    completed, layers = set(), []")
    lines.append("    while remaining:")
    lines.append("        ready = sorted(tid for tid, deps in remaining.items() if deps.issubset(completed))")
    lines.append("        if not ready:")
    lines.append("            layers.append(sorted(remaining.keys()))")
    lines.append("            break")
    lines.append("        layers.append(ready)")
    lines.append("        completed.update(ready)")
    lines.append("        for tid in ready:")
    lines.append("            del remaining[tid]")
    lines.append("    return layers")
    lines.append("")
    lines.append("# ── Manifest Generation ───────────────────────────────────────")
    lines.append("def generate_manifest():")
    lines.append("    layers = compute_layers(TASKS)")
    lines.append("    task_map = {t['id']: t for t in TASKS}")
    lines.append("    manifest = {")
    lines.append("        \"goal\": GOAL,")
    lines.append("        \"generated_at\": datetime.now(timezone.utc).isoformat(),")
    lines.append("        \"total_tasks\": len(TASKS),")
    lines.append("        \"total_layers\": len(layers),")
    lines.append("        \"layers\": []")
    lines.append("    }")
    lines.append("    for i, layer_ids in enumerate(layers):")
    lines.append("        layer_tasks = []")
    lines.append("        for tid in layer_ids:")
    lines.append("            t = task_map[tid]")
    lines.append("            layer_tasks.append({")
    lines.append("                \"id\": t['id'],")
    lines.append("                \"title\": t['title'],")
    lines.append("                \"agent_type\": t['agent'],")
    lines.append("                \"depends_on\": t['dependencies'],")
    lines.append("                \"prompt\": t['description'],")
    lines.append("            })")
    lines.append("        manifest[\"layers\"].append({")
    lines.append("            \"index\": i,")
    lines.append("            \"parallel\": len(layer_ids) > 1,")
    lines.append("            \"tasks\": layer_tasks")
    lines.append("        })")
    lines.append("    return manifest")
    lines.append("")
    lines.append("# ── Entry Point ───────────────────────────────────────────────")
    lines.append("if __name__ == '__main__':")
    lines.append("    import argparse")
    lines.append("    parser = argparse.ArgumentParser(")
    lines.append("        description='Workflow Manifest Generator')")
    lines.append("    parser.add_argument('--json', action='store_true',")
    lines.append("                        help='Output manifest as JSON')")
    lines.append("    parser.add_argument('--summary', action='store_true',")
    lines.append("                        help='Print human-readable summary')")
    lines.append("    args = parser.parse_args()")
    lines.append("")
    lines.append("    manifest = generate_manifest()")
    lines.append("")
    lines.append("    if args.json or not args.summary:")
    lines.append("        print(json.dumps(manifest, indent=2, ensure_ascii=False))")
    lines.append("    if args.summary or not args.json:")
    lines.append("        print(f\"\\n⚡ Workflow: {GOAL}\")")
    lines.append("        print(f\"   Tasks: {manifest['total_tasks']} | Layers: {manifest['total_layers']}\")")
    lines.append("        for layer in manifest['layers']:")
    lines.append("            parallel = '⚡ PARALLEL' if layer['parallel'] else '→  SERIAL'")
    lines.append("            print(f\"\\n   Layer {layer['index']} ({parallel}):\")")
    lines.append("            for t in layer['tasks']:")
    lines.append("                deps = f\" ← {', '.join(t['depends_on'])}\" if t['depends_on'] else ''")
    lines.append("                print(f\"     [{t['agent_type']}] {t['id']}: {t['title']}{deps}\")")

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
