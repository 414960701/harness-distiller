# Codex-like 持久化、恢复与迁移

## 目录

1. 存储原则
2. 逻辑 schema
3. Append 事务
4. 快照与索引
5. 启动恢复
6. 副作用恢复
7. Fork 与 rollback
8. Schema 迁移
9. 保留、导出与删除
10. 故障注入与验收

## 存储原则

`公开事实`：公开实现包含 rollout、state SQLite、migration、recovery 和 app-server rollout 测试。
`设计综合`：以 append-only event/rollout 作为审计源，以 SQLite 等数据库作为查询索引和派生投影。
索引损坏时必须能由 rollout 重建；rollout 损坏时不能用旧索引伪装完整。
完成事件广播之前，对应 canonical state 必须 durable。
单 thread 默认单写者，通过数据库租约或进程锁防止双写。

## 逻辑 schema

```sql
threads(
  id primary key, created_at, updated_at, status,
  workspace_identity_json, config_digest,
  head_sequence, snapshot_sequence, schema_version
)

turns(
  id primary key, thread_id, ordinal, status,
  started_at, ended_at, terminal_error_json,
  input_item_id, final_item_id, budget_json
)

items(
  id primary key, thread_id, turn_id, sequence,
  type, status, canonical_json, content_hash,
  causation_id, created_at, completed_at
)

events(
  event_id primary key, thread_id, turn_id,
  sequence unique(thread_id, sequence), type,
  payload_json, causation_id, occurred_at, checksum
)

effects(
  idempotency_key primary key, call_id, tool_name,
  intent_json, state, receipt_json, updated_at
)

approvals(
  id primary key, thread_id, turn_id, call_id,
  request_json, state, resolution_json, expires_at
)

checkpoints(
  id primary key, thread_id, sequence,
  context_ref, workspace_ref, created_at, checksum
)

artifacts(
  hash primary key, size, mime, storage_ref,
  redaction_class, created_at, retention_until
)
```

实现可以拆表，但必须保留 id、顺序、终态、因果、checksum 和 schema version。
canonical JSON 序列化要稳定，避免 map 顺序造成 hash 漂移。

## Append 事务

推荐每个状态变化使用一笔本地事务：

1. 验证 actor 当前 `head_sequence`；
2. 分配下一 sequence 和 event id；
3. 追加 rollout frame：长度、版本、payload、checksum；
4. fsync 到配置要求的 durability；
5. 在数据库事务中 upsert item/turn 投影和 head；
6. commit 数据库；
7. 发布进程内 event；
8. 异步投递客户端。

如果 rollout 与 SQLite 无法原子提交，使用 write-ahead marker：`prepared -> rollout_appended -> indexed`。
崩溃后以 rollout 为准补索引；发现索引领先于 durable rollout 时回退索引。
同一 causation/idempotency key 的重复 append 返回既有 event，不产生新副作用。

## 快照与索引

快照是加速器，包含 thread 投影、最后 sequence、活跃计划、上下文头和待审批摘要。
快照不包含无法验证的运行中进程状态；进程需从 effect receipt 恢复。
创建快照时记录 rollout offset 和 checksum。
加载流程是 snapshot + `sequence > snapshot_sequence` 的事件。
快照生成可异步，但发布前必须确认 head 没被误标为快照已覆盖。
列表、搜索和最近 thread 使用索引，不扫描全部 rollout。

## 启动恢复

恢复算法：

```text
recover(thread):
  acquire_single_writer_lease(thread)
  scan rollout frames until last valid checksum
  quarantine partial trailing frame
  compare durable head with indexed head
  rebuild missing projections idempotently
  load latest valid snapshot and replay tail
  classify nonterminal turns/items/effects
  reconcile processes and remote leases
  close or resume according to recovery policy
  append recovery.completed report
```

尾部半写 frame 可以截到最后有效边界，但必须保存 quarantine 和诊断。
中部 checksum 失败视为严重损坏，不可静默跳过并继续拼接。
恢复过程本身可重入；恢复中再次崩溃不会重复迁移或副作用。
客户端只在 recovery completed 后订阅可写 runtime。

## 副作用恢复

effect 状态：`planned`、`authorized`、`started`、`confirmed`、`failed`、`unknown`。
`planned` 或 `authorized` 但未 started 可安全标记 cancelled。
`started` 且没有 receipt 必须查询 executor：本地 PID identity、远程 lease 或外部 idempotency endpoint。
查询确认完成后写 receipt 和 tool result，不重新执行。
确认未开始且工具声明幂等时可用原 key 重试。
无法确认的文件写、git push、删除或外部 API 写入进入 `unknown` 并请求人工复核。
纯读调用可以重新执行，但仍要闭合旧 item，避免两个 result 对一个 call。

## Fork 与 rollback

fork 创建新 thread id，记录 parent id 与 parent sequence。
历史可以内容寻址共享，但新事件 sequence 从明确规则开始，不能与父 thread 混用订阅 cursor。
fork 默认复制会话状态，不自动复制正在运行的进程和 pending approval。
若创建独立 worktree，checkpoint 同时记录 git/workspace identity。

rollback 追加 `thread.rolled_back`，建立新的有效 head 投影，不删除历史 rollout。
conversation rollback 只改变模型可见与 UI 有效历史。
workspace rollback 使用 patch journal 或三方合并，并检测 rollback 后用户修改。
任何 destructive workspace rollback 都需独立审批和预览。

## Schema 迁移

每个 rollout frame 和数据库都携带 schema version。
迁移函数按 `N -> N+1` 小步、幂等、可重跑设计。
顺序固定：备份/检查点 -> 迁移 rollout 读取器 -> 数据库 DDL -> backfill -> 校验 -> 切换写版本。
新增字段使用兼容默认值；删除字段至少跨一个读写兼容窗口。
大表 backfill 分批并记录 cursor，避免长事务锁住 app-server。
升级失败保留旧 rollout 和 migration journal，不能留下“版本已升、数据未完”的假状态。
降级只承诺读取仍兼容的数据；不支持时应明确拒绝写入。

迁移验证包括：行数、head sequence、checksum、终态分布、随机 thread replay hash。
公开测试中的 rollout migration 可作为行为参考，但本设计不复制其私有数据格式。

## 保留、导出与删除

archive 只改变可见性，不删除 rollout。
delete 先写 tombstone，再按保留政策异步回收 artifact 和索引。
共享 artifact 使用引用计数或可达性扫描，不能因删除一个 fork 破坏另一个。
导出包含 manifest、schema version、events/items、artifact checksums 和 redaction report。
导入必须生成新安装内 id 映射并验证所有 hash。
日志、遥测和备份遵循独立的敏感数据保留期。

## 故障注入与验收

- 在 rollout append 每个字节边界模拟断电，恢复到最后完整 frame；
- 在副作用完成、receipt 写入前崩溃，不重复执行；
- 删除 SQLite 后可由 rollout 重建同一 transcript 和终态；
- 修改一个中部 frame 会被检测并阻止可写恢复；
- 连续执行同一 migration 三次结果一致；
- 10 万事件恢复在约定 SLO 内且内存有界；
- fork 后删除父 thread 不破坏子 thread artifact；
- rollback 不撤销 checkpoint 之后的用户独立修改；
- 两个 runtime 抢同一 thread 时只有一个获得写租约；
- 老客户端读取新增未知 item 时保持 sequence 连续。

事件结构见 [protocol-state.md](protocol-state.md)，执行副作用见 [workspace-execution.md](workspace-execution.md)。
公开源码地图见 [sources.md](sources.md)。
