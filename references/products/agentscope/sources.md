# AgentScope 来源与证据边界

## 研究基线

- 研究日期：2026-08-08。
- 稳定 tag：`v2.0.6`。
- 固定 commit：`29b592358c2e983a0d10dd5227316b7a02d8c23a`。
- 仓库：https://github.com/agentscope-ai/agentscope
- 发布树：https://github.com/agentscope-ai/agentscope/tree/29b592358c2e983a0d10dd5227316b7a02d8c23a
- 许可证：https://github.com/agentscope-ai/agentscope/blob/29b592358c2e983a0d10dd5227316b7a02d8c23a/LICENSE

本页链接到 commit，而不是 `main`。官方 `2.0.6dev` 页面是开发版说明；它能证明官方的概念分类，不能自动证明稳定 tag 中每个页面的全部行为。

## 固定源码地图

| 论断 | 固定证据 | 可推出 | 不可推出 |
|---|---|---|---|
| Agent 有显式 ReAct loop 与中断入口 | [agent/_agent.py](https://github.com/agentscope-ai/agentscope/blob/29b592358c2e983a0d10dd5227316b7a02d8c23a/src/agentscope/agent/_agent.py) | reasoning/acting、tool、interrupt 是显式控制流 | 分布式 exactly-once |
| ReAct/Context 可配置 | [agent/_config.py](https://github.com/agentscope-ai/agentscope/blob/29b592358c2e983a0d10dd5227316b7a02d8c23a/src/agentscope/agent/_config.py) | max iterations、压缩等可配置 | 默认值适合所有模型 |
| Message 由 typed blocks 组成 | [message/_base.py](https://github.com/agentscope-ai/agentscope/blob/29b592358c2e983a0d10dd5227316b7a02d8c23a/src/agentscope/message/_base.py) | text/thinking/tool/data 可结构化投影 | 公共 wire protocol 已版本化 |
| Event 覆盖流式块、工具、HITL、中断 | [event/_event.py](https://github.com/agentscope-ai/agentscope/blob/29b592358c2e983a0d10dd5227316b7a02d8c23a/src/agentscope/event/_event.py) | reply/event 可增量消费 | event 已持久或幂等 |
| AgentState 保存上下文、reply、permission、tool、task | [state/_state.py](https://github.com/agentscope-ai/agentscope/blob/29b592358c2e983a0d10dd5227316b7a02d8c23a/src/agentscope/state/_state.py) | 进程内状态有明确 schema | service storage 原子写入 |
| Permission 有 mode/rule/decision/engine | [permission](https://github.com/agentscope-ai/agentscope/tree/29b592358c2e983a0d10dd5227316b7a02d8c23a/src/agentscope/permission) | policy decision 可独立测试 | 已强制 syscall/网络隔离 |
| Tool 有 schema、group、response 与 builtin | [tool](https://github.com/agentscope-ai/agentscope/tree/29b592358c2e983a0d10dd5227316b7a02d8c23a/src/agentscope/tool) | 工具注册与执行可分层 | 任意第三方 tool 安全 |
| Workspace 聚合 tool/MCP/skill/offload | [workspace/_base.py](https://github.com/agentscope-ai/agentscope/blob/29b592358c2e983a0d10dd5227316b7a02d8c23a/src/agentscope/workspace/_base.py) | workspace 是能力与资源边界 | WorkspaceBase 本身是 sandbox |
| 有 Local 与 sandboxed workspace 实现 | [workspace](https://github.com/agentscope-ai/agentscope/tree/29b592358c2e983a0d10dd5227316b7a02d8c23a/src/agentscope/workspace) | backend 可替换 | 所有部署都启用强隔离 |
| Workspace Manager 支持隔离分配策略 | [workspace_manager/_base.py](https://github.com/agentscope-ai/agentscope/blob/29b592358c2e983a0d10dd5227316b7a02d8c23a/src/agentscope/app/workspace_manager/_base.py) | per-agent/per-user 生命周期可建模 | 资源边界等同安全边界 |
| Service 有 bus/storage/channel/router | [app](https://github.com/agentscope-ai/agentscope/tree/29b592358c2e983a0d10dd5227316b7a02d8c23a/src/agentscope/app) | 可拆 headless runtime 与适配器 | 任意部署已多租户安全 |
| MessageBus 有 log/pubsub/lock/cancel/inbox | [message_bus/_base.py](https://github.com/agentscope-ai/agentscope/blob/29b592358c2e983a0d10dd5227316b7a02d8c23a/src/agentscope/app/message_bus/_base.py) | service 可做单 session 互斥与重连 | Redis 配置天然 exactly-once |
| Channel 有 capability 与事件适配 | [channel/_base.py](https://github.com/agentscope-ai/agentscope/blob/29b592358c2e983a0d10dd5227316b7a02d8c23a/src/agentscope/app/channel/_base.py) | 渠道可作为投影层 | 各渠道 UI 完全等价 |

## 官方 dev 文档地图

- Agent：https://docs.agentscope.io/versions/2.0.6dev/en/building-blocks/agent/overview
- Model：https://docs.agentscope.io/versions/2.0.6dev/en/building-blocks/model
- Context：https://docs.agentscope.io/versions/2.0.6dev/en/building-blocks/context/overview
- Tool：https://docs.agentscope.io/versions/2.0.6dev/en/building-blocks/tool/overview
- Plan：https://docs.agentscope.io/versions/2.0.6dev/en/building-blocks/plan
- Permission：https://docs.agentscope.io/versions/2.0.6dev/en/building-blocks/permission-system/overview
- Middleware：https://docs.agentscope.io/versions/2.0.6dev/en/building-blocks/middleware
- RAG：https://docs.agentscope.io/versions/2.0.6dev/en/building-blocks/rag
- Long-Term Memory：https://docs.agentscope.io/versions/2.0.6dev/en/building-blocks/long-term-memory
- Workspace：https://docs.agentscope.io/versions/2.0.6dev/en/building-blocks/workspace/overview
- Service：https://docs.agentscope.io/versions/2.0.6dev/en/deploy/agent-service
- Team：https://docs.agentscope.io/versions/2.0.6dev/en/deploy/agent-team
- Channel：https://docs.agentscope.io/versions/2.0.6dev/en/deploy/channel/overview

## 证据标签

- `official-doc`：官方页面明确描述；若是 dev 页面，记录 `stability=dev`。
- `code`：固定 commit 可定位类、字段或控制流。
- `test`：固定 commit 的公开测试可重复验证。
- `inference`：为生成可靠产品补充的工程设计，不冒充原实现。
- `unknown`：云端配置、线上 SLO、私有提示词、未公开 UI 行为。

## 使用规则

实现文档中的 schema 只要没有逐字段固定源码证据，就视为 `inference`。对外宣称“AgentScope-like”时应列出 verified capability，而不是声称源码等价。升级版本必须重新固定 tag/commit、运行差异检查并更新本页；不能把 `main` 的新目录静默归入 2.0.6。
