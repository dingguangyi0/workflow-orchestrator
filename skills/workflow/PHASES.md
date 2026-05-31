# ⚡ Dynamic Workflow Orchestrator — Phase Reference

> Detailed protocol for each execution phase.
> Read on-demand when entering a specific phase.
> The slim SKILL.md contains the quick reference and routing table.

---

## 🧠 Phase 1: GOAL ANALYSIS & DECOMPOSITION

### Step 1.1: Decompose the Goal

Spawn a general-purpose Agent with the orchestrator's instructions to generate the JSON plan:

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

After the plan is validated, generate an executable Python orchestration script.

```bash
python3 ${CLAUDE_PLUGIN_ROOT}/skills/workflow/scripts/workflow_engine.py generate \
  "$WORKFLOW_DIR/plan.json" --output "$WORKFLOW_DIR/workflow.py"
```

Show script preview alongside DAG:
```bash
cat "$WORKFLOW_DIR/plan.json" | python3 ${CLAUDE_PLUGIN_ROOT}/skills/workflow/scripts/dag.py --script
```

Script cache:
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

**Wait for user confirmation before proceeding to Phase 3.**

---

## ⚡ Phase 3: LAYERED PARALLEL EXECUTION

### Step 3.1: Read State & Classify Tasks

```bash
cat "$WORKFLOW_DIR/state.json"
cat "$WORKFLOW_DIR/plan.json" | python3 ${CLAUDE_PLUGIN_ROOT}/skills/workflow/scripts/task_schema.py --layers
```

For the current layer (starting from 0), classify each ready task:

| Agent type | Execution mode | Reason |
|-----------|---------------|--------|
| `explorer` | **sync_main** | Needs full file system access |
| `worker` (research) | **sync_main** | Needs WebSearch/WebFetch |
| `worker` (analysis) | **agent_background** | Works with context from deps |
| `implementer` | **agent_background** | Writes code within sandbox |
| `reviewer` | **agent_background** | Reviews with pre-fetched context |

**Layer 0 Rule**: ALL Layer 0 tasks run in MAIN context (Step 3.2).
Explorer and research tasks need full permissions that background agents lack.

### Step 3.2: Execute Sync Tasks (MAIN CONTEXT)

For ALL sync_main tasks in the current layer, execute them YOURSELF:

1. Read the task description as your instructions
2. Use your full tools (Read, Bash, Grep, Glob, WebSearch, WebFetch)
3. Document findings in structured format
4. Update state immediately after each task:
```bash
python3 ${CLAUDE_PLUGIN_ROOT}/skills/workflow/scripts/task_schema.py --update-status \
  --task <id> completed --output <id> "<findings summary>" \
  < "$WORKFLOW_DIR/state.json" > "$WORKFLOW_DIR/state.json.tmp" \
  && mv "$WORKFLOW_DIR/state.json.tmp" "$WORKFLOW_DIR/state.json"
```

**For Layer 0 specifically**: Execute all explorer/research tasks sequentially
in main context. This sacrifices Layer 0 parallelism but ensures reliability —
background agents cannot access project files or the web.

### Step 3.3: Pre-Fetch Context for Background Tasks

For agent_background tasks, collect context from completed dependencies:
- Task ID and title from each completed dependency
- Output summary (max 500 chars each)
- Key file paths discovered in exploration
- The original workflow goal

### Step 3.4: Launch Background Tasks (PARALLEL)

Launch ALL ready agent_background tasks in a SINGLE tool call batch,
each as a separate `Agent` invocation with `run_in_background: true`:

```
Agent(
  description: "<task.id>: <task.title>"
  subagent_type: "general-purpose"
  run_in_background: true
  prompt: |
    You are a <task.agent> specialist.
    
    ## Task <task.id>: <task.title>
    ## Overall Goal: <plan.goal>
    
    <task.description>
    
    ## Expected Output
    <task.expected_output>
    
    ## Context from Completed Tasks
    <summaries of completed dependency tasks, max 500 chars each>
    <key file paths from exploration>
    
    Output a structured report. Include specific file paths,
    concrete findings, and actionable details.
```

Send ALL Agent calls for the current layer in ONE message.

### Step 3.5: Wait for Completion

**Do NOT poll.** The system re-invokes you when background agents complete.
- Safety net: if >3 agents launched, send a single ScheduleWakeup(90s)
- Hard timeout: 90s — if agents haven't completed, check individually

