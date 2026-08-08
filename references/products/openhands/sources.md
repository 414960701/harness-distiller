# OpenHands 证据与版本登记

## 目录

- [研究基线](#研究基线)
- [证据规则](#证据规则)
- [官方文档](#官方文档)
- [Canvas 固定源码](#canvas-固定源码)
- [SDK 固定源码](#sdk-固定源码)
- [Agent Server 与 Workspace](#agent-server-与-workspace)
- [测试证据](#测试证据)
- [边界与限制](#边界与限制)
- [复核方法](#复核方法)

## 研究基线

| 字段 | 固定值 |
|---|---|
| 调研日期 | 2026-08-08 |
| Canvas 仓库 | `OpenHands/OpenHands` |
| Canvas commit | `4470813ce58f5ac384e3d367d34518e10106526b` |
| Canvas 版本 | `@openhands/agent-canvas==1.12.0` |
| SDK 仓库 | `OpenHands/software-agent-sdk` |
| SDK commit | `c7e270aae43a6e9bcc8723d27b85c680ab38e156` |
| SDK 版本 | `1.41.0` |
| Python | `>=3.12` |
| License | 两仓库均 MIT |

GitHub star、默认分支和滚动文档会变化，不作为实现语义。所有源码结论使用 40 位 commit permalink。

## 证据规则

| 标签 | 含义 | 用法 |
|---|---|---|
| `official-doc` | 官方滚动文档 | 产品入口、公开配置、推荐用法 |
| `code` | 固定 commit 源码 | 字段、分支、默认值、模块边界 |
| `test` | 固定 commit 测试 | 可观察 oracle、异常和兼容行为 |
| `legacy` | 历史架构或兼容路径 | 只能描述迁移，不冒充当前主路径 |
| `inference` | 本 skill 的设计综合 | 独立复刻所需但非原项目事实 |

冲突时采用：同 commit 测试与代码 > 同版本包元数据 > 官方滚动文档 > 设计综合。

## 官方文档

- [SDK 首页](https://docs.openhands.dev/sdk)：SDK 产品面与入口。
- [SDK 架构](https://docs.openhands.dev/sdk/arch/overview)：Agent、Conversation、Event、Workspace 分层。
- [Getting started](https://docs.openhands.dev/sdk/getting-started)：包安装和支持版本。
- [Hello world](https://docs.openhands.dev/sdk/guides/hello-world)：最小 Agent/Conversation 用法。
- [Conversation persistence](https://docs.openhands.dev/sdk/guides/convo-persistence)：恢复与 state 说明。
- [Context condenser](https://docs.openhands.dev/sdk/guides/context-condenser)：压缩入口。
- [Agent Server alive API](https://docs.openhands.dev/sdk/guides/agent-server/api-reference/server-details/alive)：服务 API 示例。
- [Agent Canvas backends](https://docs.openhands.dev/openhands/usage/agent-canvas/backends)：UI 可连接的 backend。
- [ACP agents](https://docs.openhands.dev/openhands/usage/agent-canvas/acp-agents)：Canvas 的 ACP 接入。
- [LLM profiles](https://docs.openhands.dev/openhands/usage/settings/llm-settings#llm-profiles)：模型配置体验。

## Canvas 固定源码

- [package.json](https://github.com/OpenHands/OpenHands/blob/4470813ce58f5ac384e3d367d34518e10106526b/package.json)：Agent Canvas 版本、React/Electron 与测试命令。
- [README](https://github.com/OpenHands/OpenHands/blob/4470813ce58f5ac384e3d367d34518e10106526b/README.md)：当前 Canvas 定位、backend 和安装入口。
- [MIT License](https://github.com/OpenHands/OpenHands/blob/4470813ce58f5ac384e3d367d34518e10106526b/LICENSE)：许可证事实。
- [event store](https://github.com/OpenHands/OpenHands/blob/4470813ce58f5ac384e3d367d34518e10106526b/src/stores/use-event-store.ts)：事件去重、排序和按 conversation 隔离。
- [event type guards](https://github.com/OpenHands/OpenHands/blob/4470813ce58f5ac384e3d367d34518e10106526b/src/types/agent-server/type-guards.ts)：Action、Observation、Message、State、Delta 类型投影。
- [conversation store](https://github.com/OpenHands/OpenHands/blob/4470813ce58f5ac384e3d367d34518e10106526b/src/stores/conversation-store.ts)：活动会话、tab 和 mode。
- [event service](https://github.com/OpenHands/OpenHands/blob/4470813ce58f5ac384e3d367d34518e10106526b/src/api/event-service/event-service.api.ts)：历史分页与 confirmation 响应。
- [conversation service](https://github.com/OpenHands/OpenHands/blob/4470813ce58f5ac384e3d367d34518e10106526b/src/api/conversation-service/agent-server-conversation-service.api.ts)：本地 agent-server API adapter。
- [runtime service](https://github.com/OpenHands/OpenHands/blob/4470813ce58f5ac384e3d367d34518e10106526b/src/api/runtime-service/agent-server-runtime-service.ts)：runtime 健康与命令入口。
- [event grouping](https://github.com/OpenHands/OpenHands/blob/4470813ce58f5ac384e3d367d34518e10106526b/src/components/conversation-events/chat/group-events.ts)：连续工具事件折叠规则。
- [browser store](https://github.com/OpenHands/OpenHands/blob/4470813ce58f5ac384e3d367d34518e10106526b/src/stores/browser-store.ts)：浏览器投影。
- [child conversation launch](https://github.com/OpenHands/OpenHands/blob/4470813ce58f5ac384e3d367d34518e10106526b/src/services/child-conversation-launch.ts)：子会话启动与幂等 ledger。
- [self hosting](https://github.com/OpenHands/OpenHands/blob/4470813ce58f5ac384e3d367d34518e10106526b/docs/SELF_HOSTING.md)：自托管拓扑。

## SDK 固定源码

- [root pyproject](https://github.com/OpenHands/software-agent-sdk/blob/c7e270aae43a6e9bcc8723d27b85c680ab38e156/pyproject.toml)：四包 workspace。
- [SDK pyproject](https://github.com/OpenHands/software-agent-sdk/blob/c7e270aae43a6e9bcc8723d27b85c680ab38e156/openhands-sdk/pyproject.toml)：`1.41.0` 与 Python 要求。
- [MIT License](https://github.com/OpenHands/software-agent-sdk/blob/c7e270aae43a6e9bcc8723d27b85c680ab38e156/LICENSE)：许可证事实。
- [Agent](https://github.com/OpenHands/software-agent-sdk/blob/c7e270aae43a6e9bcc8723d27b85c680ab38e156/openhands-sdk/openhands/sdk/agent/agent.py)：初始化、step、并行 action、确认和 finish。
- [parallel executor](https://github.com/OpenHands/software-agent-sdk/blob/c7e270aae43a6e9bcc8723d27b85c680ab38e156/openhands-sdk/openhands/sdk/agent/parallel_executor.py)：并行工具调度。
- [LocalConversation](https://github.com/OpenHands/software-agent-sdk/blob/c7e270aae43a6e9bcc8723d27b85c680ab38e156/openhands-sdk/openhands/sdk/conversation/impl/local_conversation.py)：run/arun、pause、interrupt、fork、condense。
- [ConversationState](https://github.com/OpenHands/software-agent-sdk/blob/c7e270aae43a6e9bcc8723d27b85c680ab38e156/openhands-sdk/openhands/sdk/conversation/state.py)：状态字段、active branch、autosave。
- [Event base](https://github.com/OpenHands/software-agent-sdk/blob/c7e270aae43a6e9bcc8723d27b85c680ab38e156/openhands-sdk/openhands/sdk/event/base.py)：不可变事件、id、source、parent。
- [EventLog](https://github.com/OpenHands/software-agent-sdk/blob/c7e270aae43a6e9bcc8723d27b85c680ab38e156/openhands-sdk/openhands/sdk/conversation/event_store.py)：追加、索引、锁、event tree。
- [View](https://github.com/OpenHands/software-agent-sdk/blob/c7e270aae43a6e9bcc8723d27b85c680ab38e156/openhands-sdk/openhands/sdk/context/view/view.py)：模型上下文投影与原子性检查。
- [LLM condenser](https://github.com/OpenHands/software-agent-sdk/blob/c7e270aae43a6e9bcc8723d27b85c680ab38e156/openhands-sdk/openhands/sdk/context/condenser/llm_summarizing_condenser.py)：摘要压缩。
- [tool schema](https://github.com/OpenHands/software-agent-sdk/blob/c7e270aae43a6e9bcc8723d27b85c680ab38e156/openhands-sdk/openhands/sdk/tool/schema.py)：Action/Observation discriminated union。
- [MCP client](https://github.com/OpenHands/software-agent-sdk/blob/c7e270aae43a6e9bcc8723d27b85c680ab38e156/openhands-sdk/openhands/sdk/mcp/client.py)：MCP 生命周期。
- [skill loading](https://github.com/OpenHands/software-agent-sdk/blob/c7e270aae43a6e9bcc8723d27b85c680ab38e156/openhands-sdk/openhands/sdk/skills/fetch.py)：skills 解析与发现。
- [plugin loader](https://github.com/OpenHands/software-agent-sdk/blob/c7e270aae43a6e9bcc8723d27b85c680ab38e156/openhands-sdk/openhands/sdk/plugin/loader.py)：plugin 聚合。

## Agent Server 与 Workspace

- [Agent Server README](https://github.com/OpenHands/software-agent-sdk/blob/c7e270aae43a6e9bcc8723d27b85c680ab38e156/openhands-agent-server/openhands/agent_server/README.md)：REST/WebSocket、本地存储与安全声明。
- [conversation service](https://github.com/OpenHands/software-agent-sdk/blob/c7e270aae43a6e9bcc8723d27b85c680ab38e156/openhands-agent-server/openhands/agent_server/conversation_service.py)：创建、恢复和生命周期。
- [event service](https://github.com/OpenHands/software-agent-sdk/blob/c7e270aae43a6e9bcc8723d27b85c680ab38e156/openhands-agent-server/openhands/agent_server/event_service.py)：事件分页、广播和确认。
- [conversation lease](https://github.com/OpenHands/software-agent-sdk/blob/c7e270aae43a6e9bcc8723d27b85c680ab38e156/openhands-agent-server/openhands/agent_server/conversation_lease.py)：单写者租约。
- [WebSocket](https://github.com/OpenHands/software-agent-sdk/blob/c7e270aae43a6e9bcc8723d27b85c680ab38e156/openhands-agent-server/openhands/agent_server/sockets.py)：订阅和发送。
- [server models](https://github.com/OpenHands/software-agent-sdk/blob/c7e270aae43a6e9bcc8723d27b85c680ab38e156/openhands-agent-server/openhands/agent_server/models.py)：API 模型与默认 confirmation policy。
- [workspace base](https://github.com/OpenHands/software-agent-sdk/blob/c7e270aae43a6e9bcc8723d27b85c680ab38e156/openhands-sdk/openhands/sdk/workspace/base.py)：执行、文件、git、pause/resume 合同。
- [LocalWorkspace](https://github.com/OpenHands/software-agent-sdk/blob/c7e270aae43a6e9bcc8723d27b85c680ab38e156/openhands-sdk/openhands/sdk/workspace/local.py)：宿主执行事实。
- [DockerWorkspace](https://github.com/OpenHands/software-agent-sdk/blob/c7e270aae43a6e9bcc8723d27b85c680ab38e156/openhands-workspace/openhands/workspace/docker/workspace.py)：容器生命周期。
- [remote API workspace](https://github.com/OpenHands/software-agent-sdk/blob/c7e270aae43a6e9bcc8723d27b85c680ab38e156/openhands-workspace/openhands/workspace/remote_api/workspace.py)：远程 runtime attach/pause/resume。
- [confirmation policy](https://github.com/OpenHands/software-agent-sdk/blob/c7e270aae43a6e9bcc8723d27b85c680ab38e156/openhands-sdk/openhands/sdk/security/confirmation_policy.py)：Never/Always/Risky 规则。
- [security analyzer](https://github.com/OpenHands/software-agent-sdk/blob/c7e270aae43a6e9bcc8723d27b85c680ab38e156/openhands-sdk/openhands/sdk/security/analyzer.py)：风险分析接口。

## 测试证据

- [agent tool recovery](https://github.com/OpenHands/software-agent-sdk/blob/c7e270aae43a6e9bcc8723d27b85c680ab38e156/tests/sdk/agent/test_tool_call_recovery.py)：损坏/不完整工具调用恢复。
- [confirmation mode](https://github.com/OpenHands/software-agent-sdk/blob/c7e270aae43a6e9bcc8723d27b85c680ab38e156/tests/sdk/conversation/local/test_confirmation_mode.py)：等待与拒绝。
- [interrupt](https://github.com/OpenHands/software-agent-sdk/blob/c7e270aae43a6e9bcc8723d27b85c680ab38e156/tests/sdk/conversation/test_interrupt.py)：异步取消。
- [event tree](https://github.com/OpenHands/software-agent-sdk/blob/c7e270aae43a6e9bcc8723d27b85c680ab38e156/tests/sdk/conversation/test_event_tree.py)：分支和 parent。
- [fork](https://github.com/OpenHands/software-agent-sdk/blob/c7e270aae43a6e9bcc8723d27b85c680ab38e156/tests/sdk/conversation/local/test_fork.py)：会话 fork。
- [condenser atomicity](https://github.com/OpenHands/software-agent-sdk/blob/c7e270aae43a6e9bcc8723d27b85c680ab38e156/tests/sdk/context/view/test_view_condensation_batch_atomicity.py)：压缩批次原子性。
- [security integration](https://github.com/OpenHands/software-agent-sdk/blob/c7e270aae43a6e9bcc8723d27b85c680ab38e156/tests/sdk/agent/test_security_policy_integration.py)：风险与确认组合。
- [lease contention](https://github.com/OpenHands/software-agent-sdk/blob/c7e270aae43a6e9bcc8723d27b85c680ab38e156/tests/agent_server/stress/test_lease_contention.py)：并发 writer。
- [WebSocket reconnect storm](https://github.com/OpenHands/software-agent-sdk/blob/c7e270aae43a6e9bcc8723d27b85c680ab38e156/tests/agent_server/stress/test_websocket_reconnect_storm.py)：重连压力。
- [Docker workspace](https://github.com/OpenHands/software-agent-sdk/blob/c7e270aae43a6e9bcc8723d27b85c680ab38e156/tests/workspace/test_docker_workspace.py)：容器 lifecycle。
- [Canvas mock LLM E2E](https://github.com/OpenHands/OpenHands/blob/4470813ce58f5ac384e3d367d34518e10106526b/tests/e2e/mock-llm/conversations/mock-llm-conversation.spec.ts)：端到端对话。
- [Canvas event store test](https://github.com/OpenHands/OpenHands/blob/4470813ce58f5ac384e3d367d34518e10106526b/__tests__/stores/use-event-store.test.ts)：前端事件去重/隔离。

## 边界与限制

- `OpenHands/OpenHands` 当前主线是 Agent Canvas；旧 Python monolith 的历史目录不能作为 1.41 runtime 事实。
- Agent Server README 明确是轻量本地存储入口，不等于生产级多租户 control plane。
- LocalWorkspace 是宿主执行；只有隔离配置经逃逸测试后才能声称 sandbox。
- ConfirmationPolicy 与 SecurityAnalyzer 提供决策/提示，不构成 OS 强制边界。
- EventLog 的本地文件锁不可靠跨 NFS；生产副本需要独立协调存储。
- OpenHands Cloud 的内部调度、账单、企业策略和私有 eval 基础设施不在公开证据内。

## 复核方法

1. `git ls-remote` 验证两个 commit 可达。
2. 检查所有源码 URL 都含 40 位 commit。
3. 重读四个 `pyproject.toml` 和 Canvas `package.json`，不要混用版本。
4. 对滚动文档执行 HTTP 检查并记录日期。
5. 用测试复核 loop、event tree、confirmation、interrupt、lease 和 workspace。
6. 升级时新建证据快照；兼容差异写迁移，不静默重写事实。
