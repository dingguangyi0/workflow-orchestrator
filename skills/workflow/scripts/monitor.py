#!/usr/bin/env python3
"""
Workflow Orchestrator — Real-Time Progress Monitor

A visual dashboard that displays workflow progress in real-time.
Designed to be called by the main Claude instance at each progress check,
or run as a background watcher that polls the workflow state file.

Features:
  - Color-coded progress bars (█ = completed, ▒ = in progress, ░ = pending, ▓ = failed)
  - Per-task status with spinners for running tasks
  - Overall completion percentage
  - DAG visualization with status overlays
  - Estimated time remaining

Usage:
  # One-shot display (read state from stdin):
  echo '<workflow_state_json>' | python3 monitor.py

  # Watch mode (poll a state file):
  python3 monitor.py --watch /tmp/workflow_state.json --interval 5

  # Generate a compact status line (for inline display):
  echo '<workflow_state_json>' | python3 monitor.py --compact

Output format mimics Claude Code's Dynamic Workflows terminal UI.
"""

from __future__ import annotations

import json
import os
import sys
import time
from datetime import datetime, timezone
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from task_schema import (
    WorkflowState, TaskPlan, TaskResult, TaskStatus, TaskDefinition,
    topological_layers, STATUS_ICONS, AGENT_ICONS,
)
from term_utils import Term, strip_ansi


# ── Dashboard Renderer ───────────────────────────────────────────────────────

