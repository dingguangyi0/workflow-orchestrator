# T5: 差距分析报告 — 现有架构 vs AI Agent 能力

**日期**: 2026-05-31  
**依赖**: T1 (模块结构), T2 (架构模式), T3 (Agent框架调研), T4 (协议与基础设施调研)  
**目标**: 系统化识别现有 Spring Boot 多模块企业平台与 AI Agent 目标架构之间的差距，输出可操作的优先行动项

---

## 目录

1. [能力映射表：现有架构 vs AI Agent 增强方向](#1-能力映射表现有架构-vs-ai-agent-增强方向)
2. [缺失能力清单](#2-缺失能力清单)
3. [架构冲突识别](#3-架构冲突识别)
4. [差距严重性矩阵与优先行动项](#4-差距严重性矩阵与优先行动项)
5. [可复用资产盘点](#5-可复用资产盘点)
6. [综合发现与建议](#6-综合发现与建议)

---

## 1. 能力映射表：现有架构 vs AI Agent 增强方向

### 1.1 元数据驱动架构 (JSON Schema → Java 代码生成)

| 维度 | 现有能力 | AI Agent 增强方向 | 契合度 | 具体行动 |
|------|---------|------------------|--------|---------|
| **Schema 定义** | JSON Schema 文件定义实体/字段/关系/校验规则 | MCP Tool Schema 自动生成（从 JSON Schema 提取 Tool 的 inputSchema） | ⭐⭐⭐⭐⭐ 极高 | 开发 `Schema2MCP` 转换器，将 JSON Schema 映射为 MCP Tool 的参数定义 |
| **代码生成** | `json-schema-plugin` → 自动生成 POJO、DAO、Service 骨架 | Agent 辅助代码生成增强（生成 @Tool 注解、@AiService 接口、单元测试） | ⭐⭐⭐⭐ 高 | 扩展 Maven 插件，新增 Agent 代码生成目标（`generate-agent-tools`） |
| **实体注册** | 元数据注册中心（`MetadataRegistry`）集中管理所有实体定义 | 动态 Tool 注册（Agent 运行时从 Registry 拉取元数据，实时注册为可调用工具） | ⭐⭐⭐⭐⭐ 极高 | 实现 `MetadataDrivenToolProvider`：监听 Registry 变更，自动同步到 LangChain4j Tool 注册表 |
| **动态字段** | 运行时字段动态加载，支持租户自定义扩展 | Function Calling 参数动态解析（LLM 根据元数据描述自动构造查询参数） | ⭐⭐⭐⭐ 高 | 将字段级别的 `description` 属性作为 Tool Parameter 的 `@Description` 来源 |
| **关系映射** | 实体间关联关系（1:1, 1:N, N:M）在 JSON Schema 中定义 | Knowledge Graph / Graph RAG 的关系推理（将元数据关系图作为 Agent 推理上下文） | ⭐⭐⭐ 中 | 将元数据关系导出为 Neo4j/图谱格式，供 Agentic RAG 的关系遍历使用 |
| **权限控制** | 字段级别/行级别数据权限（租户隔离） | Agent 上下文安全边界（确保 Agent 仅能访问当前租户范围内的 Tool 和 Resource） | ⭐⭐⭐⭐⭐ 极高 | 在 MCP Server 层实现租户感知的 Tool 过滤；Tool 执行时注入租户上下文 |

**关键洞察**: 元数据驱动架构是本项目 **最强的可复用资产**。JSON Schema 的 `title/description/properties` 结构与 MCP Tool 的 `name/description/inputSchema` 天然同构，转换成本极低。这是整个 AI Agent 升级的"快赢" (Quick Win) 切入点。

### 1.2 API / Impl 契约分离

| 维度 | 现有能力 | AI Agent 增强方向 | 契合度 | 具体行动 |
|------|---------|------------------|--------|---------|
| **接口契约** | 每个模块严格分离 `api/` (接口定义) 和 `impl/` (实现) | Agent 能力契约化 — 将 API 接口声明映射为 Agent Skill 声明 | ⭐⭐⭐⭐⭐ 极高 | 基于现有 `*-api` 模块自动生成 Agent Card 的 `skills` 部分 |
| **模块边界** | 16 个模块通过 API 接口通信，边界清晰 | A2A Agent 边界天然对齐 — 每个微服务模块成为独立 A2A Agent | ⭐⭐⭐⭐⭐ 极高 | 为每个 `*-api` 模块生成 A2A Agent Card，其 `skills` 由 API 方法签名派生 |
| **版本契约** | Maven 版本统一管理（`app-build-plugins` 中的 `<revision>` 属性） | API 版本兼容性直接影响 Agent 工具调用稳定性 | ⭐⭐⭐ 中 | 建立 Tool API 版本策略：主版本变更前的弃用期公告；Agent 工具注册时标注版本 |
| **实现隔离** | `impl/` 内部实现对外不可见 | Agent 不透明模型 (Opaque Agent) — A2A 协议的核心设计原则之一 | ⭐⭐⭐⭐ 高 | A2A Agent Card 只暴露 `skills`（接口），不暴露内部 Tool/Memory 细节 |
| **自动化测试** | API 层定义了清晰的契约接口 | Agent 行为契约测试 — 基于 API 契约自动生成 Agent 可达性测试 | ⭐⭐⭐⭐ 高 | 从 API 接口自动生成 Agent Tool 调用基线测试；端到端 Agent 行为一致性验证 |

**关键洞察**: API / Impl 分离模式是 **A2A 协议的天然前置条件**。每个 `*-api` 模块已经是事实上的 "Agent Capability 声明"，无需架构改造，只需格式映射。

### 1.3 GraphQL API 网关

| 维度 | 现有能力 | AI Agent 增强方向 | 契合度 | 具体行动 |
|------|---------|------------------|--------|---------|
| **动态 Schema** | GraphQL Introspection — 客户端可动态查询 Schema | MCP Resource/Tool 自省 — LLM 通过 `resources/list` 和 `tools/list` 发现可用 API | ⭐⭐⭐⭐⭐ 极高 | 在 MCP Server 中实现 `tools/list` → 动态获取 GraphQL Schema → 每个 Query/Mutation 映射为一个 Tool |
| **查询灵活性** | 客户端精确指定所需字段，避免 Over-fetching | Agent 动态 Tool 选择 — LLM 根据用户意图选择最合适的 Query/Mutation 工具 | ⭐⭐⭐⭐ 高 | 实现 GraphQL Query 的 Tool 参数映射：LLM 构造 GraphQL 变量，后端执行查询 |
| **字段描述** | GraphQL Schema 支持 `description` 字段 | Tool Description 源信息 — LLM 依赖工具描述做出调用决策 | ⭐⭐⭐⭐⭐ 极高 | 将 GraphQL 字段的 `description` 直接生成为 Tool 的 `description` 属性 |
| **类型系统** | GraphQL 强类型系统 | Tool 的 `inputSchema` JSON Schema 定义 | ⭐⭐⭐⭐⭐ 极高 | GraphQL 类型 → JSON Schema 转换器（graphql-java 库已内置此能力） |
| **网关统一入口** | 所有 API 通过单一 GraphQL 端点暴露 | MCP 统一端点 — API Gateway 同时服务于 GraphQL 和 MCP 协议 | ⭐⭐⭐⭐ 高 | 在 Spring Cloud Gateway 增加 `/mcp` 路由，复用现有的认证/限流/审计 Filter |
| **同步请求-响应** | GraphQL 是同步 Request-Response 模式 | Agent Streaming 场景需要异步响应 — SSE / Streamable HTTP | ⚠️ 模式冲突 (见 §3.3) | — |

**关键洞察**: GraphQL 与 MCP 协议的 **自省机制高度同源**。`{ __schema { types { name fields { name description } } } }` 本质上就是 MCP 的 `tools/list` 所做的事情。这是一个极高回报的集成点。

### 1.4 gRPC 微服务通信

| 维度 | 现有能力 | AI Agent 增强方向 | 契合度 | 具体行动 |
|------|---------|------------------|--------|---------|
| **强类型契约** | Protobuf 定义 service/message | Python-Java Bridge 的类型安全通信层 | ⭐⭐⭐⭐⭐ 极高 | 复用现有 gRPC 基础设施：定义 `agent_orchestrator.proto`，Java 侧作为 Client，Python 侧作为 Server |
| **双向流** | gRPC 原生支持 Bidirectional Streaming | Agent 流式执行反馈 — 实时推送 Agent 执行进度、中间输出、中断请求 | ⭐⭐⭐⭐⭐ 极高 | `rpc ExecuteWorkflow(stream AgentEvent) returns (stream AgentResult)` |
| **已有基础设施建设** | 项目已具备 gRPC 1.11 + Protobuf 编译流水线 | 零额外基础设施即可搭建 Python-Java Bridge | ⭐⭐⭐⭐⭐ 极高 | 唯一新增：Python 侧的 `grpcio` + `protobuf` 编译 |
| **服务发现** | 现有的 gRPC 服务注册/发现机制 | A2A Agent Card 可集成到同一服务注册中心（Eureka/Nacos） | ⭐⭐⭐⭐ 高 | Agent Card endpoint 注册为与 gRPC service 同级的服务元数据 |
| **负载均衡** | gRPC Client 已具备负载均衡能力 | 多 Python Agent Engine 副本的水平扩展 | ⭐⭐⭐⭐ 高 | Python Agent Engine 作为无状态 sidecar，扩缩容与 Spring Boot 实例解耦 |

**关键洞察**: gRPC 是 T3 报告中推荐度最高的 Python-Java 互操作方案。本项目的 **已有 gRPC 基础设施直接消除了搭建 Bridge 的最大障碍**。T5 的推荐是：不需要 REST Sidecar 作为过渡，直接使用 gRPC Bridge。

### 1.5 MyBatis 代码自动生成 (MBG)

| 维度 | 现有能力 | AI Agent 增强方向 | 契合度 | 具体行动 |
|------|---------|------------------|--------|---------|
| **代码生成** | `mbg-plugins` 从数据库 Schema 自动生成 Entity/Mapper/XML | Agent 辅助代码生成增强 — LLM 审查/优化生成的代码、补充业务逻辑 | ⭐⭐⭐⭐ 高 | 将 MBG 生成的代码作为 Agent 的 Code Review 输入和自定义业务逻辑生成的上下文 |
| **DAO 层** | 自动生成的 CRUD Mapper | 自动生成 LLM Tool Wrapper — 将每个 Mapper 方法包装为 @Tool | ⭐⭐⭐⭐⭐ 极高 | 扩展 `mbg-plugins`：新增 `generateAgentTools=true` 选项，自动生成带 @Tool/@Description 的包装器 |
| **SQL 映射** | XML Mapper 中手写复杂 SQL | Agent 辅助 SQL 优化（慢查询分析 → 索引建议 → 改写建议） | ⭐⭐⭐ 中 | RAG 索引慢查询日志 + 执行计划；Agent 通过自然语言辅助 SQL 优化 |
| **代码一致性** | 生成代码保证团队代码风格一致 | Agent 辅助生成标准 — 将 MBG 模板作为 Agent 代码生成的 Prompt 上下文 | ⭐⭐⭐⭐ 高 | 将 MBG Velocity 模板导出为 Agent 的 Code Generation System Prompt |

**关键洞察**: MBG 是"AI 辅助开发"的天然入口。MBG 已经解决了"生成什么"，Agent 可以解决"生成后怎么做"——辅助业务逻辑填充、单元测试生成、代码审查。

### 1.6 Drools 规则引擎

| 维度 | 现有能力 | AI Agent 增强方向 | 契合度 | 具体行动 |
|------|---------|------------------|--------|---------|
| **业务规则** | DRL 文件定义声明式业务规则 | Agent Guardrails / 策略执行 — LLM 输出在执行前经过 Drools 规则校验 | ⭐⭐⭐⭐⭐ 极高 | 将 Drools 规则作为 LangChain4j `@Moderate` 或 OpenAI `OutputGuardrails` 的后端实现 |
| **规则可解释性** | Drools 规则是显式的 if-then 声明 | Agent 决策可解释性 — 当 Guardrail 触发时，返回具体的规则 ID 和原因 | ⭐⭐⭐⭐ 高 | Guardrail 违规响应中包含：`ruleId`, `ruleDescription`, `violatedCondition`, `suggestedFix` |
| **规则热更新** | Drools KieContainer 支持运行时规则更新 | Agent 策略的动态调整 — 无需重启即可更新 Agent Guardrail 规则 | ⭐⭐⭐⭐ 高 | 规则更新后触发 Agent Guardrail 重载，而非 Agent 重启 |
| **规则复杂度** | 复杂规则链（规则流/RuleFlow） | Agent Workflow — Drools RuleFlow 的编排模式可映射到 Agentic Workflow | ⭐⭐⭐ 中 | Drools RuleFlow 作为 LangGraph StateGraph 的设计参考 |
| **人机协同** | Drools 的 `decision` 节点可暂停等待输入 | Human-in-the-Loop — 映射为 LangGraph 的 `interrupt()` 模式 | ⭐⭐⭐ 中 | 仅在引入 LangGraph 后适用；Drools decision 可与 LangGraph checkpoint 协同 |

**关键洞察**: Drools 是 **Agent Guardrail 的成熟基础设施**。无需从零构建策略执行引擎，只需将 Drools 规则引擎包装为 Guardrail 接口。这是"已有资产最大化利用"的典型场景。

### 1.7 Maven 版本统一管理 + 构建插件链

| 维度 | 现有能力 | AI Agent 增强方向 | 契合度 | 具体行动 |
|------|---------|------------------|--------|---------|
| **插件体系** | `json-schema-plugin`, `app-build-plugins`, `mbg-plugins`, `app-archetype` | Agent 工具自动生成插件 — 新增 Maven 插件目标在编译期自动生成 Agent 相关代码 | ⭐⭐⭐⭐⭐ 极高 | 开发 `app-agent-plugins` Maven 模块，提供 `generate-mcp-tools` / `generate-agent-card` 目标 |
| **Archetype** | `app-archetype` 快速生成新模块骨架 | AI 增强 Archetype — 新模块默认包含 @AiService + MCP Server 骨架 | ⭐⭐⭐⭐ 高 | 扩展 Archetype：可选 `--with-ai` 参数，生成含 AI Agent 基础设施的新模块 |
| **版本统一** | 父 POM 管理所有依赖版本 | AI 依赖版本管理的一致性保障 | ⭐⭐⭐ 中 | 新增 AI 相关依赖（langchain4j-bom, spring-ai-bom）纳入统一版本管理 |
| **构建生命周期** | 标准 Maven 生命周期 | 构建时 Agent 工具注册表生成 — 编译期扫描 @Tool 注解，生成注册表清单 | ⭐⭐⭐⭐ 高 | 在 `process-classes` 阶段执行 Agent Tool 扫描和注册表生成 |

**关键洞察**: Maven 插件体系是 **Agent 能力自动化的编译器**。通过扩展已有插件链，可以在不修改业务代码的前提下，在构建期自动为现有 API 生成 MCP Tool 包装、Agent Card、Agentic RAG 配置等。

---

### 1.8 能力映射总结

```
┌─────────────────────────────────────────────────────────────────┐
│              现有架构资产 → AI Agent 增强价值                    │
│                                                                  │
│  元数据驱动 ─────────────────► MCP Tool 自动生成 ★★★★★          │
│  API/Impl 分离 ─────────────► A2A Agent Card 自动生成 ★★★★★     │
│  GraphQL 网关 ──────────────► MCP Resource/Tool 端点 ★★★★★      │
│  gRPC 通信 ─────────────────► Python-Java Bridge (零新增) ★★★★★ │
│  MyBatis 代码生成 ──────────► Agent 辅助开发 + Tool 生成 ★★★★   │
│  Drools 规则引擎 ───────────► Agent Guardrails 后端 ★★★★★       │
│  Maven 插件链 ──────────────► 编译期 Agent 代码生成 ★★★★★        │
│                                                                  │
│  结论: 7大架构模式中 5 个具有 ★★★★★ 的 AI Agent 契合度          │
│        GRPC 基础设施直接消除了 Python Bridge 的最大障碍           │
└─────────────────────────────────────────────────────────────────┘
```

---

## 2. 缺失能力清单

以下能力是当前架构 **完全不具备**，但 AI Agent 升级所必需的。按缺失层级从基础设施到应用层排列。

### 2.1 基础设施层缺失

| # | 缺失能力 | 关键性 | 现有架构中的空白 | 推荐方案 | 预计工作量 |
|---|---------|--------|----------------|---------|-----------|
| **M1** | **LLM 集成层** | 🔴 Critical | 项目中无任何 LLM SDK 依赖；无 API Key 管理机制；无模型提供商抽象 | LangChain4j 的 `ChatLanguageModel` 抽象 + Spring Boot Starter 自动配置 | 2-3 人周 |
| **M2** | **向量数据库** | 🔴 Critical | 现有 PostgreSQL 未启用 pgvector 扩展；无 Embedding 存储/检索能力 | PgVector（利用现有 PostgreSQL，零新基础设施）或 Milvus（如需大规模） | 1-2 人周 (PgVector) / 3-4 人周 (Milvus) |
| **M3** | **Embedding 服务** | 🔴 Critical | 无文本 Embedding 生成能力；无向量化管道 | Spring AI EmbeddingClient + OpenAI `text-embedding-3-small` 或本地 BGE-M3 | 1 人周 |
| **M4** | **Prompt 管理系统** | 🟡 High | 无 Prompt 模板存储/版本管理；Prompt 硬编码在代码中的风险 | LangChain4j 的 `@SystemMessage` + `@UserMessage` 模板 + 外部化 Prompt 配置（配置中心/数据库） | 2-3 人周 |
| **M5** | **Agent 状态持久化** | 🟡 High | 无 Agent 执行状态的 Checkpoint/Resume 机制 | Phase 1-2: LangChain4j ChatMemory (会话级); Phase 3+: LangGraph PostgresSaver (工作流级) | 1-2 人周 (ChatMemory) / 3-4 人周 (Checkpoint) |
| **M6** | **流式响应基础设施** | 🟡 High | GraphQL 仅支持同步请求-响应；gRPC 有 stream 但未用于 Agent | Spring Boot SSE (Server-Sent Events) + LangChain4j `StreamingChatLanguageModel`；gRPC Bidirectional Streaming 用于 LangGraph 集成 | 2-3 人周 |
| **M7** | **Python 运行时环境** | 🟡 High | 项目中无 Python 依赖；无 Python 部署/运维流程 | Docker 容器化 Python Agent Engine + gRPC Server；Kubernetes Sidecar 模式 | 3-4 人周 |
| **M8** | **Agent 可观测性/Tracing** | 🟢 Medium | 有 Micrometer 基础指标采集，但无 LLM 调用追踪/Agent 执行链追踪 | 扩展 Micrometer → 新增 LLM Token/延迟/成本指标；集成 LangSmith 或自建 Agent Trace 存储 | 2-3 人周 |
| **M9** | **语义缓存层 (Semantic Cache)** | 🟢 Medium | 仅 Redis 用于业务缓存，无语义相似度缓存 | Redis + 向量相似度匹配：缓存相似问题的 LLM 响应 | 1-2 人周 |

### 2.2 应用层缺失

| # | 缺失能力 | 关键性 | 现有架构中的空白 | 推荐方案 | 预计工作量 |
|---|---------|--------|----------------|---------|-----------|
| **M10** | **MCP Server 实现** | 🔴 Critical | 无 MCP 协议端点；现有 API 无法被 Agent 以标准协议调用 | Spring AI MCP Server Starter 或自建 JSON-RPC 2.0 端点 | 2-3 人周 |
| **M11** | **A2A Agent 端点** | 🟡 High | 无 Agent 间通信机制；无 Agent Card 暴露 | A2A Java SDK → 为每个微服务模块生成 Agent Card + Task API | 3-4 人周 |
| **M12** | **Agentic RAG Pipeline** | 🟡 High | 无 RAG 检索管道；无文档索引/检索流程 | Spring AI RAG Pipeline: DocumentReader → TextSplitter → Embedding → VectorStore → Retriever | 2-3 人周 (基础) / 6-8 人周 (Agentic) |
| **M13** | **Agent 安全边界** | 🟡 High | 无 Agent 专用的权限校验/速率限制/内容审计 | 在 MCP/A2A 网关层实现：租户上下文注入、Tool 级 ACL、LLM 输入输出过滤 | 3-4 人周 |
| **M14** | **Tool Schema 注册表** | 🟢 Medium | 无中心化的 Tool/Resource 注册和发现 | 在元数据注册中心（MetadataRegistry）之上扩展 Tool Registry 子模块 | 1-2 人周 |

### 2.3 缺失能力总结

```
missing 能力分布:
  Critical: M1(LLM集成), M2(向量DB), M3(Embedding), M10(MCP Server)
  High:     M4(Prompt管理), M5(状态持久化), M6(流式响应), M7(Python运行时),
            M11(A2A端点), M12(Agentic RAG), M13(Agent安全)
  Medium:   M8(可观测性), M9(语义缓存), M14(Tool注册表)
```

**关键发现**: 14 项缺失能力中，仅 4 项（M1, M10, M2, M3）是 Phase 1 必须解决的 Critical 阻塞项。其余 10 项可按优先级分阶段建设。这说明 **基础 Agent 能力可以快速打通，不会出现"必须全部建完才能用"的困境**。

---

## 3. 架构冲突识别

以下识别现有架构中与 AI Agent 目标架构存在 **设计冲突** 或 **需要升级** 的技术债务。

### 3.1 Java 8 → Java 17+ / Spring Boot 2.4 → 3.x 升级路径

| 维度 | 详情 |
|------|------|
| **冲突描述** | LangChain4j v1.15 和 Spring AI v2.0 均要求 Java 17+，而项目当前使用 Java 8。Spring Boot 2.4 也需升级到 3.x 才能使用最新的 AI Starter。 |
| **冲突根源** | 项目长期停留 Java 8，可能是出于兼容性/稳定性考虑。但 AI Agent 生态的 Java 框架已经全面迁移到 Java 17+。 |
| **严重性评级** | 🔴 **Critical** — 所有 AI Agent 框架的 **硬依赖** |
| **影响范围** | 全项目：POM 文件、编译配置、容器基础镜像、CI/CD 流水线 |
| **缓解建议** | 1. 如果已计划 Java 升级，将 AI Agent 升级作为升级的驱动力之一<br>2. 如果尚未计划，Phase 0 单独执行 Java 8→17 升级（预计 2-4 人周，主要是兼容性测试）<br>3. 可以先用 Java 17 编译 AI 相关模块，其余模块保持 Java 8（不推荐：增加构建复杂度） |
| **依赖的后续决策** | Spring Boot 3.x 移除了部分旧 API，对应的 GraphQL/gRPC/Drools 依赖也需升级 |
| **升级影响面估计** | `javax.*` → `jakarta.*` 迁移（约 2000+ 文件需修改 import）；Spring Security 配置变更；Actuator 端点路径变更 |

**扩展影响链**:
```
Java 8 → 17+
  ├── Spring Boot 2.4 → 3.x
  │     ├── GraphQL-Java 版本升级
  │     ├── gRPC 版本升级 (1.11 → 最新)
  │     ├── Drools 版本兼容性验证
  │     └── MyBatis Spring Boot Starter 升级
  ├── javax.* → jakarta.* 迁移
  │     └── 所有模块的 import 语句
  └── LangChain4j / Spring AI 引入 (仅 Java 17+ 支持)
```

### 3.2 Python 依赖引入的运维复杂度

| 维度 | 详情 |
|------|------|
| **冲突描述** | 当前纯 Java/Maven 技术栈，运维团队仅需管理 JDK。引入 LangGraph/CrewAI 将增加 Python 运行时、pip 依赖管理、Python Docker 镜像维护。 |
| **冲突根源** | LangGraph 是目前唯一成熟的复杂 Agent 编排方案，但仅支持 Python。T3 推荐通过 gRPC Bridge 引入，但这意味着运维层面增加 Python 技术栈。 |
| **严重性评级** | 🟡 **High** — 运维复杂度翻倍，但可以通过容器化隔离 |
| **影响范围** | 运维团队技能要求、CI/CD 流水线、监控/告警体系、安全扫描 |
| **缓解建议** | 1. **Phase 1-2 暂不引入 Python**：仅使用 LangChain4j/Spring AI 覆盖 80% 场景<br>2. Python Agent Engine 作为独立容器部署（Kubernetes Sidecar），与 Java 主应用生命周期解耦<br>3. 使用 Multi-stage Docker 构建固化 Python 依赖版本<br>4. 建立 Python 依赖安全扫描流水线（`pip-audit`, `safety`）<br>5. Python Engine 仅暴露 gRPC 端口，无直接外部访问 |
| **成本量化** | 新增：Python 3.12+ 运行时；~15-20 个 pip 依赖（langgraph, grpcio, protobuf, langchain-core）；Docker 镜像增加约 500MB |

### 3.3 同步 GraphQL vs 异步 Agent Streaming 的模式差异

| 维度 | 详情 |
|------|------|
| **冲突描述** | GraphQL 网关是同步 Request-Response 模型（客户端发送查询 → 服务端执行 → 返回完整结果）。Agent 执行是异步/流式的（LLM 逐 token 输出、Agent 多步推理中间状态需推送）。 |
| **冲突根源** | 两种通信范式的根本差异。GraphQL 的 `@defer/@stream` 指令 (2023 规范) 有一定缓解但尚未广泛支持。 |
| **严重性评级** | 🟡 **High** — 影响用户体验，但不阻塞基础功能 |
| **影响范围** | GraphQL 网关的请求处理模型；前端应用的响应消费模式 |
| **缓解建议** | 1. **短任务**：保持 GraphQL 同步模式（<5秒的 Agent 任务走原有 GraphQL）<br>2. **长任务/流式**：通过 SSE 或 WebSocket 独立端点提供 Agent Streaming，不走 GraphQL<br>3. **混合模式**：GraphQL Mutation 提交 Agent 任务 → 返回 `taskId` → SSE 订阅任务进度 → GraphQL Query 获取最终结果<br>4. 长期：关注 GraphQL `@stream` 指令的框架支持成熟度 |
| **架构建议** | Agent 流式端点与 GraphQL 网关并列部署在 API Gateway 层：<br>`/graphql` → 同步 API<br>`/agent/stream` → Agent 流式 API (SSE)<br>`/mcp` → MCP JSON-RPC 端点 |

### 3.4 自动生成代码的维护性挑战

| 维度 | 详情 |
|------|------|
| **冲突描述** | `app-common-api` 模块有 3770 文件 / 114 万行代码，其中大量为 `json-schema-plugin` 和 `mbg-plugins` 自动生成。引入 Agent 后将新增更多自动生成代码（Tool Wrapper、Agent Card、MCP Schema）。 |
| **冲突根源** | 自动生成代码量膨胀到可能超出可控范围；生成代码的手动修改会被下一次生成覆盖；版本控制中的 diff 噪音。 |
| **严重性评级** | 🟢 **Medium** — 可通过工程实践缓解 |
| **影响范围** | `app-common-api` 模块的代码质量、构建时间、IDE 加载性能 |
| **缓解建议** | 1. 将 Agent 相关生成代码放在独立模块（`app-agent-tools`），不混入 `app-common-api`<br>2. 生成代码标记 `@Generated` 注解，Git 中通过 `.gitattributes` 标记为 `linguist-generated=true`（GitHub diff 默认折叠）<br>3. 所有 Agent 生成代码纳入 Maven `clean` 阶段清理，保证可复现性<br>4. 生成代码的 CI 检查：如果生成代码与预期不一致则构建失败 |

### 3.5 安全模型差异：API 鉴权 vs Agent 鉴权

| 维度 | 详情 |
|------|------|
| **冲突描述** | 现有 API 鉴权基于用户 Token → 角色 → 权限的层级模型。Agent 场景中，一个 Agent 可能代表多个用户执行操作，需要更细粒度的"调用链鉴权"。 |
| **冲突根源** | MCP/A2A 协议中，Agent 可以调用其他 Agent 的 Tool，形成 N 层嵌套调用。现有 RBAC 无法表达"Agent A 代表用户 U 调用 Agent B 的 Tool T"这种委派语义。 |
| **严重性评级** | 🟡 **High** — 安全模型缺陷可能导致权限提升 |
| **影响范围** | API Gateway 认证 Filter；权限校验中间件；审计日志格式 |
| **缓解建议** | 1. Agent 间调用传递完整的"调用链上下文"（类似 AWS IAM 的信任链）<br>2. MCP/A2A 端点单独进行认证（不同于用户 API）<br>3. Agent-to-Agent 通信使用 mTLS + Service Account Token<br>4. 租户上下文在整个调用链中不可丢失 |

### 3.6 架构冲突总结

```
冲突严重性分布:
  Critical: Java 8→17+ / Spring Boot 2.4→3.x (阻塞所有 AI 框架引入)
  High:     Python 运维复杂度 / GraphQL同步vs Agent异步 / Agent安全模型
  Medium:   自动生成代码膨胀 / 其他较小冲突
```

**最关键的发现**: **Java 8 → 17+ 的升级是唯一的硬阻塞项**。其他所有冲突都可以通过架构设计缓解或分阶段解决，不会阻塞 Phase 1 启动。建议将 Java 升级作为 Phase 0，与现有路线图并行或前置。

---

## 4. 差距严重性矩阵与优先行动项

### 4.1 差距严重性评级标准

| 评级 | 定义 | 判断标准 |
|------|------|---------|
| 🔴 **Critical** | 阻断性差距 — 不解决无法启动 AI Agent 升级 | 硬依赖缺失；架构硬冲突 |
| 🟡 **High** | 重大差距 — 不解决严重影响功能完整性 | 核心能力缺失；重大架构冲突 |
| 🟢 **Medium** | 重要差距 — 应在 3-6 个月内解决 | 影响性能/用户体验/运维效率 |
| ⚪ **Low** | 优化项 — 可在 6-12 个月内解决 | 锦上添花；无功能阻塞 |

### 4.2 完整差距严重性矩阵

| # | 差距项 | 类型 | 严重性 | 短期可解？ | 阻塞 Phase | 优先行动项 | 建议时间窗口 |
|---|--------|------|--------|-----------|-----------|-----------|-------------|
| **G1** | Java 8 → 17+ 升级 | 架构冲突 | 🔴 Critical | 是 (已知路径) | All | 执行 Java 17 升级 + Spring Boot 3.x 迁移 → 兼容性测试覆盖 | 0-4 周 (Phase 0) |
| **G2** | LLM 集成层缺失 | 能力缺失 | 🔴 Critical | 是 | Phase 1 | 引入 LangChain4j Spring Boot Starter；配置 API Key 管理 | 0-2 周 |
| **G3** | MCP Server 缺失 | 能力缺失 | 🔴 Critical | 是 | Phase 1 | 搭建 MCP Server 端点；映射 2-3 个核心 API 为 MCP Tool | 2-4 周 |
| **G4** | 向量数据库缺失 | 能力缺失 | 🔴 Critical | 是 | Phase 1 | 启用 PostgreSQL pgvector 扩展；创建 embedding 表和索引 | 0-1 周 |
| **G5** | Embedding 服务缺失 | 能力缺失 | 🔴 Critical | 是 | Phase 1 | 配置 Spring AI EmbeddingClient；测试 OpenAI/BGE-M3 质量 | 1-2 周 |
| **G6** | Python 运维复杂度 | 架构冲突 | 🟡 High | 否 (组织决策) | Phase 3+ | 仅当 LangChain4j 无法满足编排需求时才引入；优先评估 Spring AI v2.0 GA | 按需 (3-6 月) |
| **G7** | GraphQL 同步 vs Agent 异步 | 架构冲突 | 🟡 High | 部分可解 | Phase 2 | SSE 端点设计与实现；短任务走 GraphQL，长任务走 SSE | 4-8 周 |
| **G8** | Agent 安全模型 | 架构冲突 | 🟡 High | 部分可解 | Phase 2 | 设计调用链上下文模型；MCP/A2A 端点独立认证 | 4-8 周 |
| **G9** | Prompt 管理系统缺失 | 能力缺失 | 🟡 High | 是 | Phase 1-2 | 外部化 Prompt 模板（数据库/配置中心）；版本管理 | 2-4 周 |
| **G10** | Agent 状态持久化缺失 | 能力缺失 | 🟡 High | 部分可解 | Phase 2 | LangChain4j ChatMemory (Phase 1)；PostgresSaver (Phase 3) | Phase 1: 1 周 / Phase 3: 3-4 周 |
| **G11** | 流式响应基础设施缺失 | 能力缺失 | 🟡 High | 是 | Phase 2 | Spring SSE Controller + LangChain4j Streaming | 2-3 周 |
| **G12** | A2A Agent 端点缺失 | 能力缺失 | 🟡 High | 是 | Phase 3 | A2A Java SDK 集成；Agent Card 生成 | 3-4 周 |
| **G13** | Agentic RAG Pipeline 缺失 | 能力缺失 | 🟡 High | 是 | Phase 2-3 | 基础 RAG (Phase 1) → 混合检索 (Phase 2) → Agentic (Phase 3) | 按 Phase 递进 |
| **G14** | 自动生成代码膨胀 | 架构冲突 | 🟢 Medium | 是 | Phase 1+ | Agent 代码独立模块；@Generated 标记；Git diff 折叠 | 持续实践 |
| **G15** | Agent 可观测性缺失 | 能力缺失 | 🟢 Medium | 是 | Phase 2 | 扩展 Micrometer；LLM 调用追踪；Token/成本仪表盘 | 3-4 周 |
| **G16** | 语义缓存层缺失 | 能力缺失 | 🟢 Medium | 是 | Phase 2-3 | Redis + 向量相似度匹配 | 1-2 周 |
| **G17** | Tool Schema 注册表缺失 | 能力缺失 | 🟢 Medium | 是 | Phase 1 | 在 MetadataRegistry 基础上扩展 Tool 注册子模块 | 1-2 周 |
| **G18** | GraphQL `@stream` 支持 | 架构冲突 | ⚪ Low | 否 (等框架成熟) | Phase 4+ | 关注 graphql-java 对 `@stream` 指令的支持 | >6 月 |

### 4.3 优先行动项 (按紧迫度排序)

#### 立即行动 (Phase 0 — 前置条件，0-4 周)

```
Priority 1: G1 — Java 8 → 17+ 升级 + Spring Boot 2.4 → 3.x
  ├── 影响：阻塞所有 AI Agent 框架引入
  ├── 工作量：2-4 人周 (含兼容性测试)
  ├── 回滚方案：保留 Java 8 Docker 镜像，新模块单独 Java 17
  └── 验收标准：全模块编译通过 + 回归测试通过
```

#### Phase 1 (基础 AI 能力，0-4 周)

```
Priority 2: G2 — LLM 集成层引入 [Dependency: G1]
  ├── LangChain4j Spring Boot Starter 集成
  ├── 创建 @AiService 接口原型
  └── 验收：成功调用 LLM 并返回响应

Priority 3: G4 + G5 — 向量数据库 + Embedding [Dependency: G1]
  ├── PostgreSQL pgvector 扩展启用
  ├── Spring AI EmbeddingClient 配置
  └── 验收：文本 → Embedding → VectorStore 存储 → 相似度查询

Priority 4: G3 — MCP Server 原型 [Dependency: G1, G2]
  ├── 搭建 MCP JSON-RPC 端点
  ├── 将 2-3 个元数据查询 API 映射为 MCP Tool
  └── 验收：LLM 通过 MCP 协议成功调用业务 API

Priority 5: G9 — Prompt 外部化 [Dependency: G2]
  ├── Prompt 模板存储（数据库表/配置文件）
  └── 验收：Prompt 修改无需重新部署
```

#### Phase 2 (Agent 深化，4-8 周)

```
Priority 6: G7 — Agent Streaming 端点 [Dependency: G2]
Priority 7: G11 — 流式响应基础设施 [Dependency: G7]
Priority 8: G13 — 基础 RAG Pipeline [Dependency: G4, G5]
Priority 9: G10 — Agent 状态持久化 (ChatMemory) [Dependency: G2]
Priority 10: G8 — Agent 安全模型设计 [Dependency: G3]
Priority 11: G15 — 可观测性集成 [Dependency: G2]
```

#### Phase 3+ (高级能力，8+ 周)

```
Priority 12: G12 — A2A Agent 端点 (按需)
Priority 13: G6 — Python Agent Engine 引入 (仅当 LangChain4j 不足时)
Priority 14: G16 — 语义缓存
Priority 15: G13-advanced — Agentic RAG 升级 (自反思/多源检索)
```

### 4.4 严重性热力图

```
能力维度 / 严重性      Critical    High    Medium   Low
─────────────────────────────────────────────────────
LLM 集成                  ██
向量数据库                ██
Embedding                 ██
MCP Server                ██
Java 版本升级             ██
─────────────────────────────────────────────────────
Prompt 管理                         ██
Agent 状态持久化                     ██
流式响应                             ██
Python 运行时                        ██
A2A 端点                             ██
Agentic RAG                          ██
Agent 安全模型                       ██
GraphQL vs 异步                      ██
─────────────────────────────────────────────────────
可观测性                                      ██
语义缓存                                      ██
Tool 注册表                                   ██
代码膨胀管理                                   ██
─────────────────────────────────────────────────────
GraphQL @stream                                        ██
```

---

## 5. 可复用资产盘点

差距分析不仅要看"缺什么"，更要认清"有什么可复用"来决定实施成本。

### 5.1 高价值可复用资产

| 资产 | 复用方式 | 节省工作量 | 降低风险 |
|------|---------|-----------|---------|
| **元数据注册中心** | 直接扩展为 MCP Tool 注册中心 + Agent 技能目录 | ~4-6 人周 | 避免建设新的 Tool 发现机制 |
| **gRPC 基础设施** | 复用 Protobuf 编译流水线 + gRPC Server/Client 代码生成 | ~3-4 人周 | 避免从零搭建 Python-Java 通信 |
| **Drools 规则引擎** | 包装为 Agent Guardrail 后端实现 | ~2-3 人周 | 避免从零建设策略执行引擎 |
| **API Gateway** | 扩展路由规则支持 MCP/A2A 端点；复用认证/限流 Filter | ~2-3 人周 | 避免建设独立的 Agent 网关 |
| **PostgreSQL** | 现有 DB 直接启用 pgvector 扩展 | ~1 人周 | 避免引入新数据库实例的运维 |
| **Maven 插件体系** | 新增 Agent 代码生成 target，复用插件执行生命周期 | ~3-4 人周 | 避免代码生成的碎片化 |
| **API/Impl 分离** | 每个 `*-api` 模块直接推导 A2A Agent Card | ~2-3 人周 | 避免 Agent 能力的逆向梳理 |
| **构建基础设施** | CI/CD 流水线、容器化部署、监控告警均可复用 | ~2-3 人周 | 避免建设独立 Agent 运维体系 |

**总节省**: 通过复用现有 8 项关键资产，预计节省 **21-29 人周** 的工作量，并显著降低引入新组件带来的运维风险。

### 5.2 需谨慎处理的资产

| 资产 | 风险 | 处理建议 |
|------|------|---------|
| **app-common-api (114 万行)** | 大量自动生成代码与手工代码混在一起；改动影响面广 | Agent 相关代码放入独立新模块，不混入此模块 |
| **现有权限模型 (RBAC)** | 无法直接表达 Agent 调用链鉴权 | 新设计 Agent 专用鉴权层，不与现有 RBAC 耦合 |
| **GraphQL Schema (可能是最大入口)** | 全部 API 映射为 Tool 会导致 Tool 数量爆炸 | 仅将"对 Agent 有用的"Query/Mutation 暴露为 Tool；非暴露的 API 保持 GraphQL |

---

## 6. 综合发现与建议

### 6.1 核心发现

1. **"高契合、低阻碍"架构**: 项目的 7 大架构模式中有 5 个与 AI Agent 具有五星级契合度（元数据驱动、API/Impl 分离、GraphQL 网关、gRPC 通信、Drools 规则引擎、Maven 插件链）。这意味着 AI Agent 升级的**集成成本远低于"从零建设"的项目**。

2. **唯一硬阻塞项是 Java 版本**: 在 18 项差距中，仅有 G1 (Java 8→17+) 是真正的阻断性依赖。其他差距都可以通过架构设计分阶段解决。建议将 Java 升级作为独立的 Phase 0。

3. **gRPC 是压制性优势**: 现有 gRPC 基础设施直接解决了 T3 报告中最推荐的 Python-Java Bridge 方案的最大障碍。在纯 Java 项目中，搭建 gRPC Bridge 通常需要 3-4 人周，本项目几乎零成本。

4. **"快赢"路径清晰**: 元数据 → MCP Tool 自动生成、API/Impl → A2A Agent Card、Drools → Agent Guardrails 是三个可以快速交付高价值的集成点，每个仅需 1-3 人周。

5. **Phase 1 可持续降级**: 如果资源受限，Phase 1 可以使用 LangChain4j（纯 Java）+ PgVector（复用 PostgreSQL）+ 简单 @Tool 注解（无需 MCP 协议）快速打通"Agent 调用业务 API"的基础链路。MCP 协议化的 Tool 暴露可以在 Phase 2 补充。

6. **Python 风险可控**: 即使完全不引入 Python/LangGraph，使用 LangChain4j 的 Agentic Workflow（Sequential/Parallel/Conditional/Loop）也能覆盖 80% 以上的企业编排场景。真正的 Human-in-the-Loop 中断控制才需要 LangGraph，属于 Phase 3+ 的高级需求。

### 6.2 一句话总结

> **现有架构是 AI Agent 升级的"理想土壤"——7 大架构模式与 Agent 范式高度同构，唯一的硬阻塞项是 Java 8→17+ 升级。从"元数据→MCP Tool 自动生成"切入，可在 4 周内打通首个 AI Agent 功能链路。**

---

*本报告综合了 T1 (模块结构分析)、T2 (架构模式分析)、T3 (Agent 框架调研) 和 T4 (协议与基础设施调研) 的产出，为后续 T6 (集成架构设计) 提供差距输入。*
