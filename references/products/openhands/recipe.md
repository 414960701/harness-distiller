# OpenHands 差量配方

## 目录

- [共享基线](#共享基线)
- [Canonical Overlay](#canonical-overlay)
- [产品特征映射](#产品特征映射)
- [四级增量](#四级增量)
- [实现顺序](#实现顺序)
- [直接升级](#直接升级)
- [证据状态](#证据状态)

本页只描述 OpenHands 相对共享 35 模块的差量。通用 agent loop、protocol、sandbox、context、workspace、persistence、UI 和交付规范见 [../../knowledge/index.md](../../knowledge/index.md) 与 [../../levels.md](../../levels.md)。

## 共享基线

所有等级沿用这些共享模块的边界：`agent-loop`、`model-adapter`、`protocol-events`、`context-engine`、`tool-runtime`、`workspace`、`filesystem`、`shell-process`、`permission-policy`、`state-persistence`、`testing` 和 `reliability`；具体 capability 仍按目标等级逐步启用，不把 usable 的完整持久化提前承诺给 runnable。

OpenHands 配方通常再选择：`middleware-hooks`、`mcp`、`skills-plugins`、`subagents`、`sandbox`、`browser-computer`、`observability`、`evals`、`desktop-web`、`cli-tui` 与 `deployment-update`。

## Canonical Overlay

| 最低等级 | canonical capability ID | 最小 oracle |
|---|---|---|
| runnable | `conversation.event-tree` | parent/leaf/navigate/replay |
| runnable | `tools.action-observation` | action/result 一一闭合 |
| runnable | `agent.parallel-actions` | 安全并行与确定合并 |
| runnable | `workspace.adapter` | local/fake conformance |
| usable | `context.condenser` | 原子摘要与 View 等价 |
| usable | `security.confirmation` | analyze/wait/approve/reject |
| usable | `server.remote-conversation` | REST/WS/resume/reconnect |
| usable | `surface.agent-canvas` | snapshot+events UI projection |
| productive | `runtime.container` | lifecycle/resource/isolation |
| productive | `browser.interaction` | structured state/tab/artifact |
| productive | `extensions.skills-plugins` | provenance/precedence/trust |
| productive | `subagents.child-conversation` | lineage/budget/workspace/取消 |
| polished | `runtime.remote-lease` | lease/fencing/receipt/failover |
| polished | `security.defense-in-depth` | path/process/network/secret |
| polished | `deployment.multi-tenant` | tenant isolation/migration/SLO |

逐项可执行 oracle 见 [acceptance-tests.md](acceptance-tests.md)。15 个 ID 必须原样写入 Blueprint 和 capability evidence，不得换成文档内部标签。

## 产品特征映射

| 产品特征 | canonical ID | 关键差量 |
|---|---|---|
| Conversation/EventLog | `conversation.event-tree` | event immutable，parent 分支，active leaf |
| Action/Observation | `tools.action-observation` | provider response 到 typed tool loop |
| ParallelToolExecutor | `agent.parallel-actions` | 并行执行、原序 append、Finish 截断 |
| Workspace family | `workspace.adapter`、`runtime.container`、`runtime.remote-lease` | local/container/remote 同协议 |
| Context View/Condenser | `context.condenser` | tool-loop 与 condensation 原子性 |
| Analyzer/Policy | `security.confirmation`、`security.defense-in-depth` | 决策和 enforcement 分离 |
| Agent Server | `server.remote-conversation` | API、WebSocket、history、confirmation |
| Agent Canvas | `surface.agent-canvas` | chat、terminal、browser、diff 投影 |
| Browser tool | `browser.interaction` | tab、structured state、screenshot |
| Skill/Plugin/MCP/Hook | `extensions.skills-plugins` | lazy load、source、merge、policy ceiling |
| Child conversation | `subagents.child-conversation` | 新 conversation、lineage、隔离 |
| 生产 control plane | `deployment.multi-tenant` | 不冒充公开 OSS 默认能力 |

## 四级增量

### runnable 能跑

Python SDK/headless；scripted model；Event tree Conversation；Action/Observation；Finish；安全可控的 action 并行；Local/Fake workspace；read/edit/terminal；pause/interrupt；JSONL trace。

此级明确标注 LocalWorkspace 是宿主执行。可在单进程文件存储中运行，但保留 offset、idempotency 和 workspace identity 字段。

### usable 能用

在同一 loop 上增加 View properties、LLM condenser、persistent state、confirmation/security analyzer、Agent Server、REST/WebSocket、历史分页和最小 Canvas。

Canvas 至少有 conversation、chat/tool cards、status/stop、confirmation、files/diff/terminal；断线可从 snapshot+events 恢复。

### productive 顺手

增加 Docker/container runtime、browser、skills/plugins/hooks、planning、child conversations、observability 和 eval regression；MCP 已在 usable 通过共享 `tools.mcp` 启用，此级只增加扩展治理与组合优化。

并行工具按资源锁；父子会话有 lineage、budget、workspace mode 和取消；浏览器与 terminal 绑定 runtime identity。

### polished 好用

增加远程 runtime control plane、lease/fencing/receipt、强 sandbox、network/secret policy、签名配置、多租户授权、备份迁移、SLO、容量和发布门禁。

只有逃逸、外传、旧 writer、跨租户、killpoint 和恢复测试通过才能使用 polished 标签。

## 实现顺序

1. 定义 Event/Action/Observation JSON Schema 和 golden fixtures。
2. 实现 append-only EventRepository、active branch 与 View property tests。
3. 用 scripted model 跑 Agent/Conversation 垂直切片。
4. 接入 Fake/Local Workspace，完成 cancel、timeout 和 receipt。
5. 增加 condenser 与持久化恢复。
6. 增加 security analyzer、confirmation、hooks。
7. 以同一 protocol 暴露 Agent Server/WebSocket。
8. Canvas 从 snapshot+events 投影，不导入 runtime private state。
9. 增加 container/browser/extensions/subagents。
10. 最后加入 remote control plane、fencing 和多租户。

每一步运行此前全部等级回归；不得先做完整 Canvas 再补 runtime。

## 直接升级

用户可以从 runnable 直接选择 polished，但升级器按依赖拓扑原位执行：

1. schema/version/offset/idempotency 字段兼容；
2. EventLog 和 state 迁移；
3. confirmation 与 executor enforcement 分离；
4. Local workspace 替换为 container/remote adapter；
5. server/Canvas 消费同一事件；
6. skills/plugins/browser/subagents 保持 capability snapshot；
7. lease/fencing/receipt 和 tenant namespace；
8. 安全、迁移、SLO 和发布门禁。

不得创建第二套 polished agent loop，不得删除 runnable 事件，不得静默把 local conversation 搬到不同 workspace。

## 证据状态

- 有实现路径和 oracle 证据：`verified`；
- 已实现但未执行验收：`implemented-not-verified`；
- 仅存在官方文档或计划：`deferred`；
- OSS 之外的生产补强必须标 `design-synthesis`。

`deployment.multi-tenant` 和 polished 安全/control-plane 是复刻产品所需设计综合，不声称 OpenHands 公开仓库默认交付相同服务。