def render_dashboard(state: WorkflowState, compact: bool = False) -> str:
    """
    Render the full monitoring dashboard.
    This is the main visual output — designed to look like Claude Code's
    Dynamic Workflows progress view.
    """
    if compact:
        return _render_compact(state)

    lines = []
    plan = state.plan
    results = state.results
    total = state.total_count
    width = 78

    # ═══════════ Header ═══════════
    lines.append("")
    lines.append(f"{Term.BOLD}{Term.CYAN}╔{'═' * (width - 2)}╗{Term.RESET}")

    # Title
    goal_text = plan.goal if plan else "Workflow in progress..."
    title = f"⚡ DYNAMIC WORKFLOW"
    padding = width - len(title) - 2
    lines.append(f"{Term.BOLD}{Term.CYAN}║{Term.RESET} {Term.BOLD}{Term.YELLOW}{title}{Term.RESET}{' ' * padding}{Term.BOLD}{Term.CYAN}║{Term.RESET}")

    # Goal
    goal_display = f"🎯 {goal_text[:width - 8]}"
    lines.append(f"{Term.BOLD}{Term.CYAN}║{Term.RESET} {goal_display}{' ' * (width - len(goal_display) - 2)}{Term.BOLD}{Term.CYAN}║{Term.RESET}")

    lines.append(f"{Term.BOLD}{Term.CYAN}╠{'═' * (width - 2)}╣{Term.RESET}")

    # ── Stats Row ──
    completed = state.completed_count
    failed = state.failed_count
    in_prog = state.in_progress_count
    pending = state.pending_count
    skipped = sum(1 for r in results.values() if r.status == TaskStatus.SKIPPED.value)

    stat_parts = [
        f"{Term.GREEN}✅ {completed} done{Term.RESET}",
        f"{Term.YELLOW}🔄 {in_prog} running{Term.RESET}",
        f"{Term.GRAY}⬜ {pending} pending{Term.RESET}",
        f"{Term.RED}❌ {failed} failed{Term.RESET}",
    ]
    if skipped > 0:
        stat_parts.append(f"{Term.DIM}⏭️ {skipped} skipped{Term.RESET}")

    stat_line = "  ".join(stat_parts)
    lines.append(f"{Term.BOLD}{Term.CYAN}║{Term.RESET}  {stat_line}{' ' * (width - len(stat_line) - 4)}{Term.BOLD}{Term.CYAN}║{Term.RESET}")

    # ── Progress Bar ──
    bar_width = width - 10
    if total > 0:
        filled_done = int(bar_width * completed / total)
        filled_prog = int(bar_width * in_prog / total)
        filled_fail = int(bar_width * failed / total)
        filled_skip = int(bar_width * skipped / total)
        empty = bar_width - filled_done - filled_prog - filled_fail - filled_skip

        bar = (
            f"{Term.BG_GREEN}{' ' * filled_done}{Term.RESET}"
            f"{Term.BG_YELLOW}{' ' * filled_prog}{Term.RESET}"
            f"{Term.BG_RED}{' ' * filled_fail}{Term.RESET}"
            f"{Term.DIM}{'░' * empty}{Term.RESET}"
        )
        pct = round((completed + skipped) / total * 100)
        bar_line = f"  {bar} {pct}%"
        lines.append(f"{Term.BOLD}{Term.CYAN}║{Term.RESET}{bar_line}{' ' * (width - len(bar_line) - 2)}{Term.BOLD}{Term.CYAN}║{Term.RESET}")

    lines.append(f"{Term.BOLD}{Term.CYAN}╠{'─' * (width - 2)}╣{Term.RESET}")

    # ── Phase Indicator ──
    phase_map = {
        "init": "🚀 Initializing...",
        "planning": "🧠 Planning — decomposing goal...",
        "executing": f"⚡ Executing — Layer {state.current_layer + 1}/{state.total_layers}",
        "handling_failures": "🔧 Handling failures — retrying...",
        "aggregating": "📊 Aggregating results...",
        "done": "✅ Complete",
    }
    phase_text = phase_map.get(state.phase, state.phase)
    lines.append(f"{Term.BOLD}{Term.CYAN}║{Term.RESET}  {Term.BOLD}Phase:{Term.RESET} {phase_text}{' ' * (width - len(phase_text) - 11)}{Term.BOLD}{Term.CYAN}║{Term.RESET}")
    lines.append(f"{Term.BOLD}{Term.CYAN}╠{'─' * (width - 2)}╣{Term.RESET}")

    # ── Task List ──
    layers = topological_layers(plan.tasks) if plan else []
    task_map = {t.id: t for t in plan.tasks} if plan else {}

    for layer_idx, layer in enumerate(layers):
        # Only show current and upcoming layers
        is_current = layer_idx == state.current_layer
        is_past = layer_idx < state.current_layer
        is_future = layer_idx > state.current_layer

        layer_marker = f"{'✅' if is_past else '⚡' if is_current else '📋'} Layer {layer_idx}"
        if is_current:
            layer_marker = f"{Term.BOLD}{Term.YELLOW}{layer_marker}{Term.RESET}"
        elif is_past:
            layer_marker = f"{Term.DIM}{layer_marker}{Term.RESET}"
        else:
            layer_marker = f"{Term.GRAY}{layer_marker}{Term.RESET}"

        lines.append(f"{Term.BOLD}{Term.CYAN}║{Term.RESET}  {layer_marker}{' ' * (width - len(layer_marker) - 4)}{Term.BOLD}{Term.CYAN}║{Term.RESET}")

        for tid in layer:
            task = task_map.get(tid)
            result = results.get(tid)
            if not task:
                continue

            agent_icon = AGENT_ICONS.get(task.agent, "📌")

            if result:
                status = result.status
                if status == TaskStatus.COMPLETED.value:
                    icon = f"{Term.GREEN}✅{Term.RESET}"
                    task_color = Term.GREEN
                elif status == TaskStatus.IN_PROGRESS.value:
                    icon = f"{Term.YELLOW}{Term.spinner()}{Term.RESET}"
                    task_color = Term.YELLOW
                elif status == TaskStatus.FAILED.value:
                    icon = f"{Term.RED}❌{Term.RESET}"
                    task_color = Term.RED
                elif status == TaskStatus.BLOCKED.value:
                    icon = f"{Term.RED}🚫{Term.RESET}"
                    task_color = Term.RED
                elif status == TaskStatus.SKIPPED.value:
                    icon = f"{Term.DIM}⏭️{Term.RESET}"
                    task_color = Term.DIM
                else:
                    icon = f"{Term.GRAY}⬜{Term.RESET}"
                    task_color = Term.GRAY
            else:
                icon = f"{Term.GRAY}⬜{Term.RESET}"
                task_color = Term.GRAY

            # Task line
            tid_formatted = f"{Term.DIM}[{tid}]{Term.RESET}"
            deps = f" {Term.DIM}← {', '.join(task.dependencies)}{Term.RESET}" if task.dependencies else ""

            task_line = f"     {icon} {agent_icon} {tid_formatted} {task_color}{task.title}{Term.RESET}{deps}"
            # Truncate if too long
            if len(strip_ansi(task_line)) > width - 4:
                max_title = width - len(strip_ansi(f"     {icon} {agent_icon} {tid_formatted} {deps}")) - 6
                task_line = f"     {icon} {agent_icon} {tid_formatted} {task_color}{task.title[:max_title]}...{Term.RESET}{deps}"

            lines.append(f"{Term.BOLD}{Term.CYAN}║{Term.RESET}{task_line}{' ' * (width - len(strip_ansi(task_line)) - 2)}{Term.BOLD}{Term.CYAN}║{Term.RESET}")

            # Show error for failed tasks
            if result and result.status == TaskStatus.FAILED.value and result.error_message:
                err = result.error_message[:width - 10].replace('\n', ' ')
                err_line = f"     {Term.RED}└─ {err}{Term.RESET}"
                lines.append(f"{Term.BOLD}{Term.CYAN}║{Term.RESET}{err_line}{' ' * (width - len(strip_ansi(err_line)) - 2)}{Term.BOLD}{Term.CYAN}║{Term.RESET}")

    # ── Empty space filler ──
    lines.append(f"{Term.BOLD}{Term.CYAN}║{Term.RESET}{' ' * (width - 2)}{Term.BOLD}{Term.CYAN}║{Term.RESET}")

    # Footer
    pct = round((completed + skipped) / total * 100) if total > 0 else 0
    footer = f"  {pct}% complete • {completed}/{total} tasks done • {in_prog} running"
    lines.append(f"{Term.BOLD}{Term.CYAN}╠{'═' * (width - 2)}╣{Term.RESET}")
    lines.append(f"{Term.BOLD}{Term.CYAN}║{Term.RESET} {Term.BOLD}{footer}{Term.RESET}{' ' * (width - len(footer) - 3)}{Term.BOLD}{Term.CYAN}║{Term.RESET}")
    lines.append(f"{Term.BOLD}{Term.CYAN}╚{'═' * (width - 2)}╝{Term.RESET}")
    lines.append("")

    return "\n".join(lines)


