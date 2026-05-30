#!/usr/bin/env python3
"""
Workflow Orchestrator — Workflow Manager
Handles template save/load, checkpoint/resume, and workflow lifecycle.

Usage:
  # Save current plan as template
  python3 workflow_manager.py --save my-template --plan plan.json

  # List saved templates
  python3 workflow_manager.py --list

  # Load template
  python3 workflow_manager.py --load my-template

  # Resume from checkpoint
  python3 workflow_manager.py --resume /tmp/claude-workflow-session/state.json

  # Initialize from template
  python3 workflow_manager.py --from-template my-template --goal "custom goal"
"""

from __future__ import annotations

import json
import os
import sys
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from task_schema import TaskPlan, WorkflowState, TaskResult, TaskStatus, topological_layers

TEMPLATES_DIR = os.path.expanduser("~/.claude/workflows/templates")
WORKFLOWS_DIR = os.path.expanduser("~/.claude/workflows")
CHECKPOINT_DIR = os.path.expanduser("~/.claude/workflows/checkpoints")


def ensure_dirs():
    for d in [TEMPLATES_DIR, CHECKPOINT_DIR]:
        os.makedirs(d, exist_ok=True)


def save_template(name: str, plan_json: dict) -> str:
    """Save a task plan as a reusable template."""
    ensure_dirs()
    template = {
        "name": name,
        "saved_at": datetime.now(timezone.utc).isoformat(),
        "plan": plan_json,
        "usage_count": 0,
    }
    filepath = os.path.join(TEMPLATES_DIR, f"{name}.json")
    with open(filepath, "w") as f:
        json.dump(template, f, indent=2)
    return filepath


def list_templates() -> list[dict]:
    """List all saved templates."""
    ensure_dirs()
    templates = []
    if not os.path.exists(TEMPLATES_DIR):
        return templates
    for fname in sorted(os.listdir(TEMPLATES_DIR)):
        if fname.endswith(".json"):
            try:
                with open(os.path.join(TEMPLATES_DIR, fname)) as f:
                    t = json.load(f)
                    templates.append({
                        "name": t.get("name", fname[:-5]),
                        "saved_at": t.get("saved_at", ""),
                        "goal": t.get("plan", {}).get("goal", ""),
                        "task_count": len(t.get("plan", {}).get("tasks", [])),
                        "usage_count": t.get("usage_count", 0),
                    })
            except (json.JSONDecodeError, KeyError):
                pass
    return templates


def load_template(name: str) -> Optional[dict]:
    """Load a template by name."""
    filepath = os.path.join(TEMPLATES_DIR, f"{name}.json")
    if not os.path.exists(filepath):
        return None
    with open(filepath) as f:
        template = json.load(f)
    # Increment usage
    template["usage_count"] = template.get("usage_count", 0) + 1
    with open(filepath, "w") as f:
        json.dump(template, f, indent=2)
    return template["plan"]


def customize_template(plan: dict, goal: str, substitutions: Optional[dict] = None) -> dict:
    """Customize a template plan with a new goal and optional substitutions."""
    plan["goal"] = goal
    plan["created_at"] = datetime.now(timezone.utc).isoformat()
    if substitutions:
        # Apply text substitutions to all task fields
        for task in plan.get("tasks", []):
            for field in ["title", "description", "expected_output"]:
                if field in task:
                    for old, new in substitutions.items():
                        task[field] = task[field].replace(old, new)
    return plan


def save_checkpoint(state_json: dict, label: str = "") -> str:
    """Save a workflow state checkpoint."""
    ensure_dirs()
    ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    fname = f"checkpoint_{ts}_{label}.json" if label else f"checkpoint_{ts}.json"
    filepath = os.path.join(CHECKPOINT_DIR, fname)
    state_json["checkpoint_label"] = label
    state_json["checkpoint_at"] = datetime.now(timezone.utc).isoformat()
    with open(filepath, "w") as f:
        json.dump(state_json, f, indent=2)
    return filepath


