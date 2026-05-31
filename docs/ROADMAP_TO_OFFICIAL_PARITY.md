# 完全对标官网 Dynamic Workflows 路线图 — v2

> ⚡ **重大发现**：Claude Agent SDK 已发布，支持程序化子 Agent 生成、并行执行、隔离上下文。
> 之前标记为「无法实现」的几项核心能力，现在都可以通过 SDK 实现。
> 
> SDK 包：Python `claude-agent-sdk` v0.1.65 / TypeScript `@anthropic-ai/claude-agent-sdk`
> 
> **另外两个关键发现**：
> 1. **Hooks 可以直接生成子 Agent** — `hooks.json` 中 `type: "agent"` 的 hook 可以在 PreToolUse/SubagentStop 等事件触发 Agent 执行
> 2. **MCP Server 可以作 Agent 生成桥** — 第三方项目 `cc-agent` 已证明 MCP Server 可以接收编排指令，spawn Agent 进程，收集结果

---

## 关键发现：Claude Agent SDK 能力

### SDK 提供的核心能力

| 能力 | 说明 | 对标官网 |
|------|------|---------|
| **程序化子 Agent 生成** | `query()` + `Task` 工具 → 主 Agent 可以编程方式生成子 Agent | ✅ 官网 `agent()` |
| **并行执行** | 2-4+ 子 Agent 同时运行，各自的独立上下文 | ✅ 官网 `parallel()` |
| **隔离上下文** | 每个子 Agent 有自己独立的上下文窗口，互不污染 | ✅ 官方架构核心 |
| **工具作用域** | 每个子 Agent 只能使用指定的工具（安全！） | ✅ |
| **文件系统 Agent 定义** | `.claude/agents/` 目录下的 Markdown 定义（与我们的插件格式相同！） | ✅ 完全兼容 |
| **结构化输出** | 子 Agent 返回 JSON 合约 | ✅ 官网 `StructuredOutput` |
| **Python API** | `pip install claude-agent-sdk`，Python 3.10+ | ❌ 官网用 JS |
| **TypeScript API** | `npm install @anthropic-ai/claude-agent-sdk` | ✅ 官网也用 JS |

### SDK 子 Agent 生成示例

```python
from claude_agent_sdk import query, ClaudeAgentOptions

# 定义子 Agent（与我们的 agents/ 目录格式完全兼容！）
agents = {
    "explorer": {
        "description": "代码探索专家，只读",
        "tools": ["Read", "Grep", "Glob"],
        "prompt": "You are a code exploration specialist...",
        "model": "haiku"
    },
    "implementer": {
        "description": "代码实现专家",
        "tools": ["Read", "Write", "Edit", "Bash"],
        "prompt": "You are an implementation specialist...",
        "model": "sonnet"
    }
}

# 主编排 Agent 只有 Task 工具——它只能生成子 Agent
options = ClaudeAgentOptions(
    system_prompt="You are a workflow orchestrator...",
    allowed_tools=["Task"],    # ← 只能生成子 Agent，不能自己操作
    agents=agents,
    permission_mode="bypassPermissions"
)

# 运行编排——SDK 自动处理并行生成和结果收集
async for message in query(prompt="分析项目架构并实现升级", options=options):
    print(message)
```

### 与我们的插件的关系

**好消息：我们的 Agent 定义目录已经完全兼容 SDK。**
- 我们的 `agents/explorer.md`、`agents/worker.md` 等可以**直接作为 SDK 子 Agent 使用**
- SDK 的 `.claude/agents/` 格式 = 我们的 `agents/*.md` 格式（YAML 前置元数据 + Markdown 指令）

**挑战：SDK 是外部运行时，插件运行在 Claude Code 内部。**
- SDK 脚本是独立的 Python/TS 程序，需要 `pip install` 或 `npm install`
- 插件在 Claude Code 内部运行，不能直接调用外部 SDK

---

## 修正后的可实现性评估

| 官网能力 | 之前判断 | 现在判断 | 实现方式 |
|---------|---------|---------|---------|
| `node:vm` 沙箱运行脚本 | ❌ 不能 | ⚠️ 不需要 | SDK 有自己的隔离机制 |
| 脚本直接调用 `Agent()` | ❌ 不能 | ✅ **可以通过 SDK 实现** | SDK 的 `Task` 工具 + `query()` |
| agent worktree 隔离 | ❌ 不能 | ⚠️ 需要验证 | SDK 可能支持 |
| budget API | ❌ 不能 | ❌ 仍不能 | SDK 无此 API |
| 原生 `/workflows` TUI | ❌ 不能 | ❌ 仍不能 | 需要 Claude Code UI 集成 |
| 1000 Agent 容量 | ❌ 上下文限制 | ✅ **可以达到** | SDK 隔离上下文 |
| `pipeline()` 无屏障 | ✅ 可自行实现 | ✅ 更容易了 | SDK 原生支持 |
| `StructuredOutput` | ✅ 可自行实现 | ✅ SDK 原生支持 | JSON schema 输出 |
| 收敛循环 | ✅ 可自行实现 | ✅ 更容易了 | 脚本控制多轮 |
| 确定性缓存 | ✅ 可自行实现 | ✅ 可脚本控制 | Python 控制逻辑 |

