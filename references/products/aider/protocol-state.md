# Aider-like 协议与状态

## 目录

- [兼容模型](#兼容模型)
- [实体 schema](#实体-schema)
- [Command 协议](#command-协议)
- [Event 协议](#event-协议)
- [状态机与不变量](#状态机与不变量)
- [重放与兼容](#重放与兼容)
- [故障映射](#故障映射)

## 兼容模型

原 Aider 是终端 Python 应用，并未公开名为 thread/turn/item/event 的网络协议。本文件用共享 harness 的四层协议表达同一行为，属于设计综合：`thread` 对应长期 Coder session；`turn` 对应一次用户消息及所有 reflection；`item` 对应消息、模型调用、edit、commit、validation 或 command；`event` 是 UI、日志与恢复共享的不可变记录。

协议目标是让 CLI、未来 TUI/GUI、测试和存储消费同一真源，而不是从 stdout 反向猜状态。

## 实体 schema

```yaml
Thread:
  id: uuid
  version: 1
  root_uri: file-uri
  mode: code|ask|architect|help|context
  status: active|closed
  created_at: timestamp
  config_revision: integer
  active_turn_id: uuid|null
  chat_files: [relative-path]
  read_only_files: [relative-path]
  last_head_sha: string|null

Turn:
  id: uuid
  thread_id: uuid
  seq: integer
  parent_turn_id: uuid|null
  state: created|preprocessing|compiling_context|model_running|architect_review|editor_running|parsing_edits|awaiting_confirmation|applying|committing|validating|reflecting|completed|failed|cancelled
  mode_snapshot: string
  input_item_id: uuid
  reflection_count: integer
  started_at: timestamp
  ended_at: timestamp|null
```

```yaml
Item:
  id: uuid
  thread_id: uuid
  turn_id: uuid
  ordinal: integer
  kind: message|model_call|edit_set|confirmation|file_change|git_commit|validation|shell_command|diagnostic|usage
  state: proposed|running|completed|failed|cancelled|rejected
  payload: object
  created_at: timestamp
```

`ordinal` 在 turn 内单调递增。payload 必须按 `kind` 做 discriminated schema；未知字段可保留，未知 kind 不得执行。

## Command 协议

所有入口先转换成 Command：

```yaml
Command:
  id: uuid
  thread_id: uuid
  expected_thread_revision: integer
  kind: submit_message|cancel_turn|confirm|add_files|drop_files|set_mode|run_slash_command|undo|close
  payload: object
  actor: user|automation
  idempotency_key: string
  issued_at: timestamp
```

典型 payload：

```yaml
submit_message:
  text: string
  mode_override: code|ask|architect|help|context|null

confirm:
  confirmation_id: uuid
  decision: allow_once|allow_session|deny|deny_forever

add_files:
  paths: [string]
  access: editable|read_only

undo:
  expected_head_sha: string
```

同一 thread 在 active turn 存在时拒绝第二个 `submit_message`，或显式排队；不得并发进入两个 writer。`mode_override` 只对本消息有效，对应 `/ask text` 等 one-shot 命令；`set_mode` 对应 sticky `/chat-mode`。

斜杠命令由 parser 变成 typed command，不应把 `/git`、`/run` 的文本直接交给 shell。未知命令返回 `command.unknown`；参数校验失败返回结构化 diagnostic。

## Event 协议

```yaml
Event:
  id: uuid
  schema_version: 1
  thread_id: uuid
  turn_id: uuid|null
  item_id: uuid|null
  seq: integer
  type: string
  timestamp: timestamp
  payload: object
  redaction: none|secrets|content
```

最低事件集：

- `thread.created`, `thread.config_changed`, `thread.files_changed`；
- `turn.started`, `turn.state_changed`, `turn.completed`, `turn.failed`, `turn.cancelled`；
- `message.accepted`, `model.requested`, `model.delta`, `model.completed`, `model.failed`；
- `edit.parsed`, `edit.previewed`, `edit.rejected`, `workspace.file_applied`；
- `confirmation.requested`, `confirmation.resolved`；
- `git.dirty_checkpointed`, `git.commit_created`, `git.commit_failed`, `git.undo_completed`；
- `validation.started`, `validation.completed`；
- `history.summary_started`, `history.summary_committed`, `cache.rebuilt`；
- `usage.updated`, `diagnostic.created`。

`model.delta` 可以不持久化全文或采用可压缩 sidecar；最终 `model.completed` 必须带 response hash。任何 secret、环境变量值、API key 和完整敏感 prompt 在持久化前 redact。

## 状态机与不变量

允许的关键迁移：

```text
created -> preprocessing -> compiling_context -> model_running
model_running -> completed                         # ask/help
model_running -> architect_review -> editor_running # architect
model_running|editor_running -> parsing_edits
parsing_edits -> awaiting_confirmation|applying|reflecting|failed
awaiting_confirmation -> applying|completed|failed
applying -> committing|validating|reflecting|failed
committing -> validating|failed
validating -> reflecting|completed
reflecting -> compiling_context|failed
nonterminal -> cancelled
```

不变量：

1. thread 同时至多一个 active turn。
2. `workspace.file_applied` 之前必须存在同 turn 的 `edit.parsed` 和授权结果。
3. read-only path 永远没有 `workspace.file_applied`。
4. `git.commit_created` 的 sha 必须能在 repo 读取，且加入 session commit set 后才能 `/undo`。
5. `turn.completed` 只出现一次，且之后不能追加有副作用的 item。
6. event seq 对 thread 单调递增；重复 idempotency key 返回原结果。
7. reflection 属于同一 turn，`reflection_count` 严格递增且不超过 budget。
8. model delta 绝不直接驱动 file apply。

## 重放与兼容

重放顺序按 `(thread_id, seq)`；从最近 snapshot 开始，事件补齐派生状态。工作区内容和 Git graph 是外部真源，不能仅靠 event 重建文件。重启时比较 `last_head_sha`、tracked/dirty 状态与持久化 snapshot：不一致则发 `workspace.diverged`，暂停 pending apply。

schema version 使用 additive evolution：新增可选字段不升 major；改变枚举语义或删除字段才升 major。消费者遇到未知 event type 要保存并忽略投影，不能执行未知副作用。事件 migration 必须幂等并保留原始备份。

CLI renderer 可从事件生成 Aider 风格输出：model delta 变 Markdown 流；confirmation event 变提示；file applied/commit/validation event 变状态行。测试直接断言 event，不解析 ANSI 文本。

## 故障映射

```yaml
ErrorEnvelope:
  code: provider_transient|provider_permanent|context_exceeded|edit_malformed|workspace_conflict|permission_denied|command_timeout|validation_failed|git_failed|cancelled|internal
  message: safe-string
  retryable: boolean
  source_item_id: uuid|null
  details: object
```

`validation_failed` 可以伴随 `turn.completed`，因为用户可能选择保留失败修改；`edit_malformed` 在有 reflection budget 时不是终止；`permission_denied` 对可选 edit 可完成，对任务必需 edit 则失败或完成为 no-change。`internal` 默认不可自动重试写入阶段。

安全事件至少记录被拒绝路径、规则 id 和 actor，但不要记录 root 外文件内容。协议验收见 [acceptance-tests.md](acceptance-tests.md)。