### Step 3.6: Validate Output & Update State

For each completed background agent:

**1. Validate output** — check it is NOT permission-error or empty:
```bash
echo '<agent_output>' | python3 ${CLAUDE_PLUGIN_ROOT}/skills/workflow/scripts/task_schema.py --validate-output
```

**2. If valid** (exit code 0): mark as completed:
```bash
python3 ${CLAUDE_PLUGIN_ROOT}/skills/workflow/scripts/task_schema.py --update-status \
  --task <id> completed --output <id> "<output summary>" \
  < "$WORKFLOW_DIR/state.json" > "$WORKFLOW_DIR/state.json.tmp" \
  && mv "$WORKFLOW_DIR/state.json.tmp" "$WORKFLOW_DIR/state.json"
```

**3. If invalid** (exit code 1 — permission error / empty):
- Mark status as `failed` with error_message = validation reason
- **Retry ONCE in MAIN context** using your full permissions
- Set error_message for the retry: `--error <id> "auto-retry after validation failure"`
- If main context retry succeeds → mark completed
- If main context retry also fails → escalate to user

### Step 3.7: Advance to Next Layer

After all tasks in the current layer are settled (completed/failed/skipped):

```bash
# Show incremental results
cat "$WORKFLOW_DIR/state.json" | python3 ${CLAUDE_PLUGIN_ROOT}/skills/workflow/scripts/monitor.py --compact

# Auto-checkpoint
python3 ${CLAUDE_PLUGIN_ROOT}/skills/workflow/scripts/workflow_manager.py checkpoint \
  "$WORKFLOW_DIR/state.json" --label "layer-<N>-complete"
```

Briefly summarize this layer's key outputs to the user, then proceed to
the next layer (or Phase 6 if all layers are done).

---

## 🔍 Phase 3.5: AGENT OUTPUT VALIDATION

After each background agent completes, validate its output BEFORE marking
the task as completed. Background agents have limited sandbox permissions
and may return permission errors instead of actual work.

### Validation Steps

1. Check the agent's response for permission/access failure patterns:
   - "permission denied", "cannot access", "I cannot read"
   - "tool not available", "restricted sandbox"
   - "WebSearch/Bash/Fetch denied"
2. Check output is non-empty and meaningful (≥ 50 chars)
3. If validation fails → retry ONCE in MAIN context

### Programmatic Validation

```bash
echo '<agent_output>' | python3 ${CLAUDE_PLUGIN_ROOT}/skills/workflow/scripts/task_schema.py --validate-output
```

Returns: `{"valid": true/false, "reason": "permission_error|empty_output|output_too_short|valid"}`

### Retry Protocol

When validation fails:
1. Mark task as `failed` in state with validation reason
2. Execute the task YOURSELF in main context (you have full permissions)
3. You have access to Read, Bash, Grep, Glob, WebSearch, WebFetch
4. Update state with your results (mark completed with your output)
5. If you also fail → escalate to user with clear error message

## 🔧 Phase 4: REAL-TIME MONITORING (Event-Driven)

Status updates happen automatically:
1. **Agent completion** → show compact status
2. **Layer completion** → show full dashboard
3. **User asks** → show full dashboard on demand

Auto-status on agent completion:
```bash
cat "$WORKFLOW_DIR/state.json" | python3 ${CLAUDE_PLUGIN_ROOT}/skills/workflow/scripts/monitor.py --compact
```

Full dashboard:
```bash
cat "$WORKFLOW_DIR/state.json" | python3 ${CLAUDE_PLUGIN_ROOT}/skills/workflow/scripts/monitor.py
```

---

## 🔍 Phase 4.5: ADVERSARIAL VERIFICATION (Conditional)

### When to Verify

Verification is **required** for layers that contain `implementer` or `reviewer` agent tasks.
Layers with only `explorer` and `worker` tasks **skip** verification by default.

Use `--strict-verify` to force verification on all layers.

### Decision Matrix

| Layer contains | Action |
|---------------|--------|
| Any `implementer` or `reviewer` task | ✅ Run adversarial verification |
| Only `explorer` and `worker` tasks | ⏭️ Skip (factual findings, low risk) |
| User passed `--strict-verify` | ✅ Verify all layers |

### Verification Protocol (when triggered)

