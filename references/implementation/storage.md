# 状态存储、事务与恢复

## 推荐表

```sql
threads(id PK, status, parent_thread_id, forked_from_turn_id, workspace_id,
        recipe, level, config_snapshot_id, revision, created_at, updated_at)
turns(id PK, thread_id FK, status, stop_reason, context_snapshot_id,
      tool_catalog_version, budget_json, usage_json, error_json,
      started_at, ended_at, revision)
items(id PK, thread_id FK, turn_id FK, kind, status, payload_json,
      correlation_id, created_at, completed_at)
events(id PK, thread_id FK, turn_id FK, sequence, type, payload_json,
       causation_id, correlation_id, schema_version, created_at,
       UNIQUE(thread_id, sequence))
tool_calls(id PK, turn_id FK, tool_name, tool_version, args_json, args_hash,
           idempotency_key, status, result_item_id, revision)
approvals(id PK, tool_call_id FK, action_hash, status, scope_json,
          policy_version, expires_at, resolved_at)
artifacts(id PK, uri, sha256, mime, size, storage_key, created_by_call_id,
          retention, created_at)
checkpoints(id PK, thread_id FK, turn_id FK, event_sequence,
            workspace_snapshot_ref, context_snapshot_ref, created_at)
outbox(id PK, aggregate_id, event_json, published_at, attempts)
```

字段类型按数据库调整，但语义和唯一约束保留。

## 事务边界

一次领域变化与对应 event/outbox 在同一事务提交。例如 tool result：更新 tool_calls 终态、插入 tool_result item、追加 event、写 outbox 必须原子完成。

执行外部副作用不能和数据库共享事务，采用：

1. 持久 execution intent 与 idempotency key；
2. executor 执行并产生 receipt；
3. 持久 receipt/result；
4. 恢复时查询 receipt 或标 indeterminate。

## 单写者

同一 thread/turn 使用进程内 mutex、数据库 lease 或 actor mailbox 保证单写者。lease 包含 owner、expiry、fencing token；过期 worker 的迟到写被 fencing token 拒绝。

## Snapshot 与 projection

事件是事实；snapshot 加速读取。snapshot 记录最后 sequence 和 schema version。重建时加载 snapshot，再应用后续 events。发现 gap 或 hash 不一致时丢弃 snapshot 重新回放。

## Fork / rollback / archive

- fork 保存 parent_thread_id 与边界 turn/sequence；artifact 可引用共享不可变 blob；
- rollback 追加 marker/新 projection，不物理删除历史；
- archive 改状态和保留策略；delete 是独立、权限更高的操作；
- workspace rollback 与 conversation rollback 分开选择。

## Migration

每次迁移有版本、forward、必要时 rollback/compat reader、fixture 和幂等保护。事件 schema 的破坏性升级使用 upcaster 或保留旧 reducer；不得批量覆写原始事件而无备份。

## 恢复算法

启动时：

1. 完成/回滚未完成数据库迁移；
2. 发布未发送 outbox；
3. 查找无终态 turn 和过期 lease；
4. 回放到最新合法 sequence；
5. 对 running model request 可重新请求；
6. 对 running tool 查询 receipt；
7. 对 PTY/background process 查询 executor registry；
8. 无法证明结果的外部动作标 indeterminate 并请求用户决定。

## 验收

- 在每个事务步骤 kill 进程并重启；
- 重复投递同 command/event；
- 数据库满、磁盘满、artifact 写成功但事务失败；
- 旧 schema fixture 升级、降级读取；
- 两 worker 争抢同 turn；
- fork 后父子独立继续；
- archive/unarchive 不丢事件；
- snapshot 损坏后完整回放得到相同 projection。

