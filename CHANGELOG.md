# Changelog

All notable changes to the Workflow Orchestrator project will be documented in this file.

## [2.2.0] — 2026-06-01

### Changed — Repositioning (Official `/workflow` now available to all users)

**Name change**: `workflow-orchestrator` → `wf-orchestrator`

**Skill consolidation**: Removed `/workflow` skill to avoid conflict with official Claude Code built-in `/workflow` command. Plugin now only uses `/wf` abbreviation.

- `plugin.json`: Removed `./skills/workflow` from skills list; updated name and description
- `marketplace.json`: Updated name, description, keywords, skills list
- `skills/wf/SKILL.md`: Rewritten from shortcut-forwarder to full standalone protocol
- `skills/workflow/SKILL.md`: Deprecated — redirects to `/wf`

**New positioning** — on top of official DW, not replacing it:
- Agent SDK bridge (`claude-agent-sdk` integration coming in v2.3)
- Multi-model routing (Haiku/Sonnet/Opus per task role — official uses one model)
- Cross-platform (DeepSeek/OpenRouter compatible)
- Template ecosystem (5 built-in + custom)
- Pre-execution DAG visualization
- Markdown execution reports

---

## [2.1.1] — 2026-06-01

### Added (documentation & planning)
- `docs/IMPROVEMENT_PLAN_v2.2.md` — 8-gap improvement plan from real-world `/wf` testing
- `docs/ROADMAP_TO_OFFICIAL_PARITY.md` — full parity roadmap vs official Dynamic Workflows, including Claude Agent SDK integration strategy (Hook → MCP Bridge → SDK Direct)
- `docs/agent-protocols-infrastructure-report.md` — MCP/A2A/Agentic RAG protocol research (T4 output)
- `reports/` — T3-T8 workflow execution outputs (AI framework research, gap analysis, integration architecture, risk assessment, migration roadmap)

### Key findings
- Claude Agent SDK (`claude-agent-sdk` v0.1.65) confirmed — supports programmatic sub-agent spawning, isolated contexts, parallel execution
- 3 upgrade paths identified: Hook-based (low effort), MCP Bridge (medium), SDK Direct (high)
- Agent definitions in `agents/` directory are SDK-compatible (same `.claude/agents/` format)

---

## [2.1.1] — 2026-05-31

### Simplified: removed over-engineered execution strategy

**Empirical finding**: Background agents with `subagent_type: "general-purpose"`
+ `run_in_background: true` successfully pass file access, Bash, and WebSearch
tests. Plugin-registered agent types (`worker`, `explorer`, etc.) cannot be used
as `subagent_type` values — they are prompt templates only. The v2.1.0 "sync_main"
execution strategy was based on a false premise.

**Removed:**
- `classify_execution_mode()` function — unnecessary task classification
- `sync_main` execution path — all tasks now use standard background Agent() calls
- Layer 0 sync rule — Layer 0 now runs in parallel like all other layers

**Added:**
- **Permission warm-up** (PHASES.md Step 3.0): before launching agents, do a quick
  `ls <project_dir>` in main context to pre-authorize file access for the session.
  Background agents inherit the session's permission grants.

**Kept (from v2.1.0):**
- `validate_agent_output()` + `--validate-output` CLI — safety net for agent failures
- Stats recalculation fix in `--update-status`, `resume()`, `resume_from_checkpoint()`
- Orphaned task detection with timeout
- Agent output validation protocol (Phase 3.5)

**Protocol:** PHASES.md Phase 3 simplified from 7-step classification-based
execution back to clean parallel launch model. SKILL.md reverted to simple
Agent Type Mapping table with permission warm-up guidance.

---

## [2.1.0] — 2026-05-31

### Fixed (from real-world `/wf` execution testing)

**Bug fixes:**
- **Stale `stats` after `--update-status`** (`task_schema.py`): `--update-status` now reconstructs `WorkflowState` and outputs via `to_dict()`, ensuring `stats` (completed/failed/in_progress/pending/progress_pct) are always in sync with `results`.
- **Resume state with stale stats** (`workflow_engine.py`): `resume()` now reconstructs `WorkflowState` and uses `_save_state()` which recalculates `stats` via `to_dict()`.
- **Resume checkpoint stale stats** (`workflow_manager.py`): `resume_from_checkpoint()` now reconstructs `WorkflowState` → `to_dict()` before saving.

### Added (execution strategy redesign)

**Permission-aware execution:**
- `classify_execution_mode()`: Tasks are classified as `sync_main` (explorers needing file access) or `agent_background` (implementers/reviewers) based on agent type.
- **Layer 0 Rule**: All Layer 0 tasks (explorer + early worker) run synchronously in MAIN context — they need full file system and web access that background agents lack.
- `validate_agent_output()`: Detects permission errors ("permission denied", "cannot access", "tool not available", etc.), empty output, and too-short output (< 50 chars).
- `--validate-output` CLI flag: Programmatic output validation returning `{"valid": true/false, "reason": "..."}`.
- **Auto-retry fallback**: When background agent output fails validation, retry ONCE in MAIN context with full permissions.

**State management:**
- `detect_interrupted_workflow()`: Now also detects orphaned `in_progress` tasks stuck beyond 5-minute timeout.