Launch a reviewer Agent:
```
Agent(
  description: "Adversarial review of Layer N"
  subagent_type: "general-purpose"
  run_in_background: true
  prompt: |
    You are an ADVERSARIAL reviewer. CHALLENGE every finding. Never accept.

    ## Completed Tasks in This Layer
    <all task outputs from current layer>

    For EVERY finding, answer:
    1. Could this be WRONG? Try to refute it.
    2. Is there contradictory evidence I missed?
    3. What was NOT found that should have been?

    Output confidence labels:
    ✅ CONFIRMED — verified against multiple sources / tested
    ⚠️ LIKELY — plausible but not fully verified
    ❓ UNVERIFIED — cannot confirm, needs re-check
```

### Process Verification Results

- ✅ CONFIRMED → accept, pass to downstream
- ⚠️ LIKELY → accept with caveat
- ❓ UNVERIFIED → auto re-check with a second reviewer using a different prompt angle

### Auto Re-check (for ❓ only)

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

### Escalation

If re-check still produces ❓, flag to user: "N findings remain unverified. Continue or pause?"

---

## 🚨 Phase 5: FAILURE HANDLING

### Step 5.1: Record Failure
Update state: status = `failed`, set `error_message`

### Step 5.2: Retry Decision

| Condition | Action |
|-----------|--------|
| First failure (retry_count = 0) | **Auto-retry once** with more detailed instructions |
| Second failure (retry_count = 1) | Check if task has downstream dependents |
| Has downstream dependents | Mark `blocked`, ask user: skip or manual fix? |
| No downstream dependents | Mark `skipped`, continue with remaining tasks |
| >30% of tasks failed | **Pause execution**, show report, ask user |

### Step 5.3: Retry Execution

```
Agent(
  description: "[RETRY] <task.title>"
  subagent_type: "general-purpose"
  run_in_background: true
  prompt: |
    ## RETRY: <task.title> (ID: <task.id>)
    ## Previous Attempt Failed With:
    <error_message>
    ## Task Description (revised with more detail)
    <task.description>
    ## Additional Guidance
    - Try a different approach from the previous attempt.
    - If you encounter the same issue, explain WHY.
    - Be extra careful with file paths and dependencies.
    ## Context from Completed Tasks
    <summaries>
```

### Step 5.4: Escalation

```
⚠️ Task <task.id> "<task.title>" failed after 2 attempts.
   Error: <error_message>
   This task blocks: <list of dependent tasks>
   Options:
   1. Skip — mark as failed, skip dependents, continue
   2. Manual — I'll guide you through fixing it manually
   3. Abort — stop the entire workflow
```

---

## 📊 Phase 6: RESULT AGGREGATION

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

### Step 6.4: Executive Summary

```
🎉 Workflow Complete!
✅ 5/6 tasks completed successfully
❌ 1 task failed (T4: description)

📁 Key Deliverables:
  - path/to/file (new/modified)

📋 Full report available. Use /workflow report for details.
```

### Step 6.5: Save Checkpoint & Cleanup

```bash
python3 ${CLAUDE_PLUGIN_ROOT}/skills/workflow/scripts/workflow_manager.py checkpoint \
  "$WORKFLOW_DIR/state.json" --label "complete"
```

Offer to save as template:
```
💾 Save this workflow as a reusable template? [Y/n]
```

If yes:
```bash
python3 ${CLAUDE_PLUGIN_ROOT}/skills/workflow/scripts/workflow_manager.py save \
  <name> --plan "$WORKFLOW_DIR/plan.json"
```

---

## 🔄 Checkpoint & Resume Protocol

### Automatic Checkpointing
After each layer completes:
```bash
python3 ${CLAUDE_PLUGIN_ROOT}/skills/workflow/scripts/workflow_manager.py checkpoint \
  "$WORKFLOW_DIR/state.json" --label "layer-<N>-complete"
```

### Detecting Interrupted Workflows
When `/workflow resume` is invoked:
```bash
python3 ${CLAUDE_PLUGIN_ROOT}/skills/workflow/scripts/workflow_manager.py resume \
  --auto --output-dir "$WORKFLOW_DIR"
```

### Resume Behavior
1. Load state.json from checkpoint
2. Reset any `in_progress` tasks to `pending`
3. Show current progress dashboard
4. Continue from the last uncompleted layer
5. **No re-execution** of completed tasks

---

## 🔄 Context Passing Protocol

Each agent receives:

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
```
