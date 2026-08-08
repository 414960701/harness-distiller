# AgentScope-like 协议与状态

## 目录

两层模型 → 聚合关系 → Command → Event → Item → Reply transition → 顺序/去重 → Snapshot → 错误 → 兼容 → fixtures。

## 两层模型

AgentScope 固定源码公开 `Msg/content blocks` 与 `AgentEvent`，其中 reply 近似一次 agent 响应。为支持完整 harness，本 dossier 在外层增加 `thread/session -> turn/reply -> item/message|tool|plan|artifact -> event`。外层字段是 `inference`，内层 block/event 类型由 [sources.md](sources.md) 的 code 证据支持。

## 聚合关系

```text
AgentDefinition 1--N Session(thread)
Session 1--N Reply(turn)
Reply 1--N Item
Session 1--N Event
Reply 1--1 CapabilitySnapshot
ToolCall 0--1 ConfirmationRequest 0--1 ConfirmationResolution
Team 1--N MemberSession
ChannelBinding N--1 Session
```

`session_id` 是并发与恢复边界，`reply_id` 是一次 ReAct loop，`item_id` 是可渲染事实，`event_id/cursor` 是增量传输边界。

## Command envelope

```json
{
  "protocol_version": "1.0",
  "command_id": "cmd_01",
  "type": "session.input.submit",
  "idempotency_key": "client-42:message-9",
  "actor": {"type": "user", "id": "u1"},
  "session_id": "ses_01",
  "expected_version": 17,
  "payload": {"content": [{"type": "text", "text": "inspect repo"}]},
  "created_at": "2026-08-08T12:00:00Z"
}
```

必需命令：`agent.create/update`、`session.create/input.submit/resume/interrupt`、`confirmation.resolve`、`workspace.attach/release`、`channel.bind/unbind`、`team.member.create/message`。未知 command type 拒绝；未知可选字段保留或忽略，不能改变旧字段语义。

## Event envelope

```json
{
  "protocol_version": "1.0",
  "event_id": "evt_018",
  "cursor": 18,
  "type": "TOOL_CALL_END",
  "session_id": "ses_01",
  "reply_id": "rep_01",
  "item_id": "item_call_7",
  "causation_id": "model_call_2",
  "correlation_id": "cmd_01",
  "sequence_in_reply": 12,
  "payload": {"block_id": "call_7", "name": "Read", "input": {"path": "README.md"}},
  "created_at": "2026-08-08T12:00:03Z"
}
```

AgentScope event 类型至少映射 reply start/end、model call start/end、text/data/thinking block start/delta/end、tool call/result start/delta/end、exceed max iters、require user confirm/external execution、confirm result、interrupt 与 custom。传输层不能把 delta 当完整 item 持久真相；projector 需按 block id 组装。

## Item schema

| kind | 核心字段 | 不变量 |
|---|---|---|
| `message` | role, blocks[], finished_reason | blocks 有稳定 id/顺序 |
| `tool_call` | call_id, name, raw/normalized args, state | 同 call 只执行一次 |
| `tool_result` | call_id, state, blocks, artifacts, error | 必须关联 call |
| `plan` | tasks{id,description,state}[], revision | 同 revision 原子更新 |
| `confirmation` | request_id, args_hash, decision, expiry | resolve 一次 |
| `context_summary` | covered_item_ids, summary, model, hash | 不删除原 event |
| `artifact` | uri, media_type, size, sha256, scope | 读时验证 scope/hash |

## Reply transition

允许状态：`queued -> running -> waiting_confirmation|waiting_external|cancelling -> completed|interrupted|error|exceed_max_iters`。`waiting_* -> running` 需要匹配 continuation token。任何终态到非终态非法。session snapshot 的 version 每次 committed transition 单调加一。

## 顺序、去重与并发

- 服务为每个 session 提供单 writer 或等价 compare-and-set。
- event cursor 在 session 内单调，不要求跨 session 全局排序。
- command 以 `(actor,idempotency_key)` 去重；tool side effect 以 `call_id + args_hash` 去重。
- channel delivery 使用独立 delivery id；重发 event 不能重跑工具。
- Team 的跨 session 消息保存 source session/event id，防止回环和重复。

## Snapshot 与重放

Snapshot 包含 `last_cursor/state_version/active_reply/items_projection/plan/workspace_ref/capability_hash`。客户端先读 snapshot，再订阅 `after_cursor=last_cursor`；若 log 已裁剪，服务返回 `cursor_expired` 并要求重取 snapshot。Projector 必须是纯函数或按 event id 幂等。

## 错误模型

```json
{
  "code": "permission_denied",
  "category": "policy",
  "message": "write outside working directory",
  "retryable": false,
  "details": {"rule_id": "rule_4"},
  "trace_id": "tr_9"
}
```

固定 category：`validation|model|policy|executor|workspace|storage|transport|cancelled|internal`。公开 error 先脱敏；原异常放受控 trace。HTTP、WebSocket、channel 文本只映射同一错误对象，不另造语义。

## 版本兼容

只允许新增可选字段、新事件 type 在 capability negotiation 后发送。字段删除、类型改变、终态语义改变需 major 版本和 migrator。CustomEvent 必须命名空间化；不能把关键安全状态藏入仅新客户端理解的 custom payload。

## Golden fixtures

至少保存：纯文本 reply、单 tool、并行 tools、ASK/ALLOW、ASK/DENY、interrupt、max iters、context compression、external execution、channel reconnect、team message。每个 fixture 同时断言 schema、事件顺序、snapshot 重放和旧客户端降级。
