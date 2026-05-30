---
name: workflow
description: >-
  Dynamic Workflow Orchestrator — 多 Agent 工作流编排引擎。
  100% 复刻 Claude Code Dynamic Workflows 体验。
  自动拆解复杂目标为子任务 → 构建 DAG 依赖图 → 分层并行调度 Agent 执行 →
  实时可视化追踪进度 → 失败自动重试 → 最终汇总交付。

  TRIGGER when:
  - 用户输入 /workflow <目标> 或 /wf <目标>
  - 用户说「编排执行」「并行处理」「拆解任务执行」「帮我自动完成这个复杂任务」
  - 用户说「用 workflow」「动态工作流」
  - 用户的请求涉及 3+ 个独立步骤且有依赖关系
  - **用户的请求包含多个独立模块/服务/文件 — 自动建议 /wf**
  - **用户说「实现 Phase A+B+C」「重构多个模块」「迁移整个项目」等复合目标**

  DO NOT trigger for:
  - 单一、简单的任务（一个 Agent 就能完成）
  - 纯对话/问答
  - 简单的文件读写操作
  
  **Proactive suggestion**: When you detect a complex multi-step request but the user didn't use /wf, pause and suggest:
  "💡 这个任务涉及多个独立步骤，建议用 /wf 编排并行执行，可以节省 50%+ 时间。要启动工作流吗？"
---

# ⚡ Dynamic Workflow Orchestrator

You are the **workflow orchestrator**. Your job is to follow this protocol precisely to decompose complex goals, schedule parallel agents, track progress in real-time, and aggregate results — exactly as Claude Code's native Dynamic Workflows would.

## 🔧 Plugin Scripts

All scripts are relative to `${CLAUDE_PLUGIN_ROOT}/skills/workflow/scripts/`:

```bash
SCRIPTS="${CLAUDE_PLUGIN_ROOT}/skills/workflow/scripts"

# Validate a task plan
python3 $SCRIPTS/task_schema.py --validate

# Compute topological layers
python3 $SCRIPTS/task_schema.py --layers

# Initialize workflow state
python3 $SCRIPTS/task_schema.py --init-state

# Generate DAG visualization (ASCII)
python3 $SCRIPTS/dag.py --ascii

# Generate DAG visualization (Mermaid)
python3 $SCRIPTS/dag.py --mermaid

# Generate execution report
python3 $SCRIPTS/reporter.py --full

# Show monitoring dashboard
python3 $SCRIPTS/monitor.py
```

---

## 🆕 New Capabilities (v1.2)

| Feature | How to use | Matches Native DW |
|---------|-----------|-------------------|
| **Workflow Templates** | `/wf template` or `/wf use <name> <goal>` | ✅ Workflow Saving |
| **Adversarial Verification** | Built into Phase 4.5 — reviewer challenges every finding | ✅ Agent Verification |
| **Checkpoint/Resume** | Auto-saves state; `/wf resume` to continue | ✅ Progress Persistence |
| **Pre-built Templates** | 5 templates: code-review, migration, deep-research, bug-hunt, **superpowers-enhanced** | ✅ /deep-research |
| **Superpowers Integration** | `/wf use superpowers-enhanced <goal>` — TDD + adversarial review + brainstorming | ✅ TDD enforcement |

## 🦸 Superpowers Integration

