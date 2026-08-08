# AgentScope 体验蒸馏

## 事实：公开交互入口

官方文档公开了 Agent 的 configure、run、HITL 与 interrupt，以及 Agent Service、Agent Team、Discord/飞书/自定义渠道、路由、MCP Hub、Skill Hub 和 Workspace Manager 等部署入口：

- https://docs.agentscope.io/versions/2.0.6dev/en/building-blocks/agent/configure-agent
- https://docs.agentscope.io/versions/2.0.6dev/en/building-blocks/agent/run-agent
- https://docs.agentscope.io/versions/2.0.6dev/en/building-blocks/agent/human-in-the-loop
- https://docs.agentscope.io/versions/2.0.6dev/en/deploy/agent-service
- https://docs.agentscope.io/versions/2.0.6dev/en/deploy/agent-team
- https://docs.agentscope.io/versions/2.0.6dev/en/deploy/channel/overview
- https://docs.agentscope.io/versions/2.0.6dev/en/deploy/hub/overview
- https://docs.agentscope.io/versions/2.0.6dev/en/deploy/workspace-manager

## 源码观察

源码根下的 `app`、`event`、`message`、`state` 与其他 building-block 包并列：https://github.com/agentscope-ai/agentscope/tree/29b592358c2e983a0d10dd5227316b7a02d8c23a/src/agentscope 。这支持以消息/事件连接应用入口；没有足够证据时，不应推断某个网页、桌面端或渠道的具体视觉布局。

## 设计综合：AgentScope 风格而非界面仿制

该配方的体验签名是：

1. **配置可见**：启动前展示 model、tools、skills、workspace、permission mode 和 channel 的解析结果。
2. **运行可见**：用户能看到 turn 状态、计划、模型流、tool request/result、审批与 artifact，而不是一段不可恢复的日志。
3. **环境可见**：workspace roots、网络状态、MCP/skill 可用性和执行位置始终可检查。
4. **人工可接管**：interrupt、补充输入、审批和拒绝都使用稳定 request id，可在服务重启后恢复。
5. **部署可组合**：同一 headless runtime 可接 SDK、CLI、Web 或消息渠道；渠道只是协议适配器。

## 事件投影

建议最小事件集：

- `agent.configured`
- `turn.started | turn.waiting | turn.resumed | turn.finished`
- `context.compressed | context.offloaded`
- `plan.updated`
- `tool.requested | tool.progress | tool.completed`
- `approval.requested | approval.resolved`
- `workspace.resource_changed`
- `channel.delivery_state_changed`

UI 只从 snapshot + event stream 重建。渠道消息可折叠内部细节，但不得改变安全决策或绕过 approval。

## 产品体验场景

- 从配置创建 agent，连接一个本地 Python tool 和一个 MCP tool，运行后能解释每个能力的来源。
- 长任务触发压缩和 offload，用户仍能展开 artifact 并恢复早期证据。
- 危险工具进入审批；用户拒绝后 agent 可重规划，不能重复弹出同参数请求。
- 运行中 interrupt，稍后通过另一个 surface 恢复同一 turn。
- 将同一 agent 作为服务连接消息渠道；断线重连不丢 item，也不重复发送工具副作用。

## 非目标

- 不复制 AgentScope 标识、配色、文案或未公开提示词。
- 不用“支持很多渠道”替代 CLI/TUI/Web 的事件一致性验证。
- 不把部署成功等同于多租户安全、可观测性或生产 SLO 已完成。

## 界面与渠道验收补充

- 界面分别展示 permission mode、workspace backend 与 enforcement profile。
- Channel 声明 streaming/button/file/thread/size capability，不支持时显式降级。
- provider webhook id 用作 command 幂等键，delivery id 不得触发第二次 agent side effect。
- Team 视图显示 worker session、来源、permission/workspace scope，不合并内部状态。
- cursor 过期要求重取 snapshot；confirmation 过期或参数漂移必须新建请求。
