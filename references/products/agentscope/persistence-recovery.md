# AgentScope 状态、持久化与恢复

## 目录

事实边界 → schema → AgentState → 事务 → tool effect → 恢复 → bus → team/channel → workspace → 迁移 → 保留 → 故障注入。

## 事实与补充设计

固定源码 `AgentState` 包含 session、summary、context、reply context、permission/tool/task/middleware context，并带旧 reply 字段迁移；app 层存在 storage、message bus、session run lock、event log、cancel/inbox/wakeup 与 Redis 实现。以下关系库 schema、事务和恢复算法是 `inference`，用于让生成物达到可靠 harness，而非宣称官方逐表使用。

## 持久 schema

```sql
agents(id, owner_id, definition_json, definition_version, created_at, updated_at)
sessions(id, agent_id, owner_id, status, state_version, last_cursor,
         workspace_id, capability_hash, active_reply_id, created_at, updated_at)
replies(id, session_id, status, cur_iter, finished_reason, continuation_json,
        lease_owner, lease_until, started_at, ended_at)
items(id, session_id, reply_id, kind, payload_json, payload_hash, created_at)
events(id, session_id, reply_id, cursor, type, payload_json, causation_id,
       correlation_id, created_at, UNIQUE(session_id,cursor))
tool_calls(id, reply_id, name, args_json, args_hash, state, decision_id,
           execution_id, effect_state, result_item_id, UNIQUE(reply_id,id))
confirmations(id, tool_call_id, request_json, args_hash, status, resolution_json,
              expires_at, UNIQUE(tool_call_id))
checkpoints(id, session_id, reply_id, state_version, event_cursor, state_json,
            schema_version, created_at)
artifacts(id, owner_scope, uri, sha256, size, media_type, state, expires_at)
outbox(id, session_id, event_id, destination, state, attempts, next_attempt_at)
idempotency(actor_id, key, command_hash, result_ref, created_at, UNIQUE(actor_id,key))
```

可用文档库/KV 实现等价模型，但单 writer、unique constraint、CAS version、append order 与审计字段不能丢失。

## AgentState 序列化

Checkpoint 的 `state_json` 至少保存 `session_id/summary/context/reply_context/permission_context/tool_context/tasks_context/middleware_context`。不序列化打开的 socket、协程、SDK client 或明文 secret；这些由 adapter 在恢复时重建。Pydantic/class type 等运行时对象先转为版本化 JSON schema/ref。

## 单次状态事务

```text
BEGIN
  assert sessions.state_version == expected_version
  insert immutable items
  insert events with next per-session cursor
  update tool_call/reply/session projection
  insert outbox rows for channel/live notification
  sessions.state_version += 1; sessions.last_cursor = cursor
COMMIT
publish outbox asynchronously
```

event、projection 与 tool effect receipt 的提交顺序必须明确。UI publish 失败不回滚 agent 事实；outbox 重试按 event id 去重。

## 工具 exactly-once 边界

数据库只能保证调用记录一次，不能让任意外部副作用天然 exactly-once。执行前写 `prepared`，backend 接受幂等键后写 `started`，拿到 effect receipt 后原子写 `committed + result item/event`。崩溃时：

- `prepared`：可安全重新调度；
- `started` 且 backend 可查询：按 execution id reconcile；
- `started` 且不可查询：标 `effect_unknown`，等待人工决定；
- `committed`：只重放 result，不执行；
- read-only 且参数 hash 不变：可按策略重试。

## Reply 恢复算法

```text
recover(session_id):
  acquire fenced session lease
  load newest valid checkpoint
  replay events after checkpoint cursor
  verify projection hashes and terminal count
  reconcile prepared/started tool calls
  rebuild model/tool/MCP/workspace adapters from refs
  if waiting_confirmation: re-emit same request id
  elif waiting_external: await same continuation
  elif running and no unsafe unknown effect: resume at durable boundary
  elif terminal: expose snapshot only
  else: mark needs_attention with recovery report
```

恢复不能把旧 partial model delta 当新 prompt 重发，除非 model adapter 有明确 continuation；安全做法是关闭失败 model call，保存其 partial item，再开启新 attempt。

## MessageBus 与分布式 state

Bus 的 queue/log/pubsub/lock/registry 是协调原语，不是唯一事实源。durable event/state 先提交 storage，再通过 outbox/bus 通知。session lock 需要 fencing token，单纯 TTL 锁可能在长工具运行时产生双 writer。Redis 断线时暂停新 writer；不能无条件降级本地锁继续同一共享 session。

## Team、Channel 与投影

每个 worker session 独立 event stream；leader feed 使用 projector 将选定事件镜像到 leader，镜像保存 source event id 并幂等。channel delivery 单独维护 `destination_message_id/status`，重发不改变 agent event。channel 输入以 provider event id 作为 idempotency key。

## Workspace 恢复

Session 只存 workspace ref/version/lease，不把运行容器本身序列化。Manager 恢复时 `reconnect(workspace_id, instance_ref)`；失败后只有在策略允许且没有未知副作用时新建。新 workspace 必须重新挂载显式资源并生成新 capability hash，不能假设旧临时文件仍在。

## 迁移

每个 checkpoint 有 `schema_version`。迁移必须纯函数、可重复、保留未知字段，并提供 backward fixture。参考源码把旧 top-level `reply_id/cur_iter` 迁入 `reply_context` 的做法；生成项目还需数据库 migration。升级顺序：停止新 writer→备份→schema expand→双读/回填→切换 writer→contract cleanup。

## 数据保留与删除

Event log、artifact、RAG source、LTM 和 trace 有不同 retention。删除用户数据时写 tombstone、撤销 credential/lease、清理 artifact/vector/memory 派生物；审计若依法保留则脱敏。压缩 summary 不得成为逃逸删除的隐藏副本。

## 故障注入

- 在 transaction commit 前后 kill process，验证单终态和 cursor 连续。
- tool 外部成功但 result 未提交时 kill，验证 reconcile/unknown 分支。
- Redis lock 过期且旧 worker 恢复，fencing 拒绝旧写。
- outbox 重发、channel 429、WebSocket 重连不重复 item。
- checkpoint 损坏时回退上一 checkpoint 并重放；全部损坏时 fail closed。
- schema N-1 fixture 可迁移，迁移二次执行结果不变。

## 恢复验收

任何自动恢复都必须给出 `recovered_from_cursor/reconciled_calls/new_lease_token/warnings`。无法证明副作用状态时不可继续自动规划；标记 needs_attention 比重复副作用更正确。
