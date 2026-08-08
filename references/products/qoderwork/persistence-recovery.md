# QoderWork-like 持久化与恢复

> Task、会话、artifacts、Awareness 以及归档可长期保留是 `confirmed` 行为；具体存储、事务和恢复协议均为 `inference`。

## 目录

- [持久化目标](#1-持久化目标)
- [建议存储分层](#2-建议存储分层)
- [提交边界](#3-提交边界)
- [检查点](#4-检查点)
- [启动恢复流程](#5-启动恢复流程)
- [ToolCall 恢复矩阵](#6-toolcall-恢复矩阵)
- [Artifact 恢复](#7-artifact-恢复)
- [Awareness 恢复与清除](#8-awareness-恢复与清除)
- [Scheduled task 恢复](#9-scheduled-task-恢复)
- [备份、迁移与回滚](#10-备份迁移与回滚)
- [黑盒 oracle](#11-黑盒-oracle)

## 1. 持久化目标

- 应用崩溃或重启后，Task 列表、transcript、Task Monitor 与 artifact cards 一致恢复。
- 多个 Task 的故障域分离，一个损坏任务不阻止应用启动。
- 已提交的非幂等外部动作不会因恢复而重复执行。
- Working Folder 内容、会话数据库与 artifact store 的不一致可被检测和修复。
- Awareness 支持备份、恢复与彻底清除，包括搜索索引。
- schema 升级后旧任务仍可读、可导出并可继续新 Run。

## 2. 建议存储分层

| 数据 | 建议存储 | 关键性质 |
|---|---|---|
| Task/Turn/Step 事件 | SQLite/Postgres append log | 事务、序号、索引 |
| 投影与搜索 | 可重建数据库/FTS | 可删除重建 |
| artifact/blob | content-addressed store | hash、去重、流式 |
| Working Folder 文件 | 用户目录 | grant、原子写、版本 |
| secrets | OS keychain/secret broker | 不入事件与备份正文 |
| Awareness 原文 | 独立加密 store | 可逐条管理 |
| Awareness 向量索引 | 可重建索引 | 清除时同步删除 |
| runtime temp | task/run scoped temp | 启动时清理/恢复 |

## 3. 提交边界

单个事件批次必须原子提交 `events + outbox + projection cursor`。
大 blob 先写临时对象、计算 hash、fsync，再提交引用事件，最后移入正式命名空间。
Working Folder 写入使用 write intent：记录目标、旧 hash、temp hash、阶段与 owner run。
外部动作先记录 action intent，执行后记录 provider receipt。
UI 只展示 committed event，不消费 worker 内存中的乐观状态作为事实。

```yaml
WriteIntent:
  id: string
  task_id: string
  target: canonical_path_handle
  expected_old_hash: string|null
  temp_blob_hash: string
  phase: prepared|published|committed|rolled_back|needs_review
ActionReceipt:
  action_key: string
  provider: string
  external_id: string|null
  status: confirmed|rejected|unknown
  response_digest: string
```

## 4. 检查点

检查点是事件 reducer 的优化，不是新的事实源。
每 N 个事件或 Run 终态保存 `state snapshot + through_seq + reducer_version + checksum`。
恢复时先校验检查点，再重放后续事件。
损坏或版本不兼容时丢弃检查点，从事件重建。
模型上下文 summary 与运行时检查点分开；前者是有损 context item，后者是无损状态投影。

## 5. 启动恢复流程

1. 以只读方式打开元数据库并执行完整性检查。
2. 加载 schema 版本，必要时先复制可恢复备份再迁移。
3. 枚举 active Run，检查 runtime lease 与 heartbeat。
4. 对过期 lease 创建 `RunRecoveryStarted`，不直接重启工具。
5. 扫描 prepared/published WriteIntent 并核对 temp、target 与 hash。
6. 扫描 running ToolCall；按幂等性和 receipt 分类处理。
7. 重建落后或校验失败的 UI/搜索投影。
8. 启动 Sidebar，逐任务延迟加载 transcript 与 artifact。

## 6. ToolCall 恢复矩阵

| 类型 | 有 receipt | 无 receipt | 恢复动作 |
|---|---|---|---|
| 纯读 | 可重用 | 可安全重试 | 标记旧 attempt 后重试 |
| 幂等写 | 核对 action key | 可带同 key 重试 | 保存服务端版本 |
| 本地原子写 | 核对 WriteIntent/hash | 查看 temp/target | commit、rollback 或冲突 |
| 外发/发布 | 以 external id 确认 | 状态 unknown | 不重发，要求解析 |
| Computer Use | 观察帧过期 | 状态 unknown | 永不自动续动作 |
| MCP 写 | 按 server receipt | 取决于 tool 声明 | 未声明则按非幂等 |

## 7. Artifact 恢复

artifact 元数据与实际文件 hash 不符时标为 `stale`，不继续显示 Ready。
Working Folder 文件被用户在外部修改时创建 external change 记录。
blob 存在但无引用时进入 quarantine，达到保留期后可回收。
事件引用 blob 但对象缺失时 card 显示 unavailable，并提供重新生成/重新绑定。
预览缓存可随时删除重建，不影响 artifact 原件。
归档 Task 不删除 artifact；永久删除需单独明确流程与保留策略。

## 8. Awareness 恢复与清除

备份至少记录 USER、长期记忆、短期记忆、来源与 schema 版本。
secrets、OAuth token 和系统权限不得随普通 Awareness 备份导出。
恢复先进入 staging，展示新增、覆盖、冲突和敏感条目。
Clear Memory 是事务操作：删除原文、provenance 关联、摘要缓存与所有向量/全文索引条目。
清除后执行反向检索 oracle，发现残留则操作失败并继续隔离残留索引。
Skill evolution 的 diff 不应混入 Awareness 备份，除非用户显式选择。

## 9. Scheduled task 恢复

调度器保存 intended fire time，而不是只依赖内存 timer。
进程恢复后按 schedule 的 misfire policy 决定 skip、run_once 或 catch_up。
每次触发用 `schedule_id + intended_fire_time` 作为唯一键。
已创建 TaskRun 的触发不得再创建第二个 Run。
时区变更和夏令时必须保存原时区与解析后的 UTC 时间。
连续失败触发退避和用户通知，不能无限后台重试。

## 10. 备份、迁移与回滚

迁移前创建带版本、checksum 和创建时间的数据库备份。
迁移脚本可重复运行，记录每一步完成标记。
事件永不就地改写；通过 upcaster 或新事件表达新语义。
回滚至少保证旧版本以只读方式导出任务和 artifacts。
扩展版本与 TaskConfigSnapshot 一起保存，缺少旧扩展时任务仍可查看。

## 11. 黑盒 oracle

1. 在事件提交、blob 发布、文件 rename 的每个边界 kill 进程，恢复后无半成品 Ready card。
2. 外发成功但本地崩溃时，恢复不重复外发。
3. 删除 artifact 原文件后，card 变 unavailable/stale 而非继续 Ready。
4. 损坏一个 Task 检查点，只重建该任务且其他任务立即可用。
5. Awareness Clear 后全文、向量和摘要检索均无残留。
6. scheduled trigger 在重启前后只创建一次 Run。
7. schema 迁移失败能从备份恢复并只读导出。
8. 归档/恢复不改变 Task 的 transcript、hash 与 artifacts。
