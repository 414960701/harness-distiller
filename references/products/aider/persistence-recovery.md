# Aider-like 持久化、事务与恢复

## 目录

- [持久化分层](#持久化分层)
- [数据库 schema](#数据库-schema)
- [事务边界](#事务边界)
- [Git 与 history 恢复](#git-与-history-恢复)
- [cache 与总结恢复](#cache-与总结恢复)
- [启动恢复算法](#启动恢复算法)
- [迁移与保留](#迁移与保留)
- [故障 oracle](#故障-oracle)

## 持久化分层

公开 Aider 主要依赖 Git commits、Markdown chat history、input history、配置文件和 repo tag cache，而不是完整 durable agent database。为了让其他模型实现可恢复的产品，本规范增加最小 SQLite/event store；它属于设计综合，并保持 Git/工作区为文件真源。

真源优先级：

1. 当前 filesystem 内容与 Git object graph；
2. 已提交 event/turn/item 数据；
3. chat history 文本；
4. 可重建 repo map/tag/prompt cache。

cache 永远不能覆盖 1/2。数据库丢失时仍可从 Git 和 history 开新 session；Git 丢失时数据库不能伪造可 undo commit。

## 数据库 schema

```sql
CREATE TABLE threads (
  id TEXT PRIMARY KEY, root_uri TEXT NOT NULL, mode TEXT NOT NULL,
  status TEXT NOT NULL, config_json TEXT NOT NULL,
  config_revision INTEGER NOT NULL, last_head_sha TEXT,
  created_at TEXT NOT NULL, updated_at TEXT NOT NULL
);
CREATE TABLE turns (
  id TEXT PRIMARY KEY, thread_id TEXT NOT NULL, seq INTEGER NOT NULL,
  state TEXT NOT NULL, mode_snapshot TEXT NOT NULL,
  reflection_count INTEGER NOT NULL DEFAULT 0,
  input_item_id TEXT, error_json TEXT, started_at TEXT NOT NULL, ended_at TEXT,
  UNIQUE(thread_id, seq)
);
CREATE TABLE items (
  id TEXT PRIMARY KEY, turn_id TEXT NOT NULL, ordinal INTEGER NOT NULL,
  kind TEXT NOT NULL, state TEXT NOT NULL, payload_json TEXT NOT NULL,
  created_at TEXT NOT NULL, UNIQUE(turn_id, ordinal)
);
CREATE TABLE events (
  id TEXT PRIMARY KEY, thread_id TEXT NOT NULL, seq INTEGER NOT NULL,
  turn_id TEXT, item_id TEXT, type TEXT NOT NULL,
  payload_json TEXT NOT NULL, created_at TEXT NOT NULL,
  UNIQUE(thread_id, seq)
);
CREATE TABLE git_checkpoints (
  id TEXT PRIMARY KEY, thread_id TEXT NOT NULL, turn_id TEXT,
  kind TEXT NOT NULL, base_sha TEXT, commit_sha TEXT,
  paths_json TEXT NOT NULL, created_in_session INTEGER NOT NULL,
  created_at TEXT NOT NULL
);
```

```sql
CREATE TABLE confirmations (
  id TEXT PRIMARY KEY, turn_id TEXT NOT NULL, action TEXT NOT NULL,
  subject_hash TEXT NOT NULL, decision TEXT, rule_id TEXT NOT NULL,
  requested_at TEXT NOT NULL, resolved_at TEXT
);
CREATE TABLE apply_journals (
  id TEXT PRIMARY KEY, turn_id TEXT NOT NULL, state TEXT NOT NULL,
  base_head_sha TEXT, manifest_json TEXT NOT NULL,
  created_at TEXT NOT NULL, committed_at TEXT
);
CREATE TABLE schema_migrations (
  version INTEGER PRIMARY KEY, checksum TEXT NOT NULL, applied_at TEXT NOT NULL
);
```

消息全文、diff 和 command output 可以放 content-addressed sidecar，数据库只存 hash/引用；sidecar 必须权限收紧、可 redact、可执行 retention。

## 事务边界

Command 接收事务：校验 idempotency key、插入 turn/item、推进 thread active_turn、追加 `turn.started` 在一个 DB transaction。模型网络调用不持有 DB lock；调用前 item=`running`，结束后用新事务写 outcome。

Apply 是“DB journal + filesystem + Git”的 saga，不可能用单个 SQLite transaction 原子覆盖：

1. 写 `apply_journals(state=prepared)`，包含 preimage/postimage hash 和安全备份引用；
2. filesystem apply，每文件完成更新 manifest；
3. 成功后 `state=files_applied`；
4. Git commit，成功写 checkpoint，失败写 diagnostic；
5. `state=committed` 或 `applied_uncommitted`；
6. 事务结束后清理过期 preimage。

崩溃发生在任意点，启动恢复可根据 journal 和实际 hash判定继续、回滚或人工处理。不得简单把所有 `running` turn 标 completed。

## Git 与 history 恢复

每轮开始记录 HEAD；每个 auto commit 的 full SHA 和 path set 入库。恢复时重新验证 SHA 可达、当前 HEAD 和 dirty state。`aider_commit_hashes` 从当前 session 的 `created_in_session=1` checkpoint 重建，不从 commit message 文本猜测。

chat history 是面向人的 Markdown/文本副本，写入采用 append + flush；它可以恢复对话语义，但不保留完整 typed state。读取后用 parser 分割 user/assistant messages；超过 soft token limit 立即排队总结。格式不完整时保留可解析前缀，记录 warning，不阻止访问工作区。

input history 仅用于终端历史，不应自动进入模型上下文。配置快照保留当时 model/format/mode；恢复时如果当前 config 不兼容，创建 revision 并提示，而非静默改写旧 turn。

## cache 与总结恢复

repo tag cache：key 为 file identity + mtime/hash + parser version；SQLite error 时隔离损坏文件，尝试重建，仍失败则内存 dict 降级。tree/map cache 和 prompt cache 都可丢弃。

后台 history summary 记录 `source_messages_hash`。worker 完成时：

```python
if hash(current_done_messages) == source_messages_hash:
    replace_head_with_summary()
    emit("history.summary_committed")
else:
    discard_result()
```

崩溃留下 `summary_started` 无 completed 不影响原历史；重启后重新排队。summary 文本不能删除 Git checkpoint 或 validation facts，必要 facts另存 typed items。

## 启动恢复算法

```python
def recover(thread_id):
    run_schema_migrations()
    thread = load_thread(thread_id)
    workspace = inspect_files_and_git(thread.root_uri)
    for journal in unfinished_journals_oldest_first():
        classify = compare_hashes(journal, workspace)
        if classify == "no_files_applied": mark_rolled_back()
        elif classify == "all_postimages": mark_files_applied()
        elif classify == "recoverable_partial": restore_preimages()
        else: mark_needs_attention_and_block_writes()
    reconcile_git_checkpoints(workspace.head)
    fail_or_cancel_orphan_running_items()
    expire_unresolved_confirmations()
    rebuild_event_projection()
    return resumable_thread()
```

模型调用在崩溃后默认不自动重发，因为 provider 是否已计费/返回未知；标记 `interrupted` 并允许用户重试。validation 命令亦不自动重跑，除非显式配置为 idempotent。等待确认可恢复，但 command/edit hash 必须仍匹配且未过期。

## 迁移与保留

迁移文件具有递增 version 和 checksum；启动前备份 DB，单事务应用纯 DB migration。需要 sidecar 重写时使用两阶段 migration 和 checkpoint，可重复执行。降级版本只允许只读打开。

默认 retention：保留 Git checkpoints；turn/event metadata 长期保留；model delta 可压缩/删除；command output 和 prompt content 可按天数清理；secret-redacted 原文不应另留副本。用户 `/clear` 清理聊天上下文不等于删除 Git/history/audit，UI 必须说明范围。

## 故障 oracle

- tag cache 文件随机截断：主会话仍启动，发 `cache.rebuilt` 或 memory fallback。
- chat history 最后一条写半截：恢复可解析前缀，未制造 assistant 回复。
- apply 第一个文件后 kill -9：重启要么完整回滚，要么识别所有 postimage；绝不无提示继续。
- files applied 后 commit 失败：显示 `applied_uncommitted`，`/undo` 不宣称可用。
- summary worker 基于旧消息完成：hash 不匹配，结果丢弃。
- DB 重放重复 Command：idempotency key 返回原 turn，不重复写文件/commit。
- 当前 HEAD 外部前移：标 `workspace.diverged`，pending undo/apply 暂停。
- migration 中断：备份仍可打开，重跑不产生重复行。
