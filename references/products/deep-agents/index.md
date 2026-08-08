# LangChain Deep Agents 产品蒸馏索引

## 目录

- [范围与版本](#范围与版本)
- [产品特征](#产品特征)
- [十三篇阅读路由](#十三篇阅读路由)
- [生成流程](#生成流程)
- [边界矩阵](#边界矩阵)
- [关键事实](#关键事实)
- [实现完成标准](#实现完成标准)
- [证据限制](#证据限制)

## 范围与版本

本目录蒸馏 LangChain Deep Agents 的 Python 开源框架与官方文档。

固定基线：

- Deep Agents commit：`d60560d695e8c436e11dee96965e7a1447409737`；
- Python 包：`deepagents==0.7.5`；
- 锁定依赖：LangChain 1.3.14、LangGraph 1.2.9；
- LangGraph 1.2.9 commit：`95af6a00718588e7b7ce17310e8006d267896a77`；
- 官方滚动文档访问日期：2026-08-08。

完整来源和 permalink 见 [sources.md](sources.md)。Deep Agents 建立在 LangGraph/LangChain 之上；本目录只记录 batteries-included harness 差量，不重复实现 Pregel、checkpoint saver 或 Agent Protocol server 的全部内部。

## 产品特征

- **事实（official-doc）**：官方文档提供 backends、context engineering、tools、memory、RAG、skills、subagents、permissions、human-in-the-loop、sandboxes、fault tolerance、streaming、frontend 和 production 专页。
- **源码观察（code）**：Python 包包含 `graph.py`、`_messages_reducer.py`、`_models.py`、`_tools.py`，以及 `backends`、`middleware`、`profiles` 目录；仓库还公开 `THREAT_MODEL.md`。
- **设计综合（inference）**：Deep Agents 最有辨识度的组合是“LangGraph durable runtime + middleware 组装 + todo planning + filesystem backend + subagent 隔离 + permission/HITL + frontend event projection”。共享模型、工具、策略、sandbox、事件和状态合同仍是本仓库真源。

## 十三篇阅读路由

1. [sources.md](sources.md)：版本、官方文档、固定源码、测试和边界。
2. [product-contract.md](product-contract.md)：产品行为、输入、非目标和完成定义。
3. [architecture.md](architecture.md)：Deep Agents、LangChain、LangGraph、伴生包与服务分层。
4. [agent-loop.md](agent-loop.md)：组装算法、状态机、middleware、终止和取消。
5. [protocol-state.md](protocol-state.md)：thread/turn/item/event、schema 与 reducer。
6. [context-tools.md](context-tools.md)：context、filesystem、tools、skills、memory、RAG、subagents。
7. [workspace-execution.md](workspace-execution.md)：backend、logical path、sandbox 与 artifact。
8. [safety-runtime.md](safety-runtime.md)：permission、HITL、threat model、enforcement。
9. [persistence-recovery.md](persistence-recovery.md)：checkpoint、事务、receipt、恢复和迁移。
10. [experience.md](experience.md)：typed stream、Todo、ACP、frontend projection。
11. [recipe.md](recipe.md)：14 项蓝图 capability、四等级和直接升级。
12. [acceptance-tests.md](acceptance-tests.md)：逐 capability 可执行 oracle 与发布门禁。
13. 本 [index.md](index.md)：选择性加载和生成流程。

## 生成流程

让另一个模型复刻时，按以下顺序工作：

1. 先从 product-contract 冻结交付等级、surface、部署和非目标。
2. 只读取当前阶段需要的实现文档，避免一次加载全部资料。
3. 生成 Blueprint，并确认 overlay capability ID 与 recipe 一致。
4. 先建协议、状态、事件、ID 和错误枚举，再写具体 middleware。
5. 实现最小纵切：model -> file tool -> result -> final -> event replay。
6. 在 runnable 显式启用 Todo；再加 permission/HITL、skills、memory 和同步 subagent，完成 usable。
7. 加 RAG adapter、recovery 和 frontend stream，完成 productive。
8. 加强 sandbox、remote backend、service 和 managed profile，完成 polished。
9. 每项只在 acceptance oracle 通过后标 `verified`。
10. 所有外部/托管依赖在 manifest 单独列出。

## 边界矩阵

| 层 | 本目录要求 | 原项目所有者 |
|---|---|---|
| Harness assembly | profile、middleware、backend、subagent | Deep Agents OSS |
| Agent middleware | Todo 可选、filesystem、summary、HITL 等 | Deep Agents + LangChain |
| Durable graph | state、channel、checkpoint、interrupt | LangGraph |
| File/resource | State/Filesystem/Store/Composite/Sandbox protocol | Deep Agents + provider |
| Surface | SDK stream、ACP、CLI/Code、自建 Web | 伴生 OSS 包/调用方 |
| Observability | metadata、callback、trace adapter | OSS hooks + 可选 LangSmith |
| Production service | auth、tenant、HA、deployment | 调用方或伴生服务 |

## 关键事实

- 0.7.5 的 task planning 是 opt-in，不可写为默认能力。
- 默认 backend 是 `StateBackend()`，不是宿主 filesystem。
- 默认 general-purpose 同步 subagent 可由 profile 关闭或显式覆盖。
- 同步 subagent 隔离 messages/todos/private fields，但可能共享其他 state/backend。
- async subagent 需要远程 Agent Protocol server；本地 middleware 只是客户端。
- filesystem permissions 只作用于内置文件工具，不作用于 execute/custom/MCP。
- `SandboxBackendProtocol` 表示可执行 backend 接口；隔离强度由实现和部署验证。
- Skills 是 SKILL.md source；Memory 是 AGENTS.md source；RAG 需外接。
- checkpointer 为 HITL 与 durable resume 基础，但外部副作用仍要 receipt/幂等。
- ACP 是 agent-editor 协议，不是模型调用外部工具的 MCP。

## 实现完成标准

一个生成项目只有满足以下条件才称为 implementation-ready：

- 领域对象和 JSON/DB schema 可直接实现；
- loop、tool、approval、subagent 都有状态机；
- backend、policy、sandbox 和 service 边界分离；
- Todo、skills、memory、RAG 的来源和 scope 分离；
- snapshot + events 能重建 UI；
- checkpoint 恢复不盲目重放外部副作用；
- 14 项 overlay capability 全部能映射到等级和 oracle；
- closed/managed 能力没有冒充 OSS core；
- 失败、安全、迁移和回滚均有测试；
- 证据引用固定 commit，不使用 `main` 推断实现。

## 证据限制

- 官方伴生服务的部署、观测或评测能力不能自动算作纯 OSS 包能力；recipe 中需标注部署形态。
- backend 抽象不自动等于强 sandbox；local filesystem、远程 sandbox 与 policy enforcement 分别验证。
- 文档中“memory”可能包含项目指令/长期资料等多种语义，生成实现时按共享 `context-engine`、`long-term-memory` 和 `rag-index` 分开。
- 官方文档是滚动内容；默认值和实现顺序必须回到 [固定源码登记](sources.md#deep-agents-固定源码)。
- LangGraph 依赖通过 LangChain 进入；锁文件版本与 LangGraph `main` 不能混用。
- 设计综合使用 `inference` 标签，不伪称 Deep Agents 原仓库已有同名 schema 或 event ledger。
