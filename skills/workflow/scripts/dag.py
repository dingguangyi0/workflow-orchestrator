#!/usr/bin/env python3
"""
Workflow Orchestrator — DAG Builder & Visualizer

Converts a task plan JSON into:
  - Mermaid flowchart (for rendering in terminals/IDEs that support Mermaid)
  - ASCII layered view (for pure terminal display)
  - JSON layer output (for programmatic consumption)

Usage:
  echo '<plan_json>' | python3 dag.py --mermaid
  echo '<plan_json>' | python3 dag.py --ascii
  echo '<plan_json>' | python3 dag.py --layers
  echo '<plan_json>' | python3 dag.py --all
"""

from __future__ import annotations

import json
import sys
import os
from typing import Optional

# Add parent dir to path so we can import task_schema
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from task_schema import TaskPlan, TaskDefinition, topological_layers, TaskStatus


# ── Color & Style Constants ──────────────────────────────────────────────────

class Colors:
    """ANSI escape codes for terminal styling."""
    RESET = "\033[0m"
    BOLD = "\033[1m"
    DIM = "\033[2m"
    RED = "\033[31m"
    GREEN = "\033[32m"
    YELLOW = "\033[33m"
    BLUE = "\033[34m"
    MAGENTA = "\033[35m"
    CYAN = "\033[36m"
    WHITE = "\033[37m"
    BG_GREEN = "\033[42m"
    BG_YELLOW = "\033[43m"
    BG_RED = "\033[41m"
    BG_BLUE = "\033[44m"

    @staticmethod
    def supports_color() -> bool:
        """Check if terminal supports color output."""
        if not sys.stdout.isatty():
            return False
        term = os.environ.get("TERM", "")
        if term == "dumb":
            return False
        return True


C = Colors

# Disable colors if terminal doesn't support them
if not C.supports_color():
    for attr in dir(C):
        if not attr.startswith("_") and isinstance(getattr(C, attr), str):
            setattr(C, attr, "")


# Import icons from task_schema
from task_schema import STATUS_ICONS, AGENT_ICONS

PRIORITY_COLORS = {
    "critical": C.RED,
    "high": C.YELLOW,
    "medium": C.CYAN,
    "low": C.DIM,
}


# ── Mermaid Generator ────────────────────────────────────────────────────────

def generate_mermaid(plan: TaskPlan, results: Optional[dict] = None) -> str:
    """
    Generate a Mermaid flowchart from a task plan.
    Optionally overlay task statuses from results dict.
    """
    lines = ["```mermaid", "flowchart TD"]
    lines.append(f"  GOAL[\"🎯 {_escape_mermaid(plan.goal)}\"]")
    lines.append("  GOAL ~~~ L0")

    layers = topological_layers(plan.tasks)
    task_map = {t.id: t for t in plan.tasks}

    # Style each layer as a subgraph
    for layer_idx, layer in enumerate(layers):
        lines.append(f"  subgraph L{layer_idx}[\"Layer {layer_idx}\"]")
        for tid in layer:
            task = task_map.get(tid)
            if not task:
                continue
            icon = AGENT_ICONS.get(task.agent, "📌")
            status_suffix = ""
            if results and tid in results:
                status_icon = STATUS_ICONS.get(results[tid].status, "")
                status_suffix = f" {status_icon}"
            lines.append(f"    {tid}[\"{icon} {task.title}{status_suffix}\"]")
        lines.append("  end")

    # Add dependency edges
    for task in plan.tasks:
        for dep in task.dependencies:
            style = ""
            if results:
                dep_status = results.get(dep, None)
                if dep_status and dep_status.status == TaskStatus.COMPLETED.value:
                    style = ":::completed"
                elif dep_status and dep_status.status == TaskStatus.FAILED.value:
                    style = ":::failed"
            lines.append(f"  {dep} --> {task.id}{style}")

    # Add style definitions
    lines.append("")
    lines.append("  classDef completed stroke:#4CAF50,stroke-width:2px")
    lines.append("  classDef failed stroke:#F44336,stroke-width:2px,stroke-dasharray: 5 5")
    lines.append("  classDef inprogress stroke:#FF9800,stroke-width:2px")

    # Apply styles based on results
    if results:
        for tid, result in results.items():
            if result.status == TaskStatus.COMPLETED.value:
                lines.append(f"  class {tid} completed")
            elif result.status == TaskStatus.FAILED.value:
                lines.append(f"  class {tid} failed")
            elif result.status == TaskStatus.IN_PROGRESS.value:
                lines.append(f"  class {tid} inprogress")

    lines.append("```")
    return "\n".join(lines)


