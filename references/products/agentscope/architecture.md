# AgentScope 架构蒸馏

## 事实：官方公开的构件

AgentScope 2.0.6dev 文档将 Agent 的配置、运行、人工介入和中断分开说明，并把 Context、Tool、Permission System、Middleware、Plan、RAG、Long-Term Memory 与 Workspace 作为 building blocks：

- Agent overview: https://docs.agentscope.io/versions/2.0.6dev/en/building-blocks/agent/overview
- Configure/run/interrupt: https://docs.agentscope.io/versions/2.0.6dev/en/building-blocks/agent/configure-agent 、https://docs.agentscope.io/versions/2.0.6dev/en/building-blocks/agent/run-agent 、https://docs.agentscope.io/versions/2.0.6dev/en/building-blocks/agent/interrupt-agent
- Message and event: https://docs.agentscope.io/versions/2.0.6dev/en/building-blocks/message-and-event
- Middleware: https://docs.agentscope.io/versions/2.0.6dev/en/building-blocks/middleware

这些事实支持“AgentScope 不是只有一个模型调用循环”的结论，但不单独证明其持久化、幂等和 sandbox 达到本仓库 `polished` 等级。

## 源码观察：职责可定位

公开源码根目录同时包含 `agent`、`app`、`credential`、`event`、`message`、`middleware`、`model`、`permission`、`rag`、`skill`、`state`、`tool` 与 `workspace`：

- https://github.com/agentscope-ai/agentscope/tree/29b592358c2e983a0d10dd5227316b7a02d8c23a/src/agentscope

由此可观察到：

1. Message/Event 与 Agent 分包，适合蒸馏为可投影的事件协议，而不是让 UI 读取 agent 内部对象。
2. Permission 与 Workspace/Tool 分包，适合保留“决策、路由、执行”三层边界。
3. Model、Embedding、TTS 分开公开，模型适配层不应只抽象聊天补全。
4. Skill、MCP、Tool、Workspace 同时存在，说明“能力声明、远程协议、可调用工具、运行资源”是不同概念。

以上是目录级观察；具体类之间的调用关系应在锁定 commit 后补充行号证据。

## 设计综合：映射到共享九边界

| 共享边界 | AgentScope 差量 | 蒸馏要求 |
|---|---|---|
| Protocol | Message/Event 是显式构件 | 仍使用共享 `Command/Event/Item` 版本合同；只增加 AgentScope 风格事件，不另建协议 |
| Turn orchestrator | Agent 可配置、运行、中断、HITL | 将中断和人工输入做成持久状态，不用进程内 callback 代替 |
| Model adapter | LLM、Embedding、TTS 分面 | 用 capability negotiation 暴露 chat/embed/tts，不伪造跨 provider 等价 |
| Context engine | compress、offload、environment awareness | 保留 fragment provenance、offload reference 与压缩边界 |
| Tool runtime | Python tool、MCP、skills、tool management | 统一落到共享 `ToolSpec/ToolCall/ToolResult` |
| Policy | mode、rule、tool check | 编译为 `allow/deny/ask/amend` 决策，不耦合 UI |
| Executor | Workspace 运行和资源管理 | Workspace 不是强制沙箱；执行仍服从共享 sandbox 合同 |
| State | 源码有 state 包 | 采用共享 thread/turn/item/event/checkpoint，不推断内部 schema |
| Surface | Agent service/team/channel | 通过共享事件协议连接服务与渠道，渠道不直接调用 agent 对象 |

## 不变量

- 所有工具副作用先经过 policy，再由 executor 执行。
- Context 压缩生成新 item 和恢复引用，不覆盖历史事实。
- Workspace 资源、MCP 工具和 skill 都受相同身份、scope、取消和审计约束。
- Agent 中断、审批等待、模型重试和渠道断连都有明确终态或可恢复状态。

## 不采纳的误读

- 不把“官方有 Permission System”写成“已经具备强制 sandbox”。
- 不把 MCP Gateway 当成权限边界；MCP 只负责能力发现与调用协议。
- 不因源码有 `state` 目录就宣称具备分布式 durable execution。
- 不复制 AgentScope 的命名到最终产品公共 API；能力 id 使用本仓库稳定名称。

## 服务拓扑补充

- SDK、HTTP 与 Channel 统一生成 command，不直接突变 AgentState。
- Session 使用单 writer；Storage 是事实源，MessageBus 负责协调与通知。
- Team worker 拥有独立 session，通过带来源 id 的 inbox 消息协作。
- Workspace Manager 分配资源，Permission 决策授权，Sandbox backend 强制隔离，三者不可合并。
- 固定源码与永久链接的逐项证据见 [sources.md](sources.md)。
- runnable 到 polished 始终复用同一 protocol/runtime，只增加持久化、服务与 enforcement。
