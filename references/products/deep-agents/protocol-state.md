# Deep Agents Protocol 与 State 规范

## 目录

- [边界](#边界)
- [领域对象](#领域对象)
- [命令 Schema](#命令-schema)
- [事件 Schema](#事件-schema)
- [核心状态 Schema](#核心状态-schema)
- [Reducer 规则](#reducer-规则)
- [状态机](#状态机)
- [兼容与投影](#兼容与投影)
- [安全约束](#安全约束)
- [协议测试](#协议测试)

## 边界

Deep Agents 的 Python 对象和 LangGraph state 是内部实现面；跨进程、ACP 和 frontend 需要独立的版本化协议。

协议对象使用 `thread -> turn -> item -> event` 层级：

- `thread`：可恢复会话与 checkpoint 命名空间；
- `turn`：一次用户输入到稳定终态；
- `item`：message、todo、tool call、approval、subagent、artifact；
- `event`：对 item 的有序事实变更。

不得直接把 pickle、TypedDict 或 LangGraph 私有 channel 作为网络协议。

## 领域对象

| 对象 | 稳定主键 | 关键字段 |
|---|---|---|
| Thread | `thread_id` | owner、created_at、head_sequence、checkpoint_ref |
| Turn | `turn_id` | thread_id、status、capability_snapshot、budget |
| Item | `item_id` | turn_id、kind、status、parent_item_id |
| Event | `event_id` | sequence、type、payload、causation_id |
| ToolCall | `call_id` | tool、args_hash、policy、attempt、receipt |
| Approval | `approval_id` | call_id、choices、scope、expires_at |
| SubagentRun | `child_id` | mode、agent_name、remote_thread_id、remote_run_id |
| Artifact | `artifact_id` | logical_uri、digest、media_type、provenance |
| Todo | `todo_id` | content、status、depends_on、evidence |

所有 ID 由 runtime 生成，不能信任模型提供的 ID。

## 命令 Schema

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "title": "DeepAgentCommand",
  "type": "object",
  "required": ["version", "command_id", "thread_id", "type", "payload"],
  "properties": {
    "version": {"const": "1.0"},
    "command_id": {"type": "string"},
    "thread_id": {"type": "string"},
    "turn_id": {"type": ["string", "null"]},
    "expected_sequence": {"type": ["integer", "null"]},
    "type": {"enum": ["turn.start", "turn.cancel", "approval.resolve", "todo.patch", "subagent.update", "subagent.cancel"]},
    "payload": {"type": "object"}
  },
  "additionalProperties": false
}
```

写命令使用 `expected_sequence` 做 optimistic concurrency；重复 `command_id` 返回原结果。

## 事件 Schema

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "title": "DeepAgentEvent",
  "type": "object",
  "required": ["version", "event_id", "thread_id", "turn_id", "sequence", "type", "payload"],
  "properties": {
    "version": {"const": "1.0"},
    "event_id": {"type": "string"},
    "thread_id": {"type": "string"},
    "turn_id": {"type": "string"},
    "sequence": {"type": "integer", "minimum": 1},
    "type": {"type": "string"},
    "causation_id": {"type": ["string", "null"]},
    "payload": {"type": "object"},
    "created_at": {"type": "string", "format": "date-time"}
  },
  "additionalProperties": false
}
```

最小事件词表：

- `turn.started | turn.checkpointed | turn.interrupted | turn.resumed | turn.finished`；
- `message.delta | message.completed`；
- `todo.replaced | todo.updated`；
- `tool.requested | tool.policy_decided | tool.progress | tool.committed | tool.failed`；
- `approval.requested | approval.resolved | approval.expired`；
- `subagent.started | subagent.progress | subagent.finished | subagent.cancelled`；
- `context.compacted | artifact.created | backend.changed`；
- `runtime.warning | runtime.failed`。

## 核心状态 Schema

```json
{
  "schema_version": 1,
  "messages": [],
  "files": {},
  "todos": [],
  "async_tasks": {},
  "pending_calls": {},
  "approvals": {},
  "artifacts": {},
  "turn": {"status": "ready", "sequence": 0},
  "capability_snapshot": {},
  "private": {"summarization_event": null}
}
```

与源码的映射：

| 外部字段 | Deep Agents/LangGraph 内部 | 处理 |
|---|---|---|
| messages | `DeepAgentState.messages` + DeltaChannel | 按 message ID merge/remove/reset |
| files | `StateBackend` state key | 只在选用 state backend 时存在 |
| todos | TodoListMiddleware state | planning opt-in 时存在 |
| async_tasks | AsyncSubAgentState | task_id 为 remote thread_id |
| private.summarization_event | `_summarization_event` | 不向 child/frontend 原样公开 |
| pending_calls | LangGraph pending writes + harness ledger | 不能只依赖 messages 推断 |

## Reducer 规则

### Messages

- 写入前由 runtime 保证稳定 message ID；
- 同 ID 新消息替换旧消息；
- `RemoveMessage(id)` 删除目标；
- `REMOVE_ALL_MESSAGES` 清空此前消息；
- reducer 重放必须确定，不生成随机 ID；
- 只有 list flatten，其余 message-like 视为单项。

### Async tasks

- reducer 对 task_id 做字典 merge；
- update 不改变 task_id/thread_id；
- follow-up run 可以更新 run_id；
- status 不限制为闭集时，未知值仍保留并投影为 `unknown`。

### Todo

- 提交使用整体 replace 或 revision-aware patch；
- status 只允许 `pending/in_progress/completed/cancelled`；
- 删除有依赖项的 todo 前先拒绝或级联明确事件；
- 不允许两个并行 write 覆盖同一 revision。

## 状态机

Turn 状态：

```text
ready -> running -> waiting_approval -> running
                 -> waiting_subagent -> running
                 -> completed | failed | cancelled | indeterminate
```

Tool 状态：

```text
requested -> policy_decided -> waiting_approval? -> dispatched
          -> committed | failed | cancelled | indeterminate
```

Async task 状态：

```text
created -> running -> success | error | cancelled
                 \-> updating -> running
```

非法 transition 必须返回 conflict，不由 reducer 猜测修正。

## 兼容与投影

- snapshot 带 `schema_version` 与 `head_sequence`；
- client 先取 snapshot，再订阅 `sequence > head_sequence`；
- 事件至少一次传输，projection 以 event_id 去重；
- 未知 event type 被保留并忽略，不中断旧客户端；
- 字段删除走 major version；新增 optional 字段走 minor；
- ACP adapter 把 session 映射为 thread，把 prompt 映射为 turn；
- LangGraph `messages/updates/tasks/custom` stream 先归一化再对外发布；
- 前端不能根据文本猜 tool status 或 approval 状态。

## 安全约束

- event payload 中 secret、header、env 和大文件内容默认脱敏/外置；
- tool args 同时保存规范化摘要与受控加密原文；
- approval event 固定参数 hash，edit 后创建新 hash；
- child event 带 parent lineage，不能伪造父 sequence；
- external remote event 标记 trust domain；
- private middleware state 永不自动出现在 frontend snapshot；
- tenant_id/owner_id 在存储主键和每次查询中强制；
- 删除 thread 时同步处理 checkpoint、artifact 和 remote task retention。

## 协议测试

1. 同一事件重复两次，projection 结果不变。
2. sequence 缺口触发补拉，不静默跳过。
3. 旧 client 遇到未知事件仍可显示最终状态。
4. message replace/remove/reset 重放与在线结果一致。
5. Todo 并发 revision 冲突返回 409 等价错误。
6. approval 参数在请求后被修改时拒绝执行。
7. async task 更换 run_id 后仍以原 task_id 查询。
8. parent cancellation 后的 child late event 不修改主结果。
9. snapshot + 全量 events 与直接数据库状态哈希一致。
10. schema migration 前后 thread、turn、item、event 数量与终态一致。
