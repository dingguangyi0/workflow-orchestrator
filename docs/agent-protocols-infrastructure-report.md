# AI Agent 协议与基础设施调研报告
## T4: Agent Protocols & Infrastructure (MCP / A2A / Agentic RAG)

> **调研日期**: 2026-05-31  
> **调研范围**: 2025-2026 年 AI Agent 基础设施层的五大关键技术  
> **目标**: 为 Spring Boot 多模块企业平台架构的 AI Agent 升级提供技术选型依据

---

## 目录

1. [MCP (Model Context Protocol)](#1-mcp-model-context-protocol)
2. [A2A (Agent-to-Agent Protocol)](#2-a2a-agent-to-agent-protocol)
3. [OpenAI Agents SDK](#3-openai-agents-sdk)
4. [Microsoft AutoGen](#4-microsoft-autogen)
5. [Agentic RAG](#5-agentic-rag)
6. [能力矩阵综合对比](#6-能力矩阵综合对比)
7. [企业架构集成可行性评分](#7-企业架构集成可行性评分)
8. [MCP + A2A 与现有 API 网关对接方案](#8-mcp--a2a-与现有-api-网关对接方案)
9. [Agentic RAG 技术栈推荐 (Spring/Java 生态)](#9-agentic-rag-技术栈推荐-springjava-生态)
10. [成熟度评估](#10-成熟度评估)
11. [综合建议与实施路线图](#11-综合建议与实施路线图)

---

## 1. MCP (Model Context Protocol)

### 1.1 概述

MCP 是由 Anthropic 于 2024 年 11 月开源的标准协议，2025 年末已捐赠给 Linux 基金会联合管理。它定义了 AI 应用（客户端）与外部数据源/工具（服务器）之间的标准化接口。

**当前状态**: v2025-11-25 规范；Streamable HTTP 传输正在标准化；OAuth 2.1 认证规范制定中。

### 1.2 核心架构

MCP 采用两层架构：

```
┌──────────────────────────────────────────────────┐
│                  Data Layer                       │
│  (JSON-RPC 2.0: Lifecycle, Primitives,           │
│   Notifications)                                 │
├──────────────────────────────────────────────────┤
│                Transport Layer                    │
│  (stdio, HTTP+SSE, Streamable HTTP)              │
└──────────────────────────────────────────────────┘
```

### 1.3 核心原语 (Primitives)

| 原语 | 提供方 | 描述 |
|------|--------|------|
| **Tools** | Server | 可执行的函数（类似 API endpoint），LLM 可调用以完成操作 |
| **Resources** | Server | 数据源/上下文信息，如文件、数据库记录、API 响应 |
| **Prompts** | Server | 可复用的提示模板，参数化设计 |
| **Sampling** | Client | 请求 LLM 进行采样/补全（Server 发起） |
| **Elicitation** | Client | 向用户请求额外信息 |
| **Logging** | Client | 发送调试/日志消息 |
| **Tasks** | Utility | 持久化任务执行（长时间运行的操作） |

### 1.4 传输层协议

| 传输方式 | 应用场景 | 成熟度 |
|----------|----------|--------|
| **stdio** | 本地开发、子进程通信 | 生产就绪 |
| **HTTP + SSE** | 远程服务器、HTTP 环境 | 生产就绪 |
| **Streamable HTTP** | 云原生部署（替代 HTTP+SSE） | 标准化中 (2026) |

### 1.5 生命周期

```
Client                                    Server
  │─────────── initialize ────────────────→│
  │←──────── initialized ─────────────────│
  │─── notifications/initialized ─────────│
  │                                         │
  │────────── resources/list ─────────────→│
  │←──────── resources/list (resp) ────────│
  │────────── tools/list ─────────────────→│
  │←──────── tools/list (resp) ───────────│
  │                                         │
  │────────── tools/call ─────────────────→│
  │←──────── tools/call (resp) ───────────│
  │                                         │
  │─── notifications/tools/list_changed ──→│ (server 推送)
  │                                         │
  │─── notifications/resources/updated ───→│ (server 推送)
```

### 1.6 2026 年企业采用状况

| 指标 | 数值 |
|------|------|
| 活跃公共 MCP Server 数量 | 10,000+ |
| 月度 SDK 下载量 | 9,700 万+ (2026.03) |
| MCP 市场规摸 | ~$1.8B (2025) → 预计 $10.3B+ (2026) |
| GitHub 仓库中的 Server 总数 | ~36,000 |
| 企业采用痛点: 无认证 Server | 38.7% |
| 企业采用痛点: 速率限制缺失 | 97.6% |

**治理里程碑 (2025.09-2026.04)**:
- 2025.09: 官方 MCP Registry 上线
- 2025.12: 正式捐赠给 Linux 基金会 (联合发起方: Anthropic, Block, OpenAI; 白金成员: AWS, Google, Microsoft, Cloudflare, GitHub, Bloomberg)
- 2026.04: Linux 基金会举办首届 MCP Dev Summit (纽约)

### 1.7 与 GraphQL/gRPC API 层的对接

MCP 的 **Tools** 原语可以与现有 API 层形成互补关系：

- **GraphQL → MCP Tools**: 每个 GraphQL Query/Mutation 可以包装为 MCP Tool，利用 MCP 的 Tool Description 让 LLM 自省式发现和调用
- **gRPC → MCP Tools**: gRPC service method 映射为 MCP Tool；已有 `mcp-grpc-transport` 社区实现允许直接以 gRPC 协议承载 MCP 消息
- **REST API → MCP Resources**: REST 端点可暴露为 MCP Resources，支持 `resources/read` 和 `resources/list` 方法

---

## 2. A2A (Agent-to-Agent Protocol)

### 2.1 概述

A2A 由 Google 于 2025 年 4 月 Google Cloud Next 大会上发布，2025 年 6 月捐赠给 Linux 基金会。它是一种开放的 Agent 间通信协议，定义 Agent 如何发现彼此、安全地委派任务和协调协作。

**当前状态**: v1.0 已发布 (2026.03)；5 种语言的 SDK 生产就绪 (Python, JavaScript, Java, Go, .NET)。

### 2.2 核心设计理念

- **不透明 Agent 模型 (Opaque Agent)**: Agent 绝不暴露内部工具、记忆或推理过程 — 仅暴露声明的能力和输出。这对企业知识资产保护至关重要
- **任务 (Task)**: A2A 的核心抽象，是有状态的生命周期对象
- **Agent Card**: 基于 JSON 的能力发现文档，通过 `/.well-known/agent-card.json` 暴露

### 2.3 Agent Card 发现机制

```
┌──────────────────────────────────────────────┐
│         Agent Card (agent-card.json)          │
├──────────────────────────────────────────────┤
│  identity:   名称、描述、提供者、版本           │
│  interfaces: JSONRPC / gRPC / HTTP+JSON URL   │
│  capabilities: streaming, pushNotifications   │
│  skills:     技能 ID、标签、输入/输出示例       │
│  security:    OAuth 2.0 / OIDC / API Key      │
│  signatures:  加密签名 (JWS, ECDSA)            │
└──────────────────────────────────────────────┘
         ↓
   Client 通过 GET /.well-known/agent-card.json 发现
         ↓
   验证签名 → 获取 extendedAgentCard (认证后) → 建立通信
```

### 2.4 任务生命周期

```
                  ┌──────────┐
         submit → │submitted │
                  └────┬─────┘
                       ↓
                  ┌──────────┐
                  │ working  │ ←→ input-required
                  └────┬─────┘
                       ↓
           ┌───────────┼───────────┐
           ↓           ↓           ↓
      ┌─────────┐ ┌─────────┐ ┌──────────┐
      │completed│ │ failed  │ │canceled  │
      └─────────┘ └─────────┘ └──────────┘
```

- **submitted**: 客户端提交任务
- **working**: Agent 正在处理
- **input-required**: Agent 需要客户端提供更多信息
- **completed**: 任务成功完成，附带 Artifacts
- **failed**: 任务失败
- **canceled**: 任务被取消
- **rejected**: 任务被拒绝

### 2.5 传输层支持

| 传输绑定 | 协议 | 状态 |
|----------|------|------|
| **JSONRPC** | JSON-RPC 2.0 over HTTP + SSE | ✅ v1.0 核心 |
| **gRPC** | gRPC (Protocol Buffers 定义) | ✅ v1.0 |
| **HTTP+JSON** | REST 风格 | ✅ v1.0 |

### 2.6 行业采用状况 (截至2026.04)

- **150+ 组织**支持，22,000+ GitHub Stars
- **云平台**: Google Vertex AI Agentspace、Azure AI Foundry、AWS Bedrock AgentCore Runtime
- **企业 SaaS**: Salesforce, SAP, ServiceNow, Workday, Atlassian
- **AI 框架**: LangChain, CrewAI, LlamaIndex
- **未加入**: Anthropic (专注 MCP), OpenAI (尚未公开采用)

### 2.7 MCP vs A2A: 定位对比

| 维度 | MCP | A2A |
|------|-----|-----|
| **目的** | Agent ↔ 工具/数据 | Agent ↔ Agent |
| **方向** | 垂直 (Agent 向下调用) | 水平 (Agent 对等通信) |
| **粒度** | 函数级 (Tool 参数) | 服务级 (Agent 技能) |
| **状态** | 无状态函数调用 | 有状态任务生命周期 |
| **治理** | Linux 基金会 | Linux 基金会 |
| **心智模型** | "我能用什么?" | "谁能和我合作?" |
| **认证** | OAuth 2.1 (制定中) | OAuth 2.0 / OIDC / mTLS |

**结论**: MCP 和 A2A 是互补关系，而非竞争关系。企业级 Agent 平台通常需要两者并存。

---

## 3. OpenAI Agents SDK

### 3.1 概述

OpenAI Agents SDK 是一个轻量级多 Agent 编排框架，支持 Python (`openai-agents`) 和 TypeScript/JavaScript (`@openai/agents`)，于 2025 年发布。

**当前版本**: Python v0.7.0 / JS v0.x (2026)

### 3.2 核心概念

#### Agent 类型

| 类型 | 描述 | 使用场景 |
|------|------|----------|
| **Agent** | 基础 Agent，有指令、工具、Handoff 目标 | 通用任务处理 |
| **RealtimeAgent** | 支持语音实时交互的 Agent | 语音助手、实时对话 |

#### Agent 配置要素
- `name`: 标识
- `instructions`: 系统指令
- `model`: 使用的 LLM 模型
- `tools`: 可调用的工具函数 (`@function_tool`)
- `handoffs`: 可委派任务的目标 Agent 列表
- `input_guardrails` / `output_guardrails`: 安全护栏
- `output_type`: 结构化输出 Pydantic 模型

### 3.3 Handoff 模式

Handoff 是 OpenAI Agents SDK 最核心的特色 — Agent 可以将对话控制权转移给另一个 Agent。

```python
from agents import Agent, handoff

billing_agent = Agent(name="Billing agent")
refund_agent = Agent(name="Refund agent")

triage_agent = Agent(
    name="Triage agent",
    handoffs=[
        billing_agent,
        handoff(refund_agent, 
                tool_description_override="Transfer to refund processing",
                on_handoff=refund_callback)
    ]
)
```

**Handoff 机制特点**:
- 可自定义输入 Schema (Pydantic 模型验证)
- 支持 `on_handoff` 回调
- 可选择性覆盖工具名称和描述
- Agent 会收到 `prompt_with_handoff_instructions()` 注入的 Handoff 指令

### 3.4 Guardrails (安全护栏)

| 类型 | 执行时机 | 触发行为 |
|------|----------|----------|
| **Input Guardrails** | Agent 收到用户输入时 | `InputGuardrailTripwireTriggered` 异常 → 中断执行 |
| **Output Guardrails** | Agent 生成输出时 | `OutputGuardrailTripwireTriggered` 异常 → 中断执行 |
| **Tool Input Guardrails** | 工具调用前 | `ToolGuardrailFunctionOutput.reject_content()` |
| **Tool Output Guardrails** | 工具返回后 | `ToolGuardrailFunctionOutput.reject_content()` |

**关键设计**: Guardrails 本身可以使用另一个 Agent 进行评估（Agent-as-Judge 模式）。

### 3.5 Tracing (追踪)

默认追踪覆盖整个 `Runner.run()` 操作，并对以下各环节创建独立 Span:
- 每次 Agent 运行
- LLM 生成调用
- 工具函数调用
- Guardrails 执行
- Handoffs 转换
- 音频输入/输出 (STT/TTS)

支持导出到 OpenAI Dashboard、自定义 Span Processor 或第三方平台 (LangSmith 等)。

### 3.6 与企业架构的集成考量

- **轻量级**: 核心库不到数千行代码，易于审计
- **Python/JS 为主**: Java 生态需通过 gRPC/HTTP 桥接或容器化微服务集成
- **无内置持久化**: Session/Tracing 需要外部存储 (已提供接口)
- **模型灵活性**: 支持 OpenAI 模型及兼容 API 的其他提供商

---

## 4. Microsoft AutoGen

### 4.1 概述

AutoGen 是微软开发的多 Agent 对话框架，支持 Agent 自主工作或与人类协作。提供了两个主要编程模型。

**当前版本**: Python v0.7.4 (2026)

### 4.2 核心架构

AutoGen 采用**事件驱动、发布-订阅**的 Actor 模型：

```
┌───────────────────────────────────────────────┐
│         SingleThreadedAgentRuntime             │
│  ┌──────────┐  ┌──────────┐  ┌─────────────┐ │
│  │ Editor   │  │ Writer   │  │Illustrator  │ │
│  │ Agent    │  │ Agent    │  │  Agent      │ │
│  └────┬─────┘  └────┬─────┘  └──────┬──────┘ │
│       │Topic          │Topic           │Topic  │
│  ┌────┴───────────────┴────────────────┴─────┐│
│  │        Group Chat Topic (pub/sub)         ││
│  └────────────────────┬──────────────────────┘│
│              ┌────────┴────────┐              │
│              │ GroupChatManager│              │
│              │ (Speaker Select.)│              │
│              └─────────────────┘              │
└───────────────────────────────────────────────┘
```

### 4.3 主要 Agent 类型

| Agent | 描述 |
|-------|------|
| **AssistantAgent** | 基于 LLM 的助手，可生成代码 |
| **UserProxyAgent** | 代表人类的代理，可执行代码 |
| **CodeExecutorAgent** | 代码执行专用 Agent (支持 Docker 隔离) |
| **GroupChatManager** | 多 Agent 群聊协调者，负责选择发言者 |
| **RoutedAgent** | 基于消息路由的 Agent 基类 |

### 4.4 关键特性

#### 群聊 (Group Chat)
- 多个专业 Agent 共享一个对话主题
- GroupChatManager 使用 LLM 选择下一位发言者
- 支持循环发言 (RoundRobin) 或智能选择

#### 代码执行
- 支持本地命令行执行 (`LocalCommandLineCodeExecutor`)
- 支持 Docker 容器隔离执行 (`DockerCommandLineCodeExecutor`)
- 可配置审批函数控制代码安全性

#### 终止条件
- 基于消息数 (`MaxMessageTermination`)
- 基于关键词 (如 "TERMINATE")
- 基于文本内容匹配

### 4.5 与企业平台集成的考量

- **Python 原生**: 与 Java/Spring 平台集成需要容器化或 gRPC 桥接
- **事件驱动架构**: 天然适合基于消息总线的企业架构
- **Docker 代码执行**: 为 Agent 代码执行提供了安全隔离（对企业信息安全有重要意义）
- **人类参与模式**: `UserProxyAgent` 可配置为 `ALWAYS`/`NEVER`/`TERMINATE` 三种人类输入模式

---

## 5. Agentic RAG

### 5.1 RAG 技术演化

| 代际 | 名称 | 时间 | 核心特征 |
|------|------|------|----------|
| Gen 1 | Naive RAG | 2023 | Query → Vector Search Top-K → Context → LLM |
| Gen 2 | Advanced RAG | 2023-2024 | 查询重写 → 混合搜索(BM25+向量) → RRF 融合 → 重排序 → LLM |
| Gen 3 | Modular RAG | 2024 | 可插拔、可并行的检索器，加权融合 |
| Gen 4 | Graph RAG | 2024-2025 | 知识图谱 + 社区检测 (Microsoft GraphRAG) |
| **Gen 5** | **Agentic RAG** | **2025-2026** | Agent 驱动的自适应检索、多步推理、工具使用 |

### 5.2 Agentic RAG 工作流程

```
用户查询
   ↓
意图分类器 (Router: 需要检索？直接回答？)
   ↓ (如需检索)
查询计划器 → 并行多源检索
   │              ├─ 向量搜索 (语义)
   │              ├─ 关键词搜索 (BM25)
   │              ├─ 知识图谱遍历
   │              └─ API/工具调用
   ↓
自反思 (结果是否充分？)
   ↓ (不充分则迭代)    ↓ (充分)
返回重新检索       答案生成 + 引用
                      ↓
                   幻觉检查 (Faithfulness)
                      ↓
                   最终响应
```

### 5.3 向量数据库选型

#### 综合对比表

| 向量数据库 | 类型 | 最佳场景 | Java SDK | Spring AI 支持 | 2026 市场信号 |
|-----------|------|----------|----------|---------------|-------------|
| **Milvus** (Zilliz) | 开源 + 托管 | 亿级规模、<10ms 延迟 | ✅ 原生 | ✅ 官方 Starter | 云原生趋势 |
| **Pinecone** | 仅托管 | 零运维、快速上线 | ❌ (REST API) | ✅ 官方集成 | 向 Nexus 知识引擎转型 |
| **Weaviate** | 开源 + 托管 | 混合搜索 (BM25+向量) | ✅ GraphQL | ❌ (需自建) | 稳定增长 |
| **PgVector** | PostgreSQL 扩展 | 与业务数据共存 | ✅ (JDBC) | ✅ 官方 Starter | 中小企业首选 |
| **ChromaDB** | 开源嵌入 | 原型/小规模 | ❌ (仅 Python) | ✅ 自动配置 | 实验阶段 |
| **Qdrant** | 开源 + 托管 | 复杂元数据过滤 | ✅ REST | ❌ (社区) | 向信息检索层转型 |

#### 选型建议（针对 Java/Spring 生态）

| 场景 | 推荐 | 理由 |
|------|------|------|
| **快速原型 / 小型项目** | PgVector | 无需新基础设施，直接集成到现有 PostgreSQL |
| **中型企业 / 混合搜索需求** | Milvus + PgVector | Milvus 负责向量搜索，PgVector 存储元数据 |
| **大规模 / 亿级向量** | Milvus (分布式) | 分布式架构、硬件加速、子 10ms 延迟 |
| **零运维偏好** | Pinecone | 全托管、自动扩缩，但存在供应商锁定风险 |
| **强合规 / 审计要求** | Weaviate | 开源可选、混合搜索、可审计 |

### 5.4 分块策略对比

| 策略 | 召回率 (NDCG@10) | 速度 | 成本 | 推荐场景 |
|------|-----------------|------|------|----------|
| **固定大小** (Fixed-size) | 0.62 | ⭐⭐⭐⭐⭐ | 低 | 均匀内容 |
| **递归字符分割** (Recursive) | 0.68 | ⭐⭐⭐⭐ | 低 | **默认推荐** — LangChain 标准 |
| **语义分割** (Semantic) | **0.79** | ⭐⭐ | 高 | 高质量 Q&A 系统 |
| **父-子分割** (Parent-Child) | 0.77 | ⭐⭐⭐ | 中 | **生产环境推荐** — 检索用小子块，上下文用大父块 |

**生产最佳实践**:
- 检索阶段使用 256-512 token 的小块（提高精度）
- 上下文阶段使用 ~2000 token 的父块（保证完整性）
- 块大小应在实际数据上通过实验调整
- LangChain4j / Spring AI 均已内置上述策略

### 5.5 2026 年关键趋势

1. **混合检索已呈主流**: 2026 Q1 企业采用率从 10.3% 飙升至 33.3%
2. **独立向量 DB 份额下滑**: 企业倾向于定制栈 + 平台原生检索
3. **知识编译 (Knowledge Compilation)**: Pinecone Nexus 为代表，在 Agent 查询前预编译知识产物
4. **Graph RAG 融合**: 向量搜索做语义入口，知识图谱遍历深挖关系
5. **治理元数据图**: 以实时权威状态查询替代异步快照，降低幻觉

---

## 6. 能力矩阵综合对比

| 能力维度 | MCP | A2A | OpenAI Agents SDK | Microsoft AutoGen | Agentic RAG (通用) |
|----------|-----|-----|-------------------|-------------------|---------------------|
| **通信模式** | Client↔Server (垂直) | Agent↔Agent (水平) | SDK 内嵌编排 | 事件驱动 Pub/Sub | 检索管道 |
| **状态管理** | 无状态 | 有状态 (Task) | Session 抽象 | 有状态 (Runtime) | 无状态 (检索) |
| **服务发现** | 手动配置 / Registry | Agent Card (自描述) | 代码声明 | 代码注册 | 不适用 |
| **安全模型** | OAuth 2.1 (制定中) | OAuth 2.0 / OIDC / mTLS | Guardrails | 审批函数 (Approval) | 数据层 ACL |
| **流式支持** | SSE / Streamable HTTP | SSE (JSONRPC 内置) | 原生流式 | 消息流 | 不适用 |
| **代码执行** | 无内置 | 无内置 | 无内置 | ✅ Docker 隔离 | 不适用 |
| **跨语言** | ✅ JSON-RPC (语言无关) | ✅ 多 SDK | 仅 Python/TS | 仅 Python | 语言无关 |
| **多 Agent 协作** | ❌ (非设计目标) | ✅ 核心能力 | ✅ Handoff | ✅ Group Chat | ❌ (检索层) |
| **追踪/可观测** | 社区方案 | 无内置 | ✅ 内置 Tracing | ⚠️ 社区方案 | RAGAS 评估 |
| **Java/Spring 原生** | ⚠️ 需自建 Server | ✅ Java SDK | ❌ (需桥接) | ❌ (需桥接) | ✅ Spring AI |

---

## 7. 企业架构集成可行性评分

评分标准: 1=难以集成, 2=需要大量适配, 3=中等工作量, 4=良好适配, 5=天然契合

| 技术 | 集成难度 | API 对齐度 | 安全合规 | 运维复杂度 | 生态系统 | **综合评分** |
|------|----------|-----------|----------|-----------|----------|------------|
| **MCP** | 3 | 4 | 3 | 3 | 5 | **3.6** |
| **A2A** | 3 | 4 | 4 | 3 | 4 | **3.6** |
| **OpenAI Agents SDK** | 4 | 2 | 3 | 2 | 3 | **2.8** |
| **Microsoft AutoGen** | 4 | 2 | 3 | 3 | 3 | **3.0** |
| **Agentic RAG (Spring AI)** | 2 | 5 | 4 | 2 | 5 | **3.6** |

### 评分详解

#### MCP — 评分 3.6

- **优势**: 协议标准化程度最高；Linux 基金会治理保证长期稳定；与 Spring Boot 的 API 层可以良好对接（Tool ↔ API 映射）
- **劣势**: Java 侧 MCP Server 实现相对较新；认证规范仍在制定中；需要额外开发 MCP ↔ GraphQL/gRPC 的适配层
- **关键风险**: OAuth 2.1 认证规范未最终定稿；38.7% 的 MCP Server 仍未实现认证

#### A2A — 评分 3.6

- **优势**: Java SDK 已生产就绪；任务生命周期契合企业工作流引擎；Agent Card 自描述机制适用微服务注册中心
- **劣势**: 与企业现有 API 网关的集成需要适配；国内生态尚未成熟；Anthropic/OpenAI 尚未正式支持

#### OpenAI Agents SDK — 评分 2.8

- **优势**: Guardrails 安全机制完善；Tracing 内建可观测性；Handoff 模式语义清晰
- **劣势**: Python/TS 专属，与 Java 平台需要桥接层；模型供应商绑定风险

#### Microsoft AutoGen — 评分 3.0

- **优势**: Docker 代码执行隔离；事件驱动架构适配消息总线；群聊模式适合复杂协作场景
- **劣势**: 纯 Python；与 Spring 平台集成需要容器化 + 消息中间件桥接

#### Agentic RAG (Spring AI) — 评分 3.6

- **优势**: Spring AI 直接支持 Java 生态；VectorStore 抽象支持多种数据库切换；自动配置简化运维
- **劣势**: Spring AI 仍在快速迭代 (v2.0.0-m6)；高级 Agentic RAG 模式需要自行编排

---

## 8. MCP + A2A 与现有 API 网关对接方案

### 8.1 目标架构

```
                     ┌──────────────────┐
                     │   API Gateway     │
                     │  (Kong/Spring     │
                     │   Cloud Gateway)  │
                     └──┬───────┬───────┬┘
                        │       │       │
          ┌─────────────┘       │       └─────────────┐
          ↓                     ↓                     ↓
   ┌─────────────┐    ┌────────────────┐    ┌─────────────────┐
   │ MCP Ingress │    │  A2A Ingress   │    │  Existing APIs  │
   │ (JSON-RPC   │    │ (Agent Card    │    │ (GraphQL/gRPC/  │
   │  2.0)       │    │  + Task API)   │    │  REST)          │
   └──────┬──────┘    └───────┬────────┘    └────────┬────────┘
          │                   │                      │
   ┌──────┴──────┐    ┌──────┴────────┐    ┌────────┴────────┐
   │ MCP Server  │    │  A2A Agent    │    │  Microservices  │
   │ Registry    │    │  Registry     │    │  (Spring Boot)  │
   └─────────────┘    └───────────────┘    └─────────────────┘
```

### 8.2 MCP 对接方案

#### 方案 A: API Gateway 层面集成 (推荐)

```
┌────────────────────────────────────────────┐
│         Spring Cloud Gateway                │
│                                              │
│  /mcp/** → MCP-Server (JSON-RPC 转发)       │
│  /api/** → 现有微服务 (保持不变)             │
│  /.well-known/mcp → Server 元数据            │
│                                              │
│  Filter: Auth (OAuth2.1), Rate Limit, Log   │
└────────────────────────────────────────────┘
```

**实施步骤**:
1. 在 API Gateway 配置 `/mcp/**` 路由指向 MCP Server
2. Gateway Filter 层统一处理认证 (OAuth 2.1 Token 验证)
3. 速率限制、审计日志在 Gateway 层统一实施
4. MCP Server 注册到服务发现 (Consul/Eureka/Nacos)

#### 方案 B: Service Mesh 层面 (Sidecar)

- 每个 Spring Boot 微服务通过 Sidecar 暴露 MCP Tools
- 适合需要将现有业务 API 直接暴露为 MCP Tool 的场景
- 减少代码侵入，但增加运维复杂度

#### MCP ↔ GraphQL/gRPC 映射策略

| MCP 原语 | GraphQL 映射 | gRPC 映射 |
|----------|-------------|----------|
| `tools/list` | `{ __schema { types { name fields { name } } } }` | gRPC Server Reflection |
| `tools/call` | Query/Mutation 执行 | Unary/Streaming RPC |
| `resources/list` | Schema 中暴露的资源类型 | 自定义 Service |
| `resources/read` | 对应 Query | 对应 Unary RPC |
| `prompts/get` | 参数化模板 Query | 参数化 RPC |

**推荐**: 通过 Spring AI MCP Server Starter 快速构建 MCP Server，将现有的 `@RestController`、`@GrpcService` 暴露为 MCP Tools。

### 8.3 A2A 对接方案

#### Agent Card 与企业服务注册中心

```
┌───────────────────────────────────────────┐
│       Service Registry (Eureka/Nacos)      │
│                                            │
│  Agent-A: /a2a/v1 (JSONRPC)               │
│  Agent-A: /.well-known/agent-card.json     │
│  Agent-B: /a2a/v1 (gRPC)                  │
│  Agent-B: /.well-known/agent-card.json     │
└───────────────────────────────────────────┘
        ↑ 代理注册              ↑ Agent 发现
┌───────────────┐        ┌───────────────┐
│   Agent-A     │        │  Agent-B      │
│ (Spring Boot) │ ←A2A→  │ (Spring Boot) │
└───────────────┘        └───────────────┘
```

**实施建议**:
1. 使用 A2A Java SDK 的 `A2AServer` 在 Spring Boot 应用内启动 Agent
2. Agent Card 通过 Spring Actuator 端点暴露 (`/actuator/agent-card`)
3. Agent 间通信通过内部服务网格 (如 Istio mTLS) 保证安全
4. Task 状态持久化到企业数据库 (MySQL/PostgreSQL)

### 8.4 双协议共存建议

**MCP 用于**: Agent 调用工具和数据源 (内部和外部)
**A2A 用于**: Agent 间任务委派和协作 (跨团队、跨系统)

```
              ┌─────────────────────┐
              │   企业 AI Agent     │
              │   Orchestrator     │
              └──────┬──────┬──────┘
                     │      │
            MCP (tool calls)  A2A (task delegation)
                     │      │
              ┌──────┴──┐ ┌─┴──────────┐
              │ 业务 API │ │ 其他 Agent  │
              │ 数据库   │ │ (跨部门)    │
              └─────────┘ └────────────┘
```

---

## 9. Agentic RAG 技术栈推荐 (Spring/Java 生态)

### 9.1 推荐技术栈全景

```
┌────────────────────────────────────────────────────┐
│                   Application Layer                 │
│  Spring Boot 3.x + Spring AI 2.x                   │
├────────────────────────────────────────────────────┤
│                  Agent Orchestration                │
│  LangChain4j (可选) 或 自研 Workflow Engine          │
├──────────────┬─────────────────┬──────────────────┤
│  Embedding   │  Vector Store   │  LLM Gateway     │
│  ─────────── │  ─────────────  │  ─────────────   │
│  OpenAI      │  Milvus/PgVector│  Spring AI       │
│  text-embed  │  (按规模选)     │  ChatClient      │
│  -3-small    │                 │                  │
│  或          │  备选:          │  备选:           │
│  BGE-M3      │  Pinecone(托管) │  LangChain4j     │
│  (本地部署)   │  Weaviate(混合) │  ChatLanguageModel│
├──────────────┴─────────────────┴──────────────────┤
│              Data/Infrastructure Layer              │
│  PostgreSQL (业务数据) + Redis (语义缓存)           │
│  Elasticsearch (关键词搜索, 可选)                   │
└────────────────────────────────────────────────────┘
```

### 9.2 Maven 依赖推荐

```xml
<!-- Spring AI 核心 -->
<dependency>
    <groupId>org.springframework.ai</groupId>
    <artifactId>spring-ai-starter-vector-store-milvus</artifactId>
</dependency>

<!-- 或使用 PgVector (与现有 PostgreSQL 共存) -->
<dependency>
    <groupId>org.springframework.ai</groupId>
    <artifactId>spring-ai-autoconfigure-vector-store-pgvector</artifactId>
</dependency>

<!-- 或使用 Pinecone (零运维) -->
<dependency>
    <groupId>org.springframework.ai</groupId>
    <artifactId>spring-ai-pinecone-store</artifactId>
</dependency>

<!-- LangChain4j (高级 Agent 编排) -->
<dependency>
    <groupId>dev.langchain4j</groupId>
    <artifactId>langchain4j-spring-boot-starter</artifactId>
    <version>1.0.0-beta1</version>
</dependency>

<!-- Embedding 模型: OpenAI -->
<dependency>
    <groupId>org.springframework.ai</groupId>
    <artifactId>spring-ai-openai-spring-boot-starter</artifactId>
</dependency>
```

### 9.3 分阶段实施建议

#### 阶段 1: 基础 RAG (生产就绪，1-2 周)
- Spring AI + PgVector (利用现有 PostgreSQL)
- 递归字符分割 (RecursiveCharacterTextSplitter)
- 基础相似度搜索

#### 阶段 2: 混合检索 (生产优化，2-4 周)
- 引入 BM25 关键词搜索 (Elasticsearch 或 PgVector 全文搜索)
- 重排序 (Cohere Rerank 或 BGE-Reranker)
- 父-子分块策略

#### 阶段 3: Agentic RAG (高级，4-8 周)
- 查询路由 (意图分类 → 选择检索策略)
- 多源并行检索 (向量 + 关键词 + 知识图谱)
- 自反思循环 (结果质量评估，不足则迭代)
- 语义缓存 (Redis + 相似度匹配)

#### 阶段 4: 知识编译 (2027 前瞻)
- 预编译知识产物（类似 Pinecone Nexus 模式）
- 结构化引用 + 置信度评分
- 实时权威数据源查询替代快照

### 9.4 性能优化建议

| 优化手段 | 预期收益 | 实现方式 |
|----------|----------|----------|
| **语义缓存** | 40%+ 成本降低 | Redis + 相似度阈值 |
| **混合检索** | 召回率 +15-20% | BM25 + 向量 + RRF 融合 |
| **重排序** | 精确率 +10-15% | BGE-Reranker-v2-m3 |
| **父-子分块** | 上下文质量 +20% | LangChain4j ParentDocumentRetriever |
| **查询重写** | 准确率 +10% | LLM 查询扩展 |

---

## 10. 成熟度评估

| 技术 | 成熟度 | 等级 | 说明 |
|------|--------|------|------|
| **MCP 协议规范** | 🟢 生产就绪 | 4/5 | 规范稳定；认证规范待完善；10,000+ 活跃 Server |
| **MCP Java SDK** | 🟡 实验性 | 2/5 | Java 侧 SDK 较新 (2025 Q4)；企业验证案例少 |
| **MCP Streamable HTTP** | 🟡 标准化中 | 3/5 | SEP 2243 草案阶段；预计 2026 年终稿 |
| **A2A 协议规范** | 🟢 生产就绪 | 4/5 | v1.0 稳定版 (2026.03)；5 种语言 SDK；150+ 组织采用 |
| **A2A Java SDK** | 🟢 生产就绪 | 4/5 | 官方 Java SDK 与 v1.0 同步发布 |
| **OpenAI Agents SDK** | 🟢 生产就绪 | 4/5 | Python 成熟；JS beta；Guardrails/Tracing 完善 |
| **AutoGen (Microsoft)** | 🟢 生产就绪 | 3/5 | 架构稳定；版本迭代快速 (v0.5→v0.7) |
| **Agentic RAG** | 🟡 实验性→生产 | 3/5 | 模式已明确；各家企业实现差异大；标准化进行中 |
| **Spring AI** | 🟡 快速迭代中 | 3/5 | v2.0.0-m6 里程碑；API 快速演进；生产验证案例增长中 |
| **Milvus** | 🟢 生产就绪 | 5/5 | 最成熟的分布式向量 DB；云原生支持完善 |
| **Pinecone** | 🟢 生产就绪 | 4/5 | 托管成熟；向 Nexus 平台转型中 |
| **PgVector** | 🟢 生产就绪 | 4/5 | PostgreSQL 生态内高度成熟 |
| **Weaviate** | 🟢 生产就绪 | 4/5 | 混合搜索成熟；开源 + 云版本 |
| **ChromaDB** | 🟡 实验性 | 2/5 | 适合原型；无 Java SDK；生产特性缺失 |

---

## 11. 综合建议与实施路线图

### 11.1 核心建议

#### 立即采用 (0-3 个月)

| 技术 | 行动 | 优先级 |
|------|------|--------|
| **Spring AI + PgVector** | 在现有 Spring Boot 项目中集成基础 RAG 能力 | 🔴 高 |
| **MCP 协议** | 搭建 MCP Server 试点，将 2-3 个核心 API 暴露为 MCP Tools | 🔴 高 |
| **A2A 协议** | 了解规范，关注 Java SDK 生态发展 | 🟡 中 |

#### 短期规划 (3-6 个月)

| 技术 | 行动 | 优先级 |
|------|------|--------|
| **Agentic RAG** | 实施混合检索 + 父-子分块 + 重排序 | 🔴 高 |
| **MCP Gateway** | 在 API Gateway 层统一管理 MCP 请求的认证/限流/日志 | 🔴 高 |
| **A2A 试点** | 在 2 个跨部门 Agent 场景试点 A2A 通信 | 🟡 中 |
| **Milvus** | 如数据量增长至千万级，从 PgVector 迁移到 Milvus | 🟡 中 |

#### 长期观察 (6-12 个月)

| 技术 | 行动 | 优先级 |
|------|------|--------|
| **OpenAI Agents SDK** | 如需 Python 侧复杂 Agent 编排，通过 gRPC 桥接到 Java 平台 | 🟢 低 |
| **AutoGen** | 如需多 Agent 群聊 + 代码执行，容器化部署后桥接 | 🟢 低 |
| **知识编译** | 关注 Pinecone Nexus 等知识预编译模式；2027 再评估 | 🟢 低 |

### 11.2 关键风险与缓解

| 风险 | 等级 | 缓解措施 |
|------|------|----------|
| MCP OAuth 2.1 规范未定稿 | 🟡 中 | 使用 API Key + Gateway 层认证作为过渡方案 |
| Spring AI API 不稳定性 | 🟡 中 | 锁定版本到稳定发布版；封装抽象层隔离 API 变化 |
| A2A 国内生态滞后 | 🟡 中 | 优先在内部系统间使用；对外关注国际标准演进 |
| 向量 DB 选型后悔 | 🟢 低 | Spring AI 的 VectorStore 抽象可降低切换成本 |
| MCP + A2A 双协议维护成本 | 🟡 中 | MCP 优先（Agent↔工具；覆盖面更广）；A2A 按需引入 |

### 11.3 一句话总结

> 对于 Spring Boot 多模块企业平台，**Agentic RAG (Spring AI + PgVector/Milvus) 和 MCP 协议应作为首批落地技术**。MCP 解决 Agent 如何调用企业 API 和数据的标准化问题，Agentic RAG 解决 Agent 如何获取和利用企业知识的问题。A2A 在跨系统 Agent 协作场景成熟后引入。OpenAI Agents SDK 和 Microsoft AutoGen 作为可选增强，在 Python 微服务场景中按需桥接。

---

## 参考资料

- MCP 官方规范: https://modelcontextprotocol.org
- A2A 官方规范: https://a2a-protocol.org
- OpenAI Agents SDK: https://github.com/openai/openai-agents-python
- Microsoft AutoGen: https://microsoft.github.io/autogen
- Spring AI Reference: https://docs.spring.io/spring-ai/reference
- CData MCP 2026 报告: https://www.cdata.com/blog/2026-year-enterprise-ready-mcp-adoption
- Google A2A 一周年博客: https://opensource.googleblog.com/2026/04/a-year-of-open-collaboration-celebrating-the-anniversary-of-a2a.html
- VentureBeat RAG 重建报告: https://venturebeat.com/data/the-retrieval-rebuild-why-hybrid-retrieval-intent-tripled-as-enterprise-rag-programs-hit-the-scale-wall

---

*本报告由 AI Agent 调研工作流生成，基于 2026 年 5 月最新数据*
