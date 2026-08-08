# Deep Agents 差量配方

## 目录

- [基线模块](#基线模块)
- [蓝图 Overlay](#蓝图-overlay)
- [分析标签与 canonical 映射](#分析标签与-canonical-映射)
- [四等级增量](#四等级增量)
- [直接升级](#直接升级)
- [配方验收集](#配方验收集)

本页只写相对共享 35 模块的产品差量。通用实现合同见 [knowledge/index](../../knowledge/index.md)，四等级与原位升级见 [levels](../../levels.md)。

## 基线模块

所有等级继承：`agent-loop`、`model-adapter`、`protocol-events`、`context-engine`、`tool-runtime`、`workspace`、`filesystem`、`permission-policy`、`state-persistence`、`testing`、`reliability`。

Deep Agents 配方通常还选择：`planning`、`middleware-hooks`、`mcp`、`skills-plugins`、`subagents`、`rag-index`、`long-term-memory`、`sandbox`、`shell-process`、`observability`、`evals`，以及请求表面对应的 `cli-tui`、`ide` 或 `desktop-web`。本页不复制这些模块的通用全文。

## 蓝图 Overlay

| 最低等级 | canonical capability ID | Oracle |
|---|---|---|
| runnable | `middleware.harness-stack` | 栈顺序、替换和保护测试 |
| runnable | `planning.todo` | 默认无 Todo，opt-in 后 revision 测试 |
| runnable | `filesystem.backend` | backend conformance |
| usable | `subagents.isolated` | message/private/state isolation |
| usable | `permissions.hitl` | deny/interrupt/resume |
| usable | `skills.loading` | discovery/override/trust |
| usable | `memory.cross-session` | Store namespace 跨 thread |
| productive | `rag.pipeline` | retrieval/citation/injection |
| productive | `fault-tolerance.replay` | killpoint/receipt/replay |
| productive | `frontend.streaming` | snapshot + event projection |
| polished | `backend.sandbox` | escape/network/secret/limit |
| polished | `backend.remote` | lease/retry/provider migration |
| polished | `service.production` | tenant/HA/backup/SLO |
| polished | `profiles.managed-permissions` | ceiling/signature/rollback |

逐项可执行 oracle 见 [acceptance-tests.md](acceptance-tests.md)。`rag.pipeline` 和 polished 四项是复刻配方差量，不冒充 0.7.5 core 默认内置。

## 分析标签与 canonical 映射

下表的 `deepagents.*` 仅用于文档内聚合分析，**不是 Blueprint capability ID，禁止写入 Blueprint**。生成器只写上一节 canonical ID；一个分析标签可映射多个 canonical ID。

| 分析标签（不得写入蓝图） | canonical ID | 共享模块 | Deep Agents 差量 |
|---|---|---|---|
| `deepagents.graph.composition` | `fault-tolerance.replay` | agent-loop, state-persistence | graph/reducer/checkpoint 组合长任务 |
| `deepagents.middleware.stack` | `middleware.harness-stack` | middleware-hooks | 预置能力按确定顺序组装 |
| `deepagents.todo` | `planning.todo` | planning | todo 是可恢复协作 item |
| `deepagents.backend.files` | `filesystem.backend`, `backend.sandbox`, `backend.remote` | workspace, filesystem, sandbox | backend 共享 logical URI |
| `deepagents.subagent.isolation` | `subagents.isolated` | subagents | child context/state 边界 |
| `deepagents.context.skills_memory` | `skills.loading`, `memory.cross-session`, `rag.pipeline` | context-engine, skills-plugins, rag-index, long-term-memory | 来源、scope、provenance 分层 |
| `deepagents.permissions.interrupt` | `permissions.hitl`, `profiles.managed-permissions` | permission-policy, state-persistence | durable approval 与 permission ceiling |
| `deepagents.frontend.events` | `frontend.streaming`, `service.production` | protocol-events, desktop-web/cli-tui | snapshot+events 与生产服务 |

## 四等级增量

| 等级 | 只增加的产品差量 | 验收 |
|---|---|---|
| `runnable` 能跑 | 单 graph agent；静态 tools；本地 backend；最小 middleware；Todo opt-in；结构化事件 | 完成读取→工具→写入→终止；Todo revision 可重放；取消和工具失败产生稳定终态 |
| `usable` 能用 | context budget/compaction；skills、memory；MCP；durable checkpoint/interrupt；单层 subagent；交互主表面 | 审批等待与进程重启后恢复；记忆不跨 scope；subagent 权限不超过父级；恢复不重复副作用 |
| `productive` 顺手 | 可组合 middleware；并行 subagents；RAG；fault-tolerant replay；typed stream；trace/eval；后台任务 | middleware 顺序和失败可诊断；并行写冲突被隔离；RAG 引用可验证；trace 串起父子 lineage |
| `polished` 好用 | 强 sandbox/网络/secret policy；remote backend；嵌套配额；协议协商；插件生命周期；迁移、SLO、发布 gate | 逃逸/外传测试通过；旧客户端可协商；断连/崩溃/迟到结果正确；恶意 skill/middleware 被隔离并可回滚 |

## 直接升级

`runnable -> polished` 可一次选择，但升级器按依赖拓扑执行：

1. state/event schema 与 reducer 兼容；
2. checkpoint、call id、幂等和 interrupt continuation；
3. backend logical URI 与 workspace migration；
4. permission + sandbox enforcement；
5. todo/context/middleware；
6. subagents、skills、RAG、memory；
7. remote backend、frontend negotiation、SLO 与发布 gate。

不得为高级等级另建一套 agent loop，亦不得让 frontend 直接读取 LangGraph 私有 state。每步完成后运行之前等级全部回归。

## 配方验收集

- **启动**：profile、model、middleware、tools、backend、permission 的解析结果可见且可追溯。
- **编辑**：长仓库任务用 todo 推进，patch、tool、artifact 与最终验证有 lineage。
- **委派**：父子 agent 上下文、预算、workspace 和权限隔离；取消向下传播。
- **受限动作**：审批展示规范化参数；deny/amend/expiry 均有黑盒测试。
- **恢复**：model stream、tool commit 前后、approval、subagent 和远程 backend 断线均可恢复或进入明确 `indeterminate`。
- **安全**：symlink、进程、网络、secret、恶意 tool/skill/middleware 输出覆盖。
- **体验**：任一 surface 断线后可由 snapshot+event sequence 重建 todo、graph、subagent、approval 与 artifact。

只有上述场景有可执行证据时，capability 才能标为 `verified`；官方文档存在但本地未验证的能力标为 `implemented-not-verified` 或 `deferred`。
