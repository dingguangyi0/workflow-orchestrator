# WF Orchestrator v2.2 改进方案

> 基于 v2.1.1 完整 9 任务实测 + 8 个漏洞分析

## 实测回顾

v2.1.1 完成了一个 9 任务、5 层的工作流（分析 Spring Boot 平台 → AI Agent 升级报告）。整体可用，但暴露出 8 个明确差距。

## 漏洞一览

| # | 漏洞 | 严重性 | 实测表现 |
|---|------|--------|---------|
| 1 | 输出校验太弱 | 🔴 Critical | T2 分析错项目，3000 字报告质量高但内容完全错误，校验没发现 |
| 2 | 上下文传递太少 | 🔴 Critical | T5→T6 只传 500 字摘要，下游 Agent 丢了 95% 的上游信息 |
| 3 | 计划不可修改 | 🟡 High | 中途发现需要加任务或调整依赖，只能取消重来 |
| 4 | 用户看不到中间进展 | 🟡 High | 全程只看到 `44% ✅4 🔄1`，不知道 Agent 发现了什么 |
| 5 | 产出路径不统一 | 🟡 Medium | T3→reports/，T4→docs/，T9→项目目录/docs/，各自为政 |
| 6 | 错误发现靠人工 | 🟡 High | T2 的错误是我肉眼发现的，没有自动检测机制 |
| 7 | state.json 放 /tmp 脆弱 | 🟡 Medium | /tmp 重启就清空，长时间工作流有丢失风险 |
| 8 | 无时间/资源预估 | 🟢 Low | 确认计划时不知道要等多久，用户没有预期 |

---

## 改进方案

### 1. 输出校验增强（新增 "内容质量" 校验层）

**现状**：`validate_agent_output()` 只检查权限错误、空输出、<50 字符

**改进**：增加三层校验

| 层级 | 检查内容 | 触发动作 |
|------|---------|---------|
| **L1: 格式校验** | 空输出、权限错误、过短 | 已有，标记 failed |
| **L2: 质量校验**（新增） | "I cannot find"、"no results"、"wrong project" 等模式 | 标记 `valid_with_warnings`，提醒主上下文审查 |
| **L3: 内容相关性**（新增） | 输出是否包含 task.file_patterns 中的关键文件名、是否提及 expected_output 关键词 | L3 不匹配 → 自动注入更精确 prompt 重试 |

**代码**：`task_schema.py` 新增 `_QUALITY_WARNING_PATTERNS` 和 `_check_content_relevance()` 函数

**CLI**：新增 `--validate-output-quality --expected-files "pom.xml,src/" --expected-project "platform"` 参数

### 2. 上下文传递升级（摘要 → 完整文件引用）

**现状**：Agent 之间只传 300-500 字摘要

**改进**：
- 每个任务完成后，**存完整输出到文件**：`$WORKFLOW_DIR/outputs/T3_full.md`
- TaskResult 新增 `full_output_file` 字段记录路径
- 下游 Agent 的 prompt 中包含：`📄 完整上游报告: $WORKFLOW_DIR/outputs/T3_full.md`，Agent 自己去读
- TaskDefinition 新增 `needs_full_context: ["T5"]` 字段，声明需要哪些上游的完整输出
- 摘要仍然保留（500 字），作为 Agent 的"速览索引"

**优势**：不增加上下文窗口压力（Agent 按需读取），不丢失信息

### 3. 动态计划修改

**新增命令**：`/wf modify`

**功能**：
- 查看当前计划状态 + 各任务进度
- 添加新任务（指定依赖关系）
- 移除未开始的任务
- 修改未开始任务的描述/期望输出
- 修改后自动重建 DAG 层级、重校验

**Agent 触发**：Agent 输出中的特殊标记 `🔧 DYNAMIC_TASK: {"title":"...","agent":"..."}` 会被解析，自动提示用户是否添加

**CLI**：`task_schema.py --modify-plan --add-task '...' --after T5`

### 4. 增量进展展示

**改进**：每层完成后自动展示本层发现

```
⚡ Layer 0 完成
   ✅ T1: 16模块，~159万行，7大架构模式
   ✅ T2: 元数据驱动+MCP契合度★★★★★
   ✅ T3: LangChain4j推荐为主引擎
   ✅ T4: MCP+Agentic RAG建议首批落地

→ Layer 1 启动中...
```

**实现**：
- `monitor.py --compact` 增加最近完成任务的摘要行
- `reporter.py` 新增 `--layer-summary` 标志
- PHASES.md Phase 3.6 协议增加「展示本层发现」

### 5. 统一产出目录

**改进**：
- `TaskPlan` 新增 `output_base_dir` 字段
- 默认值：`<项目根目录>/reports/workflow-YYYYMMDD-HHMMSS/`
- 所有 Agent 的 prompt 中注入标准输出路径
- Phase 1 初始化时自动 `mkdir -p`

### 6. 智能错误发现

**新增检测模式**（`task_schema.py`）：
```python
_WRONG_SCOPE_PATTERNS = [
    "analyzed the wrong", "does not exist", "not found",
    "couldn't find any", "no such file"
]
```

