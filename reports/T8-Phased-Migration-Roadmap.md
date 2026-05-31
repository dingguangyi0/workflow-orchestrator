# T8: 分阶段迁移路线图

**日期**: 2026-05-31
**依赖**: T5 (差距分析), T6 (集成架构设计)
**目标**: 基于差距分析和集成架构设计，制定可执行的分阶段 AI Agent 升级路线图

---

## 目录

1. [路线图总览](#1-路线图总览)
2. [Phase 0: 基础设施现代化](#2-phase-0-基础设施现代化)
3. [Phase 1: Agent 核心能力](#3-phase-1-agent-核心能力)
4. [Phase 2: MCP + Agentic RAG](#4-phase-2-mcp--agentic-rag)
5. [Phase 3: 高级编排与护栏](#5-phase-3-高级编排与护栏)
6. [Phase 4: 智能自动化](#6-phase-4-智能自动化)
7. [总体甘特图与资源估算](#7-总体甘特图与资源估算)
8. [跨 Phase 风险与全局缓解](#8-跨-phase-风险与全局缓解)
9. [决策里程碑与 Go/No-Go 节点](#9-决策里程碑与-gono-go-节点)

---

## 1. 路线图总览

### 1.1 总体目标

将现有 Spring Boot 多模块企业平台（Java 8 + Spring Boot 2.4）分阶段升级为 AI Agent 增强架构，目标能力：

```
元数据驱动平台 ──────────────────────► AI Agent 增强平台

现有能力:                              目标能力:
├── JSON Schema → 代码生成          ├── JSON Schema → MCP Tool 自动生成
├── API/Impl 分离                   ├── API → A2A Agent Card 自动生成
├── GraphQL 网关                     ├── GraphQL → MCP Resource/Tool 端点
├── gRPC 微服务通信                  ├── gRPC → Python LangGraph Bridge
├── Drools 规则引擎                  ├── Drools → Agent Guardrails 后端
├── MyBatis 代码自动生成              ├── MyBatis → Agent Tool Wrapper 自动生成
└── Maven 插件体系                   └── Maven → 编译期 Agent 代码生成
```

### 1.2 5 Phase 时间线与依赖

```
Phase 0: 基础设施现代化 (4-6 周)            ◀ 硬前置，阻塞所有后续 Phase
  │
  ├──► Phase 1: Agent 核心能力 (6-8 周)     ◀ 首个可演示的 AI Agent 功能
  │       │
  │       ├──► Phase 2: MCP + Agentic RAG (8-12 周)  ◀ 协议标准化 + 智能检索
  │       │       │
  │       │       ├──► Phase 3: 高级编排与护栏 (8-12 周)  ◀ 复杂工作流 + 安全体系
  │       │       │       │
  │       │       │       └──► Phase 4: 智能自动化 (6-8 周)  ◀ 自愈 + 多 Agent 协作
  │       │       │
  │       │       └──► (部分并行: Phase 2 结束前 2 周可启动 Phase 3 设计)
  │       │
  │       └──► (部分并行: Phase 1 结束前 2 周可启动 Phase 2 设计)
  │
  └──► (可并行推进 Phase 0 基础设施验收 + Phase 1 设计文档)
```

### 1.3 总人周估算

| Phase | 名称 | 时间 | 核心人数 | 人周 | 关键里程碑 |
|-------|------|------|---------|------|-----------|
| **Phase 0** | 基础设施现代化 | 4-6 周 | 2-3 人 | 8-14 | 全模块 Java 17 编译通过 |
| **Phase 1** | Agent 核心能力 | 6-8 周 | 3-4 人 | 16-28 | LLM 通过 Tool 查询业务数据 |
| **Phase 2** | MCP + Agentic RAG | 8-12 周 | 3-5 人 | 24-48 | MCP 协议端点生产可用 |
| **Phase 3** | 高级编排与护栏 | 8-12 周 | 3-5 人 | 24-54 | Human-in-the-Loop 审批链路 |
| **Phase 4** | 智能自动化 | 6-8 周 | 2-4 人 | 12-28 | 多 Agent 协作上线 |
| **合计** | — | **32-46 周** | — | **84-172 人周** | — |

> **资源模型说明**: 人周范围下限 = 最少人数×最短周数，上限 = 最多人数×最长周数。实际值取决于团队技能匹配度、Python/Jakarta 迁移经验、外部依赖就绪情况。
>
> **关键假设**: Phase 3 中 Python LangGraph Bridge 按需引入。若不引入 Python（仅使用 LangChain4j Agentic Workflow），Phase 3 工作量可降低 8-12 人周，总人周下限降至约 76 人周。

### 1.4 全局架构演进

```
Phase 0:                    Phase 1:                    Phase 2:                     Phase 3:                    Phase 4:
Java 8 → 17                 + Agent Runtime             + MCP Server                 + LangGraph Bridge           + Multi-Agent
Spring Boot 2.4 → 3.3       + LLM 接入层               + Schema2MCP                 + Drools Guardrails           + Self-Healing
依赖升级                     + @AiService                + Hybrid RAG                 + A2A Gateway                + Code Generation
CI/CD 升级                   + PgVector                  + SSE Streaming              + OpenTelemetry               + Prod Ops
                             + 基础 RAG                  + Prompt Mgmt                + Semantic Cache
                             + 简单 Workflow             + Agent Security
```

---

## 2. Phase 0: 基础设施现代化

### 2.1 Phase 概要

| 维度 | 详情 |
|------|------|
| **目标** | 将 Java 8 → 17 LTS, Spring Boot 2.4 → 3.3.x, 所有相关依赖升级，消除 AI Agent 框架引入的硬阻塞 |
| **时间范围** | 4-6 周 |
| **前置依赖** | 无（独立 Phase，可先行启动） |
| **后续 Phase** | Phase 1-4 全部依赖此 Phase 完成 |
| **团队配置** | 2-3 人（1 资深 Java + 1 DevOps + 1 QA） |

### 2.2 任务分解

#### P0-T1: Java 8 → 17 编译环境升级

| 维度 | 详情 |
|------|------|
| **描述** | 更新所有模块的 `maven-compiler-plugin` 配置，将 `<source>/<target>` 从 8 升级到 17；Docker 基础镜像从 `eclipse-temurin:8-jre` 切换到 `eclipse-temurin:17-jre`；更新 CI/CD 流水线使用的 JDK 版本；确认所有第三方依赖存在 Java 17 兼容版本 |
| **产出** | (1) 父 POM `java.version` 属性更新; (2) Dockerfile 基础镜像变更; (3) CI/CD 流水线 JDK 17 配置; (4) 依赖兼容性矩阵文档 |
| **人周** | 1.5-2.0 |
| **关键校验** | `mvn clean compile` 全部模块通过，零编译错误 |

#### P0-T2: javax.* → jakarta.* 全量迁移

| 维度 | 详情 |
|------|------|
| **描述** | Spring Boot 3.x 将 Java EE 的 `javax.*` 命名空间全面迁移到 Jakarta EE 的 `jakarta.*`。需要在全项目约 2000+ 文件中执行以下替换：`javax.persistence.*` → `jakarta.persistence.*`; `javax.servlet.*` → `jakarta.servlet.*`; `javax.validation.*` → `jakarta.validation.*`; `javax.annotation.*` → `jakarta.annotation.*`; `javax.transaction.*` → `jakarta.transaction.*`。可使用 IDE 的结构化搜索替换或工具辅助（如 OpenRewrite 的 `org.openrewrite.java.migrate.jakarta.JavaxMigrationToJakarta`） |
| **产出** | (1) 全项目 import 语句迁移完成; (2) 编译通过; (3) OpenRewrite 迁移脚本（可复现） |
| **人周** | 2.0-3.0 |
| **关键校验** | `mvn clean compile test-compile` 全部模块通过; `grep -r "javax\." --include="*.java"` 返回零结果（除合理例外） |

#### P0-T3: Spring Boot 2.4 → 3.3.x 升级

| 维度 | 详情 |
|------|------|
| **描述** | 升级 `spring-boot-starter-parent` 版本; 适配 Spring Security 6.x 配置变更（`SecurityFilterChain` lambda DSL）; 适配 Actuator 端点路径变更（`/actuator/health` 替代 `health/`）; 废弃 API 替换（`WebMvcConfigurerAdapter` → `WebMvcConfigurer`, `@EnableGlobalMethodSecurity` → `@EnableMethodSecurity`）; Spring Data 方法签名适配 |
| **产出** | (1) 父 POM Spring Boot 版本更新; (2) Spring Security 配置适配; (3) Actuator 端点适配; (4) 废弃 API 替换清单 |
| **人周** | 2.0-3.0 |
| **关键校验** | 所有微服务模块启动成功; `/actuator/health` 返回 UP; Security 认证/鉴权行为无回归 |

#### P0-T4: 依赖版本同步升级

| 维度 | 详情 |
|------|------|
| **描述** | 升级与 Spring Boot 3.x 配套的第三方依赖：GraphQL Java (→ 21.x); gRPC (1.11 → 1.63.x); MyBatis Spring Boot Starter (2.x → 3.x); Drools (→ 9.44.0.Final, 如兼容); Spring Cloud (2020.0.x → 2023.0.x); 其他传递依赖版本冲突解决 |
| **产出** | (1) 升级后的 `app-build-plugins/pom.xml` 依赖管理; (2) 依赖兼容性验证报告; (3) 版本冲突解决记录 |
| **人周** | 1.5-2.0 |
| **关键校验** | `mvn dependency:tree` 零冲突; 所有 Starter 自动配置加载正常 |

#### P0-T5: CI/CD 流水线与容器化升级

| 维度 | 详情 |
|------|------|
| **描述** | 更新 Jenkins/GitHub Actions 流水线中的 JDK 版本配置; 升级 Maven Surefire/Failsafe 插件版本; 更新 Docker Compose/K8s 部署清单中的镜像 Tag; 更新监控/健康检查端点配置; 增加 Jakarta 迁移相关的代码合规检查 |
| **产出** | (1) 更新后的 CI/CD 配置; (2) 更新后的 Dockerfile/部署清单; (3) 流水线运行验证（编译 + 测试 + 构建镜像） |
| **人周** | 1.0-2.0 |
| **关键校验** | 完整 CI/CD 流水线运行成功（编译 → 单测 → 集成测试 → 镜像构建 → 部署） |

#### P0-T6: 全量回归测试与兼容性验证

| 维度 | 详情 |
|------|------|
| **描述** | 执行全部单元测试和集成测试; 验证 GraphQL API 响应格式无变化; 验证 gRPC 服务通信正常; 验证 MyBatis 数据库操作正常; 验证 Drools 规则执行结果一致; 执行性能对比测试（升级前后响应时间、内存占用） |
| **产出** | (1) 回归测试通过报告; (2) 性能对比数据; (3) 已知问题清单及修复计划 |
| **人周** | 1.5-2.0 |
| **关键校验** | 测试覆盖率不低于升级前; 性能劣化 < 5%; 零 Blocking 级别 Bug |

### 2.3 里程碑定义

**M0: Java 17 编译成功** (第 2 周末)

| 验收项 | 标准 |
|--------|------|
| 编译 | 全部 16+ 模块 `mvn clean compile` 零错误 |
| Jakarta 迁移 | `grep -r "javax\." --include="*.java"` 零残留 |
| 依赖冲突 | `mvn dependency:tree` 无 PENDING/CONFLICT 标记 |

**M1: Spring Boot 3.x 启动成功** (第 4 周末)

| 验收项 | 标准 |
|--------|------|
| 启动 | 所有微服务模块启动成功，启动时间 < 升级前 120% |
| 健康检查 | `/actuator/health` 全部组件 UP |
| Security | 认证/鉴权回归测试 100% 通过 |
| GraphQL | Schema 自省 `{ __schema { types { name } } }` 返回与升级前一致 |

**M2: 全量回归通过** (第 6 周末)

| 验收项 | 标准 |
|--------|------|
| 单元测试 | 全部通过，通过率 >= 升级前 |
| 集成测试 | 端到端流程全部通过 |
| 性能基线 | P95 延迟 < 升级前 105%；内存占用 < 升级前 110% |
| CI/CD | 完整流水线运行成功 |

### 2.4 风险提示

| 风险 | 概率 | 影响 | 缓解措施 |
|------|------|------|---------|
| **javax → jakarta 迁移遗漏** | 高 | 运行时 `NoClassDefFoundError` | 使用 OpenRewrite 自动迁移 + `grep` 二次校验; CI 中增加 `javax` 残留检测 |
| **Spring Security 行为变更** | 中 | 认证/鉴权异常 | 提前在单独分支做 Security 配置适配; 增加安全回归测试用例 |
| **MyBatis/Drools 版本不兼容** | 中 | 数据层/规则层异常 | 在 Phase 0 早期验证两个框架的新版本兼容性; 准备回退版本 |
| **Actuator 端点路径变更** | 低 | 监控告警失效 | 提前梳理所有使用 Actuator 端点的外部系统（K8s Probe, Prometheus, 告警系统）并更新配置 |
| **gRPC Proto 代码需重新生成** | 中 | gRPC 通信中断 | 升级 protobuf-maven-plugin 版本后重新编译 `.proto`; 验证 Java 和 Python侧兼容 |
| **性能劣化** | 低 | 用户可感知的响应变慢 | 提前运行性能基线测试; 使用 Java 17 的 ZGC/Shenandoah GC 可能改善延迟 |

### 2.5 回滚方案

```
Phase 0 失败回退路径:

场景 A: javax → jakarta 迁移导致大规模编译失败
  ├── 操作: `git revert` 迁移提交; 切换到 OpenRewrite 工具重新执行
  ├── 影响: 延迟 1-2 周
  └── 触发条件: 编译错误 > 100 个文件且 4 小时内无法修复

场景 B: Spring Boot 3.x 启动失败 (依赖冲突/配置问题)
  ├── 操作: 保留 Java 17 编译环境; 回退 Spring Boot 至 2.7.x 过渡版本
  │         (Spring Boot 2.7 + Java 17 仍可引入 LangChain4j, 但缺少一些 AutoConfiguration)
  ├── 影响: 延迟 1 周; Phase 1 可并行启动但需额外适配
  └── 触发条件: 核心服务模块启动失败且 2 天内无法修复

场景 C: 依赖版本冲突无法解决
  ├── 操作: 逐个降级冲突依赖到已知兼容版本; 标记冲突项为"Phase 1 解决"
  ├── 影响: 部分依赖使用旧版本; Phase 1 可能需要额外适配
  └── 触发条件: 依赖冲突 > 5 个且影响核心功能

场景 D: 性能劣化 > 10% 且无法解释
  ├── 操作: 暂时保持 JDK 8 的 JVM 参数; 对比分析 GC 日志找出劣化原因
  ├── 影响: 延迟 1 周进行性能调优
  └── 触发条件: 性能测试 P95 延迟 > 升级前 110%

全局回滚: 保留 Phase 0 前的完整 Docker 镜像 Tag 和数据库快照; 部署回滚窗口 < 30 分钟
```

---

## 3. Phase 1: Agent 核心能力

### 3.1 Phase 概要

| 维度 | 详情 |
|------|------|
| **目标** | 引入 LangChain4j，建立 LLM 接入层，实现首个 @AiService 和 @Tool，打通"Agent 通过 MCP 调用业务 API"的基础链路 |
| **时间范围** | 6-8 周 |
| **前置依赖** | Phase 0 全部完成 (M0 + M1 至少通过) |
| **后续 Phase** | Phase 2（MCP 协议标准化）; Phase 3（高级编排） |
| **团队配置** | 3-4 人（1 资深 Java/Spring + 1 AI/LLM 工程 + 1 平台开发 + 1 QA） |

### 3.2 任务分解

#### P1-T1: app-agent 模块骨架搭建

| 维度 | 详情 |
|------|------|
| **描述** | 创建 `app-agent/` 聚合 Maven 模块及其子模块：`app-agent-core` (Agent 运行时核心), `app-agent-core-api` (Agent 接口契约层，遵循 API/Impl 分离模式), `app-agent-core-impl` (Agent 实现层)。在父 POM 中引入 LangChain4j BOM (`1.15.0-beta25`) 和 Spring AI BOM (`2.0.0-M6`); 配置 `.gitattributes` 将所有 Agent 生成代码标记为 `linguist-generated=true` |
| **产出** | (1) `app-agent/` 模块结构; (2) 父 POM 依赖管理更新; (3) `.gitattributes` 配置 |
| **人周** | 1.0-1.5 |
| **关键校验** | `mvn clean install` 新模块编译通过; 依赖树无冲突 |

#### P1-T2: LLM 接入层配置

| 维度 | 详情 |
|------|------|
| **描述** | 配置 LangChain4j Spring Boot Starter 自动配置; 选择并接入 LLM 提供商（推荐 DeepSeek-V4 作为国内优先，OpenAI GPT-4o-mini 作为国际备选）；设计 API Key 管理方案（推荐：K8s Secret + Spring Cloud Config 加密存储，避免硬编码）；配置多模型路由策略（简单任务用 mini 模型，复杂推理用 full 模型） |
| **产出** | (1) `application-ai.yml` 配置; (2) API Key 管理方案文档; (3) 模型连接测试通过 |
| **人周** | 1.0-1.5 |
| **关键校验** | `ChatLanguageModel.generate("Hello")` 成功返回响应 |

#### P1-T3: @AiService 原型开发

| 维度 | 详情 |
|------|------|
| **描述** | 基于 API/Impl 分离模式，创建第一个 @AiService 接口（如 `MetadataQueryAgent`），包含 @SystemMessage（定义 Agent 角色、可用工具、安全约束）、@UserMessage（处理用户输入）、@MemoryId（标记会话ID）。创建 `AiServices` 构建配置类，注入 ChatLanguageModel, ToolProvider, ChatMemoryStore。在 impl 层实现 Agent 的构建逻辑 |
| **产出** | (1) `MetadataQueryAgent` 接口定义; (2) `AgentToolConfiguration` 配置类; (3) 单元测试 |
| **人周** | 1.5-2.0 |
| **关键校验** | Agent 对简单自然语言问题返回有意义的回答; SystemMessage 约束生效 |

#### P1-T4: PgVector 启用 + Embedding 服务

| 维度 | 详情 |
|------|------|
| **描述** | 在现有 PostgreSQL 实例中启用 `pgvector` 扩展 (`CREATE EXTENSION vector`)；执行 DDL 创建 `agent_embedding_store` 表（包含 embedding vector(1536)、content TEXT、metadata JSONB、tenant_id），创建 IVFFlat 向量索引和全文搜索 GIN 索引；配置 Spring AI EmbeddingClient（推荐 `text-embedding-3-small`，如需本地部署可用 BGE-M3）；实现 Embedding 生成 → 存储 → 相似度查询的端到端链路 |
| **产出** | (1) PgVector DDL + 索引; (2) EmbeddingClient Bean 配置; (3) 端到端 Embedding 链路验证 |
| **人周** | 1.5-2.0 |
| **关键校验** | 文本 → Embedding → Store → 相似度检索 端到端通过; 检索延迟 < 200ms |

#### P1-T5: 基础 RAG Pipeline

| 维度 | 详情 |
|------|------|
| **描述** | 使用 LangChain4j 的 RAG 组件搭建基础检索管道：`DocumentSplitter`（递归字符分割，chunk=512, overlap=128）→ `EmbeddingStoreIngestor`（自动 Embedding + 写入）→ `EmbeddingStoreContentRetriever`（相似度检索，topK=5, minScore=0.7）。实现文档摄取 API（支持文件上传、URL、数据库记录），实现基础的"检索 → 增强 → 生成"流程 |
| **产出** | (1) `BasicRagConfiguration` 配置类; (2) `DocumentIngestionService`; (3) RAG 质量评估报告 |
| **人周** | 2.0-2.5 |
| **关键校验** | 文档上传 → 索引 → 检索 → LLM 基于检索结果问答; Top-3 命中率 > 80% |

#### P1-T6: @Tool 注解 + 业务 API 调用

| 维度 | 详情 |
|------|------|
| **描述** | 为 3-5 个核心业务场景创建 @Tool 注解的工具方法（如 `queryOrder`, `getEntitySchema`, `searchUser`）。每个 Tool 方法需要：`@Tool` 注解（含中文描述，面向 LLM 的 tool description）+ `@ToolParam` 注解（每个参数的描述，面向 LLM 决定是否调用及传参）+ Guardrail 基础接入（写操作需 `confirm` 参数确认）。Tool 实现直接调用现有的 MyBatis Mapper 或 Service Bean |
| **产出** | (1) 3-5 个 @Tool 方法; (2) Tool 调用成功记录; (3) LLM 自主决策调用 Tool 的行为测试 |
| **人周** | 1.5-2.0 |
| **关键校验** | LLM 根据用户自然语言问题自动选择合适的 Tool 并传参; Tool 返回结果格式符合预期 |

#### P1-T7: 简单 Workflow 编排

| 维度 | 详情 |
|------|------|
| **描述** | 使用 LangChain4j `SequentialAgent` 实现一个端到端的"数据查询 → 分析 → 报告"顺序工作流；使用 `ConditionalAgent` 实现"意图路由 → 分派不同 Agent"的简单条件工作流。每个工作流包含：Agent 初始化、步骤配置、错误处理（单步失败后的重试机制）、执行结果聚合 |
| **产出** | (1) `DataAnalysisWorkflow` (顺序); (2) `IntentRouterWorkflow` (条件); (3) 工作流执行成功演示 |
| **人周** | 1.5-2.0 |
| **关键校验** | 顺序工作流 3 步全成功; 条件工作流正确路由; 单步失败后重试生效 |

#### P1-T8: ChatMemory 会话持久化

| 维度 | 详情 |
|------|------|
| **描述** | 实现 LangChain4j `ChatMemoryStore` 接口，使用 PostgreSQL 持久化 Agent 会话记忆。创建 `agent_chat_memory` 表（session_id, message_index, message_type, content, metadata, tenant_id）。配置 `MessageWindowChatMemory`（窗口大小 20 条消息），支持多租户隔离（按 tenant_id 过滤） |
| **产出** | (1) `PostgresChatMemoryStore` 实现; (2) `agent_chat_memory` DDL; (3) 多轮对话上下文保持验证 |
| **人周** | 1.0-1.5 |
| **关键校验** | 多轮对话中 Agent 能正确引用历史消息; 租户 A 的对话不泄露到租户 B |

#### P1-T9: MCP Server 框架搭建 (基础)

| 维度 | 详情 |
|------|------|
| **描述** | 创建 `app-agent-mcp` 模块，搭建 MCP JSON-RPC 2.0 端点（`/mcp`）。实现 MCP 协议生命周期方法（`initialize`, `notifications/initialized`）和核心方法（`tools/list`, `tools/call`）。将 Phase 1 中创建的 @Tool 方法注册为 MCP Tool；在 API Gateway 中增加 `/mcp` 路由规则，复用现有认证 Filter |
| **产出** | (1) `McpServerController` 核心端点; (2) `MetadataDrivenToolProvider` 基础实现; (3) MCP Tool 调用端到端验证 |
| **人周** | 2.0-3.0 |
| **关键校验** | 外部 MCP Client（Claude Desktop / Cursor）可以通过 MCP 协议发现并调用 Tool |

#### P1-T10: AI 依赖注入 Maven 统一版本管理

| 维度 | 详情 |
|------|------|
| **描述** | 在 `app-build-plugins/pom.xml` 的 `<dependencyManagement>` 中统一管理 AI 相关依赖版本：`langchain4j-bom`, `spring-ai-bom`, `openai-java`, `pgvector`, `opentelemetry-bom` 等。扩展 `app-archetype` 模板，支持 `--with-ai` 参数，生成含 AI Agent 基础设施的新模块骨架（含 @AiService 接口 + MCP Server 基础配置） |
| **产出** | (1) 父 POM AI 依赖 BOM 配置; (2) 更新后的 `app-archetype`; (3) 依赖版本一致性检查脚本 |
| **人周** | 1.0-1.5 |
| **关键校验** | `app-archetype --with-ai` 生成的新模块可直接启动且包含 @AiService 基础接口 |

### 3.3 里程碑定义

**M3: 首个 AI Agent 调用成功** (第 2 周末)

| 验收项 | 标准 |
|--------|------|
| LLM 调用 | `ChatLanguageModel` 成功调用至少一个 LLM 提供商 |
| @AiService | Agent 接口定义完成，`AiServices.builder()` 构建成功 |
| 安全 | API Key 不在代码/日志中泄露 |

**M4: Agent 通过 Tool 查询业务数据** (第 5 周末)

| 验收项 | 标准 |
|--------|------|
| PgVector | Embedding 存储 + 检索功能可用 |
| @Tool | 至少 3 个 Tool 注册成功，LLM 可自动选择调用 |
| RAG | 基础 RAG 管道"文档→检索→生成"可运行 |
| ChatMemory | 多轮对话上下文保持 |
| 安全性 | 租户隔离生效（租户 A 的数据不被租户 B 访问） |

**M5: 首个端到端 Workflow 演示通过** (第 8 周末)

| 验收项 | 标准 |
|--------|------|
| Workflow | 顺序工作流"查询→分析→报告"端到端成功执行 |
| MCP | `/mcp` 端点可被外部客户端调用 |
| 错误处理 | 单步失败后重试 + 错误信息清晰可读 |
| 构建 | 全部 Agent 模块 `mvn clean install` 通过 |

### 3.4 风险提示

| 风险 | 概率 | 影响 | 缓解措施 |
|------|------|------|---------|
| **LLM API 不稳定 (限流/超时)** | 高 | Agent 可用性下降 | 实现指数退避重试（max 3次）; 本地部署小模型作为降级（Ollama + Qwen2.5-7B）; 熔断器保护 |
| **Token 成本远超预算** | 中 | 项目 ROI 受到质疑 | 从 Day 1 接入成本追踪; 优先使用低成本模型（DeepSeek-V4: $0.27/$1.10 per 1M tokens）; 大任务限制 maxTokens |
| **@SystemMessage 注入攻击** | 中 | Agent 行为被恶意操纵 | Phase 1 基础：UserMessage 输入过滤; Phase 3 增强：Drools Guardrail 完整规则 |
| **LLM 幻觉输出** | 中 | 错误信息传递给用户 | 在 SystemMessage 中强调"不确定时说不知道"; RAG 检索结果强制引用; 输出中标注置信度 |
| **PgVector 性能不足** | 低 | 检索延迟 > 500ms | 评估数据量；按需切换到 Milvus（Phase 3）；优化 IVFFlat 索引参数 |
| **MCP 协议兼容性** | 中 | 外部客户端连接失败 | 使用 MCP Inspector 工具验证协议兼容性; 参考 Spring AI MCP Server 的 Wire Compat 测试 |

### 3.5 回滚方案

```
Phase 1 失败回退路径:

场景 A: LLM API 不可用/不可接受的响应质量
  ├── 操作: 关闭 Agent AutoConfiguration（Feature Flag: app.agent.enabled=false）
  │         业务系统完全不受影响，因为 Agent 是独立的增强层
  ├── 影响: Agent 功能不可用，但现有系统零影响
  └── 触发条件: LLM API 连续 3 天可用性 < 99%

场景 B: Agent 响应质量不可接受 (幻觉率 > 20%)
  ├── 操作: 增强 SystemMessage Prompt 工程; 增加 RAG 检索严格的 minScore 阈值;
  │         评估更换模型提供商
  ├── 影响: Agent 功能标记为"Beta"，仅对内部用户开放
  └── 触发条件: 人工评估中幻觉率 > 20%

场景 C: Agent 模块构建失败
  ├── 操作: 将 app-agent 模块从主构建中 exclude (-pl !app-agent)
  ├── 影响: 不影响主业务模块构建
  └── 触发条件: app-agent 构建失败且 1 天内无法修复

全局降级开关: application-ai.yml 中 `app.agent.enabled: false` → 所有 Agent 组件不加载; 
业务系统与 Phase 0 完全相同
```

---

## 4. Phase 2: MCP + Agentic RAG

### 4.1 Phase 概要

| 维度 | 详情 |
|------|------|
| **目标** | 实现 Schema2MCP 转换器核心创新，将元数据驱动的 MCP Tool 自动生成能力产品化；构建混合检索 RAG；实现 SSE Streaming 端点；建立 Agent 安全模型；外部化 Prompt 管理 |
| **时间范围** | 8-12 周 |
| **前置依赖** | Phase 1 完成（M4 至少通过），MCP Server 基础框架可用 |
| **后续 Phase** | Phase 3（高级编排 + LangGraph） |
| **团队配置** | 3-5 人（1 AI 工程 + 1 平台开发 + 1 安全工程 + 1 DevOps + 1 QA） |

### 4.2 任务分解

#### P2-T1: Schema2MCP 转换器核心实现

| 维度 | 详情 |
|------|------|
| **描述** | 这是整个 AI Agent 升级的"核心创新"和"快赢切入点"。实现 `Schema2MCPConverter` 组件，将 JSON Schema 元数据定义（entityName, label, description, properties）自动映射为 MCP Tool 规范（name, description, inputSchema）。支持 5 种操作类型：query (列表查询)、get (单条获取)、create (创建)、update (更新)、delete (删除)。映射规则：`entity.label` → Tool.description 前缀；`property.description` → `inputSchema.properties.description`；`property.enum` → `inputSchema.properties.enum`；`property.type` 自动映射为 JSON Schema type。自动添加分页参数 (page/pageSize) 到 query Tool |
| **产出** | (1) `Schema2MCPConverter` 完整实现; (2) 单元测试（覆盖所有映射规则和操作类型）; (3) 转换质量评估（人工抽检 20 个实体的转换结果） |
| **人周** | 2.0-3.0 |
| **关键校验** | 至少 50 个实体元数据成功转换为 MCP Tool; Tool description 中文可读性通过 QA 审核; inputSchema 符合 JSON Schema Draft 2020-12 |

#### P2-T2: MetadataDrivenToolProvider 动态注册

| 维度 | 详情 |
|------|------|
| **描述** | 实现 `MetadataDrivenToolProvider` 组件，监听元数据注册中心 (`MetadataRegistry`) 的变更事件，动态同步 MCP Tool 注册表。启动时从 Registry 加载全部实体 → Schema2MCP 转换 → 注册到 MCP Server。监听 Registry 变更（ENTITY_ADDED/REMOVED/UPDATED），热更新 Tool 注册表（无需重启）。通过 MCP 协议 `notifications/tools/list_changed` 通知所有连接的 MCP 客户端。实现租户感知的 Tool 过滤（`listTools(String tenantId)` 仅返回当前租户有权限的 Tool） |
| **产出** | (1) `MetadataDrivenToolProvider` 实现; (2) Registry 事件监听器; (3) Tool 热更新端到端测试; (4) 租户隔离的 Tool 过滤测试 |
| **人周** | 2.0-2.5 |
| **关键校验** | 新增实体元数据 → MCP Tool 自动注册（延迟 < 5s）; 删除实体元数据 → MCP Tool 自动移除; 租户 A 的 clients 仅看到租户 A 有权限的 Tools |

#### P2-T3: MCP ↔ GraphQL Bridge 实现

| 维度 | 详情 |
|------|------|
| **描述** | 实现 `McpGraphQLBridge` 组件，将 MCP Tool 调用自动转换为 GraphQL Query/Mutation 执行。映射规则：`query_{EntityName}` → `graphql: query { entityName_list(...) { ... } }`; `get_{EntityName}` → `graphql: query { entityName(id:) { ... } }`; `create_{EntityName}` → `graphql: mutation { entityName_create(input:) { ... } }`; `update_{EntityName}` → `graphql: mutation { entityName_update(id:, input:) { ... } }`; `delete_{EntityName}` → `graphql: mutation { entityName_delete(id:) { ... } }`。支持：参数校验（JSON Schema Validation）、GraphQL 执行上下文注入（tenantId, userId）、结果转换（GraphQL Result → ToolResult）、GraphQLError → ToolResult.error 映射 |
| **产出** | (1) `McpGraphQLBridge` 完整实现; (2) ToolNameResolver（Tool 名 → 实体名 + 操作解析）; (3) 5 种操作的端到端测试 |
| **人周** | 2.0-3.0 |
| **关键校验** | `query_order(page:1, pageSize:10)` → GraphQL Query → 业务数据返回正确; 参数校验失败时返回可读的错误信息 |

#### P2-T4: MCP Resources + Prompts 实现

| 维度 | 详情 |
|------|------|
| **描述** | 实现 MCP 协议的 Resources 和 Prompts 功能。Resources: `resources/list` — 列出可用的资源（API 文档、数据库 Schema、业务流程图等）; `resources/read` — 读取指定 Resource 的内容。Prompts: `prompts/list` — 列出可用的 Prompt 模板（如"数据分析报告生成模板"、"数据查询模板"）; `prompts/get` — 获取指定 Prompt 模板内容。Prompt 模板支持变量替换（`{{tenantName}}`, `{{userName}}`, `{{entityName}}`） |
| **产出** | (1) `McpResourceProvider` 实现; (2) `McpPromptProvider` 实现; (3) Resource/Prompt 注册与发现端到端测试 |
| **人周** | 1.5-2.0 |
| **关键校验** | Resources 列表正确反映可用文档; Prompt 模板变量替换正确 |

#### P2-T5: SSE Streaming 端点实现

| 维度 | 详情 |
|------|------|
| **描述** | 为 Agent 流式响应场景创建独立的 SSE (Server-Sent Events) 端点 (`/agent/stream`)。与 GraphQL 同步模式解耦：短任务（< 5s）走 GraphQL 同步；长任务/流式走 SSE。使用 LangChain4j 的 `StreamingChatLanguageModel` + Spring WebFlux/Spring MVC SSE Emitter 实现逐 Token 推送到前端。SSE 事件格式：`event: token\ndata: {"text": "订单"}\n\n`; `event: done\ndata: {"totalTokens": 2450}\n\n` |
| **产出** | (1) `AgentStreamController`; (2) SSE 事件格式规范; (3) 前端 SSE 消费示例; (4) 负载测试（100 并发连接） |
| **人周** | 2.0-2.5 |
| **关键校验** | 逐 Token 输出延迟 < 100ms; 100 并发 SSE 连接无 OOM |

#### P2-T6: 混合检索 RAG Pipeline

| 维度 | 详情 |
|------|------|
| **描述** | 在 Phase 1 基础 RAG 之上，升级为混合检索架构。双通道索引：Channel A — 向量索引 (PgVector, 语义相似度); Channel B — BM25 关键词索引 (PostgreSQL tsvector/tsquery 全文搜索)。实现 RRF (Reciprocal Rank Fusion) 融合算法，合并两个通道的检索结果（默认权重：向量 0.6, BM25 0.4, k=60）。引入 Reranker（推荐 Cohere Rerank v3 或 BGE-Reranker-v2-m3 本地部署）对融合结果进行精排。实现查询重写（LLM 将用户原始问题改写为更适合检索的查询）和父-子分块（ParentDocumentRetriever，先检索子块再返回父文档上下文） |
| **产出** | (1) `HybridRetriever` 实现; (2) `Bm25Retriever` (基于 PostgreSQL 全文搜索); (3) RRF 融合 + Rerank 管道; (4) 检索质量对比报告（基础 RAG vs 混合检索） |
| **人周** | 3.0-4.0 |
| **关键校验** | 混合检索 Top-5 命中率 > 基础 RAG 至少 +10%; 检索 + 融合 + 重排总延迟 < 800ms |

#### P2-T7: Prompt 外部化管理

| 维度 | 详情 |
|------|------|
| **描述** | 设计 Prompt 模板存储方案：支持配置文件（`application-prompts.yml`）、数据库表（`agent_prompt_templates`）、配置中心（Spring Cloud Config / Nacos）三种模式。实现 Prompt 版本管理（每次修改记录版本号、修改人、修改时间）。支持 A/B 测试（同一场景可配置多套 Prompt，按百分比分流）。实现 Prompt 变量注入（`{{tenantId}}`, `{{userName}}`, `{{currentDate}}`）。Prompt 修改后无需重新部署即可生效 |
| **产出** | (1) PromptTemplate 存储表 DDL; (2) `PromptManager` 组件 (CRUD + 版本管理); (3) @SystemMessage 模板外部化适配; (4) A/B 测试分流配置 |
| **人周** | 2.0-2.5 |
| **关键校验** | Prompt 在数据库中修改后，Agent 下一次调用使用新 Prompt; 版本回退功能正常 |

#### P2-T8: Agent 安全模型设计与实现

| 维度 | 详情 |
|------|------|
| **描述** | 建立 Agent 专用安全模型，与现有 RBAC 并存但不耦合。实现三道防线：(1) Tool 级 ACL — `AgentSecurityConfig` 控制每个 Tool 的访问角色（READ/WRITE/ADMIN）; (2) 租户上下文注入 — 所有 Tool 执行前注入 tenantId，确保租户间数据隔离; (3) 调用链鉴权 — Agent 间调用传递完整调用链上下文（类似 AWS IAM 信任链），防止权限提升。MCP/A2A 端点使用独立认证（不同于用户 API），Agent-to-Agent 通信使用 mTLS + Service Account Token。实现审计日志：`agent_tool_audit_log` 记录所有 Tool 调用（trace_id, tool_name, tenant_id, user_id, params_hash, success, duration_ms）; `agent_guardrail_audit_log` 记录所有 Guardrail 触发事件 |
| **产出** | (1) `AgentSecurityConfig` 实现; (2) Tool ACL 矩阵配置; (3) 调用链上下文传递机制; (4) 审计日志 DDL + 实现; (5) 安全渗透测试报告 |
| **人周** | 3.0-4.0 |
| **关键校验** | 读权限用户调用 write Tool 被拒绝; 租户 A 无法查询租户 B 的数据; 审计日志记录完整 trace_id 调用链 |

#### P2-T9: 语义缓存层 (Semantic Cache)

| 维度 | 详情 |
|------|------|
| **描述** | 基于 Redis + 向量相似度实现语义缓存。机制：用户提问 → Embedding → 查找 Redis 中相似问题（cosine_similarity > 0.95）→ 命中则直接返回缓存响应，绕过 LLM 调用。缓存 Key 设计：`semcache:{tenantId}:{embHash}`。支持 TTL 配置（默认 1 小时，FAQ 类可更长）。实现缓存命中率监控和 cost savings 统计 |
| **产出** | (1) `SemanticCacheService` 实现; (2) Redis Lua 脚本（高效向量搜索）; (3) 缓存命中率仪表盘 |
| **人周** | 1.5-2.0 |
| **关键校验** | 同一问题重复提问 → 缓存命中（latency < 10ms vs 正常 2s）; 相似但不相同的问题 → 正确判断为未命中 |

#### P2-T10: OpenTelemetry 可观测性增强

| 维度 | 详情 |
|------|------|
| **描述** | 在 Phase 1 基础 Micrometer 指标之上，集成 OpenTelemetry 全链路追踪。为以下操作创建 Span: LLM 调用（`llm.generate` — 记录 model, provider, token.input/output, duration）; Tool 调用（`tool.execute` — 记录 tool.name, params_hash, success, duration）; RAG 检索（`rag.retrieve` — 记录 result_count, duration）; Guardrail 校验（`guardrail.execute` — 记录 allowed, reject_rule, reject_reason）。配置 OTLP Exporter → OpenTelemetry Collector → Jaeger/Tempo。新增成本追踪：按模型定价计算每次 LLM 调用的估算成本，按租户分组展示 |
| **产出** | (1) `AgentObservabilityConfig` OpenTelemetry 集成; (2) Agent 专用 Span 覆盖; (3) LLM 成本追踪器; (4) Grafana Dashboard (Agent 全链路视图) |
| **人周** | 2.0-3.0 |
| **关键校验** | 一次 Agent 请求的完整 Span 树在 Jaeger 中可查询; LLM 成本仪表盘数据与 API 计费吻合 |

### 4.3 里程碑定义

**M6: 元数据 → MCP Tool 自动生成链路打通** (第 4 周末)

| 验收项 | 标准 |
|--------|------|
| Schema2MCP | 全部核心实体（> 30 个）的 JSON Schema 转换为 MCP Tool |
| Tool 热更新 | 新增实体后 5s 内 MCP Tool 可用 |
| GraphQL Bridge | `query_*`, `get_*`, `create_*` 三种操作端到端通过 |
| 租户隔离 | 不同租户可见 Tool 列表不同 |

**M7: MCP 协议生产可用** (第 8 周末)

| 验收项 | 标准 |
|--------|------|
| MCP Endpoint | `/mcp` 端点通过 MCP Inspector 协议兼容性验证 |
| Resources | `resources/list` + `resources/read` 可用 |
| Prompts | `prompts/list` + `prompts/get` 可用，变量替换正确 |
| Streaming | SSE `/agent/stream` 100 并发稳定 |
| 混合检索 | RAG Top-5 命中率 > 85%; 检索延迟 < 800ms |

**M8: 安全模型 + 可观测性就绪** (第 12 周末)

| 验收项 | 标准 |
|--------|------|
| Tool ACL | 权限矩阵生效；3 种角色（USER/ADMIN/DATA_MANAGER）权限隔离正确 |
| 审计日志 | `agent_tool_audit_log` + `agent_guardrail_audit_log` 完整记录 |
| OTEL Tracing | 完整 Span 树可查询；覆盖 LLM/Tool/RAG/Guardrail |
| 语义缓存 | 命中率 > 15%（相似问题场景）; 缓存延迟 < 10ms |
| 安全渗透 | 5 种攻击场景（PII 泄漏、权限提升、租户跨越、Prompt 注入、超量数据）全部防护 |

### 4.4 风险提示

| 风险 | 概率 | 影响 | 缓解措施 |
|------|------|------|---------|
| **JSON Schema 质量不统一** | 高 | Schema2MCP 转换后的 Tool 描述质量差 | 在转换器中增加描述质量评分；低于阈值（如 60 分）的实体标记为"需人工审核"状态 |
| **MCP 协议规范变更** | 中 | 与外部 MCP Client 不兼容 | 关注 MCP Spec 的 GitHub Releases; 维护协议版本号在 Server Capabilities 中声明 |
| **SSE 长连接资源泄漏** | 中 | 服务内存泄漏导致 OOM | 设置 SSE 连接超时（5分钟）; 定期清理僵尸连接; 负载测试验证 |
| **Reranker 服务成本/延迟** | 中 | 检索管道延迟超标或成本过高 | 评估 Cohere Rerank API vs 本地 BGE-Reranker; 小结果集（< 20 条）跳过重排 |
| **审计日志存储膨胀** | 低 | 磁盘空间不足 | 设置日志保留策略（30 天自动归档）；使用分区表按日期分区 |
| **Prompt 管理权限泄露** | 中 | 恶意修改 Prompt 导致 Agent 行为异常 | Prompt 修改需要审批；列出 Prompt 修改历史审计日志；支持即时回滚 |

### 4.5 回滚方案

```
Phase 2 失败回退路径:

场景 A: Schema2MCP 转换质量不可接受（Tool 描述误导 LLM）
  ├── 操作: 降级为手动注册的 @Tool（Phase 1 模式）；全量实体回到人工审核队列
  ├── 影响: 只有手动注册的 Tool 可用；自动发现能力暂不可用
  └── 触发条件: 自动转换的 Tool 中 > 30% LLM 选择错误或参数传错

场景 B: 混合检索性能不达标
  ├── 操作: 降级为纯向量检索（Phase 1 的 EmbeddingStoreContentRetriever）
  ├── 影响: 检索召回率降低 ~10%；简单问答准确率不受影响
  └── 触发条件: 检索延迟 P95 > 2s 且无法通过水平扩展优化

场景 C: SSE Streaming 稳定性问题
  ├── 操作: 关闭 SSE 端点；所有 Agent 请求回退到同步请求-响应模式
  ├── 影响: 长期运行的 Agent 任务用户需等待完整结果
  └── 触发条件: SSE 连接成功率 < 95% 或生产环境出现 3 次 SSE 相关事故

场景 D: 安全模型发现绕过漏洞
  ├── 操作: 临时收紧 Tool ACL（所有写操作仅 ADMIN）; 增强审计日志监控
  ├── 影响: 非 ADMIN 用户暂时无法使用 write Tool
  └── 触发条件: 安全渗透测试发现 HIGH 级别漏洞
```

---

## 5. Phase 3: 高级编排与护栏

### 5.1 Phase 概要

| 维度 | 详情 |
|------|------|
| **目标** | 集成 LangGraph (Python gRPC Sidecar) 实现复杂工作流编排 + Human-in-the-Loop；将 Drools 深度集成到 Agent Guardrails 体系；实现 A2A 协议网关；Agentic RAG 自反思检索；大规模向量检索（Milvus）扩展 |
| **时间范围** | 8-12 周 |
| **前置依赖** | Phase 2 完成（M7 通过），Phase 1 稳定运行 |
| **后续 Phase** | Phase 4（智能自动化） |
| **团队配置** | 3-5 人（1 Python/LangGraph 工程 + 1 Java 平台 + 1 安全/规则工程 + 1 DevOps + 1 QA） |

### 4.2 任务分解 → 5.2 任务分解

#### P3-T1: Python Agent Engine 基础设施搭建

| 维度 | 详情 |
|------|------|
| **描述** | 搭建 Python 3.12+ 运行环境：创建 `agent-engine/` Python 项目；安装核心依赖（`langgraph>=1.0.8`, `grpcio>=1.63`, `langchain-openai>=0.3`）。创建 Python Docker 镜像（Multi-stage Build）; 建立 pip 依赖安全扫描流水线（`pip-audit`, `safety`）；编写 Dockerfile 和 K8s Sidecar 部署清单（`resources: {memory: "256Mi-1024Mi", cpu: "250m-1000m"}`）；实现 Python 侧的 FastAPI 健康检查端点和管理端点 |
| **产出** | (1) `agent-engine/` Python 项目结构; (2) `requirements.txt` 精确版本; (3) Dockerfile + K8s Sidecar 部署清单; (4) 健康检查 + 就绪探针 |
| **人周** | 3.0-4.0 |
| **关键校验** | Docker 镜像构建成功（镜像体积 < 800MB）; `python -c "import langgraph"` 成功; 健康检查返回 200 |

#### P3-T2: gRPC Bridge 实现 (Java ↔ Python)

| 维度 | 详情 |
|------|------|
| **描述** | 实现 Java ↔ Python 双向 gRPC 通信。Java 侧（`app-agent-bridge`）：创建 `agent_orchestrator.proto` Protobuf 契约定义（服务接口：Invoke, StreamExecute, Resume, Cancel, GetStatus；消息类型：WorkflowRequest, WorkflowResponse, AgentEvent）；复用现有 Protobuf 编译流水线生成 Java Stub/Clients；实现 `LangGraphGrpcClient`（gRPC Channel Pool、mTLS、超时控制 5s、自动重试1次）。Python 侧：实现 `LangGraphGrpcServer`（基于 grpcio + asyncio）；实现 Bidirectional Streaming 用于实时推送 Agent 执行进度、中间输出、中断请求 |
| **产出** | (1) `agent_orchestrator.proto` 完整定义; (2) Java gRPC Client; (3) Python gRPC Server; (4) 端到端通信验证（双向流）; (5) 超时/重试/熔断测试 |
| **人周** | 3.0-4.0 |
| **关键校验** | Java → Python 单次 Invoke 成功; StreamExecute 双向流正常推送事件; Resume 从 Python 中断→Java 触发→恢复成功; 超时/熔断行为正确 |

#### P3-T3: LangGraph 工作流编排引擎

| 维度 | 详情 |
|------|------|
| **描述** | 在 Python Agent Engine 中实现 LangGraph 图状态机编排。实现复杂工作流场景：(1) Human-in-the-Loop 审批 — 工作流执行到审批节点 → `interrupt()` 挂起 → 等待人工决策 → `Command(resume=...)` 恢复；(2) 多 Agent 子图嵌套（SubGraph — 主子工作流委托模式）; (3) 条件分支（`add_conditional_edges` 基于 LLM 输出路由）; (4) 循环迭代（质量门控，最多 3 次迭代）。使用 `PostgresSaver` 实现 Durable Execution 和 Checkpoint 恢复（长事务失败后从 checkpoint 重试），共享现有 PostgreSQL 实例 |
| **产出** | (1) StateGraph 工作流定义（审批流、子图嵌套流、条件路由流、质量迭代流）; (2) PostgresSaver Checkpoint 持久化; (3) interrupt() + resume() 端到端验证; (4) 断点恢复测试（模拟 Python 进程 crash） |
| **人周** | 3.0-4.0 |
| **关键校验** | 审批流：审批节点挂起 → 人工 approve → 继续执行并返回结果; Crash 恢复：工作流执行中断开 → 重启后从最新 Checkpoint 恢复; 子图嵌套：主工作流调用子工作流并正确聚合结果 |

#### P3-T4: Java 侧 LangGraph 工作流协调器

| 维度 | 详情 |
|------|------|
| **描述** | 在 Java 侧实现 `AgenticWorkflowCoordinator`，负责决策工作流复杂度并路由到合适的执行引擎：简单/中等复杂度工作流 → LangChain4j 本地执行（Phase 1 已实现）；高复杂度工作流（含 Human-in-the-Loop、长事务、多 Agent 子图） → gRPC Bridge → LangGraph (Python)。实现故障隔离与降级策略：网络超时（5s）→ gRPC `DeadlineExceeded` → 自动重试 1 次 → 仍失败则降级到 LangChain4j 本地执行；Python Engine 不可用（UNAVAILABLE）→ 触发熔断（5次失败 → 30s熔断）→ 期间所有请求降级到本地执行 → 半开恢复（每30s探测一次） |
| **产出** | (1) `AgenticWorkflowCoordinator` 实现; (2) 工作流复杂度评估逻辑; (3) CircuitBreaker 配置; (4) 降级行为验证测试 |
| **人周** | 2.0-2.5 |
| **关键校验** | 复杂工作流自动路由到 Python Engine; Python Engine 不可用 → 熔断生效 → 降级到本地; 半开恢复探测成功 → 熔断器恢复 |

#### P3-T5: Drools Guardrails 深度集成

| 维度 | 详情 |
|------|------|
| **描述** | 将现有 Drools 规则引擎深度集成到 Agent Guardrails 体系中。实现四类 Guardrail：(1) INPUT — 用户输入进入 Agent 前校验（PII 检测、有害内容过滤、租户上下文检查、速率限制）; (2) OUTPUT — Agent 输出后校验（敏感字段脱敏、数据大小限制、幻觉检测）; (3) TOOL_INPUT — Tool 调用前校验（权限检查、参数合理性）; (4) TOOL_OUTPUT — Tool 返回后校验（数据脱敏、结果大小限制）。DRL 规则文件独立于业务规则（使用独立 `agenda-group` / `ruleflow-group`），避免冲突。Guardrail 执行结果含：`ruleId`, `ruleDescription`, `violatedCondition`, `suggestedFix`, `action`（REJECT/MASK/WARN/THROTTLE）。实现 @Aspect 拦截器自动将 Guardrail 注入到 @AiService 调用管道中。规则支持热更新（复用 KieScanner 机制，无需重启 Agent） |
| **产出** | (1) `guardrail-input.drl`（PII/安全/租户/限流规则）; (2) `guardrail-output.drl`（脱敏/大小限制规则）; (3) `guardrail-tool.drl`（权限/参数校验规则）; (4) `DroolsGuardrailEngine` 实现; (5) `GuardrailAspect` AOP 拦截器; (6) Guardrail 触发测试（覆盖 10+ 规则） |
| **人周** | 3.0-4.0 |
| **关键校验** | PII 检测准确率 > 95%（基于测试数据集）; 敏感字段脱敏 100% 覆盖; Guardrail REJECT 后返回清晰的 ruleId + 建议 |

#### P3-T6: A2A Gateway 实现

| 维度 | 详情 |
|------|------|
| **描述** | 实现 A2A (Agent-to-Agent) 协议网关。基于现有 API/Impl 分离模式：每个 `*-api` 模块的接口方法自动生成 A2A Agent Card 的 `skills` 部分。A2A Agent Card 格式：`{ "name": "OrderAgent", "description": "...", "skills": [{"id": "query_order", "name": "查询订单", ...}], "endpoint": "https://...", "capabilities": {"streaming": true} }`。实现 A2A Task API（`tasks/send`, `tasks/get`, `tasks/cancel`）。Agent Card 注册到与 gRPC 同级的服务注册中心。A2A 端点使用 mTLS + Service Account Token 认证 |
| **产出** | (1) A2A Agent Card 自动生成器（基于 API 接口扫描）; (2) A2A Task API 实现; (3) Agent Card 服务注册; (4) 跨模块 Agent 通信演示 |
| **人周** | 3.0-4.0 |
| **关键校验** | Agent Card 可通过 endpoint 发现; 跨模块 Agent 成功交换 Task; mTLS 认证生效 |

#### P3-T7: Agentic RAG 自反思检索

| 维度 | 详情 |
|------|------|
| **描述** | 升级 RAG 管道为 Agentic 自适应检索。实现意图路由（Router Agent）：FAQ/GREETING → 直接回答；DOCUMENT_QUERY → 多源检索 → 生成；DATA_QUERY → MCP Tool 调用；ANALYTICAL → 多步 Agent Workflow。实现自反思检索循环（最多 3 轮）：检索 → 评估质量（LLM 判断结果是否充分）→ 不充分则查询重写（LLM 改写搜索词）→ 重新检索。实现幻觉检查（Faithfulness Checker）：验证答案中每个声明是否能在检索到的上下文找到支撑。评分标准：faithful / partially_faithful / hallucination，输出结果附标注 |
| **产出** | (1) `AgenticRagPipeline` 实现; (2) 意图分类器 `IntentRouter`; (3) 检索质量评估器 `RetrievalAssessment`; (4) `FaithfulnessChecker` 幻觉检查; (5) 自反思迭代检索日志 |
| **人周** | 3.0-4.0 |
| **关键校验** | 自反思循环在 3 轮内收敛 > 90%; 幻觉检查 precision > 80%; 带引用的答案生成正确标注 |

#### P3-T8: Milvus 大规模向量检索扩展

| 维度 | 详情 |
|------|------|
| **描述** | 当 PgVector 面对百万级以上 Embedding 时性能下降（IVFFlat 索引在高维向量下效率降低），引入 Milvus 作为大规模向量检索的扩展方案。配置 LangChain4j Milvus EmbeddingStore; 实现双写策略（PvVector + Milvus 并行写入，保证数据一致性）; 按数据量阈值自动切换检索源（< 50 万条 → PgVector; >= 50 万条 → Milvus）; Milvus 部署为独立 K8s 服务（Standalone 模式起步） |
| **产出** | (1) Milvus 部署配置; (2) `MilvusEmbeddingStore` Bean 配置; (3) 双写 + 自动路由策略; (4) 性能对比报告（PgVector vs Milvus 100 万级） |
| **人周** | 2.0-2.5 |
| **关键校验** | Milvus 检索延迟 P99 < 100ms（100 万数据）; 双写一致性无丢失; 切换过程无服务中断 |

#### P3-T9: 全链路 Tracing + Dashboard 完善

| 维度 | 详情 |
|------|------|
| **描述** | 将 Phase 2 的 OpenTelemetry 扩展到 Python Agent Engine（Python 侧的 OTel SDK + gRPC Span Context 传播）。实现跨 Java ↔ Python 边界的 Trace ID 传递（通过 gRPC metadata 传播 `traceparent` header）。完善 Grafana Dashboard：Agent 概览（请求量、成功率、P95延迟、LLM Token 消耗、成本）; Tool 调用分析（热门 Tool Top 10、Tool 调用成功率、平均延迟）; Guardrail 触发趋势（各类规则触发频次）; RAG 检索效果（检索延迟、Top-K 命中率、缓存命中率）; 租户成本分析（按租户分组的 LLM 费用） |
| **产出** | (1) Python OTel 集成; (2) 跨语言 Trace ID 传播; (3) 5 个 Grafana Dashboard 面板; (4) Alert Rule 配置（关键指标阈值告警） |
| **人周** | 2.0-3.0 |
| **关键校验** | 一次跨 Java/Python 的 Agent 请求在 Jaeger 中展示完整 Span 树; Grafana Dashboard 数据实时正确 |

#### P3-T10: 端到端集成测试与性能基准

| 维度 | 详情 |
|------|------|
| **描述** | 编写端到端集成测试覆盖全部核心场景：审批工作流（提交 → 审批挂起 → 人工 approve → 完成）、跨模块 Agent 协作（订单查询 → 用户信息查询 → 分析报告）、自反思 RAG 检索、Guardrail 全触发场景。建立性能基准：Agent 请求 P50/P95/P99 延迟；LLM Token 消耗 / 请求；Tool 调用次数 / 请求；端到端成功率。建立稳定性和压力测试：100 并发 Agent 请求持续 1 小时无故障；Python Engine Crash 后自动恢复时间 |
| **产出** | (1) 10+ 端到端集成测试用例; (2) 性能基准报告; (3) 稳定性测试报告; (4) 已知限制清单 |
| **人周** | 2.0-3.0 |
| **关键校验** | 端到端测试 100% 通过; P95 延迟符合 SLI 目标; 稳定性测试零不可恢复故障 |

### 5.3 里程碑定义

**M9: LangGraph Bridge 端到端可用** (第 5 周末)

| 验收项 | 标准 |
|--------|------|
| gRPC Bridge | Java ↔ Python Bidirectional Streaming 通信正常 |
| Human-in-the-Loop | 审批流 interrupt → resume 完整链路通过 |
| Checkpoint | Crash 恢复测试通过（从 PostgresSaver 恢复） |
| Performance | 单次 gRPC 调用延迟 < 100ms（Java-Python 往返） |

**M10: 安全护栏体系完整** (第 8 周末)

| 验收项 | 标准 |
|--------|------|
| Drools Guardrails | 4 类 Guardrail (Input/Output/ToolInput/ToolOutput) 全部实现 |
| PII 检测 | 测试集准确率 > 95% |
| 规则热更新 | DRL 文件修改后 30s 内 Guardrail 重载 |
| Agentic RAG | 自反思迭代 3 轮内收敛 > 90%; 幻觉检查 precision > 80% |
| A2A Gateway | Agent Card 发现 + 跨模块 Task 通信可用 |

**M11: 高级编排生产可用** (第 12 周末)

| 验收项 | 标准 |
|--------|------|
| 端到端测试 | 10+ 核心场景 100% 通过 |
| 性能基线 | P95 Agent 请求延迟 < 10s（含 LLM 调用） |
| 稳定性 | 100 并发 × 1h 无不可恢复故障 |
| 可观测性 | 跨 Java/Python Span 完整可查询; 5 个 Dashboard 面板就绪 |
| Milvus (可选) | 双写一致性 + 自动路由策略验证 |

### 5.4 风险提示

| 风险 | 概率 | 影响 | 缓解措施 |
|------|------|------|---------|
| **Python Agent Engine 运维复杂度** | 高 | 运维团队负担翻倍，技能要求提升 | 全面的运维文档和培训; Python Engine 作为无状态 Sidecar 降低运维难度; 建立 Python CI/CD 流水线模板 |
| **LangGraph 版本 Breaking Change** | 中 | 工作流编排异常 | 固化 `requirements.txt` 精确版本（含 hash）; CI 中增加 LangGraph API 兼容性测试 |
| **gRPC 跨语言序列化问题** | 中 | Java/Python 数据交换异常 | Proto 消息字段使用兼容类型; CI 中增加跨语言兼容性测试 |
| **Drools 规则冲突** | 中 | Guardrail 规则与业务规则互相干扰 | Guardrail 使用独立 agenda-group 和 ruleflow-group; 规则变更前在沙箱环境验证 |
| **A2A 协议版本不稳定** | 中 | 跨系统 Agent 协作失败 | 关注 A2A 协议规范更新; Agent Card 中声明协议版本号 |
| **Milvus 运维成本超预期** | 低 | 基础设施成本增加 | PgVector 容量评估持续监控; 仅在数据量超过 50 万条时启用 Milvus |

### 5.5 回滚方案

```
Phase 3 失败回退路径:

场景 A: Python Engine 稳定性无法接受（Crash > 1 次/天）
  ├── 操作: 移除 Python Sidecar; 将所有工作流降级到 LangChain4j 本地执行
  │         （放弃 Human-in-the-Loop interrupt 能力，使用轮询模式替代）
  ├── 影响: 复杂审批流暂时使用轮询模式（用户体验降级但功能不丢）;
  │         损失 LangGraph 的 Checkpoint/Durable Execution 能力
  └── 触发条件: Python Engine Crash 率 > 1 次/天 持续 1 周

场景 B: Drools Guardrail 误杀率过高（> 5% 正常请求被拒绝）
  ├── 操作: 降低 Guardrail 严格度；将 REJECT 改为 WARN；人工审核触发的规则
  ├── 影响: 部分风险场景暂时无法自动阻断（依赖人工审核降级）
  └── 触发条件: Guardrail 误杀率 > 5% 且涉及核心业务流程

场景 C: A2A Agent Card 发现机制故障
  ├── 操作: 降级为手动配置 Agent 端点（静态 endpoint 列表）; Agent 间通信走现有 gRPC
  ├── 影响: 失去 Agent 自动发现/动态注册能力
  └── 触发条件: Agent Card 注册成功 < 90% 实例

场景 D: Agentic RAG 自反思循环导致延迟超标
  ├── 操作: 关闭自反思; 退回到 Phase 2 的混合检索单次检索模式
  ├── 影响: 复杂问题的检索准确率降低 ~10%
  └── 触发条件: Agentic RAG 请求 P95 延迟 > 15s
```

---

## 6. Phase 4: 智能自动化

### 6.1 Phase 概要

| 维度 | 详情 |
|------|------|
| **目标** | 从"Agent 辅助"升级到"Agent 自动化"：Agent 辅助代码生成、自愈管道、多 Agent 协作、生产环境运维优化、持续效果评估 |
| **时间范围** | 6-8 周 |
| **前置依赖** | Phase 3 完成（M10 通过），MCP + Agentic RAG + Guardrails 稳定运行 |
| **后续 Phase** | 无（进入持续演进阶段） |
| **团队配置** | 2-4 人（1 AI 工程 + 1 平台开发 + 1 DevOps + 可选 1 数据/评估） |

### 6.2 任务分解

#### P4-T1: Agent 辅助代码生成增强

| 维度 | 详情 |
|------|------|
| **描述** | 扩展现有 Maven 插件体系（`app-agent-plugins`），在编译期自动生成 Agent 相关代码。功能包括：(1) `generate-mcp-tools` — 扫描全部元数据注册实体 → 自动生成 MCP Tool 注册清单；(2) `generate-agent-card` — 基于 API 接口扫描 → 自动生成 A2A Agent Card；(3) `generate-tool-wrappers` — 基于 MBG 生成的 Mapper → 自动生成 @Tool 注解的包装类（可选：`generateAgentTools=true`）。将 MBG Velocity 模板导出为 Agent Code Generation System Prompt 上下文。集成到 Maven 构建生命周期：`generate-mcp-tools` 在 `process-classes` 阶段执行 |
| **产出** | (1) `app-agent-plugins` Maven 插件模块; (2) `generate-mcp-tools` Mojo; (3) `generate-agent-card` Mojo; (4) Archetype `--with-ai` 参数增强 |
| **人周** | 2.0-3.0 |
| **关键校验** | `mvn app-agent:generate-mcp-tools` 零错误生成 Tool 清单; 生成代码编译通过 |

#### P4-T2: 自愈管道 (Self-Healing Pipeline)

| 维度 | 详情 |
|------|------|
| **描述** | 实现 Agent 执行的自愈机制。能力包括：(1) 自动重试 — Tool 调用失败后自动重试（指数退避：1s→2s→4s，最多3次）; (2) 智能降级 — LLM 模型不可用时自动切换到备选模型（DeepSeek → GPT-4o-mini → 本地 Ollama Qwen2.5-7B）; (3) 异常模式识别 — Agent 将连续失败的模式记录到知识库，后续相似请求自动调整策略; (4) 自动 EScalation — Agent 在 3 次重试仍失败后，自动将任务升级到人工队列（附带失败上下文和建议操作） |
| **产出** | (1) `SelfHealingExecutor` 实现; (2) 多层级 LLM 降级链; (3) 异常模式知识库; (4) 人工队列 EScalation 流程 |
| **人周** | 2.0-3.0 |
| **关键校验** | Tool 临时故障 → 自动重试 → 第 3 次成功; LLM 主模型不可用 → 自动降级到备选模型 → 用户无感知; 连续失败 3 次 → EScalation 到人工队列 |

#### P4-T3: 多 Agent 协作框架

| 维度 | 详情 |
|------|------|
| **描述** | 实现多个 Agent 的协作执行框架。场景包括：(1) 专业化 Agent 分工 — 每个业务模块的 A2A Agent 专注于其领域（OrderAgent, UserAgent, ReportAgent），通过 A2A 协议协调完成复合任务; (2) Master-Slave 模式 — 一个 Orchestrator Agent 负责任务拆解和分派，多个 Worker Agent 并行执行子任务; (3) Debate/Consensus 模式 — 多个 Agent 对同一问题独立回答，通过 LLM 对比选择最佳答案; (4) Agent 间知识共享 — Agent 执行成功的结果自动存入知识库，供其他 Agent 检索复用 |
| **产出** | (1) `MultiAgentOrchestrator` 实现; (2) Orchestrator + Worker 协作演示; (3) Debate/Consensus 模式实现; (4) Agent 间知识共享机制 |
| **人周** | 2.0-3.0 |
| **关键校验** | Orchestrator 正确拆解 4 步复合任务 → Worker Agent 并行执行 → 结果正确聚合; Debate 模式对比 3 个 Agent 输出 → 选择最优 |

#### P4-T4: 生产环境运维优化

| 维度 | 详情 |
|------|------|
| **描述** | 优化 Agent 系统在生产环境中的运营。包括：(1) 渐进式发布策略 — Canary Deployment（新 Agent 版本先部署到 10% 流量）→ 监控关键指标（成功率、延迟、成本）→ 自动回滚或扩大; (2) Agent 成本优化 — 基于成本追踪数据，自动调整模型选择策略（非高峰使用低成本模型，高峰保持主模型）; (3) 自动化告警 — 设置关键告警（Agent 成功率 < 95%, P95 延迟 > 10s, 小时成本 > $X, Guardrail 触发率突增）; (4) Runbook 文档 — 编写完整的运维操作手册（常见故障处理、版本升级流程、回滚步骤） |
| **产出** | (1) Canary 部署配置; (2) 自动模型选择策略; (3) Prometheus Alert Rules 配置; (4) Agent 运维 Runbook |
| **人周** | 1.5-2.0 |
| **关键校验** | Canary 期间指标异常自动回滚; 非高峰期自动切换到低成本模型; 所有告警规则触发验证通过 |

#### P4-T5: RAGAS 评估框架集成

| 维度 | 详情 |
|------|------|
| **描述** | 集成 RAGAS (Retrieval Augmented Generation Assessment) 框架，建立 Agent 效果的持续评估体系。评估维度：(1) Context Precision — 检索到的上下文中相关文档的占比; (2) Context Recall — 相关文档被检索到的比例; (3) Faithfulness — 生成答案的事实一致性; (4) Answer Relevancy — 答案与问题的相关程度。建立评估流水线：每周自动采样 100 个 Agent 问答 → 自动 RAGAS 评估 → 生成效果趋势报告 → 识别退化信号。评估结果接入 Grafana Dashboard |
| **产出** | (1) RAGAS 评估脚本/流水线; (2) 自动化评估（每周运行）; (3) 效果趋势 Dashboard; (4) 退化告警规则 |
| **人周** | 1.5-2.0 |
| **关键校验** | 首次评估结果基线建立; 退化信号触发告警; 评估覆盖 > 80% 的 Agent 使用场景 |

#### P4-T6: 反馈闭环与持续优化

| 维度 | 详情 |
|------|------|
| **描述** | 建立用户反馈闭环机制，驱动 Agent 持续优化。功能包括：(1) 用户满意度评分 — Agent 每次回答后提示用户评分（1-5 星 + 可选文本反馈）; (2) 负面案例自动分析 — 低分回答（< 3 星）自动记录到反馈数据库，触发人工审核; (3) Prompt 自动优化 — 基于累计的反馈数据，每周自动生成 Prompt 优化建议（通过 LLM 分析失败模式）; (4) RAG 知识库补充 — 从用户反馈中识别缺失的知识，自动创建索引任务 |
| **产出** | (1) 用户反馈 UI 组件; (2) 反馈数据库 + API; (3) Prompt 优化建议自动生成; (4) 知识库补充任务自动创建 |
| **人周** | 1.5-2.0 |
| **关键校验** | 用户反馈率 > 10%; 负面案例分析正确分类; Prompt 优化建议质量可执行 |

### 6.3 里程碑定义

**M12: 智能自动化初具规模** (第 4 周末)

| 验收项 | 标准 |
|--------|------|
| 代码生成 | `app-agent-plugins` 3 个 Maven Goal 全部可用 |
| 自愈 | 自动重试 + LLM 降级 2 个场景通过 |
| 多 Agent | Orchestrator (1+3 worker) 协作执行成功 |

**M13: 生产运营成熟** (第 8 周末)

| 验收项 | 标准 |
|--------|------|
| 评估 | RAGAS 自动化评估流程运行，效果基线建立 |
| 反馈 | 用户反馈闭环打通（评分 → 分析 → 优化建议） |
| 部署 | Canary 部署验证成功（自动回滚 + 扩大各一次） |
| 运维 | Runbook 文档完成; 告警规则全部就位; 运维团队培训完成 |
| 成本 | 月度 LLM 成本在预算范围内，成本优化策略生效 |

### 6.4 风险提示

| 风险 | 概率 | 影响 | 缓解措施 |
|------|------|------|---------|
| **自动生成代码质量参差** | 中 | 构建失败或运行时错误 | 生成代码 CI 检查（生成后立即编译 + 静态分析）; 关键代码加入 Code Review |
| **自愈体系掩盖潜在问题** | 中 | 系统性问题被自动重试"隐藏" | 设置重试率告警阈值; 超过 3 次重试的请求自动标记为需人工审查 |
| **多 Agent 协调复杂度爆炸** | 中 | Agent 间死锁/无限循环 | 设置每个复合任务的总超时（5 分钟）; 每个 Agent 调用设置单独超时; 实现全局任务看门狗 |
| **评估框架覆盖率不足** | 低 | 部分场景效果退化未被发现 | 分层评估：实时（关键指标） + 每周（RAGAS 自动） + 每月（人工抽检） |
| **用户反馈率低** | 高 | 缺少优化信号 | 低摩擦反馈设计（一键评分）; 主动抽样邀请核心用户深度反馈 |

### 6.5 回滚方案

```
Phase 4 失败回退路径:

场景 A: 自动代码生成导致构建失败
  ├── 操作: 关闭自动生成（maven property: app.agent.codegen.enabled=false）
  │         回到手动编写 Agent Tool 的模式（Phase 1-2 方式）
  ├── 影响: 新实体需手动编写 Tool 包装器（每个约 0.5h）
  └── 触发条件: 连续 3 次构建因生成代码失败

场景 B: 多 Agent 协作死锁/超时
  ├── 操作: 关闭多 Agent 协作模式; 回退到单 Agent 模式
  ├── 影响: 复合任务需用户手动拆解为多步执行
  └── 触发条件: 多 Agent 任务超时率 > 10%

场景 C: 自愈体系被证明不可靠
  ├── 操作: 关闭自动重试/降级; 保留人工 EScalation 通道
  ├── 影响: 部分临时故障导致用户可见错误
  └── 触发条件: 自动重试失败率 > 自愈尝试次数的 50%
```

---

## 7. 总体甘特图与资源估算

### 7.1 文字甘特图

```
周  1  2  3  4  5  6  7  8  9 10 11 12 13 14 15 16 17 18 19 20 21 22 23 24 25 26 27 28 29 30 31 32 33 34 35 36 37 38 39 40 41 42 43 44 45 46
    ├─────────────────── Phase 0 (4-6 周) ───────────────────────┤
    │ P0-T1  │ P0-T2  │ P0-T3  │ P0-T4  │ P0-T5    │ P0-T6       │
    │ Java17 │jakarta │  SB3   │ dep up │ CI/CD   │ 回归测试     │
    ├──M0───────────┤        ├──M1───────────┤         ├──M2──────┤
                  │                                                                                          
                  ├───────────────── Phase 1 (6-8 周) ──────────────────────────┤
                  │ P1-T1│ P1-T2 │ P1-T3 │ P1-T4 │ P1-T5 │ P1-T6 │ P1-T7 │ P1-T8 │ P1-T9  │ P1-T10 │
                  │ 骨架  │ LLM   │@AiSvc │ PgVec │ RAG   │@Tool  │  WF   │Memory │ MCP   │ 构建   │
                  │       ├──M3──┤       ├──M4────────────────┤      │       │        ├──M5──┤       │
                  │                                                                                      
                  │                             ├────────────────── Phase 2 (8-12 周) ──────────────────────────────────┤
                  │                             │P2-T1 │ P2-T2 │P2-T3 │P2-T4│ P2-T5 │ P2-T6   │ P2-T7  │ P2-T8    │ P2-T9 │ P2-T10│
                  │                             │S2MCP │ MDTP  │GQL Br│ Res │ SSE   │ Hybrid  │ Prompt │ Security │ Cache │ OTel  │
                  │                             │      ├──M6──┤      │     │       │         │        │          │       │       │
                  │                             │      │      │      ├──M7──────────────────────────────────┤       │       │       │
                  │                             │      │      │      │      │        │         │        ├──M8──────────────────┤
                  │                             │                                                                                      
                  │                             │                                ├─────────────── Phase 3 (8-12 周) ────────────────────────────┤
                  │                             │                                │P3-T1  │ P3-T2 │ P3-T3 │ P3-T4 │ P3-T5 │ P3-T6 │ P3-T7 │ P3-T8 │ P3-T9 │ P3-T10│
                  │                             │                                │Py Env │gRPC Br│LangGr │Coord  │Drools │ A2A  │AgtRAG │Milvus │ OTel  │ E2E  │
                  │                             │                                │       │       ├──M9──┤      │       │       │       │       │       │       │
                  │                             │                                │       │       │      │      ├──M10───────────┤      │       │       │       │
                  │                             │                                │       │       │      │      │      │       │       │       ├──M11─┤       │
                  │                             │                                │                                                                                      
                  │                             │                                │                                ├───────────── Phase 4 (6-8 周) ────────────┤
                  │                             │                                │                                │P4-T1 │ P4-T2 │ P4-T3 │ P4-T4 │ P4-T5 │ P4-T6 │
                  │                             │                                │                                │代码  │自愈    │多Agent│ 运维  │ RAGAS │ 反馈  │
                  │                             │                                │                                │      ├──M12─┤       │       │       ├──M13─┤
```

### 7.2 各 Phase 资源详细估算

#### Phase 0: 基础设施现代化

| 任务 | 人周 (下限) | 人周 (上限) | 所需角色 |
|------|-----------|-----------|---------|
| P0-T1: Java 17 编译环境 | 1.5 | 2.0 | Java 高级 |
| P0-T2: javax → jakarta | 2.0 | 3.0 | Java 高级 + DevOps |
| P0-T3: Spring Boot 3.x | 2.0 | 3.0 | Java 高级 |
| P0-T4: 依赖升级 | 1.5 | 2.0 | Java 高级 |
| P0-T5: CI/CD 升级 | 1.0 | 2.0 | DevOps |
| P0-T6: 回归测试 | 1.5 | 2.0 | QA |
| **Phase 0 合计** | **9.5** | **14.0** | 2-3 人 × 4-6 周 |

#### Phase 1: Agent 核心能力

| 任务 | 人周 (下限) | 人周 (上限) | 所需角色 |
|------|-----------|-----------|---------|
| P1-T1: 模块骨架 | 1.0 | 1.5 | 平台开发 |
| P1-T2: LLM 接入层 | 1.0 | 1.5 | AI 工程 |
| P1-T3: @AiService 原型 | 1.5 | 2.0 | AI 工程 + Java |
| P1-T4: PgVector+Embedding | 1.5 | 2.0 | AI 工程 + DevOps |
| P1-T5: 基础 RAG | 2.0 | 2.5 | AI 工程 |
| P1-T6: @Tool 注解 | 1.5 | 2.0 | AI 工程 + Java |
| P1-T7: 简单 Workflow | 1.5 | 2.0 | AI 工程 |
| P1-T8: ChatMemory | 1.0 | 1.5 | Java + AI 工程 |
| P1-T9: MCP 框架 | 2.0 | 3.0 | AI 工程 + 平台开发 |
| P1-T10: 构建集成 | 1.0 | 1.5 | 平台开发 |
| **Phase 1 合计** | **14.0** | **19.5** | 3-4 人 × 6-8 周 |

#### Phase 2: MCP + Agentic RAG

| 任务 | 人周 (下限) | 人周 (上限) | 所需角色 |
|------|-----------|-----------|---------|
| P2-T1: Schema2MCP | 2.0 | 3.0 | AI 工程 + 平台开发 |
| P2-T2: MDTP 动态注册 | 2.0 | 2.5 | 平台开发 |
| P2-T3: MCP-GraphQL Bridge | 2.0 | 3.0 | AI 工程 + Java |
| P2-T4: Resources+Prompts | 1.5 | 2.0 | AI 工程 |
| P2-T5: SSE Streaming | 2.0 | 2.5 | AI 工程 + Java |
| P2-T6: 混合检索 RAG | 3.0 | 4.0 | AI 工程 |
| P2-T7: Prompt 管理 | 2.0 | 2.5 | AI 工程 + 平台开发 |
| P2-T8: Agent 安全模型 | 3.0 | 4.0 | 安全工程 + Java |
| P2-T9: 语义缓存 | 1.5 | 2.0 | AI 工程 + DevOps |
| P2-T10: 可观测性增强 | 2.0 | 3.0 | DevOps + AI 工程 |
| **Phase 2 合计** | **21.0** | **28.5** | 3-5 人 × 8-12 周 |

#### Phase 3: 高级编排与护栏

| 任务 | 人周 (下限) | 人周 (上限) | 所需角色 |
|------|-----------|-----------|---------|
| P3-T1: Python 环境搭建 | 3.0 | 4.0 | Python 工程 + DevOps |
| P3-T2: gRPC Bridge | 3.0 | 4.0 | Python 工程 + Java |
| P3-T3: LangGraph 编排 | 3.0 | 4.0 | Python/LangGraph 工程 |
| P3-T4: 工作流协调器 | 2.0 | 2.5 | Java |
| P3-T5: Drools Guardrails | 3.0 | 4.0 | 安全/规则工程 + Java |
| P3-T6: A2A Gateway | 3.0 | 4.0 | 平台开发 + AI 工程 |
| P3-T7: Agentic RAG | 3.0 | 4.0 | AI 工程 |
| P3-T8: Milvus 扩展 (可选) | 2.0 | 2.5 | DevOps + AI 工程 |
| P3-T9: 全链路 Tracing | 2.0 | 3.0 | DevOps |
| P3-T10: 集成测试 | 2.0 | 3.0 | QA + AI 工程 |
| **Phase 3 合计** | **26.0** | **35.0** | 3-5 人 × 8-12 周 |
| **Phase 3 (无 Python)** | **18.0** | **24.5** | 省去 P3-T1, T2, T3 的大部分 |

#### Phase 4: 智能自动化

| 任务 | 人周 (下限) | 人周 (上限) | 所需角色 |
|------|-----------|-----------|---------|
| P4-T1: 代码生成插件 | 2.0 | 3.0 | 平台开发 + AI 工程 |
| P4-T2: 自愈管道 | 2.0 | 3.0 | AI 工程 + DevOps |
| P4-T3: 多 Agent 协作 | 2.0 | 3.0 | AI 工程 |
| P4-T4: 生产运维 | 1.5 | 2.0 | DevOps + SRE |
| P4-T5: RAGAS 评估 | 1.5 | 2.0 | AI 工程 + 数据 |
| P4-T6: 反馈闭环 | 1.5 | 2.0 | AI 工程 + 平台开发 |
| **Phase 4 合计** | **10.5** | **15.0** | 2-4 人 × 6-8 周 |

### 7.3 总计

| 场景 | 人周 | 团队配置 | 时间跨度 |
|------|------|---------|---------|
| **完整方案 (含 Python Bridge)** | **81 - 112** | 3-5 人 | 32-46 周 |
| **纯 Java 方案 (不含 Python)** | **73 - 97** | 3-4 人 | 28-40 周 |
| **最小可行方案 (Phase 0+1 仅)** | **23.5 - 33.5** | 3-4 人 | 10-14 周 |

> **选择建议**:
> - **纯 Java 方案**: 使用 LangChain4j Agentic Workflow 覆盖 80% 的编排场景。仅在需要 Human-in-the-Loop 中断控制、Durable Execution、复杂多 Agent 子图时才引入 Python LangGraph。对于大多数企业场景，纯 Java 方案已足够。
> - **完整方案**: 适用于对审批工作流中断控制、长事务 Checkpoint 恢复有强需求的场景。
> - **最小可行方案**: 适合快速验证 AI Agent 价值，PoC 阶段的选项。完成 Phase 0+1 后即可展示"Agent 辅助数据查询"的核心价值。

### 7.4 人力资源需求矩阵

| Phase | 角色 | 技能要求 | 投入程度 |
|-------|------|---------|---------|
| **Phase 0** | Java 高级 | Spring Boot, Jakarta 迁移经验, Maven | 100% |
| | DevOps | CI/CD 流水线, Docker/K8s, 监控 | 50-100% |
| | QA | 回归测试, 性能测试 | 50-100% |
| **Phase 1** | AI 工程 | LLM 应用开发, LangChain4j, Prompt 工程 | 100% |
| | Java 平台 | Spring Boot 深入, Maven 插件开发 | 50-100% |
| | DevOps | PgVector 部署, Embedding 服务 | 50% |
| | QA | Agent 行为测试, 幻觉评估 | 50% |
| **Phase 2** | AI 工程 | MCP 协议, RAG 工程, 检索系统 | 100% |
| | 平台开发 | Schema 转换, GraphQL 集成 | 100% |
| | 安全工程 | Agent 安全, ACL, 审计 | 50-100% |
| | DevOps | SSE 端点, 缓存, OpenTelemetry | 50% |
| | QA | 安全渗透测试, 协议兼容性测试 | 50% |
| **Phase 3** | Python 工程 | LangGraph, gRPC, asyncio (完整方案) | 100% |
| | Java 平台 | gRPC Client, Circuit Breaker | 50-100% |
| | 安全/规则工程 | Drools, DRL 规则编写 | 50-100% |
| | DevOps | K8s Sidecar, OTEL, Milvus | 50% |
| | QA | 端到端场景测试, 稳定性测试 | 50-100% |
| **Phase 4** | AI 工程 | 代码生成, RAGAS 评估, Agent 协作 | 100% |
| | 平台开发 | Maven 插件开发 | 50-100% |
| | DevOps/SRE | 生产运维, Canary, 告警 | 50% |
| | 数据工程 | 效果评估, 反馈分析 (可选) | 50% |

---

## 8. 跨 Phase 风险与全局缓解

### 8.1 顶级风险登记册

| # | 风险 | 影响 Phase | 严重性 | 缓解策略 |
|----|------|-----------|--------|---------|
| **R1** | Java 17 + Spring Boot 3 升级延期超过 2 周 | ALL | 🔴 Critical | 提前 1 个月启动 Phase 0; 预留 2 周 Buffer; 必要时部分模块保持 Java 8（不推荐） |
| **R2** | 核心团队成员离职 | ALL | 🔴 Critical | 每个关键角色至少有 1 个 Backup; 完善的文档 + 知识传递; 核心代码不少于 2 人 Review |
| **R3** | LLM API 大幅涨价或服务不稳定 | Phase 1-4 | 🔴 Critical | 多模型备选策略; 本地 Ollama 小模型降级; 成本追踪 + 预算预警 |
| **R4** | MCP/A2A 协议出现 Break Change | Phase 2-4 | 🟡 High | 协议版本号在 Server Capabilities 中声明; 关注协议 Spec 的 Release Notes; CI 中增加协议兼容性测试 |
| **R5** | PgVector 在大数据量下性能不达标 | Phase 2-3 | 🟡 High | 持续监控 PgVector 检索延迟; 提前准备 Milvus 迁移方案（Phase 3）; 设置数据量告警阈值 |
| **R6** | Python Agent Engine 运维事故频发 | Phase 3-4 | 🟡 High | 纯 Java 方案为默认; Python Engine 仅在明确需要时启用; 完善的健康检查和自动重启 |
| **R7** | 业务方优先级变化导致资源被抽走 | ALL | 🟡 High | 将 Phase 切分为独立可交付单元; 每 Phase 结束后重新评估继续的 ROI; 最小化对业务系统的耦合 |
| **R8** | Agent 输出质量不受业务用户认可 | Phase 1-4 | 🟢 Medium | 从 Day 1 收集用户反馈; RAGAS 评估持续监控效果; 渐进式发布（内部 → 核心用户 → 全员） |

### 8.2 全局缓解机制

```
┌───────────────────────────────────────────────────────────────────┐
│                    全局风险缓解矩阵                                 │
│                                                                    │
│  1. 架构解耦: Agent 模块为独立增强层，不侵入现有业务代码               │
│     → 即使 Agent 完全不可用，业务系统无任何影响                        │
│                                                                    │
│  2. Feature Flag: 全局开关 app.agent.enabled=false                  │
│     → 一键关闭所有 Agent 功能，回退到纯业务系统                        │
│                                                                    │
│  3. 渐进式发布: 内部 Dogfooding → Beta 用户 → GA 全量                │
│     → 每个阶段观察指标达标后再推进                                    │
│                                                                    │
│  4. 多层降级: 主 LLM → 备选 LLM → 本地 Ollama → 规则引擎兜底          │
│     → LLM 不可用时降级到确定性规则                                    │
│                                                                    │
│  5. 独立 CI/CD: Agent 模块独立构建，不阻塞主业务模块                    │
│     → mvn clean install -pl !app-agent 可跳过 Agent 构建              │
│                                                                    │
│  6. 知识传递: 每 Phase 结束时更新的架构文档 + 团队培训                  │
│     → 团队成员可以独立接手维护                                        │
└───────────────────────────────────────────────────────────────────┘
```

---

## 9. 决策里程碑与 Go/No-Go 节点

### 9.1 Go/No-Go 决策节点

```
时间线                    决策节点                            Go 条件                                No-Go 触发
═══════════════════════════════════════════════════════════════════════════════════════════════════════════════

Phase 0 完成 (第 6 周)     G0: 进入 Phase 1？               全部模块 Java 17 编译 + 启动通过           编译失败 > 3 个模块
                                                          回归测试通过率 >= 升级前                      Jakarta 迁移阻塞 > 2 周
                                                          性能劣化 < 5%

Phase 1 中期 (第 4 周)     G1: 继续 Phase 1？              @AiService 原型成功调用 LLM                 LLM API 连续 3 天不可用
                                                          至少 1 个 @Tool 端到端通过                   Token 成本超预算 2x
                                                          PgVector Embedding 链路可用

Phase 1 完成 (第 8 周)     G2: 进入 Phase 2？              M4 全部验收通过                               LLM 响应质量低于预期
                                                          Agent 安全基础就绪 (无 API Key 泄露)          幻觉率 > 20% 持续 1 周
                                                          业务方反馈"有价值"

Phase 2 中期 (第 6 周)     G3: Schema2MCP 质量决策？       自动转换的 Tool 中 > 70% LLM 选择正确          自动转换质量 < 50%
                                                          GraphQL Bridge 稳定运行                       决定改为全手动 Tool 注册

Phase 2 完成 (第 12 周)    G4: 进入 Phase 3？             M7 全部验收通过                               MCP 协议兼容性无法解决
                                                          安全渗透测试无 HIGH 级别漏洞                   安全漏洞无法在 2 周内修复
                                                          混合检索命中率 > 85%

Phase 2/3 过渡             G5: 引入 Python？              评估 LangChain4j 是否已满足 80% 编排需求      LangChain4j 已满足当前场景
                                                          是否需要 Human-in-the-Loop 中断？             不需要 HITL 或 Durable Exec
                                                          运维团队是否准备好管理 Python？

Phase 3 中期 (第 6 周)     G6: 继续 Python 路线？         gRPC Bridge 稳定通信（Crash < 1 次/周）       Python Engine 稳定性不达标
                                                          Human-in-the-Loop 审批流通过                  决定回退到纯 Java 方案

Phase 3 完成 (第 12 周)    G7: 进入 Phase 4？             M10 全部验收通过                              Drools Guardrail 误杀率 > 5%
                                                          端到端测试 100% 通过                           稳定性测试未通过
                                                          A2A 跨模块通信可用

Phase 4 中期 (第 4 周)     G8: 全面推广决策？              自动代码生成成功 + 自愈体系稳定                 自动代码生成导致 > 2 次构建失败
                                                          多 Agent 协作无死锁                           多 Agent 超时率 > 10%
                                                          运维团队完成培训

Phase 4 完成 (第 8 周)     G9: 项目收尾进入持续演进        M13 全部验收通过                              关键指标未达标
                                                          RAGAS 基线建立                               成本超预算
                                                          反馈闭环正常工作
```

### 9.2 每 Phase 完成后的可交付价值

| Phase 完成后 | 可直接使用的 AI Agent 能力 | 适用场景 | 用户群体 |
|-------------|--------------------------|---------|---------|
| **Phase 0** | — | Java 17 + Spring Boot 3 平台基础 | 开发团队 |
| **Phase 1** | Agent 辅助数据查询（自然语言 → Tool → 数据）; 基础文档问答（RAG） | IT 运维查询订单/用户; 内部 FAQ 文档搜索 | 内部测试用户 |
| **Phase 2** | MCP 标准化的 Agent 数据查询 (可被外部 MCP Client 调用); 混合检索增强的文档问答; 流式响应; Prompt 动态可配; 语义缓存 | 数据自助分析 (自然语言查询任意实体); 技术文档智能检索; 客服辅助回答 | Beta 用户 (内部 + 核心客户) |
| **Phase 3** | 复杂审批工作流 (Human-in-the-Loop); 跨模块 Agent 协作; 带护栏安全 Agent; 多步推理分析 | 自动化审批处理; 订单 + 库存 + 物流综合查询; 数据分析报告自动生成; 安全审计自动化 | 生产环境全量用户 |
| **Phase 4** | Agent 辅助代码生成 (新实体自动生成 Tool); 自愈系统; 多 Agent 协同; 效果持续评估 | 开发效率提升 (新实体自动对接 Agent); Agent 自动化运维; 企业效率全局优化 | 全体用户 + 开发团队 |

---

## 附录 A: Phase 依赖关系矩阵

```
           Phase 0  Phase 1  Phase 2  Phase 3  Phase 4
Phase 0       -        H        H        H        H
Phase 1       -        -        H        H        H
Phase 2       -        -        -        H        S
Phase 3       -        -        -        -        H
Phase 4       -        -        -        -        -

H = Hard Dependency (必须完成后才能启动)
S = Soft Dependency (建议完成后启动，可部分并行)

可并行推进:
  Phase 0 后期 (回归测试) ∥ Phase 1 前期 (设计/架构文档)
  Phase 2 后期 (安全模型) ∥ Phase 3 前期 (Python 环境搭建 + Proto 设计)
  Phase 3 后期 (集成测试) ∥ Phase 4 前期 (代码生成插件设计)
```

## 附录 B: 术语表

| 缩写 | 全称 | 说明 |
|------|------|------|
| **MCP** | Model Context Protocol | LLM 与工具/资源交互的开放协议 |
| **A2A** | Agent-to-Agent | Google 提出的 Agent 间通信协议 |
| **LangChain4j** | — | Java 生态的 LLM 应用开发框架 |
| **LangGraph** | — | LangChain 的图状态机编排库（仅 Python） |
| **RAG** | Retrieval Augmented Generation | 检索增强生成 |
| **PgVector** | — | PostgreSQL 的向量搜索扩展 |
| **SSE** | Server-Sent Events | 服务器向客户端推送事件的 HTTP 协议 |
| **OTEL** | OpenTelemetry | 可观测性标准框架 |
| **HITL** | Human-in-the-Loop | 人工参与决策的工作流模式 |
| **RRF** | Reciprocal Rank Fusion | 多路检索结果融合算法 |
| **DRL** | Drools Rule Language | Drools 规则引擎的声明式规则语言 |
| **MBG** | MyBatis Generator | MyBatis 代码自动生成器 |
| **RAGAS** | RAG Assessment | RAG 系统的效果评估框架 |

---

*本路线图基于 T5（差距分析）和 T6（集成架构设计）的产出，提供了从基础设施现代化到智能自动化的完整分阶段实施计划。建议在每 Phase 完成后根据实际进展和业务反馈调整后续 Phase 的细节。*
