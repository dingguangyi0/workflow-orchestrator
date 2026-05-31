# 完全对标官网 Dynamic Workflows 路线图 — v3

> 基于 Claude Agent SDK 深入调研更新。SDK 版本：Python `claude-agent-sdk` v0.1.65 / TypeScript `@anthropic-ai/claude-agent-sdk`

---

## 1. Claude Agent SDK 深入分析

### 1.1 API 全貌

```python
from claude_agent_sdk import query, ClaudeAgentOptions, AgentDefinition

# AgentDefinition — 子 Agent 的完整配置
AgentDefinition(
    description="LLM 用来决定何时调用此 Agent",    # 关键：描述质量决定调用准确度
    prompt="系统提示词，定义 Agent 的行为边界",
    tools=["Read", "Grep", "Glob"],                # 此 Agent 能用的工具
    model="sonnet",                                  # haiku / sonnet / opus / inherit
    disallowedTools=["Bash"],                        # 显式禁用（Python #759 新增）
    maxTurns=10,                                     # 最大对话轮次
    initialPrompt="初始消息"                          # Agent 启动时的首条消息
)

# ClaudeAgentOptions — 主编排选项
options = ClaudeAgentOptions(
    allowed_tools=["Task", "Agent"],     # ← 必须含 "Task" 或 "Agent" 才能生成子 Agent
    agents={"worker": worker, ...},      # 子 Agent 注册表
    system_prompt="You are an orchestrator...",
    permission_mode="bypassPermissions", # 跳过权限交互
    model="opus",                        # 主编排 Agent 的模型
    max_turns=50,                        # 主编排 Agent 最大轮次
)

# 流式执行
async for msg in query(prompt="任务描述", options=options):
    print(msg)  # 每个 msg 是 Claude 的一条消息或工具调用结果
```

### 1.2 Orchestrator-Worker 模式（官方架构）

```
┌─────────────────────────────────────────────────────┐
│  主编排 Agent (Opus)                                  │
│  ┌───────────────────────────────────────────────┐  │
│  │ allowed_tools: ["Task"]  ← 只能生成子 Agent    │  │
│  │ 职责：分析任务 → 拆解子任务 → 生成子 Agent      │  │
│  │      → 收集结果 → 综合判断 → 决定下一轮         │  │
│  └──────────────┬────────────────────────────────┘  │
│                 │ spawn via Task tool                 │
│     ┌───────────┼───────────┐                        │
│     ▼           ▼           ▼                        │
│  ┌──────┐  ┌──────┐  ┌──────┐                       │
│  │Worker│  │Worker│  │Worker│  子 Agent              │
│  │Sonnet│  │Sonnet│  │Haiku │  ├ 独立 200K 上下文    │
│  │Read  │  │Write │  │Search│  ├ 独立工具集          │
│  │Grep  │  │Edit  │  │Fetch │  ├ 互不污染            │
│  └──────┘  └──────┘  └──────┘  └ 结果返主编排        │
└─────────────────────────────────────────────────────┘
```

官方基准测试：此模式比单 Agent Opus 4 **高 90.2%**。

### 1.3 并行执行的真实情况

**SDK 不支持程序化 `parallel()` 原语** — 工具调用是串行的（Python #438，设计决定）。

**实际并行靠 LLM prompt 驱动**：
```
# 在 system_prompt 或 prompt 中指示：
"For this analysis, dispatch ALL subtasks AT ONCE.
Do not wait for results before launching the next sub-agent."
```
LLM 会在**单轮中生成多个 Task 工具调用**，实现并行启动。但等待仍是串行的——结果一个一个回来。

**结论**：SDK 的并行是「启动并行，收集串行」。我们需要在编排脚本层面自己实现 `pipeline()` 语义。

### 1.4 已知 Issues & 陷阱

| 问题 | 影响 | 状态 |
|------|------|------|
| **TS #163**: `AgentDefinition.tools` ∩ `Options.tools` = 子 Agent 实际工具集 | 子 Agent 工具受主 Agent 限制。解决：主 Agent `allowed_tools` 放开，用 hook 限制 | 未修复 |
| **TS #210**: Task→Agent 工具重命名混乱 | `tool_use` 发 "Agent" 但有些地方认 "Task"。`allowed_tools` 两者都要写 | v0.2.71 修复 |
| **Python #438**: 工具并行执行不支持 | 需设 `readOnlyHint=True` 才能并发只读工具 | 设计决定 |
| **SDK 仍在 alpha** | 周更，breaking changes 可能。Augment Code 社区报告：长时间 session 中思维历史被擦除 | 持续中 |

