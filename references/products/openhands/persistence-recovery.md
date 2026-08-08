# OpenHands-like 持久化与恢复规格

## 目录

- [存储模型](#存储模型)
- [Schema](#schema)
- [追加事务](#追加事务)
- [事件树与分支](#事件树与分支)
- [恢复算法](#恢复算法)
- [副作用与幂等](#副作用与幂等)
- [Lease 与多副本](#lease-与多副本)
- [迁移备份删除](#迁移备份删除)
- [故障注入](#故障注入)
- [实现检查](#实现检查)

## 存储模型

`公开事实`：SDK 使用 base state 加逐文件 EventLog；event id 唯一，parent 构成树，本地 FileStore lock 保护 append。Agent Server 另有 conversation lease。

`设计综合`：生产实现保留相同逻辑模型，但允许 SQLite/Postgres/object store：

- append-only `events` 是事实源；
- `conversation_state` 是可重建/可迁移快照；
- `conversation_index` 用于列表和搜索；
- `artifacts` content-addressed；
- `leases` 管 writer ownership；
- `outbox` 保证 event 发布；
- `receipts` 记录外部副作用。

## Schema

```sql
events(conversation_id, offset, event_id, parent_id, kind,
       schema_version, payload, payload_digest, created_at, writer_generation)
conversations(id, tenant_id, active_leaf_id, head_is_empty,
              status, workspace_identity, state_version, last_offset)
receipts(conversation_id, action_id, idempotency_key, phase,
         provider_receipt, result_digest, updated_at)
leases(conversation_id, owner_id, generation, expires_at)
outbox(conversation_id, offset, published_at, attempts)
```

唯一约束：`(conversation_id, offset)`、`event_id`、`(conversation_id,idempotency_key)`。parent 必须在同 conversation 存在，或是显式 root sentinel。

事件 payload 按 `kind + schema_version` 验证。严禁 pickle/任意 class import 作为 wire persistence。

## 追加事务

单个逻辑 append 原子执行：

1. 验证 lease generation 与 expected active leaf；
2. 分配 next offset；
3. 写 immutable event；
4. 更新 conversation head/status/stats；
5. 写 outbox；
6. commit；
7. 异步发布 WebSocket。

本地文件版先写 temp、fsync、rename，再写 base state；启动时 EventLog 可领先 state，恢复从 log 修正 projection。不能先通知 UI 再持久化 completed event。

同一 event/idempotency 重试返回原 offset；相同 key 不同 payload 返回 conflict。

## 事件树与分支

新 event 的 parent 默认为 active leaf。`navigate_to(event_id)` 只移动 HEAD 并记录 head event，不删除后代。

legacy event `parent_id=None`：index 0 为 root，之后按前一 index 连接。新格式使用显式 parent；`ROOT_PARENT_ID` 代表显式新 root。

`leaf_event_id=None` 同时可能表示旧会话未设置或用户刻意空 HEAD，因此持久化 `head_is_empty`。

Fork：读取父 active path 到选定 leaf，复制/引用 immutable history，创建新 conversation id 和独立 writer/workspace policy。父 conversation 不改变。

## 恢复算法

1. 验证 tenant、schema、checksum 和 workspace identity。
2. 获取新 lease generation。
3. 读取 snapshot/base state；损坏则从 events 重建可导出字段。
4. 扫描 event offset，发现 gap/duplicate/digest mismatch 即隔离并停止 writer。
5. 解析 parent graph，检查 missing parent/cycle。
6. 解析 active leaf/head_is_empty，重建 branch 与 View。
7. 检查 unmatched action、pending confirmation、running receipt 和 outbox。
8. 对可判定项补发事件；未知副作用标 `unknown_effect`。
9. 发布恢复后的 snapshot 与 last offset。
10. 只有检查通过才允许 run。

恢复不重新调用 condenser；使用已持久化 CondensationEvent。旧 tool spec 缺失时可显示历史，但继续运行需明确兼容 adapter 或拒绝。

## 副作用与幂等

Action lifecycle：`prepared -> dispatched -> committed|failed|unknown -> observed`。

- 文件 patch 用 expected digest 和 atomic rename；
- command 使用 action idempotency key，但通用 shell 本质非幂等；
- remote provider 返回 receipt，超时后 query-before-retry；
- confirmation 必须在 dispatch 前 durable；
- Observation 在 receipt committed 后写；
- event committed 但发布失败由 outbox 重发；
- Observation 重复发布由 event id 去重。

无法证明外部动作是否提交时，不自动执行第二次；向用户暴露 `unknown_effect` 与检查建议。

## Lease 与多副本

Lease 包含 owner、generation、expiry。续租使用 compare-and-swap；每次 event append、receipt commit 和 workspace mutation 都带 generation。

旧 writer 即使网络恢复也因 fencing token 过期失败。lease expiry 不等于立即重跑外部命令；新 writer先恢复 receipt。

SDK 本地 FIFO lock 解决线程公平，不解决多主机。File lock 在 NFS 上不可靠，生产不得仅依赖它。

## 迁移备份删除

- schema migration 有 from/to、checksum、dry-run 和 rollback plan；
- 先迁 snapshot/index，再按需 lazy-upcast immutable event；
- 保留 unknown fields 与原始 payload；
- old reader 遇新 required capability 明确拒绝；
- backup 同时覆盖 DB、artifacts、encryption metadata 和 workspace snapshot；
- restore 到隔离环境验证 projection digest；
- delete 先 tombstone/stop writer，再按 retention 删除 event/artifact/secret；
- fork 共享 artifact 时使用引用计数，避免父删除破坏子会话。

## 故障注入

Killpoints：event temp write、rename、state update、receipt before/after commit、outbox publish、lease renew、confirmation response、condenser commit、fork workspace、WebSocket ack。

每个 killpoint 重启后断言：event 无 gap、projection digest 稳定、单一终态、已确认副作用不重复、pending confirmation 可回答、old writer 被 fence。

损坏 fixture：truncated JSON、duplicate id、missing parent、cycle、unknown kind、old schema、artifact missing、wrong tenant/workspace identity。

## 实现检查

- schema、事务、恢复、迁移均有可执行测试。
- EventLog 是 append-first，UI store 可丢弃重建。
- navigate/fork 不改写旧 event。
- active leaf 与 deliberate empty head 可区分。
- committed 副作用有 receipt；unknown 不自动重试。
- lease generation 覆盖所有 mutation。
- backup restore 后 event/projection/artifact digest 一致。

协议字段见 [protocol-state.md](protocol-state.md)，产品 oracle 见 [acceptance-tests.md](acceptance-tests.md)。