def _render_compact(state: WorkflowState) -> str:
    """Render a compact one-line status for inline display."""
    total = state.total_count
    completed = state.completed_count
    failed = state.failed_count
    in_prog = state.in_progress_count
    pct = round((completed / total * 100)) if total > 0 else 0

    bar_width = 20
    filled = int(bar_width * completed / total) if total > 0 else 0
    in_prog_fill = int(bar_width * in_prog / total) if total > 0 else 0
    empty = bar_width - filled - in_prog_fill

    bar = f"{Term.BG_GREEN}{' ' * filled}{Term.RESET}{Term.BG_YELLOW}{' ' * in_prog_fill}{Term.RESET}{Term.DIM}{'░' * empty}{Term.RESET}"

    parts = [
        f"⚡ WF",
        f"[{bar}]",
        f"{pct}%",
        f"{Term.GREEN}✅{completed}{Term.RESET}",
        f"{Term.YELLOW}🔄{in_prog}{Term.RESET}",
        f"{Term.RED}❌{failed}{Term.RESET}" if failed > 0 else "",
    ]
    return " ".join(p for p in parts if p)


# ── CLI ──────────────────────────────────────────────────────────────────────

def main():
    import argparse
    parser = argparse.ArgumentParser(
        description="Real-Time Workflow Progress Monitor"
    )
    parser.add_argument("--watch", type=str, help="Watch a state JSON file (polling mode)")
    parser.add_argument("--interval", type=int, default=5, help="Poll interval in seconds (default: 5)")
    parser.add_argument("--compact", action="store_true", help="Compact one-line output")
    parser.add_argument("--once", action="store_true", help="Render once and exit (for watch mode)")
    args = parser.parse_args()

    if args.watch:
        _watch_mode(args.watch, args.interval, args.compact, args.once)
    else:
        _oneshot(args.compact)


def _load_state(raw: str) -> Optional[WorkflowState]:
    """Parse workflow state from JSON string."""
    try:
        data = json.loads(raw)
    except (json.JSONDecodeError, ValueError):
        return None

    try:
        plan = TaskPlan.from_dict(data.get("plan", {})) if data.get("plan") else None
        results = {
            k: TaskResult.from_dict(v)
            for k, v in data.get("results", {}).items()
        }
        return WorkflowState(
            plan=plan,
            results=results,
            current_layer=data.get("current_layer", 0),
            total_layers=data.get("total_layers", 0),
            phase=data.get("phase", "init"),
        )
    except Exception:
        return None


def _oneshot(compact: bool):
    """Read state from stdin and render once."""
    try:
        raw = sys.stdin.read()
    except EOFError:
        print("❌ No input provided", file=sys.stderr)
        sys.exit(1)

    state = _load_state(raw)
    if state is None:
        print("❌ Invalid workflow state JSON", file=sys.stderr)
        sys.exit(1)

    if compact:
        print(_render_compact(state))
    else:
        print(render_dashboard(state))


def _watch_mode(filepath: str, interval: int, compact: bool, once: bool):
    """Poll a state file and refresh the dashboard."""
    print(Term.HIDE_CURSOR, end="", flush=True)

    try:
        while True:
            try:
                with open(filepath, "r") as f:
                    raw = f.read()
            except FileNotFoundError:
                print(Term.CLEAR_SCREEN + Term.MOVE_HOME, end="")
                print(f"{Term.YELLOW}⏳ Waiting for workflow state file...{Term.RESET}")
                time.sleep(interval)
                continue

            state = _load_state(raw)
            if state is None:
                time.sleep(interval)
                continue

            # Clear and re-render
            print(Term.CLEAR_SCREEN + Term.MOVE_HOME, end="")
            if compact:
                print(_render_compact(state), end="\r")
            else:
                print(render_dashboard(state))

            if once or state.phase == "done":
                break

            if state.phase == "done":
                break

            time.sleep(interval)
    finally:
        print(Term.SHOW_CURSOR, end="", flush=True)


if __name__ == "__main__":
    main()
