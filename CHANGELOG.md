# Changelog

All notable changes to the Workflow Orchestrator project will be documented in this file.

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