---

## 新架构设计

### 三层模型

```
┌─────────────────────────────────────────────────────┐
│  Layer 1: 插件 (Claude Code 内部)                     │
│  ┌───────────────────────────────────────────────┐  │
│  │ SKILL.md + PHASES.md                          │  │
│  │ 用户交互：/wf <goal> → 计划生成 → DAG 展示     │  │
│  │ 状态管理：task_schema.py + monitor.py          │  │
│  │ 职责：理解目标、拆解计划、可视化、用户确认      │  │
│  └──────────────────┬────────────────────────────┘  │
│                     │ 生成编排脚本                     │
│                     ▼                                │
│  Layer 2: SDK 编排脚本 (独立 Python/TS 进程)          │
│  ┌───────────────────────────────────────────────┐  │
│  │ workflow_orchestrator.py                      │  │
│  │ 使用 claude-agent-sdk                         │  │
│  │ pipeline() 语义 + converge() 循环              │  │
│  │ 状态在 Python 变量中，不进模型上下文            │  │
│  │ 职责：执行编排逻辑、生成子 Agent、收集结果      │  │
│  └──────────────────┬────────────────────────────┘  │
│                     │ Task 工具                       │
│                     ▼                                │
│  Layer 3: 子 Agent (SDK 管理的隔离上下文)              │
│  ┌───────────────────────────────────────────────┐  │
│  │ Explorer (haiku) ─ Read/Grep/Glob             │  │
│  │ Implementer (sonnet) ─ Read/Write/Edit/Bash   │  │
│  │ Reviewer (sonnet) ─ Read/Grep/Glob            │  │
│  │ 每个子 Agent 独立上下文、独立工具集             │  │
│  └───────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────┘
```

### 插件 ↔ SDK 交互流程

```
用户: /wf "分析项目架构 → 升级报告"

1. 插件生成 plan.json (现有流程)
2. 插件生成 SDK 编排脚本 workflow.py
   └─ 脚本中包含：
      - pipeline(explore_tasks, analyze_tasks, report_task)
      - converge(implement_task, {maxRounds: 3})
      - 使用 agents/ 目录中的 Agent 定义
3. 用户运行脚本：python3 workflow.py
   └─ SDK 处理并行生成、结果收集、收敛循环
4. 结果写回 state.json
5. 插件 reporter.py 生成最终报告
```

---

## 三条升级路径（投资递增）

| 路径 | 方式 | 投入 | 收益 | 起点 |
|------|------|------|------|------|
| **A: Hook 增强** | `hooks.json` 加 `type: "agent"` hook，在 `SubagentStop` 事件触发验证 Agent，`PreToolUse` 做门控 | 低 | 更细粒度的 session 内控制 | 立即可做 |
| **B: MCP Server 桥** | 实现 MCP Server 包装 Agent SDK，提供 `spawn_agent`/`get_result`/`cancel_agent` 工具 | 中 | 外部可编程编排，语言无关 | 需要 MCP 基础设施 |
| **C: Agent SDK 直接** | 用 `claude-agent-sdk` 重写编排引擎，Python 脚本直接控制子 Agent | 高 | 完全程序化控制，streaming，session fork | 需要安装 SDK |

### 路径 A：Hook 增强（低投入，立即可做）

```json
// hooks.json — 新增 SubagentStop hook
{
  "type": "agent",
  "event": "SubagentStop",
  "prompt": "Validate the subagent's output. Check: 1) Did it complete the task? 2) Is output meaningful (>100 chars)? 3) Are there permission errors? Return {ok: true/false, reason: '...'}",
  "timeout": 30,
  "model": "haiku"
}
```

### 路径 B：MCP Server 桥（中等投入，参考 cc-agent）

```
插件生成编排 plan → MCP Server 接收 → Server 调用 Agent SDK
→ 子 Agent 执行 → 结果收集 → 返回插件
```

社区已有参考实现：`cc-agent`、`claude-code-mcp`

### 路径 C：Agent SDK 直接（完整方案）

```python
from claude_agent_sdk import query, ClaudeAgentOptions, AgentDefinition

options = ClaudeAgentOptions(
    allowed_tools=["Task"],
    agents={
        "explorer": AgentDefinition(
            description="代码探索专家", tools=["Read","Grep","Glob"],
            prompt="You are a code exploration specialist...", model="haiku"
        ),
        "implementer": AgentDefinition(
            description="代码实现专家", tools=["Read","Write","Edit","Bash"],
            prompt="You are an implementation specialist...", model="sonnet"
        ),
    },
    permission_mode="bypassPermissions"
)
async for msg in query(prompt="分析项目并实现升级", options=options):
    print(msg)
```

