# LangGraph 差量配方

## 目录

- [基线模块](#基线模块)
- [蓝图 Overlay](#蓝图-overlay)
- [事实与设计综合](#事实与设计综合)
- [四等级增量](#四等级增量)
- [直接升级](#直接升级)
- [交付规则](#交付规则)

本页只写相对共享 35 模块的产品差量。通用合同见 [knowledge/index](../../knowledge/index.md)，四等级与原位升级见 [levels](../../levels.md)。

## 基线模块

所有等级继承：`agent-loop`、`protocol-events`、`context-engine`、`state-persistence`、`reliability`、`testing`、`observability`。

生成完整 coding harness 时再选：`model-adapter`、`tool-runtime`、`workspace`、`filesystem`、`shell-process`、`permission-policy`、`sandbox`、`subagents`、`long-term-memory`、`cli-tui`、`desktop-web`。这些上层模块不能反标为 LangGraph core。

## 蓝图 Overlay

| 最低等级 | canonical capability ID | Oracle |
|---|---|---|
| runnable | `graph.state-reducers` | reducer/concurrent-update conformance |
| runnable | `runtime.pregel-supersteps` | BSP visibility/task scheduling |
| runnable | `control.command-send` | update/goto/Send/parent routing |
| runnable | `streaming.modes` | values/updates/messages/custom envelopes |
| usable | `persistence.checkpoints` | thread/state/history/namespace |
| usable | `interrupts.durable-resume` | pause/restart/resume/conflict |
| usable | `subgraphs.composition` | shared/private state and child lineage |
| usable | `store.cross-thread-memory` | namespace and tenant scope |
| productive | `durability.configurable` | sync/async/exit killpoints |
| productive | `recovery.pending-writes` | partial-success replay |
| productive | `time-travel.branching` | replay/fork/history preservation |
| productive | `observability.task-streams` | task/checkpoint/subgraph projection |
| polished | `checkpoint.production-store` | CAS/encryption/migration/backup |
| polished | `frontend.snapshot-event-projection` | reconnect/gap/dedup/hash |
| polished | `deployment.operational-boundary` | tenant/HA/SLO/platform separation |

逐项 executable oracle 见 [acceptance-tests.md](acceptance-tests.md)。

## 事实与设计综合

| capability | 上游 core 事实 | 复刻增强 |
|---|---|---|
| reducers/supersteps/Command/stream | Python/JS 固定源码与 tests | 规范 event adapter |
| checkpoints/interrupt/subgraph/Store | core protocol 与内存/外部 saver | tenant、CAS、approval policy |
| durability/pending writes/time travel | Python core 事实 | external effect receipt |
| task streams | core stream modes | snapshot + sequence projection |
| production store | saver protocol/独立 adapters | backup、encryption、migration gate |
| frontend/deployment | Studio/Deployment 产品文档 | 自建 UI/service 合同 |

不得把最后三项的增强部分冒充开源 core 默认实现。

## 四等级增量

| 等级 | 只增加的产品差量 | 交付判据 |
|---|---|---|
| `runnable` 能跑 | typed state；channel/reducer；StateGraph；Pregel superstep；Command/Send；基础 stream | fan-out/join 确定；同一步隔离；冲突写失败；取消/错误有终态 |
| `usable` 能用 | checkpointer；thread/history；interrupt/resume；subgraph；Store memory | 重启后恢复；重复 resume 幂等；child namespace 正确；跨 tenant memory 拒绝 |
| `productive` 顺手 | durability；pending writes；time travel；task/checkpoint stream；trace | killpoint state/effect digest 正确；fork 保留旧历史；projection 可诊断 |
| `polished` 好用 | 生产 saver；统一前端协议；租户/HA/backup/SLO；平台边界 | 故障转移、迁移、恢复演练、断线投影和安全门禁全通过 |

## 直接升级

可从 `runnable` 直接选择 `polished`，但仍在同一 graph runtime 上按依赖拓扑升级：

1. 冻结 graph/state/channel/reducer schema；
2. 稳定 task/path/checkpoint namespace 身份；
3. 加 checkpointer、pending writes 和 interrupt continuation；
4. 加 Store 与子图 scope；
5. 加 durability、time travel、stream/event adapter；
6. 加生产 saver、CAS、加密、迁移、backup；
7. 加前端 projection、tenant/HA/SLO 与发布门禁。

每一步回归此前等级。不得为 polished 新建一套不兼容 agent loop，也不得把 memory checkpointer 替换成数据库后便声称生产就绪。

## 交付规则

- Python 主实现应对齐 `1.2.10` 行为；JS 实现对齐相同公开语义而非私有字段。
- provider-neutral scripted nodes 是默认测试夹具，不要求付费模型。
- graph、channel、checkpoint、event schema 全部进入 artifact。
- 外部 tool/workspace effect 只有 receipt/reconcile 通过才标 verified。
- 产品 UI 只消费规范 snapshot/events。
- capability 报告逐项给 implementation path、test path、status 和 evidence digest。
- 所有闭源/托管行为明确写“平台边界”或“设计综合”。
