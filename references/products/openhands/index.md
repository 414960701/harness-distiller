# OpenHands 产品蒸馏索引

## 产品定位

OpenHands 是以事件化 Conversation 为核心、可在本地或远程 Workspace 中执行软件任务，并由 Agent Canvas、CLI 或 SDK 驱动的开源软件 Agent 产品族。

当前实现必须按两个仓库理解：

- `OpenHands/OpenHands`：Agent Canvas Web/Electron 界面、前端状态投影、后端选择和产品体验；
- `OpenHands/software-agent-sdk`：Python SDK、Agent、Conversation、Event、Condenser、Tool、Workspace、Agent Server 和测试。

研究快照：

- status: implementation-grade researched
- retrieved: 2026-08-08
- Canvas commit: `4470813ce58f5ac384e3d367d34518e10106526b`
- SDK commit: `c7e270aae43a6e9bcc8723d27b85c680ab38e156`
- Canvas package: `@openhands/agent-canvas==1.12.0`
- SDK packages: `openhands-sdk/tools/workspace/agent-server==1.41.0`
- license: 两仓库均为 MIT

## 实现级阅读顺序

不要只读配方后生成一批 UI 组件。按下列顺序建立可测试垂直切片：

1. [product-contract.md](product-contract.md)：行为、边界、证据和非目标；
2. [architecture.md](architecture.md)：Canvas、SDK、Agent Server、Workspace 拓扑；
3. [protocol-state.md](protocol-state.md)：conversation/event/action/observation/state 协议；
4. [agent-loop.md](agent-loop.md)：初始化、采样、并行工具、确认、终止和取消；
5. [context-tools.md](context-tools.md)：View、Condenser、Prompt、Tool、MCP、Skill、Plugin；
6. [workspace-execution.md](workspace-execution.md)：Local、Docker、Cloud、远程执行、终端和浏览器；
7. [safety-runtime.md](safety-runtime.md)：风险分析、确认策略、secret、hook 与强制隔离；
8. [persistence-recovery.md](persistence-recovery.md)：EventLog、状态、分支、lease、恢复和迁移；
9. [experience.md](experience.md)：Web、Electron、CLI、SDK 的事件投影；
10. [recipe.md](recipe.md)：相对共享知识的产品差量和四级升级；
11. [acceptance-tests.md](acceptance-tests.md)：15 个 capability 的可执行 oracle；
12. [sources.md](sources.md)：固定 commit 源码、测试和官方文档地图。

## 一句话架构

Canvas 只提交意图和投影事件；Agent Server 管理远程 Conversation 与订阅；Conversation 以事件树和显式状态串行推进；Agent 将 LLM response 归一化成 ActionEvent，执行工具后追加 ObservationEvent；Workspace adapter 决定命令实际发生在哪里。

## 必守边界

- `LocalWorkspace` 直接操作宿主机，不是 sandbox。
- ConfirmationPolicy 决定是否等待用户，不能替代容器或远程 runtime enforcement。
- Event 是事实记录；View、Canvas store、对话卡片都是可重建投影。
- SDK 的 `ConversationExecutionStatus` 不等于共享协议的 Thread/Turn 状态；adapter 必须显式映射。
- 当前 EventLog 是逐文件 append 和本地锁；生产化多副本必须加 durable store、lease 和 fencing。
- Canvas 当前源码证明界面行为，不证明 OpenHands Cloud 的私有编排或多租户实现。

## 最小生成仓库

- `packages/protocol`：事件、命令、错误、版本与生成客户端；
- `packages/sdk`：Agent、Conversation、Context、Condenser、Tool registry；
- `services/agent-server`：REST/WebSocket、lease、鉴权、订阅和持久化；
- `executors/workspace`：local、container、remote adapter；
- `apps/canvas`：chat、事件卡、terminal、browser、diff、settings；
- `apps/cli`：交互和 headless JSONL；
- `tests/contracts`：scripted model、workspace fixture、重放、安全和 E2E。

共享模块索引见 [../../knowledge/index.md](../../knowledge/index.md)，实现时优先引用共享规范，不在本目录复制通用理论。
