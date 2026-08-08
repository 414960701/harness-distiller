# Deep Agents 证据与版本登记

## 目录

- [研究基线](#研究基线)
- [证据等级](#证据等级)
- [官方文档](#官方文档)
- [Deep Agents 固定源码](#deep-agents-固定源码)
- [LangGraph 固定依赖](#langgraph-固定依赖)
- [测试证据](#测试证据)
- [组件与服务边界](#组件与服务边界)
- [已知限制](#已知限制)
- [复核流程](#复核流程)

## 研究基线

| 字段 | 固定值 |
|---|---|
| 调研日期 | 2026-08-08 |
| Deep Agents 仓库 | `langchain-ai/deepagents` |
| Deep Agents commit | `d60560d695e8c436e11dee96965e7a1447409737` |
| Python 包版本 | `deepagents==0.7.5` |
| Python | `>=3.11,<4.0` |
| 锁文件中的 LangChain | `1.3.14` |
| 锁文件中的 LangGraph | `1.2.9` |
| LangGraph 1.2.9 commit | `95af6a00718588e7b7ce17310e8006d267896a77` |

文档 URL 是滚动发布内容，必须记录访问日期；实现结论优先引用固定 commit permalink。

## 证据等级

| 标签 | 含义 | 可用于什么结论 |
|---|---|---|
| `official-doc` | 官方滚动文档 | 公共行为、配置入口、产品定位 |
| `code` | 固定 commit 源码 | 字段、顺序、默认值、分支和边界 |
| `test` | 固定 commit 测试 | 可观察 oracle、异常和兼容行为 |
| `dependency` | 固定依赖源码/锁文件 | Deep Agents 委托给 LangGraph 的语义 |
| `threat-model` | 仓库威胁模型 | 已知信任边界与明确安全缺口 |
| `inference` | 本仓库设计综合 | 复刻方案，不冒充原实现事实 |

冲突处理顺序为：同版本测试与代码 > 同版本锁文件 > 滚动官方文档 > 设计综合。

## 官方文档

- [Overview](https://docs.langchain.com/oss/python/deepagents/overview)：能力面；0.7 起 planning 为 opt-in。
- [Customization](https://docs.langchain.com/oss/python/deepagents/customization)：middleware 顺序、替换和 profile。
- [Context engineering](https://docs.langchain.com/oss/python/deepagents/context-engineering)：输入、运行时、压缩、隔离、长期记忆。
- [Backends](https://docs.langchain.com/oss/python/deepagents/backends)：State、Filesystem、Store、Composite 与协议。
- [Subagents](https://docs.langchain.com/oss/python/deepagents/subagents)：同步委派、状态隔离和结构化返回。
- [Async subagents](https://docs.langchain.com/oss/python/deepagents/async-subagents)：Agent Protocol 远程后台任务。
- [Permissions](https://docs.langchain.com/oss/python/deepagents/permissions)：内置 filesystem tool 的首条匹配规则。
- [Human-in-the-loop](https://docs.langchain.com/oss/python/deepagents/human-in-the-loop)：interrupt、批准、编辑、拒绝、响应。
- [Sandboxes](https://docs.langchain.com/oss/python/deepagents/sandboxes)：执行型 backend 与隔离责任。
- [Fault tolerance](https://docs.langchain.com/oss/python/deepagents/fault-tolerance)：重试、fallback、limit、错误分流。
- [Streaming](https://docs.langchain.com/oss/python/deepagents/streaming)：LangGraph stream 与 subgraph namespace。
- [Event streaming](https://docs.langchain.com/oss/python/deepagents/event-streaming)：typed projection API。
- [ACP](https://docs.langchain.com/oss/python/deepagents/acp)：编辑器协议适配；不是 MCP。
- [LangGraph persistence](https://docs.langchain.com/oss/python/langgraph/persistence)：thread/checkpoint/pending write。
- [LangGraph interrupts](https://docs.langchain.com/oss/python/langgraph/interrupts)：暂停与 `Command(resume=...)`。

## Deep Agents 固定源码

- [包与依赖](https://github.com/langchain-ai/deepagents/blob/d60560d695e8c436e11dee96965e7a1447409737/libs/deepagents/pyproject.toml)：版本和 LangChain 依赖范围。
- [锁文件](https://github.com/langchain-ai/deepagents/blob/d60560d695e8c436e11dee96965e7a1447409737/libs/deepagents/uv.lock)：解析后的 LangGraph 1.2.9。
- [graph.py](https://github.com/langchain-ai/deepagents/blob/d60560d695e8c436e11dee96965e7a1447409737/libs/deepagents/deepagents/graph.py)：工厂、默认 backend、middleware 组装和状态 schema。
- [message reducer](https://github.com/langchain-ai/deepagents/blob/d60560d695e8c436e11dee96965e7a1447409737/libs/deepagents/deepagents/_messages_reducer.py)：DeltaChannel 消息合并。
- [backend protocol](https://github.com/langchain-ai/deepagents/blob/d60560d695e8c436e11dee96965e7a1447409737/libs/deepagents/deepagents/backends/protocol.py)：文件与执行返回类型。
- [StateBackend](https://github.com/langchain-ai/deepagents/blob/d60560d695e8c436e11dee96965e7a1447409737/libs/deepagents/deepagents/backends/state.py)：thread state 内文件。
- [StoreBackend](https://github.com/langchain-ai/deepagents/blob/d60560d695e8c436e11dee96965e7a1447409737/libs/deepagents/deepagents/backends/store.py)：跨 thread store。
- [FilesystemMiddleware](https://github.com/langchain-ai/deepagents/blob/d60560d695e8c436e11dee96965e7a1447409737/libs/deepagents/deepagents/middleware/filesystem.py)：工具、permission、offload。
- [permission/HITL glue](https://github.com/langchain-ai/deepagents/blob/d60560d695e8c436e11dee96965e7a1447409737/libs/deepagents/deepagents/middleware/_fs_interrupt.py)：path predicate。
- [sync subagents](https://github.com/langchain-ai/deepagents/blob/d60560d695e8c436e11dee96965e7a1447409737/libs/deepagents/deepagents/middleware/subagents.py)：task 工具与 state filter。
- [async subagents](https://github.com/langchain-ai/deepagents/blob/d60560d695e8c436e11dee96965e7a1447409737/libs/deepagents/deepagents/middleware/async_subagents.py)：远程 thread/run 状态。
- [summarization](https://github.com/langchain-ai/deepagents/blob/d60560d695e8c436e11dee96965e7a1447409737/libs/deepagents/deepagents/middleware/summarization.py)：压缩和 history offload。
- [skills](https://github.com/langchain-ai/deepagents/blob/d60560d695e8c436e11dee96965e7a1447409737/libs/deepagents/deepagents/middleware/skills.py)：SKILL.md 发现和注入。
- [memory](https://github.com/langchain-ai/deepagents/blob/d60560d695e8c436e11dee96965e7a1447409737/libs/deepagents/deepagents/middleware/memory.py)：AGENTS.md 常驻上下文。
- [ACP server](https://github.com/langchain-ai/deepagents/blob/d60560d695e8c436e11dee96965e7a1447409737/libs/acp/deepagents_acp/server.py)：session、stream、permission 映射。
- [threat model](https://github.com/langchain-ai/deepagents/blob/d60560d695e8c436e11dee96965e7a1447409737/libs/deepagents/THREAT_MODEL.md)：LocalShell、skill/memory 注入等风险。

## LangGraph 固定依赖

- [checkpoint 基础协议](https://github.com/langchain-ai/langgraph/blob/95af6a00718588e7b7ce17310e8006d267896a77/libs/checkpoint/langgraph/checkpoint/base/__init__.py)：`Checkpoint`、`CheckpointTuple`、saver API。
- [checkpoint README](https://github.com/langchain-ai/langgraph/blob/95af6a00718588e7b7ce17310e8006d267896a77/libs/checkpoint/README.md)：thread、checkpoint_id、pending writes。
- [graph types](https://github.com/langchain-ai/langgraph/blob/95af6a00718588e7b7ce17310e8006d267896a77/libs/langgraph/langgraph/types.py)：Interrupt、Command、stream mode。
- [Pregel loop](https://github.com/langchain-ai/langgraph/blob/95af6a00718588e7b7ce17310e8006d267896a77/libs/langgraph/langgraph/pregel/_loop.py)：superstep、pending writes、durability。
- [state graph](https://github.com/langchain-ai/langgraph/blob/95af6a00718588e7b7ce17310e8006d267896a77/libs/langgraph/langgraph/graph/state.py)：schema、channel 和编译。

Deep Agents 调用 `langchain.agents.create_agent` 并传入 checkpointer/store；它没有复制 LangGraph 的调度器或 checkpoint 数据库。

## 测试证据

- [graph tests](https://github.com/langchain-ai/deepagents/blob/d60560d695e8c436e11dee96965e7a1447409737/libs/deepagents/tests/unit_tests/test_graph.py)：栈顺序、planning opt-in、继承。
- [permission tests](https://github.com/langchain-ai/deepagents/blob/d60560d695e8c436e11dee96965e7a1447409737/libs/deepagents/tests/unit_tests/test_permissions.py)：首条匹配、bulk path、interrupt。
- [subagent tests](https://github.com/langchain-ai/deepagents/blob/d60560d695e8c436e11dee96965e7a1447409737/libs/deepagents/tests/unit_tests/test_subagents.py)：状态过滤和最终结果。
- [async subagent tests](https://github.com/langchain-ai/deepagents/blob/d60560d695e8c436e11dee96965e7a1447409737/libs/deepagents/tests/unit_tests/test_async_subagents.py)：task reducer、更新、取消。
- [message reducer tests](https://github.com/langchain-ai/deepagents/blob/d60560d695e8c436e11dee96965e7a1447409737/libs/deepagents/tests/unit_tests/test_messages_reducer.py)：ID 替换、删除和重放。
- [end-to-end tests](https://github.com/langchain-ai/deepagents/blob/d60560d695e8c436e11dee96965e7a1447409737/libs/deepagents/tests/unit_tests/test_end_to_end.py)：模型—工具循环。
- [HITL integration](https://github.com/langchain-ai/deepagents/blob/d60560d695e8c436e11dee96965e7a1447409737/libs/deepagents/tests/integration_tests/test_hitl.py)：interrupt 恢复。

## 组件与服务边界

| 能力 | OSS `deepagents` | LangGraph/LangChain | 伴生包或服务 |
|---|---|---|---|
| 工厂与预置中间件 | 是 | 提供 create_agent/middleware 基类 | 否 |
| 图执行与 checkpoint | 仅配置透传 | 是 | 持久 checkpointer 需用户部署 |
| 文件 backend | 是 | Store 接口来自 LangGraph | provider backend 可选 |
| 同步 subagent | 是 | Runnable/Command | 否 |
| 异步 subagent | 客户端 middleware | SDK/Agent Protocol | 需要远程 server/deployment |
| ACP | 独立 `deepagents-acp` 包 | 使用 graph stream | IDE/client 不在核心包内 |
| tracing/eval | 发出 LangSmith metadata | callback 生态 | LangSmith 服务可选 |
| sandbox | 协议与基础实现 | 否 | 隔离强度由 provider/部署决定 |

## 已知限制

- `TodoListMiddleware` 在 0.7.5 不是默认项；必须显式加入或由 harness profile 加入。
- permissions 只覆盖内置 filesystem tools，不覆盖 `execute`、custom tool 或 MCP。
- `LocalShellBackend` 是宿主 shell，不是强 sandbox；`virtual_mode` 也不是 shell 安全边界。
- 同步 subagent 的“隔离”主要是独立消息上下文；部分非私有 state 会复制并可合并回来。
- 默认 `StateBackend` 的持久性取决于 graph state/checkpointer；不等于跨 thread memory。
- Memory 是加载指定 AGENTS.md；Skills 是发现/按需读取 SKILL.md；两者都不是向量 RAG。
- OSS 包没有内置通用 vector index；RAG 应由 tool/MCP/custom middleware 接入并保留引用。
- LangSmith tracing、Deployment、Studio 和 managed sandbox 不能算作纯 OSS 本地交付。

## 复核流程

1. 用 `git ls-remote` 验证两个 commit 仍可达。
2. 对所有 GitHub 链接确认包含 40 位 commit，而不是 `main`。
3. 对滚动文档执行 HTTP HEAD，并记录新的访问日期。
4. 重读 `pyproject.toml` 与 `uv.lock`，确认解析版本没有混用。
5. 用代码与测试复核默认 middleware 顺序和 planning 是否仍 opt-in。
6. 运行本目录 [acceptance-tests.md](acceptance-tests.md) 的来源、契约和失败注入测试。
7. 版本升级时新建证据快照，不静默改写旧结论。
