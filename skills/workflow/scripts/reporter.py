#!/usr/bin/env python3
"""
Workflow Orchestrator — Result Reporter

Generates a comprehensive Markdown report from workflow execution results.
Used in Phase 6 (Result Aggregation) of the orchestration protocol.

Usage:
  echo '<workflow_state_json>' | python3 reporter.py --full
  echo '<workflow_state_json>' | python3 reporter.py --summary
  echo '<workflow_state_json>' | python3 reporter.py --json
"""

from __future__ import annotations

import json
import sys
import os
from datetime import datetime, timezone
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from task_schema import (
    WorkflowState, TaskPlan, TaskResult, TaskStatus,
    topological_layers, STATUS_ICONS, AGENT_ICONS,
)


from term_utils import Term as C


# ── Report Generation ────────────────────────────────────────────────────────

def generate_full_report(state: WorkflowState) -> str:
    """Generate a comprehensive Markdown report."""
    lines = []
    plan = state.plan
    results = state.results

    # ── Header ──
    lines.append("")
    lines.append("# 📊 Workflow Execution Report")
    lines.append("")
    if plan:
        lines.append(f"**Goal:** {plan.goal}")
        lines.append(f"**Type:** {plan.goal_type} | **Started:** {_format_time(plan.created_at)}")
    lines.append(f"**Completed:** {_format_time(datetime.now(timezone.utc).isoformat())}")
    lines.append("")

    # ── Executive Summary ──
    lines.append("## 📈 Executive Summary")
    lines.append("")
    total = state.total_count
    completed = state.completed_count
    failed = state.failed_count
    skipped = sum(1 for r in results.values() if r.status == TaskStatus.SKIPPED.value)
    success_rate = round((completed + skipped) / total * 100) if total > 0 else 0

    lines.append(f"| Metric | Value |")
    lines.append(f"|--------|-------|")
    lines.append(f"| Total Tasks | {total} |")
    lines.append(f"| ✅ Completed | {completed} |")
    lines.append(f"| ❌ Failed | {failed} |")
    lines.append(f"| ⏭️ Skipped | {skipped} |")
    lines.append(f"| Success Rate | {success_rate}% |")
    lines.append("")

    # Progress bar
    bar_width = 40
    filled = int(bar_width * state.progress_pct / 100)
    bar = "█" * filled + "░" * (bar_width - filled)
    lines.append(f"```")
    lines.append(f"Progress: [{bar}] {state.progress_pct:.0f}%")
    lines.append(f"```")
    lines.append("")

    # ── Overall Verdict ──
    if failed == 0:
        lines.append(f"### 🎉 Verdict: ALL TASKS COMPLETED SUCCESSFULLY")
    elif failed <= total * 0.3:
        lines.append(f"### ⚠️ Verdict: PARTIAL SUCCESS — {failed} task(s) failed, see details below")
    else:
        lines.append(f"### ❌ Verdict: SIGNIFICANT FAILURES — {failed}/{total} tasks failed")
    lines.append("")

    # ── Task Timeline ──
    lines.append("## ⏱️ Task Execution Timeline")
    lines.append("")

    layers = topological_layers(plan.tasks) if plan else []
    task_map = {t.id: t for t in plan.tasks} if plan else {}

    for layer_idx, layer in enumerate(layers):
        lines.append(f"### Layer {layer_idx}")
        lines.append("")
        lines.append(f"| Status | ID | Task | Agent | Duration |")
        lines.append(f"|--------|-----|------|-------|----------|")
        for tid in layer:
            task = task_map.get(tid)
            result = results.get(tid)
            if not task or not result:
                continue

            status_icon = STATUS_ICONS.get(result.status, "⬜")
            agent_icon = AGENT_ICONS.get(task.agent, "📌")

            # Calculate duration
            duration = "—"
            if result.started_at and result.completed_at:
                try:
                    start = datetime.fromisoformat(result.started_at)
                    end = datetime.fromisoformat(result.completed_at)
                    seconds = (end - start).total_seconds()
                    if seconds < 60:
                        duration = f"{seconds:.0f}s"
                    else:
                        duration = f"{seconds/60:.1f}m"
                except (ValueError, TypeError):
                    pass

            lines.append(f"| {status_icon} | `{tid}` | {agent_icon} {task.title} | {task.agent} | {duration} |")
        lines.append("")

    # ── Task Details ──
    lines.append("## 📋 Task Details")
    lines.append("")

    for layer_idx, layer in enumerate(layers):
        for tid in layer:
            task = task_map.get(tid)
            result = results.get(tid)
            if not task or not result:
                continue

            status_icon = STATUS_ICONS.get(result.status, "⬜")
            lines.append(f"### {status_icon} {tid}: {task.title}")
            lines.append("")
            lines.append(f"- **Agent:** {task.agent}")
            lines.append(f"- **Priority:** {task.priority}")
            lines.append(f"- **Dependencies:** {task.dependencies or 'none'}")
            lines.append(f"- **Status:** {result.status}")

            if result.output_summary:
                lines.append("")
                lines.append("**Output:**")
                lines.append(f"> {result.output_summary[:500]}")

            if result.error_message:
                lines.append("")
                lines.append(f"**Error:**")
                lines.append(f"```")
                lines.append(result.error_message[:300])
                lines.append(f"```")

            if result.retry_count > 0:
                lines.append(f"- **Retries:** {result.retry_count}/{result.max_retries}")

            lines.append("")

    # ── Recommendations ──
    if failed > 0:
        lines.append("## 💡 Recommendations")
        lines.append("")
        lines.append("The following tasks failed. Consider:")
        lines.append("")
        for tid, result in results.items():
            if result.status == TaskStatus.FAILED.value:
                task = task_map.get(tid)
                task_name = task.title if task else tid
                lines.append(f"- **{tid} ({task_name}):** {result.error_message[:100] or 'No error details'}")
        lines.append("")
        lines.append("1. Check error messages above for root causes")
        lines.append("2. Fix underlying issues and re-run the failed tasks")
        lines.append("3. Consider increasing max_retries or adjusting task scope")
        lines.append("")

    # ── Files Changed (if any implementer tasks) ──
    impl_tasks = [t for t in (plan.tasks if plan else []) if t.agent == "implementer"]
    if impl_tasks:
        lines.append("## 📁 Files Modified")
        lines.append("")
        lines.append("The following tasks involved code changes. Review the agent outputs above for specific file lists.")
        lines.append("")
        for t in impl_tasks:
            result = results.get(t.id)
            if result and result.status == TaskStatus.COMPLETED.value:
                lines.append(f"- ✅ `{t.id}`: {t.title}")
        lines.append("")

    lines.append("---")
    lines.append(f"*Report generated by Workflow Orchestrator at {datetime.now(timezone.utc).isoformat()}*")
    lines.append("")

    return "\n".join(lines)