def list_checkpoints() -> list[dict]:
    """List recent checkpoints."""
    ensure_dirs()
    checkpoints = []
    if not os.path.exists(CHECKPOINT_DIR):
        return checkpoints
    for fname in sorted(os.listdir(CHECKPOINT_DIR), reverse=True)[:20]:
        if fname.endswith(".json"):
            try:
                with open(os.path.join(CHECKPOINT_DIR, fname)) as f:
                    c = json.load(f)
                    plan = c.get("plan", {})
                    stats = c.get("stats", {})
                    checkpoints.append({
                        "file": fname,
                        "label": c.get("checkpoint_label", ""),
                        "at": c.get("checkpoint_at", ""),
                        "goal": plan.get("goal", "")[:80],
                        "progress": f"{stats.get('progress_pct', 0):.0f}%",
                        "completed": stats.get("completed", 0),
                        "total": stats.get("total", 0),
                        "phase": c.get("phase", ""),
                    })
            except (json.JSONDecodeError, KeyError):
                pass
    return checkpoints


def resume_from_checkpoint(checkpoint_path: str, target_dir: str) -> Optional[dict]:
    """Resume a workflow from a checkpoint state file."""
    if not os.path.exists(checkpoint_path):
        return None

    with open(checkpoint_path) as f:
        state = json.load(f)

    # Reset in_progress tasks to pending (they didn't complete)
    for tid, result in state.get("results", {}).items():
        if result.get("status") == "in_progress":
            result["status"] = "pending"
            result["started_at"] = ""

    # Save to target workflow dir
    os.makedirs(target_dir, exist_ok=True)
    plan = state.get("plan", {})
    with open(os.path.join(target_dir, "plan.json"), "w") as f:
        json.dump(plan, f, indent=2)
    with open(os.path.join(target_dir, "state.json"), "w") as f:
        json.dump(state, f, indent=2)

    return state


def detect_interrupted_workflow(workflow_dir: str) -> Optional[dict]:
    """Check if there's an interrupted workflow to resume."""
    state_path = os.path.join(workflow_dir, "state.json")
    if not os.path.exists(state_path):
        return None
    try:
        with open(state_path) as f:
            state = json.load(f)
        phase = state.get("phase", "")
        if phase in ("executing", "handling_failures"):
            return state
    except (json.JSONDecodeError, KeyError):
        pass
    return None


# ── Pre-built Templates ─────────────────────────────────────────────────────