def _escape_mermaid(text: str) -> str:
    """Escape special characters for Mermaid."""
    return text.replace('"', '&quot;').replace("[", "&#91;").replace("]", "&#93;")


# ── ASCII Visualizer ─────────────────────────────────────────────────────────

def generate_ascii(plan: TaskPlan, results: Optional[dict] = None) -> str:
    """
    Generate a beautiful ASCII-art layered view of the DAG.
    With status overlay if results provided.
    """
    lines = []
    width = 80

    # Header
    lines.append("")
    lines.append(f"{C.BOLD}{C.CYAN}╔{'═' * (width - 2)}╗{C.RESET}")
    title = f"🎯  WORKFLOW: {plan.goal}"
    if len(title) > width - 4:
        title = title[:width - 7] + "..."
    lines.append(f"{C.BOLD}{C.CYAN}║{C.RESET} {title}{' ' * (width - len(title) - 3)}{C.BOLD}{C.CYAN}║{C.RESET}")
    lines.append(f"{C.BOLD}{C.CYAN}╠{'═' * (width - 2)}╣{C.RESET}")

    # Stats row (if results)
    if results:
        completed = sum(1 for r in results.values() if r.status == TaskStatus.COMPLETED.value)
        failed = sum(1 for r in results.values() if r.status == TaskStatus.FAILED.value)
        in_prog = sum(1 for r in results.values() if r.status == TaskStatus.IN_PROGRESS.value)
        pending = sum(1 for r in results.values() if r.status == TaskStatus.PENDING.value)
        total = len(results)
        pct = round((completed / total * 100)) if total > 0 else 0

        stat_line = f"  {C.GREEN}✅ {completed}{C.RESET} completed  {C.YELLOW}🔄 {in_prog}{C.RESET} running  {C.DIM}⬜ {pending}{C.RESET} pending  {C.RED}❌ {failed}{C.RESET} failed  "
        lines.append(f"{C.BOLD}{C.CYAN}║{C.RESET}{stat_line}{' ' * (width - len(stat_line) - 2)}{C.BOLD}{C.CYAN}║{C.RESET}")

        # Progress bar
        bar_width = width - 10
        filled = int(bar_width * pct / 100)
        bar = "█" * filled + "░" * (bar_width - filled)
        bar_line = f"  [{C.GREEN}{bar}{C.RESET}] {pct}%"
        lines.append(f"{C.BOLD}{C.CYAN}║{C.RESET}{bar_line}{' ' * (width - len(bar_line) - 2)}{C.BOLD}{C.CYAN}║{C.RESET}")

        lines.append(f"{C.BOLD}{C.CYAN}╠{'─' * (width - 2)}╣{C.RESET}")

    # Layers
    layers = topological_layers(plan.tasks)
    task_map = {t.id: t for t in plan.tasks}

    for layer_idx, layer in enumerate(layers):
        # Layer header
        layer_label = f"  Layer {layer_idx} "
        lines.append(f"{C.BOLD}{C.CYAN}║{C.RESET} {C.BOLD}{layer_label}{'─' * (width - len(layer_label) - 4)}{C.RESET} {C.BOLD}{C.CYAN}║{C.RESET}")

        for tid in layer:
            task = task_map.get(tid)
            if not task:
                continue

            agent_icon = AGENT_ICONS.get(task.agent, "📌")
            status_icon = "  "
            status_color = C.RESET

            if results and tid in results:
                result = results[tid]
                status_icon = STATUS_ICONS.get(result.status, "  ")
                if result.status == TaskStatus.COMPLETED.value:
                    status_color = C.GREEN
                elif result.status == TaskStatus.IN_PROGRESS.value:
                    status_color = C.YELLOW
                elif result.status == TaskStatus.FAILED.value:
                    status_color = C.RED
                elif result.status == TaskStatus.BLOCKED.value:
                    status_color = C.RED

            # Task line
            priority_color = PRIORITY_COLORS.get(task.priority, "")
            task_line = f"  {status_color}{status_icon}{C.RESET} {agent_icon} {priority_color}[{task.id}]{C.RESET} {task.title}"

            # Dependencies indicator
            if task.dependencies:
                deps_str = " ← " + ", ".join(task.dependencies)
                if len(task_line) + len(deps_str) > width - 4:
                    deps_str = " ← ..."
                task_line += f"{C.DIM}{deps_str}{C.RESET}"

            lines.append(f"{C.BOLD}{C.CYAN}║{C.RESET} {task_line}{' ' * (width - len(task_line) - 3)}{C.BOLD}{C.CYAN}║{C.RESET}")

        # Separator between layers
        if layer_idx < len(layers) - 1:
            lines.append(f"{C.BOLD}{C.CYAN}║{C.RESET} {'↓':^{width - 2}}{C.BOLD}{C.CYAN}║{C.RESET}")

    # Footer
    lines.append(f"{C.BOLD}{C.CYAN}╚{'═' * (width - 2)}╝{C.RESET}")
    lines.append(f"{C.DIM}  {len(plan.tasks)} tasks in {len(layers)} layers{C.RESET}")
    lines.append("")

    return "\n".join(lines)