def generate_summary(state: WorkflowState) -> str:
    """Generate a short summary (for inline display)."""
    plan = state.plan
    results = state.results
    total = state.total_count
    completed = state.completed_count
    failed = state.failed_count
    in_prog = state.in_progress_count

    lines = []
    lines.append("")
    lines.append(f"{C.BOLD}📊 Workflow Summary{C.RESET}")
    if plan:
        lines.append(f"   Goal: {plan.goal[:80]}")
    lines.append(f"   {C.GREEN}✅ {completed}{C.RESET} / {C.YELLOW}🔄 {in_prog}{C.RESET} / {C.RED}❌ {failed}{C.RESET} / Total: {total}")
    bar_width = 30
    filled = int(bar_width * state.progress_pct / 100) if total > 0 else 0
    bar = f"{C.GREEN}{'█' * filled}{C.DIM}{'░' * (bar_width - filled)}{C.RESET}"
    lines.append(f"   [{bar}] {state.progress_pct:.0f}%")

    if failed > 0:
        lines.append(f"   {C.YELLOW}⚠ {failed} task(s) failed — see /workflow report for details{C.RESET}")
    elif completed == total:
        lines.append(f"   {C.GREEN}🎉 All tasks completed!{C.RESET}")

    lines.append("")
    return "\n".join(lines)


def _format_time(iso_string: str) -> str:
    """Format ISO time string to human-readable."""
    if not iso_string:
        return "unknown"
    try:
        dt = datetime.fromisoformat(iso_string)
        return dt.strftime("%Y-%m-%d %H:%M:%S")
    except (ValueError, TypeError):
        return iso_string[:19]


# ── CLI ──────────────────────────────────────────────────────────────────────

def main():
    import argparse
    parser = argparse.ArgumentParser(description="Workflow Result Reporter")
    parser.add_argument("--full", action="store_true", help="Generate full Markdown report")
    parser.add_argument("--summary", action="store_true", help="Generate short summary")
    parser.add_argument("--json", action="store_true", help="Output state as formatted JSON")
    args = parser.parse_args()

    try:
        raw = sys.stdin.read()
        data = json.loads(raw)
    except (json.JSONDecodeError, EOFError) as e:
        print(f"❌ Invalid input: {e}", file=sys.stderr)
        sys.exit(1)

    # Reconstruct WorkflowState from dict
    plan = TaskPlan.from_dict(data.get("plan", {})) if data.get("plan") else None
    results = {
        k: TaskResult.from_dict(v)
        for k, v in data.get("results", {}).items()
    }
    state = WorkflowState(
        plan=plan,
        results=results,
        current_layer=data.get("current_layer", 0),
        total_layers=data.get("total_layers", 0),
        phase=data.get("phase", "done"),
    )

    if args.json:
        print(json.dumps(state.to_dict(), indent=2))
    elif args.summary:
        print(generate_summary(state))
    else:
        # Default to full report
        print(generate_full_report(state))


if __name__ == "__main__":
    main()