### 1.5 SDK 不包含什么

- ❌ 内置重试逻辑（需要自己实现）
- ❌ 持久执行 / 崩溃恢复（需要自己实现 checkpoint）
- ❌ 多租户部署
- ❌ 集中式可观测性仪表盘
- ❌ Agent 间直接通信（这是 MCP/A2A 的职责）

### 1.6 与我们的插件的关系

| | 插件（v2.1.1） | Agent SDK |
|---|---|---|
| **Agent 定义** | `agents/*.md`（YAML 前置元数据） | `AgentDefinition` 对象或 `.claude/agents/*.md` |
| **格式兼容** | ✅ 完全兼容 — description/prompt/tools/model 字段一一对应 | 
| **子 Agent 生成** | 主上下文内 `Agent()` 工具调用 | SDK `Task` 工具，子 Agent 独立上下文 |
| **上下文** | 共享主上下文（硬限制 ~15 任务） | 独立子 Agent 上下文（可达 50-100 任务） |
| **运行方式** | Claude Code 插件运行时 | 独立 Python/TS 进程 |
| **编排语言** | SKILL.md 文本协议 | Python/TS 代码 |
| **依赖** | 无外部依赖 | `pip install claude-agent-sdk` |

---

## 2. 修正后的可实现性评估

| 官网能力 | SDK 实现？ | 说明 |
|---------|-----------|------|
| 脚本直接生成 Agent | ✅ | `AgentDefinition` + `query()` |
| 并行执行 | ⚠️ 部分 | 启动并行（prompt 驱动），收集串行 |
| 隔离上下文 | ✅ | 每子 Agent 独立 200K 窗口 |
| `pipeline()` 无屏障 | ✅ 需自建 | SDK 无原生原语，需在脚本层实现 |
| `StructuredOutput` | ✅ | JSON schema 输出 |
| 收敛循环 | ✅ 需自建 | 脚本控制多轮 `query()` |
| 1000 Agent 容量 | ⚠️ 受限于 API 并发 | 实际可达 50-100 |
| `node:vm` 沙箱 | ⚠️ 不需要 | SDK 有自己的隔离机制 |
| agent worktree 隔离 | ❓ 需验证 | SDK 文档提及但未确认 |
| budget API | ❌ | SDK 无此 API |
| 原生 `/workflows` TUI | ❌ | 需 Claude Code UI 集成 |
| 确定性缓存 | ✅ 需自建 | 脚本层控制确定性 |

---

## 3. 新架构设计

### 三层模型

```
┌──────────────────────────────────────────────────────┐
│  Layer 1: 插件 (Claude Code 内部)                      │
│  ┌────────────────────────────────────────────────┐  │
│  │ 用户交互：/wf <goal> → 计划生成 → DAG 展示       │  │
│  │ 职责：理解目标、拆解计划、可视化、用户确认        │  │
│  │ 输出：plan.json + SDK 编排脚本                   │  │
│  └──────────────────┬─────────────────────────────┘  │
│                     │ 用户运行脚本                      │
│                     ▼                                 │
│  Layer 2: SDK 编排脚本 (独立 Python 进程)              │
│  ┌────────────────────────────────────────────────┐  │
│  │ 使用 claude-agent-sdk                           │  │
│  │ pipeline() 语义 + converge() 循环               │  │
│  │ 状态在 Python 变量中，不进模型上下文             │  │
│  │ 复用 agents/ 目录中的 Agent 定义                 │  │
│  └──────────────────┬─────────────────────────────┘  │
│                     │ Task 工具                        │
│                     ▼                                 │
│  Layer 3: 子 Agent (SDK 管理的隔离上下文)              │
│  ┌────────────────────────────────────────────────┐  │
│  │ Explorer (haiku/sonnet) ─ Read/Grep/Glob       │  │
│  │ Implementer (sonnet) ─ Read/Write/Edit/Bash    │  │
│  │ Reviewer (sonnet) ─ Read/Grep/Glob             │  │
│  │ 每 Agent 独立 200K token 上下文                  │  │
│  └────────────────────────────────────────────────┘  │
└──────────────────────────────────────────────────────┘
```