# ── CLI ──────────────────────────────────────────────────────────────────────

def main():
    import argparse
    parser = argparse.ArgumentParser(
        description="DAG Builder & Visualizer for Workflow Orchestrator"
    )
    parser.add_argument("--mermaid", action="store_true", help="Output Mermaid flowchart")
    parser.add_argument("--ascii", action="store_true", help="Output ASCII layered view")
    parser.add_argument("--layers", action="store_true", help="Output JSON layers array")
    parser.add_argument("--all", action="store_true", help="Output all formats")
    parser.add_argument("--results", type=str, help="Path to results JSON file for status overlay")
    args = parser.parse_args()

    # Read plan from stdin
    try:
        raw = sys.stdin.read()
        data = json.loads(raw)
    except (json.JSONDecodeError, EOFError) as e:
        print(f"❌ Invalid input: {e}", file=sys.stderr)
        sys.exit(1)

    plan = TaskPlan.from_dict(data)

    # Load results if provided
    results = None
    if args.results:
        try:
            with open(args.results) as f:
                from task_schema import TaskResult
                results_data = json.load(f)
                results = {
                    k: TaskResult.from_dict(v)
                    for k, v in results_data.get("results", {}).items()
                }
        except (FileNotFoundError, json.JSONDecodeError) as e:
            print(f"⚠️  Could not load results: {e}", file=sys.stderr)

    # Default to --all if no flag given
    if not (args.mermaid or args.ascii or args.layers):
        args.all = True

    if args.mermaid or args.all:
        print(generate_mermaid(plan, results))
        if args.all:
            print("")

    if args.ascii or args.all:
        print(generate_ascii(plan, results))

    if args.layers:
        layers = topological_layers(plan.tasks)
        print(json.dumps({"layers": [[tid for tid in layer] for layer in layers]}))


if __name__ == "__main__":
    main()
