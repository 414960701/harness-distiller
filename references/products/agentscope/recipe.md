# AgentScope 差量配方

本页只描述相对共享 35 模块的差量。通用合同、等级定义和安全要求分别见 [knowledge/index](../../knowledge/index.md)、[levels](../../levels.md) 与 [architecture](../../architecture.md)。

## 基线模块

所有等级继承共享 vertical slice：`agent-loop`、`model-adapter`、`protocol-events`、`context-engine`、`tool-runtime`、`workspace`、`filesystem`、`permission-policy`、`state-persistence`、`testing`。不要在本配方内重写这些合同。

按目标能力加载：

- Context/知识：`instructions-prompts`、`rag-index`、`long-term-memory`
- 工具扩展：`mcp`、`skills-plugins`、`middleware-hooks`
- 执行安全：`shell-process`、`sandbox`、`network-secrets`
- 编排部署：`planning`、`subagents`、`observability`、`evals`、`reliability`、`deployment-update`
- 交互表面：按请求选择 `cli-tui`、`desktop-web`、`notifications-input`、`auth-settings`

## 产品差量主题

下表只用于解释架构差量，不定义 capability ID；Blueprint 只能使用本页“Blueprint 闭环”列出的 15 个 canonical ID。

| 差量主题 | 共享模块 | AgentScope 差量 |
|---|---|---|
| Context offload | context-engine, filesystem | 大内容变 artifact ref；记录摘要、hash、scope、覆盖 items 与恢复路径 |
| Environment fragment | context-engine, workspace | 环境作为有 provenance/expiry 的 fragment 注入 |
| Permission evaluation | permission-policy | mode + ordered rule + per-tool check 编译为同一 `PolicyDecision` |
| Workspace resources | workspace, mcp, skills-plugins | tool、MCP、skill、artifact 进入版本化 capability snapshot |
| Middleware pipeline | middleware-hooks | model/tool/approval/turn 生命周期有确定顺序、超时和失败策略 |
| Plan state | planning, state-persistence | plan 是可持久、可中断、可由用户修改的 item |
| Service/team/channel | protocol-events, deployment-update | Agent Service/Team/Channel 只经版本协议通信 |

## 四等级增量

| 等级 | 只增加的产品差量 | 验收 |
|---|---|---|
| `runnable` 能跑 | 单 agent；静态 tools；单 workspace；基础 permission mode；结构化运行事件 | 完成读文件→模型请求→审批→受限工具→结果→终止；越界路径被拒绝；取消有明确终态 |
| `usable` 能用 | Context 压缩/offload；ordered rules 与 tool check；MCP；结构化 plan；会话恢复 | 长任务触发压缩后仍完成编辑；MCP 断连可降级；审批等待跨进程恢复；重复恢复不重放副作用 |
| `productive` 顺手 | environment-aware fragment；skills；middleware pipeline；长期记忆/RAG；Agent Team 或 subagent；trace/eval | 两个 agent 权限和 workspace 隔离；hook 顺序可诊断；记忆/RAG 不跨 scope；trace 串起 model/policy/tool/event |
| `polished` 好用 | 强 sandbox/网络策略；远程 Workspace Manager；服务/团队/渠道协议协商；插件生命周期；迁移与 SLO | symlink/进程/网络逃逸测试通过；渠道断线重连不重复副作用；旧客户端协商降级；坏 skill 可回滚且保留审计 |

## 直接升级

允许 `runnable -> polished`，但执行器必须按以下依赖顺序展开：

1. schema 与 capability snapshot；
2. protocol/event 兼容字段；
3. context offload 与状态迁移；
4. permission rules；
5. workspace/sandbox enforcement；
6. middleware、team、channel 与远程部署；
7. UI projection、回滚点和全等级回归。

不得重建 agent loop 或另起一套渠道 runtime。每完成一步都运行较低等级验收。

## 配方完成条件

- `capability-map` 能把每项差量追溯到本目录证据或明确标为设计综合。
- 至少覆盖启动、长任务、受限动作、中断恢复、服务/渠道五个黑盒场景。
- Permission 决策与 sandbox 强制分别验证。
- Context 压缩、offload、RAG 与长期记忆各有独立 provenance 和删除/失效语义。
- 未实现的 AgentScope 公开能力列入 `deferred`，不得用通用工具数量掩盖。

## Blueprint 闭环

蓝图的 `agent.react`、`model.wrapper`、`tools.toolkit`、`context.manager`、`permission.rules`、`middleware.chain`、`workspace.resources`、`planning.notebook`、`rag.pipeline`、`memory.long-term`、`teams.messaging`、`mcp.gateway`、`service.deployment`、`channels.production`、`runtime.distributed-state` 必须逐项映射到 [acceptance-tests.md](acceptance-tests.md) 的最低等级与 executable oracle，不能用一个笼统集成测试标记全部 verified。
