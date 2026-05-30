# ⚡ Workflow Orchestrator for Claude Code

> 100% 复刻 Claude Code Dynamic Workflows — 在任何 Claude Code 环境（含第三方代理）中实现多 Agent 自动编排

<p align="center">
  <b>v2.0.0 · Goal → DAG → Parallel Agents → Script Engine → Adversarial Verify → Report</b>
</p>

---

## 📖 目录

- [是什么](#-是什么)
- [快速开始](#-快速开始)
- [安装](#-安装)
- [命令参考](#-命令参考)
- [内置工作流模板](#-内置工作流模板)
- [架构设计](#-架构设计)
- [Agent 类型](#-agent-类型)
- [Superpowers 集成](#-superpowers-集成)
- [配置](#-配置)
- [执行流程](#-执行流程)
- [与原生 Dynamic Workflows 对比](#-与原生-dynamic-workflows-对比)
- [文件结构](#-文件结构)
- [常见问题](#-常见问题)

---

## 💡 是什么

**Workflow Orchestrator** 是一个 Claude Code 插件，实现了完整的多 Agent 工作流编排引擎。

当你面对一个复杂目标（比如"为 API 网关添加限流功能"或"调研微服务架构方案"），它自动：

1. **拆解**目标为 5-10 个独立子任务
2. **构建 DAG** 依赖图，找出哪些任务可以并行
3. **生成脚本** — Python 编排脚本，编排逻辑脱离主上下文
4. **调度 Agent** — 同层任务同时启动，最大化效率
5. **对抗验证** — 每层完成后强制 Reviewer 挑战每个发现
6. **实时监控** — 事件驱动，Agent 完成自动显示状态
7. **汇总报告** — 自动生成完整 Markdown 执行报告

### v2.0 新特性

| 特性 | 说明 |
|------|------|
| 🐍 **编排脚本引擎** | plan.json → 自动生成可执行 Python 编排脚本 |
| 🔍 **强制对抗验证** | 每层完成后自动 reviewer，❓标记自动重查 |
| 💾 **细粒度 checkpoint** | Agent 级断点恢复，不仅是 Layer 级 |
| 📺 **脚本可视化** | `dag.py --script` 展示生成脚本的 DSL 视图 |

### 为什么需要它

| 场景 | 没有 Workflow | 有了 Workflow |
|------|-------------|-------------|
| 多模块功能开发 | 手动一步步做，容易遗漏 | 自动拆解 7 任务，3 层并行执行 |
| 代码审查 | 一个 Agent 看完，可能有盲区 | 3 个 Agent 并行扫描 + 对抗验证 |
| 技术调研 | 自己搜、自己整理、自己写 | deep-research 模板一键完成 |
| 使用 DeepSeek 代理 | Dynamic Workflows 不可用 ❌ | 完全可用 ✅ |

---

## 🚀 快速开始

### 30 秒体验

```
/wf use deep-research Claude Code 插件生态现状
```

这会启动一个 5 任务、3 层的深度调研工作流，自动搜索 → 交叉验证 → 生成报告。

### 自定义目标

```
/wf 为支付模块添加微信支付和支付宝支付支持
/wf 重构用户服务，将 REST API 迁移到 GraphQL  
/wf 审查 src/api/ 下的所有接口安全性
```

---

## 📦 安装

### 方式一：从 GitHub 安装（推荐）

```bash
# 克隆插件
git clone https://github.com/你的用户名/workflow-orchestrator.git ~/.claude-plugin/workflow-orchestrator

# 链接技能到 Claude Code
ln -s ~/.claude-plugin/workflow-orchestrator/skills/workflow ~/.claude/skills/workflow

# 在项目中启用插件（编辑项目 .claude/settings.json）
{
  "enabledPlugins": {
    "workflow-orchestrator": true
  }
}

# 安装内置工作流模板
python3 ~/.claude-plugin/workflow-orchestrator/skills/workflow/scripts/workflow_manager.py install-builtins
```

### 方式二：从 Claude Code 插件市场安装

```bash
# 添加本仓库为插件源
/plugin marketplace add 你的用户名/workflow-orchestrator

# 安装插件
/plugin install workflow-orchestrator@你的用户名-workflow-orchestrator
```

### 方式三：手动安装

```bash
# 复制所有文件到 Claude Code 插件目录
cp -r workflow-orchestrator ~/.claude-plugin/

# 链接技能
ln -s ~/.claude-plugin/workflow-orchestrator/skills/workflow ~/.claude/skills/workflow

# 安装模板
python3 ~/.claude-plugin/workflow-orchestrator/skills/workflow/scripts/workflow_manager.py install-builtins
```

### 验证安装

```
/wf status
```

显示 "No active workflow" 即为安装成功。

---

## 📋 命令参考

### 核心命令

| 命令 | 说明 | 示例 |
|------|------|------|
| `/workflow <目标>` | 启动完整工作流 | `/wf 添加 OAuth2.0 认证` |
| `/wf <目标>` | 同上（简写） | `/wf 重构支付模块` |
| `/wf status` | 查看当前工作流状态 | `/wf status` |
| `/wf report` | 生成最近执行报告 | `/wf report` |
| `/wf resume` | 恢复中断的工作流 | `/wf resume` |

### 模板命令

| 命令 | 说明 | 示例 |
|------|------|------|
| `/wf template` | 列出所有可用模板 | `/wf template` |
| `/wf use <模板> <目标>` | 使用模板启动工作流 | `/wf use superpowers-enhanced 添加退款功能` |
| `/wf save <名称>` | 保存当前工作流为模板 | `/wf save my-payment-workflow` |

### 监控命令

| 命令 | 说明 | 示例 |
|------|------|------|
| `/wf status` | 完整仪表盘 | — |
| `/wf report` | Markdown 报告 | — |

---

## 🎯 内置工作流模板

### 1. deep-research — 深度调研

复刻 Claude Code 原生的 `/deep-research` 命令。

**流程**: 官方资料 → 社区实践 → 竞品方案 → 交叉验证 → 生成报告

```
/wf use deep-research 分布式事务在微服务中的最佳实践
```

**5 任务，3 层**:
```
Layer 0: T1(官方/权威来源) + T2(社区/实践经验) + T3(竞品/替代方案) → 并行
Layer 1: T4(交叉验证 — 挑战每个发现，搜索反例)
Layer 2: T5(综合报告 — 标记置信度)
```

### 2. code-review — 代码审查

多角度代码审查 + 对抗验证。

**流程**: 架构分析 → 安全扫描 → 性能分析 → 交叉验证 → 报告

```
/wf use code-review src/services/payment/
```

**5 任务，2 层**:
```
Layer 0: T1(架构) + T2(安全) + T3(性能) → 3 Agent 并行扫描
Layer 1: T4(对抗验证 — 挑战 T1-T3 的每个发现) → T5(综合报告)
```

### 3. superpowers-enhanced — 增强开发

集成 Superpowers 框架的 TDD 工程纪律。**推荐用于所有代码开发任务。**

**流程**: Brainstorming → 代码探索 → 编写计划 → TDD 实现 → 对抗审查 → 修复 → 最终验证

```
/wf use superpowers-enhanced 为 API 网关添加基于 IP 的速率限制
```

**7 任务，6 层**:
```
Layer 0: T1(需求分析/Socratic问答) + T2(代码库探索) → 并行
Layer 1: T3(编写实现计划 — 微任务拆解)
Layer 2: T4(TDD 实现 — RED→GREEN→REFACTOR，含自我审查)
Layer 3: T5(对抗代码审查 — 6 阶段检查，严重度分类)
Layer 4: T6(修复审查发现的问题)
Layer 5: T7(最终验证 — 全量测试 + 分支完成)
```

### 4. bug-hunt — Bug 扫描

系统化 Bug 扫描，按错误类型分类。

**流程**: 错误处理 → 边界条件 → 资源管理 → 交叉验证 → 报告

```
/wf use bug-hunt src/
```

### 5. migration — 代码迁移

系统化代码迁移/重构。

**流程**: 探索现状 → 研究目标 → 设计策略 → 执行迁移 → 验证

```
/wf use migration 将日志库从 logrus 迁移到 zerolog
```

---

## 🏗️ 架构设计

### 六阶段协议

```
用户输入 /wf <目标>
       │
       ▼
Phase 0: 触发检测 → 判断任务类型(研究/开发)，路由子命令
       │
       ▼
Phase 1: 目标拆解 → Orchestrator Agent 生成 JSON 任务计划
       │
       ▼
Phase 2: 可视化确认 → ASCII 面板 + Mermaid DAG → 用户确认
       │
       ▼
Phase 3: 分层并行执行
       │     Layer 0: [T1] [T2] [T3] ← 同时启动
       │     Layer 1: [T4] [T5]     ← 依赖满足后并行
       │     Layer 2: [T6]          ← 最终执行
       │
       ▼
Phase 4.5: 对抗验证 → Reviewer 挑战每个发现
       │
       ▼
Phase 5: 失败处理 → 自动重试 → 降级 → 阈值保护
       │
       ▼
Phase 6: 汇总报告 → 时间线 + 详情 + 产出清单 → 保存模板
```

### DAG 引擎

使用拓扑排序算法将任务分层：

```python
# 核心算法
def topological_layers(tasks):
    layers = []
    completed = set()
    remaining = {t.id: set(t.dependencies) for t in tasks}
    
    while remaining:
        ready = [tid for tid, deps in remaining.items() 
                 if deps.issubset(completed)]
        layers.append(ready)
        completed.update(ready)
        for tid in ready:
            del remaining[tid]
    return layers
```

### 状态管理

每个工作流维护一个 `state.json`，持久化到磁盘：

```json
{
  "plan": { "goal": "...", "tasks": [...] },
  "results": {
    "T1": { "status": "completed", "output_summary": "...", "started_at": "...", "completed_at": "..." },
    "T2": { "status": "in_progress", ... },
    "T3": { "status": "pending", ... }
  },
  "current_layer": 1,
  "total_layers": 3,
  "phase": "executing"
}
```

支持断点恢复 — 中断后 `/wf resume` 从断点继续，已完成的任务不重复执行。

---

## 🤖 Agent 类型

| Agent | 模型 | 角色 | 何时使用 |
|-------|------|------|---------|
| 🧠 **orchestrator** | Opus | 目标拆解、DAG 构建 | Phase 1 自动调用 |
| 🔍 **explorer** | Haiku | 代码搜索、架构分析（只读） | 需要理解现有代码时 |
| 🛠️ **implementer** | Sonnet | 代码编写、功能实现 | 需要修改/创建代码时 |
| 📋 **reviewer** | Sonnet | 代码审查、质量验证 | 实现完成后自动调用 |
| 🔧 **worker** | Haiku | 文档、配置、研究、脚本 | 通用任务 |
| 🦸 **superpowers-developer** | Sonnet | TDD 实现 + 自我审查 | Superpowers 增强模板 |
| 🦸 **superpowers-reviewer** | Sonnet | 对抗审查 + 6 阶段检查 | Superpowers 增强模板 |

> **注意**: Agent 的具体模型取决于你的 Claude Code 配置和 API 代理。上述模型为推荐配置。

---

## 🦸 Superpowers 集成

本插件与 [Superpowers](https://github.com/obra/superpowers)（177K+ stars）深度集成。

### 分工

| 层 | Workflow Orchestrator | Superpowers |
|----|----------------------|-------------|
| **宏观** | 目标拆解、DAG 编排、并行调度、监控 | — |
| **微观** | — | TDD、代码审查、Git 安全、自我审查 |

### 集成效果

```
/wf use superpowers-enhanced 实现用户邮箱验证功能

自动执行:
  1. Brainstorming — 明确需求、边界条件、设计方案
  2. 代码探索 — 理解现有用户模块架构
  3. 编写计划 — 拆成 2-5 分钟的微任务
  4. TDD 实现 — RED(写测试) → GREEN(最小实现) → REFACTOR(重构)
  5. 对抗审查 — 6 阶段检查(规格/正确性/安全/性能/质量/测试)
  6. 修复问题 — 处理审查发现
  7. 最终验证 — 全量测试 + 分支完成
```

---

## ⚙️ 配置

### 环境变量

| 变量 | 默认值 | 说明 |
|------|--------|------|
| `WF_MAX_RETRIES` | `1` | 每个任务最大重试次数 |
| `WF_MAX_TASKS` | `15` | 单次工作流最大任务数 |
| `WF_CHECK_INTERVAL` | `60` | 进度检查间隔（秒） |
| `WF_STATE_DIR` | `/tmp/claude-workflow-session` | 状态文件目录 |

### 设置示例

在 `~/.claude/settings.json` 或项目 `.claude/settings.json` 中：

```json
{
  "enabledPlugins": {
    "workflow-orchestrator": true
  },
  "effortLevel": "xhigh",
  "model": "opus"
}
```

---

## 📊 执行流程示意

```
User: /wf use deep-research Claude Code 插件生态

⚡ Dynamic Workflow initializing...
🎯 Goal: 深度调研 Claude Code 插件生态
🧠 Loading template: deep-research (5 tasks, 3 layers)

╔══════════════════════════════════════════════════════════════╗
║  ⚡ DYNAMIC WORKFLOW                                         ║
║  🎯 Deep research: Claude Code 插件生态                       ║
╠══════════════════════════════════════════════════════════════╣
║  ✅ 0 done  🔄 0 running  ⬜ 5 pending                       ║
║  ░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░ 0%                    ║
╠══════════════════════════════════════════════════════════════╣
║  ⚡ Layer 0                                                   ║
║     ⬜ 🔧 [T1] Research from official sources                 ║
║     ⬜ 🔧 [T2] Research from community                        ║
║     ⬜ 🔧 [T3] Research competitive alternatives               ║
║  📋 Layer 1                                                   ║
║     ⬜ 🔧 [T4] Cross-verify and challenge findings             ║
║  📋 Layer 2                                                   ║
║     ⬜ 🔧 [T5] Synthesize and generate report                  ║
╚══════════════════════════════════════════════════════════════╝

Proceed with execution? [Y/n]

User: Y

⚡ Executing Layer 0 — 3 agents in parallel...
[30 seconds later...]

╔══════════════════════════════════════════════════════════════╗
║  ✅ 3 done  🔄 1 running  ⬜ 1 pending                       ║
║  [████████████████████████░░░░░░░░░░] 60%                    ║
║  ✅ Layer 0 — all 3 research tasks complete                  ║
║  ⚡ Layer 1 — cross-verifying findings...                     ║
╚══════════════════════════════════════════════════════════════╝

[60 seconds later...]

🎉 Workflow Complete!
✅ 5/5 tasks completed successfully

📁 Report saved. Use /wf report to view.
💾 Save as template? [Y/n]
```

---

## 🔬 与原生 Dynamic Workflows 对比

| 维度 | 原生 Dynamic Workflows | Workflow Orchestrator |
|------|----------------------|----------------------|
| **任务拆解** | JS 脚本动态生成 | Orchestrator Agent + JSON Plan |
| **DAG 构建** | 自动 | 自动 + 可视化（ASCII/Mermaid） |
| **最大并发** | 16 并发，1000 总 Agent | 受 Claude Code Agent 工具限制 |
| **对抗验证** | 内置 | ✅ Phase 4.5 协议 |
| **断点恢复** | 内置 | ✅ Checkpoint + `/wf resume` |
| **工作流保存** | 保存为 slash command | ✅ 模板系统 + `/wf save` |
| **可视化** | `/workflows` 面板 | ✅ Monitor Dashboard + Compact |
| **Plan 依赖** | ❌ 需要 Max/Team Plan | ✅ 零依赖，任意代理可用 |
| **第三方代理** | ❌ DeepSeek 等不可用 | ✅ 完全兼容 |
| **TDD 集成** | ❌ | ✅ Superpowers 集成 |
| **预置模板** | `/deep-research` | ✅ 5 个模板 |
| **用户可见性** | 低（黑盒） | 高（每层确认 + 实时面板） |

---

## 📁 文件结构

```
workflow-orchestrator/
├── README.md                          # 本文件
├── .claude-plugin/
│   └── plugin.json                    # 插件清单 (v1.2.0)
├── .gitignore
│
├── skills/workflow/
│   ├── SKILL.md                       # 核心编排协议 (858 行)
│   └── scripts/
│       ├── task_schema.py             # 数据结构、校验、状态管理
│       ├── dag.py                     # DAG 构建、可视化 (Mermaid + ASCII)
│       ├── reporter.py                # 报告生成 (Markdown + 摘要)
│       ├── monitor.py                 # 实时监控面板 (ANSI 彩色终端)
│       └── workflow_manager.py        # 模板管理、检查点、断点恢复
│
├── agents/
│   ├── orchestrator.md                # 规划 Agent (Opus)
│   ├── explorer.md                    # 探索 Agent (Haiku)
│   ├── implementer.md                 # 实现 Agent (Sonnet)
│   ├── reviewer.md                    # 审查 Agent (Sonnet)
│   ├── worker.md                      # 通用 Agent (Haiku)
│   ├── superpowers-developer.md       # TDD 开发者 (Sonnet)
│   └── superpowers-reviewer.md        # 对抗审查者 (Sonnet)
│
├── hooks/
│   └── hooks.json                     # 生命周期钩子
│
└── docs/
    └── README.md                      # 简要文档
```

---

## ❓ 常见问题

### Q: 和原生 Dynamic Workflows 有什么区别？

原生 DW 需要 Max/Team Plan，且使用 Anthropic 官方 API。如果你使用 DeepSeek 或其他第三方代理，原生 DW 不可用。本插件在任何 Claude Code 环境都能工作。

### Q: 任务执行失败了怎么办？

插件内置了 3 级失败处理：
1. **自动重试** — 首次失败自动重试（带更详细的指令）
2. **智能降级** — 无下游依赖的任务标记为 skipped，不阻塞整体
3. **阈值保护** — 超过 30% 任务失败时暂停，询问用户

### Q: 支持多少并行任务？

理论上不限制，但受 Claude Code 的 Agent 工具限制。建议单层不超过 5 个并行任务，总任务数不超过 15。

### Q: 研究类任务为什么不用后台 Agent？

经验表明，WebSearch/WebFetch 类任务由主 Claude 同步执行更快（~30 秒 vs Agent 的 3-5 分钟），且质量相同。插件会自动检测任务类型，研究类使用同步策略。

### Q: 如何保存和复用工作流？

```
/wf save payment-refund-workflow    # 保存当前工作流
/wf template                        # 查看所有模板
/wf use payment-refund-workflow 添加支付宝退款  # 复用
```

### Q: 中断后如何恢复？

```
/wf resume    # 自动检测并恢复中断的工作流
```

已完成的任务不会重复执行，从断点继续。

### Q: 如何集成 Superpowers？

插件已内置 Superpowers 集成。使用 `superpowers-enhanced` 模板即可：

```
/wf use superpowers-enhanced <你的开发目标>
```

也可以先安装 Superpowers 插件，两者可以同时使用：

```
/plugin marketplace add obra/superpowers-marketplace
/plugin install superpowers@superpowers-marketplace
```

---

## 🤝 贡献

欢迎提交 Issue 和 PR！

- 🐛 Bug 报告：[GitHub Issues](https://github.com/你的用户名/workflow-orchestrator/issues)
- 💡 功能建议：同上
- 🔧 贡献代码：Fork → PR

### 开发

```bash
# 克隆仓库
git clone https://github.com/你的用户名/workflow-orchestrator.git
cd workflow-orchestrator

# 运行测试
cd skills/workflow/scripts
echo '{"goal":"test","tasks":[{"id":"T1","title":"test","agent":"worker","dependencies":[]}]}' | python3 task_schema.py --validate

# 安装内置模板
python3 workflow_manager.py install-builtins
```

---

## 📄 许可证

MIT License

---

<p align="center">
  <b>⚡ Built for developers who want Dynamic Workflows everywhere.</b><br>
  <sub>Works with Anthropic API • DeepSeek • OpenRouter • LiteLLM • Any Claude Code environment</sub>
</p>