### 关键设计决策

1. **插件专注于「计划」**：分解目标、生成 DAG、可视化、用户确认
2. **SDK 脚本处理「执行」**：并行生成、结果收集、收敛循环、状态管理
3. **Agent 定义共享**：`agents/` 目录同时被插件和 SDK 使用
4. **双模式运行**：SDK 模式（完整） + 协议模式（回退兼容 DeepSeek 等环境）

---

## 4. 三条升级路径

| | A: Hook 增强 | B: MCP Bridge | C: SDK 直接 |
|---|---|---|---|
| **投入** | 低 | 中 | 高 |
| **依赖** | 零 | MCP 服务端 | `pip install claude-agent-sdk` |
| **子 Agent 上下文** | 共享主上下文 | SDK 隔离 | SDK 隔离 |
| **并行** | 手动批量 | 程序化 | 程序化 |
| **收敛循环** | ❌ | ✅ 脚本控制 | ✅ 脚本控制 |
| **规模上限** | ~15 任务 | ~50 任务 | ~100 任务 |
| **何时可做** | 现在 | 需搭建 MCP 服务 | 需 SDK 环境 |

### 推荐渐进路线：A → C（跳 B）

B（MCP Bridge）在 SDK 直接可用后变得不必要。SDK 本身提供了更简洁的 API。

---

## 5. 实施路线图

### v2.2 — SDK 脚本生成器（4-6 周）

**目标**：`/wf plan → 生成 plan.json + SDK 编排脚本`

```bash
# 用户流程
/wf "分析项目架构"
→ 插件生成 plan.json + 显示 DAG
→ 用户确认
→ 插件生成 workflow.py（SDK 编排脚本）
→ 用户运行：python3 workflow.py
→ 结果写回 state.json，插件展示
```

**核心代码改动**：

`workflow_engine.py` 新增 `generate_sdk_script(plan_json) → str`：
- 将 `plan.tasks` 映射为 `AgentDefinition` 字典
- 读取 `agents/` 目录中的 YAML 前置元数据 → 提取 tools/model/prompt
- 生成 `pipeline()` 和 `converge()` 包装函数
- 生成 `async def main():` 入口

**生成脚本的 `pipeline()` 实现**：
```python
async def pipeline(stages: list[list[Task]], state: dict):
    for stage in stages:
        # 每个 stage 内并行启动
        results = await parallel_dispatch(stage, state)
        state.update(results)
        if state.should_abort():
            break
    return state
```

### v2.3 — 完整引擎（6-8 周）

- 收敛循环（多轮验证直到 new_findings == 0）
- 结构化输出强制（JSON schema 校验）
- 状态持久化与恢复（checkpoint）
- 流式进度回调

### v3.0 — 二进制分发 + 一键安装（远期）

- `pip install workflow-orchestrator` 包含 SDK 脚本引擎
- `wf init` 一键设置环境
- 插件内嵌 SDK 调用（如果 Claude Code 开放此能力）

---

## 6. 对比总结

| | v2.1.1 | v2.2 | v2.3 | 官网 DW |
|---|---|---|---|---|
| **子 Agent 生成** | Agent() 主上下文 | ✅ SDK Task | ✅ SDK Task | agent() |
| **上下文隔离** | ❌ 共享 | ✅ SDK 独立 | ✅ SDK 独立 | ✅ |
| **并行语义** | 手动批量 | pipeline() 脚本 | ✅ 就绪队列 | ✅ pipeline() |
| **收敛循环** | 单次 | 单次 | ✅ 多轮 | ✅ |
| **规模** | ~15 | ~30 | ~50 | ~1000 |
| **状态管理** | JSON + 上下文 | SDK 变量 | ✅ 持久化 | ✅ JS 变量 |
| **Agent 定义** | 手动 prompt | ✅ 复用 agents/ | ✅ 复用 agents/ | 内联 |

---

## 7. 立即行动

v2.2 是当前最高 ROI 的步骤：
1. `workflow_engine.py` 新增 `generate_sdk_script()` 
2. Agent 定义从 `agents/*.md` 自动映射为 `AgentDefinition`
3. 生成脚本输出 `pipeline()` + 收敛循环框架
4. 保留现有协议模式作为兼容回退
