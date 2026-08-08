# LangGraph 来源、版本与证据账本

## 目录

- [冻结版本](#冻结版本)
- [官方文档](#官方文档)
- [Python 源码](#python-源码)
- [Python 测试](#python-测试)
- [JavaScript 交叉证据](#javascript-交叉证据)
- [证据规则](#证据规则)

## 冻结版本

- Python release tag：[1.2.10](https://github.com/langchain-ai/langgraph/releases/tag/1.2.10)，固定 commit [`41341457342327166d72fc11952ab28fb61ec0bf`](https://github.com/langchain-ai/langgraph/tree/41341457342327166d72fc11952ab28fb61ec0bf)。
- Python 包元数据：[libs/langgraph/pyproject.toml](https://github.com/langchain-ai/langgraph/blob/41341457342327166d72fc11952ab28fb61ec0bf/libs/langgraph/pyproject.toml)，声明 `langgraph 1.2.10`、`langchain-core>=1.4.7,<2`、`langgraph-checkpoint>=4.1.0,<5`。
- Python 许可证：[MIT LICENSE](https://github.com/langchain-ai/langgraph/blob/41341457342327166d72fc11952ab28fb61ec0bf/LICENSE)。
- JS release tag：[`@langchain/langgraph@1.4.9`](https://github.com/langchain-ai/langgraphjs/releases/tag/%40langchain%2Flanggraph%401.4.9)，固定 commit [`5f9915234a5dca861ef01180fde28e52f42c6e15`](https://github.com/langchain-ai/langgraphjs/tree/5f9915234a5dca861ef01180fde28e52f42c6e15)。
- JS 许可证：[MIT LICENSE](https://github.com/langchain-ai/langgraphjs/blob/5f9915234a5dca861ef01180fde28e52f42c6e15/LICENSE)。

## 官方文档

- [Overview](https://docs.langchain.com/oss/python/langgraph/overview)：低层 orchestration/runtime 定位。
- [Graph API](https://docs.langchain.com/oss/python/langgraph/graph-api)：state、reducer、node、edge、compile。
- [Pregel runtime](https://docs.langchain.com/oss/python/langgraph/pregel)：Plan/Execution/Update 三阶段与 BSP 语义。
- [Persistence](https://docs.langchain.com/oss/python/langgraph/persistence)：thread、checkpoint、state history、pending writes、Store。
- [Interrupts](https://docs.langchain.com/oss/python/langgraph/interrupts)：durable pause 与 `Command(resume=...)`。
- [Streaming](https://docs.langchain.com/oss/python/langgraph/streaming)：values、updates、messages、custom、debug 等模式。
- [Subgraphs](https://docs.langchain.com/oss/python/langgraph/use-subgraphs)：state sharing、checkpoint propagation 与查看子图状态。
- [Memory concepts](https://docs.langchain.com/oss/python/concepts/memory)：thread-scoped 与跨 thread memory 边界。
- [LangSmith Deployment](https://docs.langchain.com/langsmith/deployment)：托管/自托管 deployment，属于平台边界。
- [LangSmith Studio](https://docs.langchain.com/langsmith/studio)：开发与可视化表面，属于产品边界。

## Python 源码

- [`StateGraph`](https://github.com/langchain-ai/langgraph/blob/41341457342327166d72fc11952ab28fb61ec0bf/libs/langgraph/langgraph/graph/state.py)：schema、node、edge、branch 与 compile。
- [`Pregel`](https://github.com/langchain-ai/langgraph/blob/41341457342327166d72fc11952ab28fb61ec0bf/libs/langgraph/langgraph/pregel/main.py)：invoke/stream/state/history/update 和 durability 表面。
- [Pregel loop](https://github.com/langchain-ai/langgraph/blob/41341457342327166d72fc11952ab28fb61ec0bf/libs/langgraph/langgraph/pregel/_loop.py)：tick、checkpoint、pending writes、interrupt。
- [Task runner](https://github.com/langchain-ai/langgraph/blob/41341457342327166d72fc11952ab28fb61ec0bf/libs/langgraph/langgraph/pregel/_runner.py)：并发 task、commit、失败与 sibling interruption。
- [调度算法](https://github.com/langchain-ai/langgraph/blob/41341457342327166d72fc11952ab28fb61ec0bf/libs/langgraph/langgraph/pregel/_algo.py)：prepare tasks、apply writes、channel version。
- [公开类型](https://github.com/langchain-ai/langgraph/blob/41341457342327166d72fc11952ab28fb61ec0bf/libs/langgraph/langgraph/types.py)：`Command`、`Send`、`Interrupt`、`StateSnapshot`、stream/durability 类型。
- [Channel base](https://github.com/langchain-ai/langgraph/blob/41341457342327166d72fc11952ab28fb61ec0bf/libs/langgraph/langgraph/channels/base.py) 与 [binary reducer](https://github.com/langchain-ai/langgraph/blob/41341457342327166d72fc11952ab28fb61ec0bf/libs/langgraph/langgraph/channels/binop.py)。
- [LastValue](https://github.com/langchain-ai/langgraph/blob/41341457342327166d72fc11952ab28fb61ec0bf/libs/langgraph/langgraph/channels/last_value.py) 与 [Topic](https://github.com/langchain-ai/langgraph/blob/41341457342327166d72fc11952ab28fb61ec0bf/libs/langgraph/langgraph/channels/topic.py)。
- [Checkpoint protocol](https://github.com/langchain-ai/langgraph/blob/41341457342327166d72fc11952ab28fb61ec0bf/libs/checkpoint/langgraph/checkpoint/base/__init__.py)：`Checkpoint`、metadata、tuple、saver API。
- [Serialization](https://github.com/langchain-ai/langgraph/blob/41341457342327166d72fc11952ab28fb61ec0bf/libs/checkpoint/langgraph/checkpoint/serde/jsonplus.py) 与 [encrypted serializer](https://github.com/langchain-ai/langgraph/blob/41341457342327166d72fc11952ab28fb61ec0bf/libs/checkpoint/langgraph/checkpoint/serde/encrypted.py)。
- [Store protocol](https://github.com/langchain-ai/langgraph/blob/41341457342327166d72fc11952ab28fb61ec0bf/libs/checkpoint/langgraph/store/base/__init__.py) 与 [in-memory store](https://github.com/langchain-ai/langgraph/blob/41341457342327166d72fc11952ab28fb61ec0bf/libs/checkpoint/langgraph/store/memory/__init__.py)。
- [Runtime injection](https://github.com/langchain-ai/langgraph/blob/41341457342327166d72fc11952ab28fb61ec0bf/libs/langgraph/langgraph/runtime.py)：context、store、stream writer、previous value。

## Python 测试

- [Pregel tests](https://github.com/langchain-ai/langgraph/blob/41341457342327166d72fc11952ab28fb61ec0bf/libs/langgraph/tests/test_pregel.py)：superstep、pending writes、subgraph、stream、store。
- [Channel tests](https://github.com/langchain-ai/langgraph/blob/41341457342327166d72fc11952ab28fb61ec0bf/libs/langgraph/tests/test_channels.py)：update/consume/checkpoint 行为。
- [Interrupt tests](https://github.com/langchain-ai/langgraph/blob/41341457342327166d72fc11952ab28fb61ec0bf/libs/langgraph/tests/test_interruption.py) 与 [interrupt migration](https://github.com/langchain-ai/langgraph/blob/41341457342327166d72fc11952ab28fb61ec0bf/libs/langgraph/tests/test_interrupt_migration.py)。
- [Time travel tests](https://github.com/langchain-ai/langgraph/blob/41341457342327166d72fc11952ab28fb61ec0bf/libs/langgraph/tests/test_time_travel.py)：replay、fork、历史保留、嵌套子图。
- [Checkpoint migration tests](https://github.com/langchain-ai/langgraph/blob/41341457342327166d72fc11952ab28fb61ec0bf/libs/langgraph/tests/test_checkpoint_migration.py)。
- [Retry tests](https://github.com/langchain-ai/langgraph/blob/41341457342327166d72fc11952ab28fb61ec0bf/libs/langgraph/tests/test_retry.py)：retry、timeout、取消和 error handler。
- [Subgraph persistence tests](https://github.com/langchain-ai/langgraph/blob/41341457342327166d72fc11952ab28fb61ec0bf/libs/langgraph/tests/test_subgraph_persistence.py)。
- [Stream v3 tests](https://github.com/langchain-ai/langgraph/blob/41341457342327166d72fc11952ab28fb61ec0bf/libs/langgraph/tests/test_stream_events_v3.py)。
- [Serde allowlist tests](https://github.com/langchain-ai/langgraph/blob/41341457342327166d72fc11952ab28fb61ec0bf/libs/langgraph/tests/test_serde_allowlist.py)。

## JavaScript 交叉证据

- [JS StateGraph](https://github.com/langchain-ai/langgraphjs/blob/5f9915234a5dca861ef01180fde28e52f42c6e15/libs/langgraph-core/src/graph/state.ts)。
- [JS Pregel](https://github.com/langchain-ai/langgraphjs/blob/5f9915234a5dca861ef01180fde28e52f42c6e15/libs/langgraph-core/src/pregel/index.ts)。
- [JS channels](https://github.com/langchain-ai/langgraphjs/tree/5f9915234a5dca861ef01180fde28e52f42c6e15/libs/langgraph-core/src/channels)。
- [JS checkpoint API](https://github.com/langchain-ai/langgraphjs/blob/5f9915234a5dca861ef01180fde28e52f42c6e15/libs/checkpoint/src/base.ts)。
- [JS Pregel tests](https://github.com/langchain-ai/langgraphjs/tree/5f9915234a5dca861ef01180fde28e52f42c6e15/libs/langgraph-core/src/tests/pregel)。

## 证据规则

- 固定 commit 的源码/测试是实现事实；浮动文档只解释公开意图。
- Python 与 JS 同名概念不保证内部字段、默认值或 stream envelope 完全相同。
- 文档没有证明 side-effect exactly-once、sandbox、permission、multi-tenant 或 HA。
- LangSmith Deployment/Studio 只能证明平台产品行为，不能反推开源 core 内部实现。
- 本 dossier 标为“设计综合”的合同，是复刻完整 harness 所需增强，不冒充上游事实。
- 上游发布后需重新锁 tag、commit、依赖、迁移测试与来源访问时间，再升级事实基线。