BUILTIN_TEMPLATES = {
    "code-review": {
        "name": "code-review",
        "description": "Comprehensive code review across multiple dimensions",
        "plan": {
            "goal": "Review code for quality, security, and performance",
            "goal_type": "development",
            "estimated_layers": 2,
            "tasks": [
                {"id": "T1", "title": "Analyze code structure and architecture", "description": "Read the codebase to understand architecture, identify key modules, and map dependencies.", "agent": "explorer", "dependencies": [], "expected_output": "Architecture overview with module map and key files", "file_patterns": [], "priority": "critical"},
                {"id": "T2", "title": "Security vulnerability scan", "description": "Review code for common vulnerabilities: injection, XSS, auth bypass, sensitive data exposure, insecure dependencies.", "agent": "explorer", "dependencies": [], "expected_output": "Security findings with severity ratings", "file_patterns": [], "priority": "critical"},
                {"id": "T3", "title": "Performance analysis", "description": "Identify performance bottlenecks: N+1 queries, unnecessary allocations, blocking operations, inefficient algorithms.", "agent": "explorer", "dependencies": [], "expected_output": "Performance issues with suggested fixes", "file_patterns": [], "priority": "high"},
                {"id": "T4", "title": "Adversarial review and cross-verification", "description": "Challenge findings from T1-T3. Try to refute each finding. Identify any missed issues. Verify suggested fixes would actually work.", "agent": "reviewer", "dependencies": ["T1", "T2", "T3"], "expected_output": "Verified findings with refutation attempts and final verdict", "file_patterns": [], "priority": "critical"},
                {"id": "T5", "title": "Generate consolidated review report", "description": "Merge T1-T4 into a single review report with prioritized action items.", "agent": "worker", "dependencies": ["T4"], "expected_output": "Final review report with severity-sorted action items", "file_patterns": [], "priority": "high"},
            ]
        }
    },
    "migration": {
        "name": "migration",
        "description": "Large-scale code migration or refactoring",
        "plan": {
            "goal": "Execute code migration with exploration, planning, and verification",
            "goal_type": "refactoring",
            "estimated_layers": 3,
            "tasks": [
                {"id": "T1", "title": "Explore current codebase structure", "description": "Map the existing codebase: entry points, key modules, dependencies, test coverage.", "agent": "explorer", "dependencies": [], "expected_output": "Complete codebase map with migration impact analysis", "file_patterns": [], "priority": "critical"},
                {"id": "T2", "title": "Research target technology and compatibility", "description": "Research the target framework/library: API differences, migration guides, known issues, community experience.", "agent": "worker", "dependencies": [], "expected_output": "Migration guide with compatibility matrix and risk assessment", "file_patterns": [], "priority": "critical"},
                {"id": "T3", "title": "Design migration strategy", "description": "Based on T1 and T2, design a phased migration plan with rollback strategy.", "agent": "worker", "dependencies": ["T1", "T2"], "expected_output": "Detailed migration plan with phases, checkpoints, and rollback steps", "file_patterns": [], "priority": "critical"},
                {"id": "T4", "title": "Execute migration - Phase 1", "description": "Implement the first phase of migration (core/infrastructure changes).", "agent": "implementer", "dependencies": ["T3"], "expected_output": "Phase 1 changes with passing existing tests", "file_patterns": [], "priority": "critical"},
                {"id": "T5", "title": "Verify migration - Phase 1", "description": "Run full test suite. Verify no regressions. Review code quality. Challenge each change.", "agent": "reviewer", "dependencies": ["T4"], "expected_output": "Verification report: test results, issues found, overall go/no-go for Phase 2", "file_patterns": [], "priority": "critical"},
            ]
        }
    },
    "deep-research": {
        "name": "deep-research",
        "description": "Mirrors Claude Code native /deep-research: parallel web research with cross-verification",
        "plan": {
            "goal": "Deep research on a topic with cross-verification",
            "goal_type": "research",
            "estimated_layers": 3,
            "tasks": [
                {"id": "T1", "title": "Research from official sources", "description": "Search official docs, whitepapers, and authoritative sources. Collect factual information.", "agent": "worker", "dependencies": [], "expected_output": "Official source findings with citations", "file_patterns": [], "priority": "critical"},
                {"id": "T2", "title": "Research from community and practice", "description": "Search blogs, forums, GitHub issues, StackOverflow. Collect practical experience and common pitfalls.", "agent": "worker", "dependencies": [], "expected_output": "Community findings with practical insights", "file_patterns": [], "priority": "critical"},
                {"id": "T3", "title": "Research competitive alternatives", "description": "Search for alternative approaches, competing tools, and comparison articles.", "agent": "worker", "dependencies": [], "expected_output": "Alternatives comparison with pros/cons", "file_patterns": [], "priority": "high"},
                {"id": "T4", "title": "Cross-verify and challenge findings", "description": "Take findings from T1-T3. Search for contradictory evidence. Try to refute each key claim. Identify any unverified assertions. Flag unsubstantiated claims.", "agent": "worker", "dependencies": ["T1", "T2", "T3"], "expected_output": "Verification report: confirmed vs challenged vs unverified findings", "file_patterns": [], "priority": "critical"},
                {"id": "T5", "title": "Synthesize and generate report", "description": "Merge verified findings from T1-T4 into a comprehensive, balanced report. Clearly mark confidence levels for each finding.", "agent": "worker", "dependencies": ["T4"], "expected_output": "Complete research report with confidence annotations and full citations", "file_patterns": [], "priority": "critical"},
            ]
        }
    },
    "bug-hunt": {
        "name": "bug-hunt",
        "description": "Systematic bug hunting across a codebase",
        "plan": {
            "goal": "Hunt for bugs across the codebase",
            "goal_type": "debugging",
            "estimated_layers": 2,
            "tasks": [
                {"id": "T1", "title": "Explore error handling patterns", "description": "Search for missing or inadequate error handling: bare excepts, swallowed errors, missing null checks.", "agent": "explorer", "dependencies": [], "expected_output": "Error handling issues with locations and severity", "file_patterns": [], "priority": "critical"},
                {"id": "T2", "title": "Explore edge cases and boundary conditions", "description": "Search for missing edge case handling: empty inputs, max values, race conditions, timeout handling.", "agent": "explorer", "dependencies": [], "expected_output": "Edge case gaps with test scenarios", "file_patterns": [], "priority": "critical"},
                {"id": "T3", "title": "Explore resource management", "description": "Search for resource leaks: unclosed connections, missing cleanup, memory accumulation, file handle leaks.", "agent": "explorer", "dependencies": [], "expected_output": "Resource management issues with fix suggestions", "file_patterns": [], "priority": "high"},
                {"id": "T4", "title": "Cross-verify bug findings", "description": "Challenge T1-T3 findings. Verify each potential bug is actually a bug (not intentional). Check if any 'fixes' would break existing behavior.", "agent": "reviewer", "dependencies": ["T1", "T2", "T3"], "expected_output": "Verified bugs with reproduction steps and fix confidence", "file_patterns": [], "priority": "critical"},
                {"id": "T5", "title": "Generate bug hunt report", "description": "Compile verified bugs into a prioritized report with reproduction steps and fix recommendations.", "agent": "worker", "dependencies": ["T4"], "expected_output": "Bug report sorted by severity with actionable fix instructions", "file_patterns": [], "priority": "high"},
            ]
        }
    },
}