**CI:**
- Stats recalculation test: Verifies `stats` block matches actual results after `--update-status`.
- Agent output validation test: Tests permission error detection, valid output, short output, and empty output.

### Changed (protocol documentation)

- **SKILL.md**: "Agent Type Mapping" replaced with "Task Execution Classification" table showing sync_main vs agent_background modes. Added Key Rules #9-10 (Layer 0 sync, validate output).
- **PHASES.md**: Phase 3 completely rewritten as "Permission-Aware Layered Execution" with 7 steps: classify → sync_main → pre-fetch context → launch background → wait → validate → advance. Added Phase 3.5 "Agent Output Validation" with retry protocol.

---

## [2.0.1] — 2026-05-31

### Fixed (15 bugs from systematic code review)

**Critical — would cause crashes or silent failures:**
- **CI grep checks broken** (`test.yml:213`): Updated outdated `@wf.agent` / `wf.run` patterns to match new manifest-based script output (`compute_layers`, `generate_manifest`, `Manifest`).
- **`resume --auto` non-functional** (`workflow_manager.py:406`): `resume --auto` now calls `resume_from_checkpoint()` to actually reset `in_progress` tasks and persist state — previously only detected and printed status then exited.
- **`exec()` sys.argv pollution** (`workflow_engine.py:454`): Replaced `exec()` with `subprocess.run()` so generated scripts run in a clean process, avoiding argparse conflicts with parent CLI arguments.
- **`Workflow.resume()` state not persisted** (`workflow_engine.py:253`): Added `json.dump()` to write reset state back to disk. Also expanded `done` set to include `skipped` tasks.

**Medium — data loss / UI inconsistency:**
- **Docstring escaping** (`workflow_engine.py:324`): Goals containing `"""` now use `json.dumps()` in docstrings to prevent broken generated scripts.
- **`to_manifest()` title loss** (`workflow_engine.py:206`): Added `title` field to `AgentTask`, populated from `TaskDefinition.title`, used in `to_manifest()` — human-readable titles are now preserved.
- **`_render_compact()` pct inconsistency** (`monitor.py:222`): Now uses `(completed+skipped)/total` and includes `failed_fill` bar segment, consistent with `render_dashboard()`.
- **`generate_ascii()` ANSI misalignment** (`dag.py:137`): Border padding now uses `strip_ansi()` for correct visible-length calculation.
- **`generate_ascii()` skipped tasks not counted** (`dag.py:129`): Added `skipped` counter and display in stats row.
- **Generated script mixed stdout** (`workflow_engine.py:409`): Mutually exclusive `--json` / `--summary` / default branches; default sends JSON to stdout, summary to stderr.
- **CI missing `term_utils.py`** (`test.yml:98`): Added `term_utils.py` to the syntax-check loop.
- **Description silently truncated** (`workflow_engine.py:347`): Removed 200-char truncation — agent prompts now preserve full instructions.

**Low — maintenance / robustness:**
- **`Term.init()` force param blocked** (`term_utils.py:87`): Guard now skips `_initialized` check when `force` is explicitly passed. Added `_restore_colors()` for recovery after disable.
- **Dead `dry_run` parameter** (`workflow_engine.py:218`): Removed unused parameter; cleaned up dead imports (`textwrap`, `Path`, `Any`).
- **4× topological sort duplication** (`workflow_engine.py:128`): `_build_layers()` now delegates to shared `topological_layers()` in `task_schema.py`. `resume()` reuses `_build_layers()` instead of inline duplicate.

### Changed
- `AgentTask` dataclass: added `title` field; removed unused `parallel` field.
- `@wf.agent()` decorator: removed `parallel` parameter.
- `Workflow.run()`: removed `dry_run` parameter (now always dry-run).

---

## [2.0.0] — 2026-05-30

### Added
- Python script engine (`workflow_engine.py`): plan.json → executable orchestration script
- `to_manifest()` method for structured agent-call manifests
- Conditional adversarial verification (implementer/reviewer layers only)
- Fine-grained checkpoint (agent-level, not just layer-level)
- `term_utils.py`: shared ANSI terminal utilities (unified from dag/monitor/reporter)
- `PHASES.md`: detailed protocol reference extracted from SKILL.md
- `/wf` shortcut skill
- GitHub CI/CD: automated tests on push/PR + release workflow on tags
- `superpowers-enhanced` template

### Changed
- SKILL.md slimmed to quick-reference + routing table
- `dag.py`, `monitor.py`, `reporter.py`: import `Term` from shared `term_utils`
- `workflow_engine.py`: removed `_execute()` — real orchestration via SKILL.md protocol
- Generated scripts: decorator DSL → standalone manifest generator
- Research/development split removed — unified DAG+Agent strategy for all task types

---

## [1.2.0] — 2026-05-29

### Added
- Workflow templates (code-review, migration, deep-research, bug-hunt)
- Adversarial verification (Phase 4.5)
- Checkpoint/resume protocol
- Superpowers integration (macro+micro architecture)
- `/wf` command routing

---

## [1.0.0] — 2026-05-28

### Added
- Initial release
- Multi-agent DAG orchestration
- Task decomposition with topological layering
- Parallel agent execution with real-time monitoring
- ASCII + Mermaid DAG visualization
- State management and reporting
