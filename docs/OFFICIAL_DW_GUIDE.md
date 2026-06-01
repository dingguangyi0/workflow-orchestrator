# Claude Code 官方 Dynamic Workflows 使用指南

> 官方文档：[code.claude.com/docs/en/workflows](https://code.claude.com/docs/en/workflows)  
> 发布公告：[Introducing dynamic workflows](https://claude.com/blog/introducing-dynamic-workflows-in-claude-code)（2026-05-28）  
> 版本要求：Claude Code v2.1.154+

---

## 1. 概述

Dynamic Workflows 将任务转化为 **JavaScript 编排脚本**，在隔离运行时执行。脚本调度子 Agent 并行工作，中间结果存在脚本变量中（不进上下文窗口），最终只返回汇总结果。

```
普通模式                          Dynamic Workflows
──────────                        ──────────────────
主 Claude 做一切                   主 Claude 写编排脚本
单 Agent 串行                     脚本并行调度 16+ 子 Agent
结果全在上下文                    中间结果在脚本变量（不占上下文）
适合单文件/模块                   适合整个代码库（最多 1000 Agent）
```

### 环境要求

| 条件 | 说明 |
|------|------|
| Claude Code 版本 | v2.1.154+ |
| 付费方案 | Pro（需手动启用）/ Max / Team / Enterprise |
| API 后端 | Anthropic API、Amazon Bedrock、Vertex AI、Microsoft Foundry |

---

## 2. 三种触发方式

### 方式一：提示词包含 `workflow` 关键词

在提示词中自然包含单词 "workflow"，Claude Code 自动识别：

```
Run a workflow to check all TypeScript files for type errors and auto-fix them
```

- 关键词高亮 → 按 **Alt+W**（macOS Option+W）跳过触发
- `/config` 中可关闭关键词触发

### 方式二：`/deep-research`（内置工作流）

```
/deep-research Bun vs Node.js vs Deno HTTP server performance 2026
```

内部 5 阶段：Scope（5 角度分解）→ Search（5 路并行搜索）→ Fetch（提取声明）→ Verify（对抗验证）→ Synthesize（引用报告）

### 方式三：`/effort ultracode`

```
/effort ultracode
```

启用后，Claude 为每个实质性任务自动判断是否启动工作流。仅当前会话有效。

---

## 3. 执行流程

### Step 1：提交任务
```
Run a workflow to find all files with hardcoded API keys in src/,
replace with env vars, and verify tests pass after each change
```

### Step 2：审查脚本（Ctrl+G）
按 **Ctrl+G** 打开生成的 JavaScript 编排脚本——确认范围无误 → "Yes, run it"

### Step 3：监控进度（`/workflows`）

| 按键 | 操作 |
|------|------|
| ↑/↓ | 选择阶段或 Agent |
| Enter | 进入详情 |
| **p** | 暂停/恢复 |
| **x** | 停止选中或全部 |
| **r** | 重启运行中的 Agent |
| **s** | 保存为命令 |
| Esc | 返回上一级 |

### Step 4：查看结果
所有子 Agent 完成 → 汇总报告返回会话。

---

## 4. 脚本 DSL API

工作流脚本是导出 `meta` 对象的 JavaScript 文件。脚本运行在隔离的 `node:vm` 沙箱中（无 Node.js API、无 `Date.now()`/`Math.random()`）。

### 核心函数

#### `agent(prompt, opts)` — 生成子 Agent
```javascript
const result = await agent(
  '审查 src/auth.ts 的安全漏洞',
  {
    label: 'auth-review',           // 显示名称
    phase: '安全审查',               // 分组
    schema: {                        // 强制结构化输出
      type: 'object',
      properties: {
        issues: { type: 'array' },
        verdict: { type: 'string', enum: ['pass', 'fail'] }
      }
    },
    model: 'sonnet',                 // haiku | sonnet | opus
    isolation: 'worktree',           // Git worktree 隔离
    agentType: 'Explore',            // 自定义子 Agent 类型
  }
)
```

#### `pipeline(items, ...stages)` — 流水线（无屏障）
```javascript
// 每个 item 完成一个 stage 立即流入下一个——不等慢的
const results = await pipeline(
  ['auth.ts', 'db.ts', 'api.ts'],
  // Stage 1: 实现
  (prev, file) => agent(`实现 ${file} 的功能`, { phase: 'Implement' }),
  // Stage 2: 测试
  (prev, file) => agent(`为 ${file} 写测试`, { phase: 'Test' }),
)
// auth.ts 完成实现 → 立刻进入测试阶段，不等 db.ts 实现完成
```

#### `parallel(thunks)` — 并行屏障
```javascript
// 所有任务同时启动，等全部完成才返回
const [security, perf, style] = await parallel([
  () => agent('安全审查', { phase: 'Review', schema: FINDINGS }),
  () => agent('性能审查', { phase: 'Review', schema: FINDINGS }),
  () => agent('风格审查', { phase: 'Review', schema: FINDINGS }),
])
```

#### `phase(title)` — 阶段分组
```javascript
phase('探索')
// 后续所有 agent() 归入此阶段

phase('验证')
// 切换到新阶段
```

#### `log(message)` — 进度输出
```javascript
log(`已处理 ${count}/${total} 个文件`)
```

#### `budget` — Token 预算控制
```javascript
while (budget.remaining() > 50_000 && bugs.length < 10) {
  const result = await agent('继续找 bug', { schema: BUGS })
  bugs.push(...result.bugs)
  log(`${bugs.length} bugs found, ${budget.remaining()} tokens left`)
}
```

---

## 5. 完整示例

### 示例 1：多维度代码审查

```javascript
export const meta = {
  name: 'code-review',
  description: 'Multi-angle code review with adversarial verification',
  phases: [
    { title: 'Review', detail: 'Parallel review across dimensions' },
    { title: 'Verify', detail: 'Adversarially verify each finding' },
  ],
}

const DIMENSIONS = [
  { key: 'security', prompt: 'Review for OWASP vulnerabilities...' },
  { key: 'performance', prompt: 'Find performance bottlenecks...' },
  { key: 'correctness', prompt: 'Check for logic errors...' },
]

// Stage 1: Review（并行）
phase('Review')
const reviews = await parallel(
  DIMENSIONS.map(d => () => agent(d.prompt, { label: d.key, schema: FINDINGS }))
)

// Stage 2: Verify（每个发现逐一验证）
phase('Verify')
const findings = reviews.flatMap(r => r.findings).filter(Boolean)
const verified = await pipeline(
  findings,
  f => agent(`Adversarially verify: ${f.title}`, { schema: VERDICT })
)

// 只保留验证通过的
return verified.filter(v => v.isReal)
```

### 示例 2：收敛循环（Loop-until-dry）
```javascript
// 持续找 bug 直到连续 2 轮无新发现
const seen = new Set(), confirmed = []
let dry = 0

while (dry < 2) {
  const found = (await parallel(FINDERS.map(f => () =>
    agent(f.prompt, { phase: 'Find', schema: BUGS })
  ))).flatMap(r => r.bugs)

  const fresh = found.filter(b => !seen.has(key(b)))
  if (!fresh.length) { dry++; continue }

  dry = 0
  fresh.forEach(b => seen.add(key(b)))
  confirmed.push(...fresh)  // 进一步验证...
}

return confirmed
```

### 示例 3：大规模迁移
```javascript
export const meta = {
  name: 'migrate-react-classes',
  description: 'Migrate React class components to functional components',
}

// 发现所有需要迁移的文件
const files = await agent(
  'Find all React class components in src/ that need migration',
  { phase: 'Discover', schema: { type: 'object', properties: { files: { type: 'array' } } } }
)

// 逐个迁移 + 验证（pipeline，不等慢任务）
phase('Migrate')
const results = await pipeline(
  files.files,
  (prev, file) => agent(`Migrate ${file} to functional component`, { phase: 'Migrate' }),
  (prev, file) => agent(`Run tests for ${file} and verify migration`, { phase: 'Verify' }),
)
```

---

## 6. 成本控制

> ⚠️ 官方警告：工作流耗时可能远高于普通对话。

| 策略 | 做法 |
|------|------|
| 缩小范围 | `src/routes/**` 而非整个项目 |
| 分阶段 | 先跑只读分析，确认后再跑修改 |
| 模型分层 | `haiku` 做探索，`sonnet` 做实现，`opus` 做关键决策 |
| 预算控制 | `while (budget.remaining() > 50_000)` 限制循环深度 |
| 随时停止 | `/workflows` → `x`，已完成结果不丢失 |
| 查看消耗 | `/usage` 做前后对比 |

---

## 7. Sub-agents 基础（不写脚本也能用）

如果不写 JS 脚本，也可以直接使用 `.claude/agents/` 目录定义子 Agent：

```markdown
---
name: code-reviewer
description: Use after feature branch is staged, before merging
tools: Read, Grep, Glob
model: sonnet
---

You are a senior code reviewer. When invoked:
1. Run `git diff` to see changed files
2. Review for security, correctness, performance
3. Return structured findings with severity
```

```markdown
---
name: test-writer
description: Write unit and integration tests for modified code
tools: Read, Write, Edit, Bash
model: sonnet
---

You are a test engineer. Generate comprehensive tests.
```

使用：Claude 会自动判断何时调用这些子 Agent，或手动指定 `--agents test-writer`。

---

## 8. 已知限制

| 限制 | 说明 |
|------|------|
| 并发 | 最多 16 并行（受 CPU 核心影响） |
| 总量 | 单次最多 1000 个 Agent |
| 不可中途输入 | 运行中不可交互（权限提示除外） |
| 脚本无 I/O | 脚本本身不能读写文件（Agent 可以） |
| Session 依赖 | 仅同 session 内可恢复 |
| Research Preview | 规格可能变更 |

---

## 9. 保存与复用

成功运行的工作流 → `/workflows` → 选中 → 按 `s` 保存：

| 位置 | 路径 | 作用域 |
|------|------|--------|
| 项目 | `.claude/workflows/` | 团队共享 |
| 个人 | `~/.claude/workflows/` | 跨项目 |

保存后作为斜杠命令使用：`/<name>`

---

## 10. 与 WF Orchestrator 插件的关系

| | 官方 Dynamic Workflows | WF Orchestrator (`/wf`) |
|---|---|---|
| **命令** | `/workflow` + 关键词 | `/wf` |
| **脚本语言** | JavaScript | Python（辅助） |
| **规模** | 1000 Agent / 16 并发 | ~15 Agent（协议模式） |
| **订阅要求** | Pro+ 计划 | 无限制 |
| **平台** | Anthropic + Bedrock + Vertex | DeepSeek / OpenRouter 等任意代理 |
| **模板** | 保存为命令 | 5 个内置模板 + 自定义 |
| **DAG 可视化** | `/workflows` TUI | ASCII + Mermaid |
| **集成** | 原生 | Agent SDK 桥接（即将推出） |

**定位**：官方 DW 适合大规模代码库级编排（审计、迁移、100+ Agent 扫荡）。WF Orchestrator 适合中等规模可定制编排、跨平台兼容、模板复用场景。
