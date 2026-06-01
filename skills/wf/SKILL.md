---
name: wf
description: >-
  ⚡ WF Orchestrator — 多 Agent 工作流编排引擎。
  Agent SDK 集成 · 多模型路由 · 跨平台兼容 · 模板复用 · DAG 可视化 · 执行报告。
  自动拆解目标 → DAG 依赖图 → 分层并行 Agent → 实时监控 → 失败重试 → 汇总报告。

  TRIGGER when:
  - 用户输入 /wf <目标>
  - 用户的请求涉及 3+ 个独立步骤且有依赖关系
  - 用户说「编排执行」「并行处理」「拆解任务执行」
  - 用户说「用 wf」「用工作流」
  - 用户的请求包含多个独立模块/服务/文件

  DO NOT trigger for:
  - 单一、简单的任务
  - 纯对话/问答
  - 简单的文件读写操作

  注意：`/workflow` 命令已由 Claude Code 官方内置功能接管。
  本插件仅使用 `/wf` 缩写。
---

# ⚡ WF Orchestrator

Follow this protocol to decompose complex goals, schedule parallel agents,
track progress, and aggregate results.

> **📖 Detailed phase instructions**: When entering a specific phase, read
> `${CLAUDE_PLUGIN_ROOT}/skills/workflow/PHASES.md` for the full step-by-step protocol.
> This file contains the routing table and quick reference only.

## 🔧 Plugin Scripts

```bash
SCRIPTS="${CLAUDE_PLUGIN_ROOT}/skills/workflow/scripts"

python3 $SCRIPTS/task_schema.py --validate          # Validate plan
python3 $SCRIPTS/task_schema.py --layers             # Compute layers
python3 $SCRIPTS/task_schema.py --init-state          # Init state
python3 $SCRIPTS/task_schema.py --update-status ...   # Update state
python3 $SCRIPTS/task_schema.py --validate-output ... # Validate agent output
python3 $SCRIPTS/dag.py --ascii                       # ASCII DAG
python3 $SCRIPTS/dag.py --mermaid                     # Mermaid DAG
python3 $SCRIPTS/dag.py --script                      # Script preview
python3 $SCRIPTS/monitor.py                           # Dashboard
python3 $SCRIPTS/monitor.py --compact                 # Compact status
python3 $SCRIPTS/reporter.py --full                   # Full report
python3 $SCRIPTS/reporter.py --summary                # Summary
python3 $SCRIPTS/workflow_manager.py ...              # Templates/checkpoints
```

---

## 📁 State Directory

```bash
WORKFLOW_DIR="${HOME}/.claude/workflows/sessions"
mkdir -p "$WORKFLOW_DIR"
```

---

## 📡 Phase 0: SUBCOMMAND ROUTING

| Input | Action |
|-------|--------|
| `/wf status` | Check state.json → dashboard or "No active workflow" |
| `/wf report` | `reporter.py --full` on existing state |
| `/wf resume` | Auto-detect interrupted → resume from checkpoint |
| `/wf template` | `workflow_manager.py list` |
| `/wf use <template> <goal>` | Load template, customize, execute |
| `/wf save <name>` | Save plan.json as template |
| `/wf <goal>` | **Full workflow execution (Phase 0→6)** |

### Built-in Templates

| Template | Description |
|----------|------------|
| `deep-research` | Parallel web research with cross-verification |
| `code-review` | Multi-angle review: architecture, security, performance |
| `migration` | Systematic migration: explore → plan → execute → verify |
| `bug-hunt` | Systematic bug hunting: errors, edge cases, resources |
| `superpowers-enhanced` | TDD + adversarial review + brainstorming |

---

## 🚀 Full Workflow Quick Reference

```
0. DETECT goal
1. PARSE   → general-purpose Agent as orchestrator → get JSON plan
2. VALIDATE → task_schema.py --validate
3. SHOW    → dag.py --ascii + summary → wait for Y/n
4. EXECUTE → Loop layers: launch ready tasks in parallel via Agent
5. VERIFY  → Phase 4.5: adversarial review (conditional — implementer/reviewer only)
6. REPORT  → reporter.py --full → present summary → offer template save
```

**Phase details**: Read `PHASES.md` when entering each phase.

---

## 🔀 Agent Type Mapping (CRITICAL)

Use `subagent_type: "general-purpose"` for ALL task agents.
Pass the role-specific system prompt in the `prompt` parameter:

| Role | Prompt prefix |
|------|--------------|
| `explorer` | "code exploration specialist. Search, read, analyze. READ-ONLY." |
| `worker` | "general-purpose worker. Research, docs, configs, scripts." |
| `implementer` | "code implementation specialist. Write/edit code, match project style." |
| `reviewer` | "code review specialist. Review for correctness, security, quality." |

**Permission warm-up**: Before launching background agents,
do a quick access check in MAIN context to ensure the session has
granted permissions for the paths and tools the agents will need.

**Fallback**: If an agent returns permission errors or empty output,
validate with `task_schema.py --validate-output`, then retry ONCE in MAIN context.

---

## ⚡ Phase 4.5: Adversarial Verification (CONDITIONAL)

| Layer contains | Action |
|---------------|--------|
| Any `implementer` or `reviewer` task | ✅ Run adversarial verification |
| Only `explorer` and `worker` tasks | ⏭️ Skip (low risk) |

See `PHASES.md` Phase 4.5 for the full verification protocol.

---

## 🚨 Phase 5: Failure Handling Quick Reference

| Condition | Action |
|-----------|--------|
| First failure | Auto-retry once |
| Second failure + has dependents | Mark `blocked`, ask user |
| Second failure + no dependents | Mark `skipped`, continue |
| >30% tasks failed | Pause, show report, ask user |

---

## 📋 State File Format

```json
{
  "plan": { "goal": "...", "tasks": [...] },
  "results": {
    "T1": { "status": "completed", "output_summary": "...", "started_at": "...", "completed_at": "..." }
  },
  "current_layer": 1,
  "total_layers": 3,
  "phase": "executing"
}
```

---

## 🎨 Visual Elements

| Icon | Meaning | Icon | Meaning |
|------|---------|------|---------|
| `⚡` | Active/start | `✅` | Completed |
| `🧠` | Planning | `🔄` | In progress |
| `📊` | Report/DAG | `⬜` | Pending |
| `🎯` | Goal | `❌` | Failed |
| `🛠️` | Implementation | `⏭️` | Skipped |
| `🔍` | Exploration | `🚫` | Blocked |
| `🔧` | General work | `🎉` | Success |
| `📋` | Review/list | `⚠️` | Warning |

---

## 🔑 Key Rules

1. `WORKFLOW_DIR="${HOME}/.claude/workflows/sessions"` — persisted path
2. `subagent_type: "general-purpose"` — for ALL task agents
3. Launch all ready tasks in ONE message — they execute in parallel
4. **No polling** — rely on system notifications. Safety net: single 60s wakeup
5. State updates: `task_schema.py --update-status --task <id> <status>`
6. Auto-checkpoint after each layer: `workflow_manager.py checkpoint`
7. Offer template save on completion: `workflow_manager.py save`
8. **Read `PHASES.md`** when entering a phase for full step-by-step instructions
9. **Permission warm-up**: before launching agents, pre-auth paths in main context
10. **Validate agent output** before marking completed — `task_schema.py --validate-output`
