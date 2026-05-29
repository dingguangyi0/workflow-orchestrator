# ⚡ Workflow Orchestrator

> 100% 复刻 Claude Code Dynamic Workflows — 多 Agent 工作流编排插件

## 概述

Workflow Orchestrator 是一个 Claude Code 插件，将复杂目标自动拆解为子任务，构建依赖图 (DAG)，分层并行调度多个 AI Agent 执行，并提供实时可视化监控。在任何 Claude Code 环境（包括 DeepSeek 代理）中模拟 ultracode 级编排能力。

## 快速开始

```
/workflow 重构用户认证模块，增加 OAuth2.0 支持
```

或者简写：

```
/wf 为所有 API 接口添加请求参数校验
```

## 功能特性

### 🧠 智能拆解
- 自动将复杂目标拆解为 5-10 个独立可执行的子任务
- 自动分析依赖关系，构建无循环依赖图
- 最大化并行度 — 无依赖的任务同时执行

### ⚡ 并行调度
- 同层任务批量并行启动（一次触发，全部执行）
- 分层执行 — 依赖满足后立即进入下一层
- 上下文自动传递 — 前置任务输出摘要传给下游

### 📊 可视化监控
- ASCII 艺术风格实时进度面板
- 彩色进度条（绿=完成，黄=进行中，灰=等待，红=失败）
- 逐层展开的任务状态展示
- Mermaid 流程图生成（支持渲染的终端/IDE）

### 🔧 容错机制
- 任务失败自动重试（默认 1 次）
- 智能降级：非关键任务失败 → 跳过继续
- 阻塞检测：关键任务失败 → 暂停并询问用户
- 超过 30% 失败率 → 自动暂停保护

### 📋 完整报告
- 执行时间线
- 每个任务的详细输出
- 失败原因分析
- 代码变更汇总

## 命令参考

| 命令 | 说明 |
|------|------|
| `/workflow <goal>` | 启动工作流编排 |
| `/wf <goal>` | 简写形式 |
| `/workflow status` | 查看当前运行的工作流状态 |
| `/workflow report` | 生成最近一次执行的完整报告 |

## 可用 Agent 类型

| Agent | 模型 | 用途 | 工具 |
|-------|------|------|------|
| 🧠 orchestrator | Opus | 目标拆解、DAG 构建 | Read, Bash, Grep, Glob |
| 🔍 explorer | Haiku | 代码搜索、架构分析 | Read, Bash, Grep, Glob |
| 🛠️ implementer | Sonnet | 代码编写、功能实现 | Read, Write, Edit, Bash, Grep, Glob |
| 📋 reviewer | Sonnet | 代码审查、测试验证 | Read, Bash, Grep, Glob |
| 🔧 worker | Haiku | 文档、配置、脚本、研究 | Read, Write, Edit, Bash, Grep, Glob, WebSearch |

## 执行流程

```
用户输入 /workflow <目标>
        │
        ▼
  Phase 1: 目标分析 → orchestrator Agent 拆解
        │
        ▼
  Phase 2: 可视化展示 → ASCII 面板 + Mermaid 图 → 用户确认
        │
        ▼
  Phase 3: 分层并行执行
        │     Layer 0: [T1] [T2] [T3] ← 同时启动
        │     Layer 1: [T4] [T5]     ← 依赖满足后同时启动
        │     Layer 2: [T6]          ← 最后执行
        │
        ▼
  Phase 5: 失败处理 → 重试 → 降级 → 升级
        │
        ▼
  Phase 6: 汇总报告 → 执行时间线 → 产出清单
```

## 配置

环境变量（可选）：

| 变量 | 默认值 | 说明 |
|------|--------|------|
| `WF_MAX_RETRIES` | `1` | 每个任务最大重试次数 |
| `WF_MAX_TASKS` | `15` | 单次工作流最大任务数 |
| `WF_CHECK_INTERVAL` | `60` | 进度检查间隔（秒） |
| `WF_STATE_DIR` | `/tmp/claude-workflow-<pid>` | 状态文件目录 |

## 与原生 Dynamic Workflows 对比

| 维度 | 原生 Ultracode | 本插件 |
|------|---------------|--------|
| 任务拆解 | ✅ 自动 | ✅ 自动 |
| DAG 构建 | ✅ 自动 | ✅ 自动 + 可视化 |
| 并行执行 | ✅ 自动 | ✅ 同层批量并行 |
| 进度追踪 | ✅ 内置 | ✅ 实时面板 + 状态文件 |
| 失败重试 | ✅ 内置 | ✅ 自动重试 + 降级 |
| 结果报告 | ✅ 内置 | ✅ Markdown + JSON |
| API 依赖 | ❌ 需要 Pro/Max plan | ✅ 无依赖，任意代理可用 |
| 用户可见性 | 低（黑盒） | 高（每层确认 + 实时面板） |

## 文件结构

```
workflow-orchestrator/
├── .claude-plugin/plugin.json    # 插件清单
├── skills/workflow/
│   ├── SKILL.md                  # 核心编排协议
│   └── scripts/
│       ├── task_schema.py        # 数据结构 + 校验
│       ├── dag.py                # DAG 构建 + 可视化
│       ├── reporter.py           # 报告生成
│       └── monitor.py            # 实时监控面板
├── agents/
│   ├── orchestrator.md           # 规划 Agent
│   ├── explorer.md               # 探索 Agent
│   ├── implementer.md            # 实现 Agent
│   ├── reviewer.md               # 审查 Agent
│   └── worker.md                 # 通用 Agent
├── hooks/hooks.json              # 生命周期钩子
└── docs/README.md                # 本文档
```

## 示例场景

### 场景 1：新功能开发
```
/wf 为用户模块添加邮箱验证功能
→ T1: 探索用户模块架构
→ T2-T3: 实现验证逻辑 + 邮件发送（并行）
→ T4: 编写测试
→ T5: 审查
```

### 场景 2：代码重构
```
/wf 将支付模块从 REST 迁移到 GraphQL
→ T1: 探索支付模块 + 现有 REST 接口
→ T2: 研究 GraphQL schema 设计
→ T3-T4: 实现 schema + resolver（并行）
→ T5: 迁移测试
→ T6: 审查 + 集成测试
```

### 场景 3：问题排查
```
/wf 排查用户登录超时问题
→ T1: 探索认证流程
→ T2: 检查日志配置
→ T3: 分析超时配置（并行 T1/T2）
→ T4: 定位根因
→ T5: 修复建议
```

## 许可证

MIT