### 推荐：A → B → C 渐进式

1. **先做 A（Hook）**：零外部依赖，立即可部署，解决验证和门控问题
2. **再做 B（MCP）**：引入外部编排能力，支持跨 session 编排
3. **最后 C（SDK）**：完整对标官网，pipeline + converge + 上下文隔离

---

## 修订后的实施路线图

### v2.2 — 即插即用的 SDK 集成（4-6 周）

**新增 `workflow_engine.py --generate-sdk-script`**

无需安装额外依赖即可生成 SDK 编排脚本。用户可选择运行。

```
python3 workflow_engine.py generate-sdk plan.json --output workflow.py
python3 workflow.py  # 使用 SDK 执行编排
```

**改动**：
- `workflow_engine.py`: 新增 `generate_sdk_script()` 函数，生成使用 `claude-agent-sdk` 的 Python 编排脚本
- `.claude-plugin/plugin.json`: 添加 `pip install claude-agent-sdk` 到安装说明
- `SKILL.md`: 新增 Phase 1.5b 可选 SDK 脚本生成
- 生成脚本使用我们的 `agents/` 目录中的 Agent 定义

### v2.3 — 完整 SDK 编排引擎（6-8 周）

**Pipeline + Converge + StructuredOutput 全部通过 SDK**

```python
# 生成的 SDK 脚本示例
from claude_agent_sdk import query, ClaudeAgentOptions
from pathlib import Path

AGENTS_DIR = Path("~/.claude-plugin/workflow-orchestrator/agents").expanduser()

# Pipeline: explore → analyze → implement → review
async def pipeline(plan, state_file):
    # Stage 1: 并行探索
    explore_tasks = [t for t in plan.tasks if t.agent == "explorer"]
    explore_results = await parallel_execute(explore_tasks)

    # Stage 2: 分析（就绪队列——任一 explore 完成即启动分析）
    analyze_results = await ready_queue_execute(
        [t for t in plan.tasks if t.agent == "worker" and t.depends_on],
        explore_results
    )

    # Stage 3: 实现 + 收敛验证
    for task in plan.tasks_with_agent("implementer"):
        result = await converge(task, max_rounds=3)
        update_state(state_file, task.id, result)

    return results
```

**改动**：
- `workflow_engine.py`: 完整的 SDK 脚本生成器，包含 `pipeline()`、`ready_queue()`、`converge()` 原语
- `task_schema.py`: ExecutionEngine 类（pipeline 语义）
- `PHASES.md Phase 3`: 新增 SDK 执行模式的文档

### v3.0 — 插件原生 SDK 集成（远期）

**探索：插件内直接调用 SDK**

如果 Claude Code 将来支持插件内嵌 SDK 调用（或通过 MCP 桥接），则整个执行流程可在插件内完成，无需外部脚本。

---

## 对比总结

| | v2.1.1 现状 | v2.2 (SDK 基础) | v2.3 (SDK 完整) | 官网 DW |
|---|---|---|---|---|
| **子 Agent 生成** | Agent() 工具（主上下文） | SDK Task 工具 | SDK Task 工具 | agent() |
| **并行执行** | 手动批量启动 | SDK 自动并行 | ✅ Pipeline 就绪队列 | ✅ pipeline() |
| **上下文隔离** | ❌ 共享主上下文 | ✅ SDK 隔离 | ✅ SDK 隔离 | ✅ 隔离 |
| **结构化输出** | 自然语言 | ✅ JSON schema | ✅ JSON schema | ✅ StructuredOutput |
| **收敛循环** | 单次验证 | 单次验证 | ✅ 多轮收敛 | ✅ 收敛循环 |
| **最大规模** | ~15 任务 | ~30 任务 | ~50 任务 | ~1000 任务 |
| **状态管理** | JSON 文件 + 上下文 | SDK 变量 + JSON | ✅ SDK 变量为主 | ✅ JS 变量 |
| **Agent 定义复用** | 手动 prompt | ✅ 复用 agents/ | ✅ 复用 agents/ | 内联定义 |

---

## 立即启动的建议

**v2.2 是最高 ROI 的下一步**。它不需要对现有架构做破坏性改动，只需：

1. 在 `workflow_engine.py` 中新增一个代码生成器
2. 生成使用 `claude-agent-sdk` 的 Python 编排脚本
3. 脚本直接复用现有的 `agents/` 目录定义
4. 用户可以选择用 SDK 模式（更快、更可靠）或协议模式（兼容所有环境）

现有 `/wf` 协议模式作为回退方案保留——在没有 SDK 的环境（如 DeepSeek 代理）中仍可使用。
