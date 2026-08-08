# Deep Agents Persistence 与 Recovery 规范

## 目录

- [边界与事实](#边界与事实)
- [存储 Schema](#存储-schema)
- [事务边界](#事务边界)
- [Checkpoint 映射](#checkpoint-映射)
- [恢复算法](#恢复算法)
- [副作用去重](#副作用去重)
- [迁移](#迁移)
- [四级升级](#四级升级)
- [故障矩阵](#故障矩阵)
- [验收](#验收)

## 边界与事实

Deep Agents 将 `checkpointer` 与 `store` 传给 LangChain `create_agent`；checkpoint 的调度、pending writes 和 interrupt resume 属于 LangGraph。

需要区分：

- StateBackend：文件在 agent state，随 thread checkpoint 才能 durable；
- StoreBackend：文件在 LangGraph BaseStore，可跨 thread；
- Checkpointer：保存 graph superstep state 与 pending writes；
- Event ledger：本复刻对 frontend 和审计提供的外部事实日志；
- Artifact store：大对象，不能内联到每个 checkpoint；
- Remote async task：状态在远端 server，本地只保存 thread/run reference。

## 存储 Schema

```sql
CREATE TABLE threads (
  thread_id TEXT PRIMARY KEY,
  tenant_id TEXT NOT NULL,
  schema_version INTEGER NOT NULL,
  head_sequence INTEGER NOT NULL,
  checkpoint_ref TEXT,
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL
);

CREATE TABLE turns (
  turn_id TEXT PRIMARY KEY,
  thread_id TEXT NOT NULL,
  status TEXT NOT NULL,
  capability_snapshot_json TEXT NOT NULL,
  started_at TEXT NOT NULL,
  finished_at TEXT
);

CREATE TABLE events (
  event_id TEXT PRIMARY KEY,
  thread_id TEXT NOT NULL,
  turn_id TEXT NOT NULL,
  sequence INTEGER NOT NULL,
  type TEXT NOT NULL,
  payload_json TEXT NOT NULL,
  UNIQUE(thread_id, sequence)
);

CREATE TABLE calls (
  call_id TEXT PRIMARY KEY,
  turn_id TEXT NOT NULL,
  args_hash TEXT NOT NULL,
  state TEXT NOT NULL,
  idempotency_key TEXT,
  receipt_json TEXT
);
```

还需 approvals、artifacts、command_dedup、schema_migrations 和 remote_tasks 表。

## 事务边界

以下写入必须同一数据库事务：

1. turn/item 当前状态；
2. 新 event 与 sequence；
3. command_id dedup 结果；
4. pending call/approval ledger；
5. thread head_sequence。

Checkpoint saver 与外部 event ledger 可能不是同一数据库，因此使用 outbox：

```text
state transition transaction
  -> write event + outbox
  -> commit
  -> publisher delivers event
  -> mark outbox delivered
```

不要先发布 UI 事件后才提交状态。

## Checkpoint 映射

LangGraph checkpoint key 包含 `thread_id`，可选 `checkpoint_ns/checkpoint_id`。

每个 checkpoint 保存 channel values、channel versions、versions_seen、pending tasks/writes 等 runtime 信息。

复刻映射：

| LangGraph 概念 | Harness 概念 | 注意 |
|---|---|---|
| thread_id | Thread | 必须租户隔离 |
| checkpoint_id | RecoveryPoint | 不等于 turn_id |
| checkpoint_ns | subgraph namespace | 不直接暴露成用户 path |
| pending writes | PendingCall/transition | 不保证外部系统 exactly-once |
| Interrupt | Approval continuation | resume 必须使用同 thread |
| Command(resume) | approval.resolve command | command_id 去重 |

DeepAgentState messages 使用 `DeltaChannel(... snapshot_frequency=50)`，目的是避免 checkpoint 随完整消息历史 O(N²) 增长；这是存储优化，不改变外部消息事实账本。

## 恢复算法

```python
def recover(thread_id):
    acquire_thread_lease(thread_id)
    cp = checkpointer.get_latest(thread_id)
    ledger = load_pending_calls_and_approvals(thread_id)
    state = replay_checkpoint(cp)
    for call in ledger:
        if call.state == "committed":
            inject_receipt_if_missing(state, call)
        elif call.state == "dispatched":
            status = reconcile_external(call)
            if status.known:
                persist_reconciliation(call, status)
            else:
                mark_indeterminate(call)
        elif call.state in {"requested", "policy_decided"}:
            safely_redispatch_or_cancel(call)
    restore_interrupts(state)
    replay_outbox()
    return state
```

恢复必须使用 checkpoint 的 capability snapshot；不能用进程启动时的新 tool/middleware 配置继续旧 turn。

## 副作用去重

| 副作用 | 策略 |
|---|---|
| read/list/search | 同 call ID 可安全重试 |
| state file write | optimistic version + deterministic update |
| local file patch | before digest + after digest + journal |
| shell command | 默认不可安全重放；使用 sandbox receipt/显式幂等脚本 |
| HTTP POST | idempotency key 或查询业务资源 |
| remote subagent start | task/thread ID 作为幂等身份 |
| approval resolution | command_id + expected_sequence |
| artifact upload | content digest 去重 |

无法确定的外部动作进入 `indeterminate`，禁止让模型自行猜“可能成功”。

## 迁移

迁移规则：

- schema 版本只单调上升；
- 先支持双读，再 backfill，再切换写格式；
- event 原文不可原地改写，必要时追加 correction event；
- checkpoint serializer 升级前做真实旧数据恢复测试；
- backend logical URI 迁移维护 redirect/alias；
- message reducer 变更使用 golden replay；
- skill/profile/middleware 版本保留在旧 turn snapshot；
- remote task 的 provider ID 不在迁移中重新创建。

回滚时仅回滚应用读写路径，不逆向删除已写的新字段或事件。

## 四级升级

| 等级 | 持久化增量 | 恢复保证 |
|---|---|---|
| `runnable` | 进程内 state、事件 ID | 仅同进程重试 |
| `usable` | durable checkpointer、SQLite/DB ledger、approval resume | 进程重启恢复 |
| `productive` | pending-call receipt、outbox、artifact、async task reconcile | 故障点不重复提交 |
| `polished` | HA lease、跨区备份、在线迁移、retention/SLO | 多实例与灾备演练 |

## 故障矩阵

| 故障点 | 恢复动作 | Oracle |
|---|---|---|
| model call 前 | 重发同 step | 无重复消息 |
| model stream 中 | 丢弃未完成 delta 或按 provider resume | 仅一个 completed message |
| tool dispatch 前 | 同 call ID 调度 | 一次副作用 |
| tool dispatch 后无 receipt | reconcile；未知则 indeterminate | 不盲重试 |
| receipt 后 checkpoint 前 | 从 call ledger 注入结果 | 不二次执行 |
| interrupt 后 | 返回相同 approval | request ID 不变 |
| approval resolve 后崩溃 | command dedup 返回原结果 | 不重复 resume |
| summary history 写失败 | 保留原 messages 或失败关闭 | 不丢上下文 |
| async start 后本地崩溃 | 通过保存的 remote thread 查询 | 不新建第二 task |
| outbox 发布前崩溃 | 重启发布 | event 至少一次、投影去重 |

## 验收

1. 在每个故障点 kill 进程，恢复后的 final/hash 与无故障基线一致。
2. 同一 approval.resolve 提交 100 次只有一次状态 transition。
3. 同一 external idempotency key 只产生一个业务对象。
4. snapshot + events 重建的投影与 live projection 一致。
5. DeltaChannel 的 message replace/remove/reset 在 checkpoint replay 后一致。
6. `thread_id` 缺失时 durable invoke 明确失败。
7. 不同 tenant 的同名 thread 无法互读。
8. StateBackend + checkpointer 重启后文件恢复；无 checkpointer 时明确不承诺。
9. StoreBackend 的 per-user/per-assistant/per-thread namespace 隔离通过。
10. remote async task 迟到结果不会覆盖 cancelled parent。
11. N-1 schema 备份能在 N 版本读取并完成一轮 turn。
12. migration 中断可安全续跑，计数、digest 和终态不变。