**改进的重试协议**（PHASES.md Phase 5）：
- 语义失败（wrong scope）→ 自动注入精确路径 + 文件列表 → 重试 1 次
- 与普通权限失败分开计数（`semantic_retry_count` vs `retry_count`）

### 7. 状态持久化

**改进**：
- `WORKFLOW_DIR` 默认从 `/tmp/` 改为 `~/.claude/workflows/sessions/`
- 所有 Python 脚本默认值同步更新
- 支持 `WORKFLOW_STATE_DIR` 环境变量覆盖
- 自动迁移：旧 /tmp 路径有数据时自动复制
- 自动清理：>7 天的旧 session 在新工作流启动时清理

### 8. 时间预估

**新增**：`task_schema.py --estimate`

**输出示例**：
```json
{
  "total_tasks": 9,
  "total_layers": 5,
  "serial_estimate_minutes": 27,
  "parallel_estimate_minutes": 8,
  "speedup_factor": 3.4,
  "max_parallel_agents": 4
}
```

**展示位置**：PHASES.md Phase 2 用户确认界面，在 DAG 展示后显示预估时间。

---

## 与官网 Dynamic Workflows 差距分析

> 数据来源：[Claude Code 官方博客](https://claude.com/blog/introducing-dynamic-workflows-in-claude-code)、[官方文档](https://code.claude.com/docs/en/workflows)、社区逆向工程

### 官网架构 vs 我们的架构

| 维度 | 官网 Dynamic Workflows | 我们的插件 |
|------|----------------------|-----------|
| **编排范式** | **脚本优先** — Claude 写 JS 编排脚本，脚本即工作流 | **计划优先** — Orchestrator Agent 生成 JSON plan，SKILL.md 协议驱动执行 |
| **运行时** | 独立 `node:vm` 沙箱，后台进程 | 主 Claude Code 进程 + Python 辅助脚本 |
| **状态管理** | JS 变量（在模型上下文外） | JSON 文件 + 模型上下文内（摘要传递） |
| **Agent 通信** | `StructuredOutput` JSON → JS 变量 → 下个 Agent（机器对机器） | 自然语言摘要（500 字）→ 主上下文 → 下个 Agent |
| **并发模型** | `pipeline()` 无层级屏障 + `parallel()` 硬屏障 | 拓扑层级（严格逐层屏障） |
| **规模设计** | 10-1000 Agent/次，16 并发 | 5-15 任务，受上下文窗口限制 |
| **确定性** | 要求确定性缓存（禁止 `Date.now()`） | 不需要，基于状态恢复 |
| **触发方式** | 自动（ultracode）或关键词 | 显式 `/wf <goal>` 命令 |
| **计划要求** | Max/Team 默认，Pro 手动，Enterprise 管理员 | 任何 Claude Code 环境均可 |
| **验证机制** | 内置收敛循环（对抗直到收敛） | 条件 Phase 4.5（仅实现/审查层） |

### 官网有但我们缺的（13 项差距）

| # | 功能 | 官网实现 | 严重性 | 计划 |
|---|------|---------|--------|------|
| 1 | **JS 脚本运行时** | 编排脚本在 `node:vm` 中独立运行，不占主上下文 | 🔴 高 | v3.0 Python 独立运行时 |
| 2 | **`pipeline()` 无屏障** | 单个 Item 完成后立即流入下阶段，不等慢的 | 🔴 高 | v2.2 就绪队列模型 |
| 3 | **收敛循环** | 反复 fan-out→verify→converge 直到对抗验证通过 | 🔴 高 | v2.2 多轮验证选项 |
| 4 | **1000 Agent 容量** | 16 并发，1000 总量 | 🟡 中 | 受限于上下文窗口 |
| 5 | **`StructuredOutput`** | Agent 必须通过专用 tool 返回 JSON，无解析风险 | 🟡 中 | v2.2 JSON 输出强制 |
| 6 | **脚本变量状态** | 中间结果在 JS 变量中，不进入模型上下文 | 🔴 高 | v3.0 架构级方案 |
| 7 | **确定性缓存** | 相同脚本+相同参数 = 100% 缓存命中 | 🟡 中 | v2.3 前缀缓存 |
| 8 | **`budget` API** | 脚本可读取剩余 Token 预算，动态调整 Agent 数量 | 🟢 低 | 暂不计划 |
| 9 | **原生 `/workflows` 仪表盘** | 内置命令查看/暂停/恢复/终止所有工作流 | 🟡 中 | 依靠 `/wf status` |
| 10 | **ultracode 自动编排** | Claude 自行决定何时启动工作流，无需用户显式调用 | 🟡 中 | 已有 `/wf` 触发 |
| 11 | **Agent worktree 隔离** | `agent(opts: {isolation: 'worktree'})` | 🟢 低 | 暂不计划 |
| 12 | **嵌套工作流** | `workflow(name, args)` 一层深度组合 | 🟢 低 | 暂不计划 |
| 13 | **Opus 4.8 深度集成** | 高努力模式、更敏锐判断 | 🟢 低 | 模型特定优化 |

### 我们比官网强的（17 项）

| # | 功能 | 为什么重要 |
|---|------|-----------|
| 1 | **平台无关** | DeepSeek/OpenRouter/LiteLLM 等任意第三方代理可用，不需要 Anthropic 计划 |
| 2 | **可复用模板系统** | 5 个内置模板 + `/wf save`/`use` 自定义模板 |
| 3 | **预执行 DAG 可视化** | ASCII + Mermaid 在确认前展示，官网只有摘要 |
| 4 | **Superpowers TDD 集成** | 完整 7 步 TDD 工作流：头脑风暴→探索→计划→TDD→对抗审查→修复→验证 |
| 5 | **细粒度对抗验证** | CONFIRMED/LIKELY/UNVERIFIED 标签 + 自动换角度重检 |
| 6 | **Agent 级 checkpoint** | 每 Agent 粒度断点恢复 + 3 级失败处理 |
| 7 | **7 个专业 Agent prompt 模板** | 每个有详细角色指令和模型匹配 |
| 8 | **完整 Markdown 执行报告** | 时间线、任务详情、失败分析、变更摘要 |
| 9 | **ANSI 终端仪表盘** | 彩色进度条、层级状态、图标 |
| 10 | **目标类型分类** | 8 种目标类型 + 路由逻辑 |
| 11 | **每层用户确认** | 官网是自主执行，我们给用户更多控制 |
| 12 | **权限预热协议** | 预授权文件路径，避免首次权限提示 |
| 13 | **开源 MIT** | 可 fork、可修改、可自托管 |
| 14 | **跨 session 状态持久化** | state.json 可以跨 session 恢复，官网仅同 session |
| 15 | **多模型路由** | 可混合 Haiku/Opus/Sonnet 按角色匹配，官网所有 Agent 用同一模型 |
| 16 | **更低运营成本** | 支持更便宜的模型/API，无需高级计划 |
| 17 | **任务优先级** | critical/high/medium/low 四级 |

### 定位建议

**"Dynamic Workflows for everywhere else"**

- 官网在 Max/Team 用户 + 100 Agent 以上大规模扫荡场景无敌
- 我们的插件在 DeepSeek/OpenRouter 代理用户 + 5-15 任务的标准场景 + 模板复用场景更有优势
- 对 Max/Team 用户：我们的差异化是模板、TDD 集成、DAG 可视化、多模型路由
- 最致命的架构差距是 **上下文窗口压力**——官网通过脚本运行时把中间态移出上下文，我们积累在上下文里。这是 v3.0 需要解决的根本问题

---

## 改进路线图（合并 8 漏洞 + 13 官网差距）

### v2.2 — 低代价改进（4-6 周）

**来自 8 漏洞**：校验增强、上下文传递、增量展示、状态持久化、时间预估
**来自官网差距**：就绪队列模型、多轮验证选项

| 优先级 | 文件 | 改动 |
|--------|------|------|
| P1 | `task_schema.py` | 内容质量校验 + 相关性检测 + 错误范围模式 + `--estimate` + `DEFAULT_STATE_DIR` |
| P1 | `PHASES.md` | 完整上下文传递（文件引用） + 动态修改 Phase 5.5 + 增量展示 + 统一输出目录 + 语义重试 + **就绪队列模式** |
| P2 | `SKILL.md` | `/wf modify` 路由 + `WORKFLOW_DIR` 默认值更新 |
| P2 | `monitor.py` | compact 模式增加最新发现展示 |
| P2 | `reporter.py` | `--layer-summary` 标志 |
| P3 | `workflow_manager.py` | session 清理 + `--output-dir` 默认值 |
| P3 | `workflow_engine.py` | `state_dir` 默认值更新 |

### v2.3 — 中等改进（6-8 周）

**来自 8 漏洞**：动态计划调整、智能错误恢复
**来自官网差距**：JSON 强制输出、确定性缓存

| 改动 | 说明 |
|------|------|
| `StructuredOutput` 强制 | Agent 输出 JSON schema 校验，不再依赖自然语言解析 |
| 前缀缓存 | 相同 task prompt 前缀 → 直接复用缓存结果 |
| 计划实时调整 | 完整的 `/wf modify` 交互模式 + Agent 自动触发 |
| 收敛循环 | 关键任务多轮验证直到结果稳定 |

### v3.0 — 架构级改进（远期）

**解决最根本差距**：上下文窗口压力

| 改动 | 说明 |
|------|------|
| Python 独立运行时 | 生成可独立执行的 `.py` 编排脚本，不依赖主上下文 |
| 脚本变量状态 | 中间结果在 Python 变量中，不在模型上下文 |
| pipeline() 语义 | Item 级就绪即流入，不等慢任务 |
| 100 Agent+ 容量 | 上下文解耦后可大幅提升规模 |

## 实施建议

- **Phase A (P1)**：校验增强 + 上下文传递 + 状态持久化（3 个 Critical 漏洞）
- **Phase B (P2)**：增量展示 + 动态修改 + 时间预估（3 个 High 漏洞）
- **Phase C (P3)**：路径统一 + 智能重试（2 个 Medium 漏洞）
