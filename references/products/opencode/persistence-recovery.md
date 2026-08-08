# OpenCode-like 持久化与恢复

## 目录

- [真源与 projection](#真源与-projection)
- [schema](#schema)
- [事务边界](#事务边界)
- [恢复算法](#恢复算法)
- [压缩与回滚](#压缩与回滚)
- [迁移](#迁移)
- [备份与清理](#备份与清理)
- [故障 oracle](#故障-oracle)

## 真源与 projection

固定基线的 SQLite 同时保存 v1 session/message/part 表、v2 durable event/event_sequence、session_message/session_input/context_epoch projection。蒸馏实现不要让这些都成为可写真源。

推荐：durable event + input inbox 是 canonical；session/message/tool/todo/usage 是事务 projector；file snapshot/artifact 是内容寻址外部对象。runnable 可先以 normalized tables 为真源，但每次转移仍要 append audit event 并定义唯一写路径。

## schema

最低表：

```text
session(id, project_id, workspace_id, parent_id, directory, title,
        agent, model_json, status, terminal_json, created_at, updated_at)
event(id, aggregate_id, seq, type, version, data_json, created_at)
event_sequence(aggregate_id, seq, owner_id, epoch)
session_input(id, session_id, prompt_json, delivery, admitted_seq,
              promoted_seq, created_at)
message(id, session_id, seq, type, data_json, created_at)
tool_intent(id, session_id, message_id, call_id, input_hash, state,
            receipt_json, created_at, updated_at)
permission_request(id, session_id, data_json, state, reply_json)
context_epoch(session_id, baseline, snapshot_json, baseline_seq)
artifact(id, sha256, mime, size, path, created_at)
migration(version, checksum, applied_at)
```

唯一索引：`event(aggregate_id,seq)`、`session_input(session_id,admitted_seq/promoted_seq)`、`message(session_id,seq)`、`tool_intent(session_id,call_id)`。

## 事务边界

发布 durable event 时在一个 SQLite transaction 内：锁/读取 aggregate seq → 验 owner/epoch → 插 event(seq+1) → 执行同步 projector → 更新 sequence → commit。commit 后才送 PubSub/SSE/share subscriber。

tool 执行跨数据库与外部副作用，不能假装单事务。采用 intent/receipt：

1. 事务写 `prepared` intent；
2. 执行带 idempotency key 的副作用；
3. 事务写 receipt + tool ended event；
4. broadcast。

本地不可查询命令在 crash 后标 `unknown/interrupted`；文件工具用 before/after hash 和 journal reconcile。

## 恢复算法

启动时：

1. 完成 SQLite integrity check、schema checksum 和迁移；
2. 找 status 非 terminal 或有 pending input 的 session；
3. 读取 event 从 projection watermark 后重放，检测 gap/version；
4. 对 prepared/running tool 查询 receipt 或检查文件/process；
5. completed receipt 只补事件，不重跑；unknown 标 needs-reconciliation；
6. pending permission 恢复或按 restart policy reject；
7. PTY/process 无法重新附着则标 exited/interrupted；
8. 恢复 session drain，并从 inbox 下一条开始。

client resume 不驱动恢复，只订阅 server 已恢复状态。重复 prompt id 返回原 admitted receipt。

## 压缩与回滚

compaction summary 与 tail boundary 进入 message/event，原 event 不删除；旧 tool output 可在 projection 标 pruned，artifact 按 retention 保存。context epoch 保存 baseline seq 与 instruction snapshot，使重放知道何时引入新规则。

revert 保存目标 message/part、before snapshot、diff、current precondition。undo/redo 是新事件，不篡改旧历史。workspace 冲突时保持 session history并返回 conflict。

## 迁移

每个 migration 有递增版本、checksum、transaction/批次 checkpoint 和 down/read compatibility 说明。启动前备份数据库或 WAL checkpoint；migration 可重入，失败不启动写服务。

v1→v2 推荐顺序：冻结写 → 给旧 message/part 建 deterministic event/projection mapping → shadow replay 对比 → 双读不双写 → 切 canonical → 保留只读 adapter。未知旧 part 作为 opaque extension 保存，不能静默丢。

## 备份与清理

数据库、artifact、snapshot、share secret 分开 retention。删除 session 使用 FK/cascade + artifact reference count；删除 event 前必须有可验证 snapshot/归档策略。cache、LSP index、provider model list 可重建，不进入备份关键路径。

导出包含 schema version、session/messages、parts、events、artifact manifest，不包含 provider/MCP secret。import 验签/校验 ID 冲突，写入新 session namespace。

## 故障 oracle

- event 插入与 projector 中间 kill：事务全无或全有；
- commit 后 broadcast 前 kill：重连从 seq 取到 event；
- tool effect 后 receipt 前 kill：不自动重复，进入 reconcile；
- projection 删除：由 event 重建 hash 相同；
- compaction 中断：旧上下文仍可读；
- migration 每批 kill：重启幂等，旧 DB 有备份；
- WAL/DB 损坏：只读诊断/恢复，不新建空库冒充成功；
- duplicate event/prompt/reply：唯一约束保证幂等；
- share queue crash：本地终态不受影响，恢复后按 key 合并。

固定 SQL/event 源码见 [sources.md](sources.md)；推荐 canonical 与 exactly-once reconciliation 是 `inference`。
