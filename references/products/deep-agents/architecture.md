# Deep Agents 架构蒸馏

## 目录

- [事实基线](#事实基线)
- [源码观察](#源码观察)
- [五层架构](#五层架构)
- [Middleware 组合](#middleware-组合)
- [Deep Agents 与 LangGraph 边界](#deep-agents-与-langgraph-边界)
- [OSS 与伴生服务边界](#oss-与伴生服务边界)
- [与共享九边界的映射](#与共享九边界的映射)
- [四级演进](#四级演进)
- [核心不变量](#核心不变量)
- [架构验收](#架构验收)

## 事实基线

官方 overview 和 customization 文档描述 Deep Agents 的预置 agent 能力和可定制入口；独立页面覆盖 backends、subagents、context engineering、permissions 与 production：

- https://docs.langchain.com/oss/python/deepagents/overview
- https://docs.langchain.com/oss/python/deepagents/customization
- https://docs.langchain.com/oss/python/deepagents/backends
- https://docs.langchain.com/oss/python/deepagents/subagents
- https://docs.langchain.com/oss/python/deepagents/going-to-production

LangGraph 官方文档提供 graph、persistence 和 interrupts，因此 Deep Agents 的恢复和 HITL 设计必须与底层 thread/checkpoint 语义一起理解：

- https://docs.langchain.com/oss/python/langgraph/graph-api
- https://docs.langchain.com/oss/python/langgraph/persistence
- https://docs.langchain.com/oss/python/langgraph/interrupts

## 源码观察

`libs/deepagents/deepagents` 包含：

- `graph.py`：顶层 graph 组装入口；
- `_messages_reducer.py`：消息状态归并职责可定位；
- `_models.py` 与 `_tools.py`：模型和工具规范化职责可定位；
- `middleware/`：预置能力以中间件组合；
- `backends/`：文件/执行资源后端抽象；
- `profiles/`：配置化 agent profile。

固定源码入口见 [sources.md](sources.md)，基线 commit 为 `d60560d695e8c436e11dee96965e7a1447409737`。

这些是文件/目录级观察。锁定 commit 前，不把默认 middleware 顺序、内部 state schema 或错误恢复细节写成稳定事实。

## 五层架构

```text
Surface/adapters
  SDK stream | typed projection | ACP | CLI/Code | custom frontend
                              |
Deep Agents harness
  profile | middleware | files | subagents | skills | memory | HITL glue
                              |
LangChain agent layer
  create_agent | model/tool node | general middleware contracts
                              |
LangGraph durable runtime
  state/channel | Pregel | checkpoint | interrupt | store | stream
                              |
Resource/enforcement
  backend | sandbox | provider | DB | artifact | external services
```

蒸馏时保留五层，不把 middleware 内部实现提升为公共协议，也不让 frontend 依赖 LangGraph 内部 state 对象。

## Middleware 组合

0.7.5 主栈的实现级顺序：

```text
Skills?
Filesystem
SubAgent?
Summarization
PatchToolCalls
AsyncSubAgent?
-- user insertion point --
profile extra middleware
provider prompt caching
Memory?
HumanInTheLoop?
final ToolExclusion?
```

架构规则：

- 同名 custom middleware 原位替换默认项；
- 新 custom middleware 插在 core 后、tail 前；
- Filesystem 与 SubAgent 等 scaffolding 不允许 profile 排除；
- final tool exclusion 位于所有 tool-injecting middleware 之后；
- middleware state schema 在 compile 前聚合；
- `PrivateStateAttr` 字段不向同步 subagent 传播；
- Todo 不在默认栈，作为 profile/user middleware 显式加入；
- 当前 turn 固化 middleware version/order，避免恢复漂移。

## Deep Agents 与 LangGraph 边界

| 主题 | Deep Agents | LangGraph |
|---|---|---|
| 工厂 | 接收产品参数并组装 | 编译并运行 graph |
| State schema | DeepAgentState 与 middleware extension | channel/reducer/checkpoint |
| Messages | 自定义 delta reducer | 稳定 ID、channel replay |
| Interrupt | 配 permission/HITL middleware | 保存与 resume continuation |
| Checkpoint | 参数透传 | saver、pending writes、durability |
| Store | backend 使用接口 | BaseStore 语义 |
| Stream | subagent/context 差量 | messages/updates/tasks/custom 基础流 |
| Fault tolerance | 选择 middleware/策略 | superstep 与 checkpoint 恢复基础 |

不能把 LangGraph 的 pending writes 等同于外部 shell/HTTP exactly-once；harness 仍需 call ledger 与 receipt。

## OSS 与伴生服务边界

| 能力 | 纯 OSS 可实现 | 需要伴生包/服务 |
|---|---|---|
| create_deep_agent 与同步 subagent | 是 | 否 |
| State/Filesystem/Store/Composite backend | 是 | Store 需具体部署 |
| ACP adapter | 是，独立包 | 需要 ACP client/IDE |
| Async subagent client | middleware 是 | 需要 Agent Protocol server |
| Prompt/trace metadata | 是 | LangSmith UI/托管存储可选 |
| Sandbox protocol | 是 | 强隔离需 provider/基础设施 |
| Managed permissions/profile | 可自建 | 官方 control plane 不在 core 包 |
| Production HA/service | 可自建 | Deployment/managed service 可选 |

## 与共享九边界的映射

| 共享边界 | Deep Agents 差量 | 约束 |
|---|---|---|
| Protocol | todo、subagent、filesystem、approval 的流事件 | 映射为版本化 Item/Event，前端不消费私有 reducer state |
| Turn orchestrator | graph 驱动长循环 | 共享终止原因、预算、取消和错误枚举不变 |
| Model adapter | 模型可配置 | 能力归一化仍由共享 adapter 完成 |
| Context engine | 专门的 context engineering、memory、skills | 每片段带 provenance/scope/budget |
| Tool runtime | 内置 filesystem/tool/MCP 能力 | 全部规范化为共享 ToolSpec/Result |
| Policy | permissions + HITL | 决策与 LangGraph interrupt continuation 分开 |
| Executor | backend/sandbox/interpreter | backend 选择不绕过 sandbox enforcement |
| State | LangGraph state/reducer/checkpoint/store | 对外提交共享 event；恢复副作用必须幂等 |
| Surface | frontend/ACP/streaming | 只通过快照与 event stream 重建 |

## 核心不变量

- Todo 是协作状态，不是隐藏 chain-of-thought。
- 子 agent 获取显式 context、budget、tools、permission 与 backend scope，不共享可变隐式状态。
- Filesystem backend 提供逻辑路径身份；所有本地/远程实现遵守相同路径、取消和 artifact 合同。
- middleware 顺序、可修改范围、失败策略和 timeout 可诊断。
- checkpoint 恢复不会重复提交已经成功的外部副作用。
- 默认 backend 与执行型 backend 的能力发现不能混淆。
- Planning opt-in 事实在 profile、文档和 UI 中一致。
- 同步 subagent 的 context 隔离不被宣传为 OS/租户隔离。
- 任何 frontend/ACP 都通过版本化投影，不直接序列化 Python state。

## 四级演进

| 等级 | 架构范围 | 关键约束 |
|---|---|---|
| `runnable` | 单进程 graph + state backend | 无隐藏远程依赖 |
| `usable` | checkpointer + store/filesystem + sync child + HITL | thread/permission 可恢复 |
| `productive` | RAG adapter + async/stream + replay | 副作用和投影可诊断 |
| `polished` | 强 sandbox + remote backend + multi-tenant service + managed profile | HA、迁移、SLO、安全门禁 |

## 架构验收

1. 组件图中每条跨层调用都有接口与 owner。
2. 导出 middleware 栈与上述顺序一致，差异有版本说明。
3. 移除 LangSmith credential 后 OSS core 的基础测试仍通过。
4. 无 Agent Protocol server 时 async capability 明确 unavailable。
5. 无 sandbox provider 时不回退到 host shell。
6. frontend 替换后 thread/turn/item 终态不变。
7. LangGraph 版本升级运行 golden checkpoint replay。
8. profile 更新不改变进行中 turn 的 capability snapshot。
9. 高等级部署仍能运行低等级纵切测试。
10. 所有事实链接回 [sources.md](sources.md)，所有设计综合有 acceptance oracle。