def install_builtin_templates():
    """Install built-in templates if they don't exist."""
    ensure_dirs()
    installed = []
    for name, template in BUILTIN_TEMPLATES.items():
        filepath = os.path.join(TEMPLATES_DIR, f"{name}.json")
        if not os.path.exists(filepath):
            wrapped = {
                "name": name,
                "saved_at": datetime.now(timezone.utc).isoformat(),
                "description": template.get("description", ""),
                "plan": template["plan"],
                "usage_count": 0,
                "builtin": True,
            }
            with open(filepath, "w") as f:
                json.dump(wrapped, f, indent=2)
            installed.append(name)
    return installed


# ── CLI ──────────────────────────────────────────────────────────────────────

def main():
    import argparse
    parser = argparse.ArgumentParser(description="Workflow Manager — templates, checkpoints, resume")
    sub = parser.add_subparsers(dest="command")

    # Save
    p_save = sub.add_parser("save", help="Save plan as template")
    p_save.add_argument("name", help="Template name")
    p_save.add_argument("--plan", required=True, help="Path to plan.json")

    # List
    sub.add_parser("list", help="List saved templates")

    # Load
    p_load = sub.add_parser("load", help="Load template")
    p_load.add_argument("name", help="Template name")

    # Customize and init
    p_use = sub.add_parser("use", help="Use template with custom goal")
    p_use.add_argument("name", help="Template name")
    p_use.add_argument("goal", help="Custom goal")
    p_use.add_argument("--output-dir", default="/tmp/claude-workflow-session", help="Output directory")

    # Checkpoint
    p_ckpt = sub.add_parser("checkpoint", help="Save checkpoint")
    p_ckpt.add_argument("state", help="Path to state.json")
    p_ckpt.add_argument("--label", default="", help="Checkpoint label")

    # List checkpoints
    sub.add_parser("checkpoints", help="List checkpoints")

    # Resume
    p_resume = sub.add_parser("resume", help="Resume from checkpoint or interrupted workflow")
    p_resume.add_argument("--from", dest="from_path", help="Path to checkpoint or state.json")
    p_resume.add_argument("--output-dir", default="/tmp/claude-workflow-session", help="Output directory")
    p_resume.add_argument("--auto", action="store_true", help="Auto-detect interrupted workflow")

    # Script cache
    sub.add_parser("script-cache", help="List cached workflow scripts")

    # Install builtins
    sub.add_parser("install-builtins", help="Install built-in workflow templates")

    args = parser.parse_args()

    if args.command == "save":
        with open(args.plan) as f:
            plan = json.load(f)
        path = save_template(args.name, plan)
        print(f"✅ Template saved: {path}")
        print(f"   Goal: {plan.get('goal', '')[:80]}")
        print(f"   Tasks: {len(plan.get('tasks', []))}")

    elif args.command == "list":
        templates = list_templates()
        if not templates:
            print("No templates found. Run 'install-builtins' to add pre-built templates.")
        else:
            print(f"{'Name':<25} {'Tasks':<8} {'Uses':<8} Goal")
            print("-" * 80)
            for t in templates:
                print(f"{t['name']:<25} {t['task_count']:<8} {t['usage_count']:<8} {t['goal'][:50]}")

    elif args.command == "load":
        plan = load_template(args.name)
        if plan is None:
            print(f"❌ Template not found: {args.name}")
            sys.exit(1)
        print(json.dumps(plan, indent=2))

    elif args.command == "use":
        plan = load_template(args.name)
        if plan is None:
            print(f"❌ Template not found: {args.name}")
            sys.exit(1)
        plan = customize_template(plan, args.goal)
        os.makedirs(args.output_dir, exist_ok=True)
        with open(os.path.join(args.output_dir, "plan.json"), "w") as f:
            json.dump(plan, f, indent=2)
        print(f"✅ Plan initialized from template '{args.name}'")
        print(f"   Goal: {args.goal}")
        print(f"   Tasks: {len(plan.get('tasks', []))}")
        print(f"   Saved to: {args.output_dir}/plan.json")

    elif args.command == "checkpoint":
        with open(args.state) as f:
            state = json.load(f)
        path = save_checkpoint(state, args.label)
        print(f"✅ Checkpoint saved: {path}")

    elif args.command == "checkpoints":
        checkpoints = list_checkpoints()
        if not checkpoints:
            print("No checkpoints found")
        else:
            print(f"{'File':<35} {'Progress':<10} {'Phase':<20} Goal")
            print("-" * 100)
            for c in checkpoints:
                print(f"{c['file']:<35} {c['progress']:<10} {c['phase']:<20} {c['goal'][:40]}")

    elif args.command == "resume":
        if args.auto:
            state = detect_interrupted_workflow(args.output_dir)
            if state is None:
                print("No interrupted workflow found")
                sys.exit(1)
            print(f"✅ Resuming interrupted workflow: {state.get('plan', {}).get('goal', '')[:80]}")
            print(f"   Progress: {state.get('stats', {}).get('progress_pct', 0):.0f}%")
            print(f"   Phase: {state.get('phase', 'unknown')}")
        elif args.from_path:
            state = resume_from_checkpoint(args.from_path, args.output_dir)
            if state is None:
                print(f"❌ Checkpoint not found: {args.from_path}")
                sys.exit(1)
            print(f"✅ Resumed from checkpoint")
            print(f"   Goal: {state.get('plan', {}).get('goal', '')[:80]}")
        else:
            print("Specify --from <path> or --auto")
            sys.exit(1)

    elif args.command == "script-cache":
        cache_dir = os.path.expanduser("~/.claude/workflows/scripts")
        os.makedirs(cache_dir, exist_ok=True)
        scripts = sorted(os.listdir(cache_dir)) if os.path.exists(cache_dir) else []
        if not scripts:
            print("No cached scripts")
        else:
            print(f"{len(scripts)} cached scripts in {cache_dir}:")
            for s in scripts:
                if s.endswith(".py"):
                    size = os.path.getsize(os.path.join(cache_dir, s))
                    print(f"  {s} ({size}B)")

    elif args.command == "install-builtins":
        installed = install_builtin_templates()
        if installed:
            print(f"✅ Installed {len(installed)} built-in templates: {', '.join(installed)}")
        else:
            print("All built-in templates already installed")

    else:
        parser.print_help()


if __name__ == "__main__":
    main()