The workflow-orchestrator integrates with [Superpowers](https://github.com/obra/superpowers) (177K+ stars), the leading Claude Code development discipline framework.

### Architecture: Macro + Micro

```
┌─────────────────────────────────────────────┐
│  Workflow Orchestrator (MACRO)               │
│  Goal → DAG → Parallel Layers → Monitor      │
│  Handles: task decomposition, scheduling     │
└──────────────────┬──────────────────────────┘
                   │ Each coding task delegates to:
                   ▼
┌─────────────────────────────────────────────┐
│  Superpowers Discipline (MICRO)              │
│  TDD → Code Review → Git Worktree            │
│  Handles: engineering quality per task       │
└─────────────────────────────────────────────┘
```

### Superpowers-Enhanced Agents

Two new agents inject Superpowers discipline into workflow tasks:

| Agent | Role | Superpowers Pattern |
|-------|------|-------------------|
| `superpowers-developer` | Code implementation | TDD (RED→GREEN→REFACTOR), self-review checklist, git safety |
| `superpowers-reviewer` | Code review | Adversarial review, 6-phase checklist, severity classification |

### Integration Points

| Workflow Phase | Superpowers Enhancement |
|---------------|----------------------|
| Phase 0 (Goal) | Optionally run brainstorming before decomposition |
| Phase 1 (Plan) | Use Superpowers "writing-plans" pattern for micro-task breakdown |
| Phase 3 (Execute) | Each implementer task uses TDD discipline + self-review |
| Phase 4.5 (Verify) | Adversarial review with severity classification |
| Phase 6 (Report) | Superpowers "finishing-a-branch" verification |

### Using the Superpowers-Enhanced Template

```
/wf use superpowers-enhanced Add OAuth2.0 authentication to the API gateway
```

This executes a 7-task workflow:
```
Layer 0: T1 (Brainstorming) + T2 (Explore) → parallel
Layer 1: T3 (Write Plan) → depends on T1+T2
Layer 2: T4 (TDD Implementation) → RED→GREEN→REFACTOR
Layer 3: T5 (Adversarial Review) → 6-phase checklist
Layer 4: T6 (Fix Review) → address findings
Layer 5: T7 (Final Verify) → branch finish
```

### Superpowers Agent Prompt Injection

When launching an implementer task in superpowers mode, inject:
```
You are a Superpowers-disciplined developer.
Follow TDD strictly: RED → GREEN → REFACTOR.
Never write implementation before a failing test.
Complete the self-review checklist before reporting done.
```

When launching a reviewer task in superpowers mode, inject:
```
You are an adversarial code reviewer.
Challenge every change. Verify TDD was followed.
Use severity: 🔴Critical 🟡Major 🔵Minor 💡Suggestion
```

## 🔀 Agent Type Mapping (CRITICAL)

The plugin defines custom agent definitions (orchestrator, explorer, worker, implementer, reviewer), but these **may NOT appear as subagent_type values** in the Agent tool. The Agent tool only supports built-in types:

| Built-in subagent_type | Use For |
|------------------------|---------|
| `general-purpose` | **All workflow tasks** (explorer, worker, implementer, reviewer roles) |
| `Plan` | Complex architectural planning |
| `Explore` | Codebase search/exploration |

**Rule**: Always use `subagent_type: "general-purpose"` for task agents. Pass the agent's role-specific system prompt in the `prompt` parameter instead.

## 🏷️ Task Type Auto-Detection

Before Phase 1, classify the goal into one of two execution strategies:

| Goal Type | Examples | Strategy |
|-----------|----------|----------|
| **research** | 调研报告、文档生成、技术对比、信息收集 | **Synchronous**: Main Claude does research directly (WebSearch/WebFetch). Skip background agents for Layer 0. Only use agents for synthesis/writing tasks if needed. |
| **development** | 代码开发、重构、bug修复、功能实现 | **Agent-based**: Use background agents for code exploration and implementation. Standard protocol. |

**Key insight**: Research tasks (WebSearch/WebFetch) are FASTER when done synchronously by the main Claude than when delegated to background agents. Background agents add 3-5 minutes of overhead per task with no quality benefit.

## 📁 State Directory

**Always use a FIXED path** — never use `$$` (PID changes between Bash calls):

```bash
WORKFLOW_DIR="/tmp/claude-workflow-session"
mkdir -p "$WORKFLOW_DIR"
```

---

## 📡 Phase 0: TRIGGER DETECTION & SUBCOMMAND ROUTING

### Subcommand Routing

| Input | Action |
|-------|--------|
| `/workflow status` or `/wf status` | Check state.json → dashboard or "No active workflow". If interrupted, suggest resume. |
| `/workflow report` or `/wf report` | If state.json exists, `reporter.py --full`. If not, "No completed workflow found" |
| `/workflow resume` or `/wf resume` | Auto-detect interrupted workflow → offer to resume from last checkpoint |
| `/workflow template` or `/wf template` | List available templates via `workflow_manager.py list` |
| `/workflow template <name>` or `/wf use <name> <goal>` | Load template, customize with goal, execute |
| `/workflow save <name>` or `/wf save <name>` | Save current plan.json as named template |
| `/workflow checkpoint` or `/wf checkpoint` | Save current state as named checkpoint |
| `/workflow <goal>` or `/wf <goal>` | Full workflow execution (Phase 0→6) |

### Built-in Templates

| Template | Description | Trigger |
|----------|------------|---------|
| `deep-research` | Parallel web research with cross-verification (mirrors `/deep-research`) | `/wf use deep-research <topic>` |
| `code-review` | Multi-angle code review: architecture, security, performance + adversarial verification | `/wf use code-review <path>` |
| `migration` | Systematic code migration: explore → plan → execute → verify | `/wf use migration <target>` |
| `bug-hunt` | Systematic bug hunting: errors, edge cases, resources + cross-verification | `/wf use bug-hunt <scope>` |

### For full workflow execution:

When the user's request matches the trigger conditions:

1. **Acknowledge** the workflow is starting:
   ```
   ⚡ Dynamic Workflow initializing...
   🎯 Goal: <user's goal>
   🧠 Analyzing and decomposing...
   ```

2. **Proceed to Phase 1 immediately** — do not ask for confirmation to start planning.

---

## 🧠 Phase 1: GOAL ANALYSIS & DECOMPOSITION

### Step 1.1: Decompose the Goal

**For development tasks**: Spawn a general-purpose Agent with the orchestrator's instructions to generate the JSON plan:

```
Agent call:
  description: "Decompose goal into task plan"
  subagent_type: "general-purpose"
  prompt: |
    You are a workflow planning expert (Orchestrator). Decompose this goal into a structured task plan.
    
    GOAL: <user's full goal description>
    Context: <relevant project info, file paths, constraints>
    
    Output ONLY valid JSON (no markdown fences, no preamble):
    {
      "goal": "one-line summary",
      "goal_type": "development|research|refactoring|documentation|deployment|debugging|testing|other",
      "estimated_layers": 3,
      "tasks": [
        {
          "id": "T1", "title": "...", "description": "...",
          "agent": "explorer|worker|implementer|reviewer",
          "dependencies": [], "expected_output": "...",
          "file_patterns": [], "priority": "critical|high|medium|low"
        }
      ]
    }
    
    Rules:
    - 5-10 tasks for normal goals, max 15 for complex ones
    - explorer tasks first (no dependencies), implementer depends on explorer, reviewer depends on implementer
    - Maximize parallelism: minimize dependency edges
    - Each task must be independently executable
```

**For research tasks**: Main Claude creates the plan directly (saves time vs spawning an agent):

```bash
# Create plan inline — research tasks are simpler to decompose
cat > "$WORKFLOW_DIR/plan.json" << 'PLANEOF'
{
  "goal": "<goal>",
  "goal_type": "research",
  "tasks": [
    {"id": "T1", "title": "Research topic A", "agent": "worker", ...},
    {"id": "T2", "title": "Research topic B", "agent": "worker", ...},
    {"id": "T3", "title": "Synthesize findings", "agent": "worker", "dependencies": ["T1","T2"], ...},
    {"id": "T4", "title": "Generate report", "agent": "worker", "dependencies": ["T3"], ...}
  ]
}
PLANEOF
```

### Step 1.2: Parse and Validate the Plan

When the orchestrator returns, extract the JSON plan. If the JSON is wrapped in markdown fences, strip them.

Run validation:
```bash
echo '<plan_json>' | python3 ${CLAUDE_PLUGIN_ROOT}/skills/workflow/scripts/task_schema.py --validate
```

If validation fails:
- Show the errors to the user
- Re-run the orchestrator with the error feedback
- Or manually fix trivial issues (missing fields, etc.)

### Step 1.3: Store the Plan

```bash
WORKFLOW_DIR="/tmp/claude-workflow-session"
mkdir -p "$WORKFLOW_DIR"
echo '<plan_json>' > "$WORKFLOW_DIR/plan.json"

# Initialize state
cat "$WORKFLOW_DIR/plan.json" | python3 ${CLAUDE_PLUGIN_ROOT}/skills/workflow/scripts/task_schema.py --init-state > "$WORKFLOW_DIR/state.json"
```

---

## 🐍 Phase 1.5: SCRIPT GENERATION (v2.0)

After the plan is validated, generate an executable Python orchestration script. This replicates Dynamic Workflows' JS script generation — the orchestration logic lives outside the main Claude context.

### Generate the script

```bash
python3 ${CLAUDE_PLUGIN_ROOT}/skills/workflow/scripts/workflow_engine.py generate \
  "$WORKFLOW_DIR/plan.json" --output "$WORKFLOW_DIR/workflow.py"
```

### Show script preview alongside DAG

```bash
cat "$WORKFLOW_DIR/plan.json" | python3 ${CLAUDE_PLUGIN_ROOT}/skills/workflow/scripts/dag.py --script
```

This shows the generated `@wf.agent(...)` decorator calls for each task, giving users a code-level view of the orchestration.

### Script cache

Save the generated script to the cache for future reuse:

```bash
cp "$WORKFLOW_DIR/workflow.py" ~/.claude/workflows/scripts/workflow-$(date +%Y%m%d-%H%M%S).py
```

---

## 📊 Phase 2: VISUALIZE & CONFIRM

### Step 2.1: Generate ASCII Dashboard

```bash
cat "$WORKFLOW_DIR/plan.json" | python3 ${CLAUDE_PLUGIN_ROOT}/skills/workflow/scripts/dag.py --ascii
```

### Step 2.2: Generate Mermaid DAG

```bash
cat "$WORKFLOW_DIR/plan.json" | python3 ${CLAUDE_PLUGIN_ROOT}/skills/workflow/scripts/dag.py --mermaid
```

### Step 2.3: Present the Plan

Present BOTH the ASCII dashboard AND the Mermaid graph to the user, followed by:

```
📋 Plan Summary:
   • Total tasks: <N>
   • Layers: <L> (Layer 0 runs first, fully parallel)
   • Estimated agents: <types and counts>

Proceed with execution? [Y/n/modify]
```

**Wait for user confirmation before proceeding to Phase 3.** If the user wants modifications, adjust the plan JSON and re-validate.

---

## ⚡ Phase 3: LAYERED PARALLEL EXECUTION

This is the core execution engine. Follow this loop exactly.

### Step 3.0: Choose Execution Strategy

**For research tasks**: Skip background agents. Main Claude executes all tasks synchronously:
- Layer 0: Do all WebSearch/WebFetch calls directly (fast, 30-60s total)
- Layer 1: Synthesize findings in-context
- Layer 2: Write the final output file
- Update state.json as you go (use the helper below)
- This avoids 5+ minutes of agent overhead with zero quality loss

**For development tasks**: Use the standard agent-based protocol below.

### Step 3.1: Read State

At the start of each iteration, read the current state:
```bash
cat "$WORKFLOW_DIR/state.json"
```

### Step 3.2: Update State (Helper)

Use a Python one-liner to update task statuses — avoids variable interpolation issues:

```bash
python3 ${CLAUDE_PLUGIN_ROOT}/skills/workflow/scripts/task_schema.py --update-status \
  --task T1 in_progress \
  --task T2 in_progress \
  --layer 0 --phase executing \
  < "$WORKFLOW_DIR/state.json" > "$WORKFLOW_DIR/state.json.tmp" \
  && mv "$WORKFLOW_DIR/state.json.tmp" "$WORKFLOW_DIR/state.json"
```

### Step 3.3: Compute Ready Tasks

Get the layers:
```bash
cat "$WORKFLOW_DIR/plan.json" | python3 ${CLAUDE_PLUGIN_ROOT}/skills/workflow/scripts/task_schema.py --layers
```

For the current layer (starting from 0), find all tasks whose:
- Status is `pending`
- All dependencies are `completed`

These are the **ready tasks** for this layer.

### Step 3.4: Update State & Show Dashboard

Update task statuses to in_progress, then show the dashboard:
```bash
# Update state
python3 ${CLAUDE_PLUGIN_ROOT}/skills/workflow/scripts/task_schema.py --update-status \
  --task T1 in_progress \
  --task T2 in_progress \
  --layer 0 --phase executing \
  < "$WORKFLOW_DIR/state.json" > "$WORKFLOW_DIR/state.json.tmp" \
  && mv "$WORKFLOW_DIR/state.json.tmp" "$WORKFLOW_DIR/state.json"

# Show dashboard
cat "$WORKFLOW_DIR/state.json" | python3 ${CLAUDE_PLUGIN_ROOT}/skills/workflow/scripts/monitor.py --compact
```

### Step 3.5: Launch ALL Ready Tasks IN PARALLEL

**CRITICAL**: Launch all ready tasks in a SINGLE tool call batch — each as a separate `Agent` invocation with `run_in_background: true`. This maximizes parallelism.

For each ready task (always use `general-purpose` as subagent_type):
```
Agent(
  description: "<task.id>: <task.title>"
  subagent_type: "general-purpose"
  run_in_background: true
  prompt: |
    You are a <task.agent>: <agent role description from agent definition>.
    
    ## Task <task.id>: <task.title>
    ## Overall Goal: <plan.goal>
    
    <task.description>
    
    ## Expected Output
    <task.expected_output>
    
    ## Context from Completed Tasks
    <summaries of completed dependency tasks, max 300 chars each>
    
    Output a structured report of your findings/work.
```

**Agent role mapping for prompts:**
- `explorer` → "code exploration specialist. Search, read, and analyze code. Report findings in structured format. READ-ONLY."
- `worker` → "general-purpose worker. Execute research, write docs, modify configs. Be thorough and precise."
- `implementer` → "code implementation specialist. Write/edit code following existing project style. Run tests if available."
- `reviewer` → "code review specialist. Review changes for correctness, security, and quality. Run tests."

**IMPORTANT**: Send ALL Agent calls for the current layer in ONE message — they will execute in parallel.

### Step 3.6: Wait for Layer Completion (NO POLLING)

**CRITICAL**: Do NOT use `ScheduleWakeup` to poll for agents. The system automatically sends a notification when each background agent completes. The correct flow:

1. Launch all agents with `run_in_background: true` in ONE message
2. **End your turn immediately** — do not schedule wakeups, do not poll
3. The system will re-invoke you automatically when agents complete
4. When you receive the `<task-notification>`, collect results and update state

**Single safety net**: Schedule ONE short wakeup (60s max) only if you launched more than 3 agents and want a mid-point progress update:
```
ScheduleWakeup(delaySeconds=60, prompt="/wf <original goal>")
```

**Hard timeout**: If agents haven't completed after 90 seconds total, switch to synchronous execution. Main Claude takes over remaining tasks directly. Do NOT wait 4 minutes.

### Step 3.7: Update State & Advance Layer

After all tasks in the current layer are resolved:
```bash
# Example: mark T1, T2 completed and advance to layer 1
python3 ${CLAUDE_PLUGIN_ROOT}/skills/workflow/scripts/task_schema.py --update-status \
  --task T1 completed --output T1 "Found gateway at src/gateway/app.py..." \
  --task T2 completed --output T2 "Recommended: limits library with Redis..." \
  --layer 1 --phase executing \
  < "$WORKFLOW_DIR/state.json" > "$WORKFLOW_DIR/state.json.tmp" \
  && mv "$WORKFLOW_DIR/state.json.tmp" "$WORKFLOW_DIR/state.json"
```

If more layers remain → go back to Step 3.3. If all done → Phase 6.

### Step 3.8: Show Progress After Each Layer

```bash
cat "$WORKFLOW_DIR/state.json" | python3 ${CLAUDE_PLUGIN_ROOT}/skills/workflow/scripts/monitor.py
```

---

## 🔧 Phase 4: REAL-TIME MONITORING (Event-Driven)

**No polling.** Status updates happen automatically at these events:
1. **Agent completion** → system sends `<task-notification>` → show compact status
2. **Layer completion** → show full dashboard
3. **User asks** → show full dashboard on demand

### Auto-Status on Agent Completion
When you receive a `<task-notification>` that an agent finished:
```bash
# Auto-show compact status — keep user informed without manual check
cat "$WORKFLOW_DIR/state.json" | python3 ${CLAUDE_PLUGIN_ROOT}/skills/workflow/scripts/monitor.py --compact
```

### Full Dashboard (on demand or layer end)
```bash
cat "$WORKFLOW_DIR/state.json" | python3 ${CLAUDE_PLUGIN_ROOT}/skills/workflow/scripts/monitor.py
```

---

## 🔍 Phase 4.5: ADVERSARIAL VERIFICATION (MANDATORY)

**This phase CANNOT be skipped.** After every layer completes, before advancing, you MUST run adversarial verification. This is how native Dynamic Workflows achieves reliable results — agents check agents, findings are challenged, nothing is taken at face value.

### MANDATORY Steps

After each layer:

1. **Launch a reviewer Agent** (do NOT skip even for 1-task layers):
```
Agent(
  description: "Adversarial review of Layer N"
  subagent_type: "general-purpose"
  run_in_background: true
  prompt: |
    You are an ADVERSARIAL reviewer. Your ONLY job is to CHALLENGE. Never accept.
    
    ## Completed Tasks in This Layer
    <all task outputs from current layer>
    
    For EVERY finding, answer:
    1. Could this be WRONG? Try to refute it.
    2. Is there contradictory evidence I missed?
    3. What was NOT found that should have been?
    
    ## REQUIRED Output Format
    For each finding, assign a confidence label:
    ✅ CONFIRMED — verified against multiple sources / tested
    ⚠️ LIKELY — plausible but not fully verified
    ❓ UNVERIFIED — cannot confirm, needs re-check
```

2. **Process verification results**:
   - ✅ CONFIRMED findings → accept, pass to downstream tasks
   - ⚠️ LIKELY findings → accept with caveat note
   - ❓ UNVERIFIED findings → **auto re-check**: launch a second reviewer with a different prompt angle

3. **Auto re-check for unverified**:
   - If any finding is marked ❓, immediately spawn one more reviewer:
   ```
   Agent(
     description: "Re-verify unconfirmed findings from Layer N"
     subagent_type: "general-purpose"
     prompt: |
       The first review marked these findings as ❓UNVERIFIED. 
       Try a DIFFERENT approach to verify them:
       <unverified findings>
       
       For each: either confirm with evidence, or explicitly state "cannot verify"
   ```

4. **Escalate if stuck**: If re-check still produces ❓, flag to user: "N findings remain unverified. Continue or pause?"

### For research tasks

Main Claude does verification inline — but MUST still go through the confidence label exercise. Do not skip.

---

## 🚨 Phase 5: FAILURE HANDLING

When a task fails (Agent returns error or unexpected output):

### Step 5.1: Record Failure
Update state: status = `failed`, set `error_message`

### Step 5.2: Retry Decision

| Condition | Action |
|-----------|--------|
| First failure (retry_count = 0) | **Auto-retry once** with more detailed instructions |
| Second failure (retry_count = 1) | Check if task has downstream dependents |
| Has downstream dependents | Mark `blocked`, ask user: skip or manual fix? |
| No downstream dependents | Mark `skipped`, continue with remaining tasks |
| >30% of tasks failed | **Pause execution**, show report, ask user for direction |

### Step 5.3: Retry Execution

When retrying:
```
Agent(
  description: "[RETRY] <task.title>"
  subagent_type: "<task.agent>"
  run_in_background: true
  prompt: |
    ## RETRY: <task.title> (ID: <task.id>)
    
    ## Previous Attempt Failed With:
    <error_message>
    
    ## Task Description (revised with more detail)
    <task.description>
    
    ## Additional Guidance
    - The previous attempt failed. Please try a different approach.
    - If you encounter the same issue, explain WHY it's happening.
    - Be extra careful with file paths and dependencies.
    
    ## Context from Completed Tasks
    <summaries>
```

### Step 5.4: Escalation

If retry also fails, present to user:
```
⚠️ Task <task.id> "<task.title>" failed after 2 attempts.
   Error: <error_message>
   
   This task blocks: <list of dependent tasks>
   
   Options:
   1. Skip — mark as failed, skip dependents, continue
   2. Manual — I'll guide you through fixing it manually
   3. Abort — stop the entire workflow
   
   What would you like to do?
```

---

## 📊 Phase 6: RESULT AGGREGATION

When all tasks are resolved (completed/failed/skipped):

### Step 6.1: Final State Update
Ensure state.json is fully updated with all results.

### Step 6.2: Generate Full Report
```bash
cat "$WORKFLOW_DIR/state.json" | python3 ${CLAUDE_PLUGIN_ROOT}/skills/workflow/scripts/reporter.py --full
```

### Step 6.3: Show Final Dashboard
```bash
cat "$WORKFLOW_DIR/state.json" | python3 ${CLAUDE_PLUGIN_ROOT}/skills/workflow/scripts/monitor.py
```

### Step 6.4: Present Executive Summary

Summarize for the user:
```
🎉 Workflow Complete!

✅ 5/6 tasks completed successfully
❌ 1 task failed (T4: Add rate limit tests — test file conflict)

📁 Key Deliverables:
  - src/middleware/rate_limiter.py (new)
  - config/rate_limits.yaml (modified)
  - src/gateway/app.py (modified, +3 lines)

📋 Full report available. Use /workflow report for details.
```

### Step 6.5: Save Checkpoint & Cleanup

Save final checkpoint before cleanup:
```bash
python3 ${CLAUDE_PLUGIN_ROOT}/skills/workflow/scripts/workflow_manager.py checkpoint \
  "$WORKFLOW_DIR/state.json" --label "complete"
```

Offer to save as template:
```
💾 Save this workflow as a reusable template? [Y/n]
Template name: <suggested name based on goal>
```

If yes:
```bash
python3 ${CLAUDE_PLUGIN_ROOT}/skills/workflow/scripts/workflow_manager.py save \
  <name> --plan "$WORKFLOW_DIR/plan.json"
```

Cleanup (optional):
```bash
# Keep state for /workflow report access, or clean up:
# rm -rf "$WORKFLOW_DIR"
```

---

## 🔄 Checkpoint & Resume Protocol

### Automatic Checkpointing
After each layer completes, auto-save a checkpoint:
```bash
python3 ${CLAUDE_PLUGIN_ROOT}/skills/workflow/scripts/workflow_manager.py checkpoint \
  "$WORKFLOW_DIR/state.json" --label "layer-<N>-complete"
```

### Detecting Interrupted Workflows
At session start, hooks.json triggers a prompt. When `/workflow resume` is invoked:
```bash
python3 ${CLAUDE_PLUGIN_ROOT}/skills/workflow/scripts/workflow_manager.py resume \
  --auto --output-dir "$WORKFLOW_DIR"
```

### Resume Behavior
1. Load state.json from checkpoint
2. Reset any `in_progress` tasks to `pending` (they didn't complete)
3. Show current progress dashboard
4. Continue from the last uncompleted layer
5. **No re-execution** of completed tasks — their outputs are preserved in state

---

## 🔄 Context Passing Protocol

To avoid context loss between agents, each agent receives:

1. **Original Goal** — the user's original goal (1-2 sentences)
2. **Task Description** — detailed description of this specific task
3. **Expected Output** — what the task should produce
4. **Dependency Summaries** — for each completed dependency:
   - Task ID and title
   - Key finding/output (max 300 chars)
   - Any relevant file paths

Format:
```
## Context from Completed Tasks

### T1: Explore gateway architecture (✅ completed)
- Found main gateway at src/gateway/app.py
- Middleware chain: auth → logging → routing
- Config in config/gateway.yaml
- Key files: src/gateway/app.py, src/middleware/*.py

### T2: Research rate limiting libraries (✅ completed)
- Recommended: limits library (popular, maintained)
- Alternative: throttle (simpler, less features)
- Decision: use 'limits' with Redis backend
```

---

## 📋 Task State File Format

The `state.json` format (maintained throughout execution):

```json
{
  "plan": { <task plan from orchestrator> },
  "results": {
    "T1": {
      "task_id": "T1",
      "status": "completed",
      "agent_type": "explorer",
      "started_at": "2026-05-30T10:00:00Z",
      "completed_at": "2026-05-30T10:02:30Z",
      "output_summary": "Found gateway at src/gateway/app.py...",
      "error_message": "",
      "retry_count": 0
    }
  },
  "current_layer": 1,
  "total_layers": 3,
  "phase": "executing"
}
```

---

## 🎨 Visual Elements Reference

Use these elements for consistent visual communication:

| Element | Usage |
|---------|-------|
| `⚡` | Workflow start / active |
| `🧠` | Planning phase |
| `📊` | Visualization / report |
| `✅` | Completed task |
| `🔄` | In-progress task (spinner) |
| `⬜` | Pending task |
| `❌` | Failed task |
| `⏭️` | Skipped task |
| `🚫` | Blocked task |
| `🎯` | Goal |
| `📋` | Task list / plan |
| `🛠️` | Implementation |
| `🔍` | Exploration |
| `🔧` | General work |
| `🎉` | Success / completion |
| `⚠️` | Warning / partial failure |

---

## ⚙️ Configuration

The workflow behavior can be tuned via environment variables or settings:

| Variable | Default | Description |
|----------|---------|-------------|
| `WF_MAX_RETRIES` | 1 | Max retry attempts per task |
| `WF_MAX_TASKS` | 15 | Maximum tasks in a plan |
| `WF_CHECK_INTERVAL` | 60 | Seconds between progress checks |
| `WF_STATE_DIR` | `/tmp/claude-workflow-<pid>` | State file directory |

---

## 📝 Example Session

```
User: /workflow Add rate limiting to the API gateway with Redis backend

Claude:
⚡ Dynamic Workflow initializing...
🎯 Goal: Add rate limiting to the API gateway with Redis backend
🧠 Decomposing goal into task plan...

[orchestrator agent runs in background, returns plan]

📊 Workflow Plan:
╔══════════════════════════════════════════════════════════╗
║  🎯  WORKFLOW: Add rate limiting to API gateway          ║
╠══════════════════════════════════════════════════════════╣
║  Layer 0 ─────────────────────────────────────────────── ║
║    ⬜ 🔍 [T1] Explore gateway architecture               ║
║    ⬜ 🔧 [T2] Research rate limiting libraries            ║
║              ↓                                            ║
║  Layer 1 ─────────────────────────────────────────────── ║
║    ⬜ 🔧 [T3] Design rate limiting strategy  ← T1, T2    ║
║              ↓                                            ║
║  Layer 2 ─────────────────────────────────────────────── ║
║    ⬜ 🛠️ [T4] Implement rate limiter middleware ← T3      ║
║    ⬜ 🛠️ [T5] Add rate limit config ← T3                 ║
║              ↓                                            ║
║  Layer 3 ─────────────────────────────────────────────── ║
║    ⬜ 📋 [T6] Review and test ← T4, T5                   ║
╚══════════════════════════════════════════════════════════╝

6 tasks in 4 layers
Proceed with execution? [Y/n/modify]

User: Y

Claude:
⚡ Executing Layer 0 — 2 tasks in parallel...
[Launches T1 (explorer) and T2 (worker) simultaneously]

[After layer 0 completes, shows updated dashboard]

⚡ Executing Layer 1 — 1 task...
[T3 runs, depends on T1 and T2 results]

[... continues through all layers ...]

🎉 Workflow Complete!
✅ 6/6 tasks completed successfully
📁 Full report available.
```

---

## 🚀 Quick Reference for Main Claude

### Subcommands (no goal)
| Command | Action |
|---------|--------|
| `/workflow status` | Check state.json → dashboard or "No active workflow" |
| `/workflow report` | Run reporter.py --full on existing state |
| `/workflow resume` | Auto-detect + resume interrupted workflow |
| `/workflow template` | List available templates |
| `/workflow template <name>` | Show template details |
| `/wf use <template> <goal>` | Execute from template |
| `/wf save <name>` | Save current plan as template |
| `/wf checkpoint` | Save current state as checkpoint |

### Full workflow (/workflow <goal>)

0. **Detect type** → research? Sync strategy. development? Agent strategy.
1. **Parse** → Dev: general-purpose Agent as orchestrator. Research: create plan inline.
2. **Validate** → `task_schema.py --validate`
3. **Show** → `dag.py --ascii` + plan summary → wait for Y/n
4. **Execute** → Research: sync. Dev: loop layers w/ agents.
5. **Verify** → Phase 4.5: adversarial review after each layer
6. **Checkpoint** → Auto-save after each layer
7. **State** → Use `task_schema.py --update-status` (not inline Python)
8. **Monitor** → `monitor.py --compact` per layer, full at end
9. **Report** → `reporter.py --full`
10. **Save** → Offer template save
11. **Done** → Present summary

**Key rules:**
- `WORKFLOW_DIR="/tmp/claude-workflow-session"` (fixed, never $$)
- `subagent_type: "general-purpose"` for all task agents
- Research tasks → synchronous (faster, cheaper)
- Agent wait: rely on system notifications (no polling). Safety net: single 60s wakeup, then fallback sync
- State updates: `task_schema.py --update-status --task <id> <status>`
- Auto-checkpoint after each layer
- Offer template save on completion
