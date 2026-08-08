# OpenHands-like 协议与状态规格

## 目录

- [协议分层](#协议分层)
- [对象模型](#对象模型)
- [事件信封](#事件信封)
- [命令](#命令)
- [事件类型](#事件类型)
- [Action 与 Observation](#action-与-observation)
- [快照与投影](#快照与投影)
- [排序重放背压](#排序重放背压)
- [错误与版本](#错误与版本)
- [映射约束](#映射约束)

## 协议分层

SDK 内部有 Conversation/Event/Action/Observation；Agent Server 暴露 REST/WebSocket；Canvas 有 TypeScript event union。复刻时必须建立一份 canonical wire schema，避免 Python Pydantic private state 成为前端协议。

共享 `thread/turn/item/event` 模型与 OpenHands 名称映射：

| canonical | OpenHands-like |
|---|---|
| thread | conversation |
| turn | run/message-to-terminal-outcome |
| item | typed Event 或 action-observation pair projection |
| event | durable Conversation Event；transport envelope 另有 sequence |

不能把 Event 的 `parent_id` 当 transport sequence；前者形成事件树，后者保证订阅顺序。

## 对象模型

ConversationSnapshot 至少包含：

- `conversation_id`、`schema_version`、`execution_status`；
- `active_leaf_event_id`、`head_is_empty`、`last_offset`；
- agent/profile/tool snapshot digest；
- workspace identity/capabilities；
- confirmation policy 与 pending request；
- iteration/budget/stats；
- lease generation（只向授权客户端暴露必要信息）。

Event 公共字段：`id`、`kind`、`timestamp`、`source`、`parent_id`、`payload`。

`source` 至少为 `agent|user|environment|hook`。Event immutable；更正用新事件。

## 事件信封

```json
{
  "protocol_version": "1.0",
  "conversation_id": "conv_01",
  "offset": 84,
  "event_id": "evt_84",
  "kind": "ObservationEvent",
  "source": "environment",
  "parent_id": "evt_83",
  "causation_id": "call_12",
  "occurred_at": "2026-08-08T10:00:00Z",
  "payload": {
    "action_id": "act_12",
    "tool_call_id": "call_12",
    "observation": {"kind": "CommandObservation", "exit_code": 0}
  }
}
```

`offset` 在 conversation append log 内单调递增；fork 的新 conversation 从自己的 offset 空间开始并记录 parent reference。

## 命令

| 命令 | 关键参数 | 前置条件 | 结果 |
|---|---|---|---|
| `conversation.create` | workspace、agent、profile | 配置有效 | snapshot |
| `conversation.resume` | id、last_offset | 可见且 lease 可得 | snapshot+events |
| `conversation.fork` | id、leaf、workspace mode | leaf 存在 | 新 id |
| `conversation.navigate` | id、leaf/null | 无活动 writer 冲突 | head event |
| `message.send` | content、attachments | 可写状态 | MessageEvent id |
| `run.start` | budget、deadline | idle/paused | run id |
| `run.pause` | reason | running/waiting | accepted |
| `run.interrupt` | reason | running | accepted |
| `confirmation.resolve` | request、decision | pending | resolution |
| `conversation.condense` | strategy | branch 可压缩 | condensation id |
| `events.search` | cursor、limit、filters | 可读 | page |
| `subscription.open` | after_offset | 已认证 | stream |
| `workspace.command` | typed request | capability/policy 允许 | receipt |

所有 mutation command 带 `request_id` 与 `idempotency_key`。相同 key 不同参数返回 conflict。

## 事件类型

- 内容：`SystemPromptEvent`、`MessageEvent`、`StreamingDeltaEvent`；
- 工具：`ActionEvent`、`ObservationEvent`、`AgentErrorEvent`；
- 上下文：`CondensationRequest`、`CondensationEvent`、`ResumeTranscriptEvent`；
- 控制：`ConversationStateUpdateEvent`、`PauseEvent`、`InterruptEvent`；
- 安全：`ConfirmationRequested`、`ConfirmationResolved`、`HookExecutionEvent`；
- 服务：`ServerErrorEvent`、`LeaseChangedEvent`、`WorkspaceStateEvent`；
- 扩展：未知 `kind` 保留 raw payload 并显示 generic card。

Transport delta 可不 durable，但 completed Message/Action/Observation 和 state transition 必须 durable。

## Action 与 Observation

Action：

```json
{
  "kind": "ActionEvent",
  "tool_name": "terminal",
  "tool_call_id": "call_12",
  "action": {"kind": "TerminalAction", "command": "pytest -q"},
  "thought_summary": "运行相关测试"
}
```

Observation：

```json
{
  "kind": "ObservationEvent",
  "action_id": "act_12",
  "tool_call_id": "call_12",
  "observation": {
    "kind": "TerminalObservation",
    "exit_code": 1,
    "stdout_artifact": "artifact://sha256/...",
    "stderr": "1 failed",
    "timed_out": false
  }
}
```

不暴露私有 chain-of-thought；只保存用户可见 thought summary。Action 参数先 schema validate，再安全判断。

## 快照与投影

服务端 snapshot 绑定 `last_offset`。客户端算法：

1. 替换当前 conversation projection；
2. 应用所有 `offset > last_offset` 的 event；
3. 按 event id 去重；
4. offset gap 时暂停实时流并补拉；
5. completed event 替换相同逻辑 id 的 optimistic/delta projection；
6. conversation 切换时不混用 event set。

Canvas 应从事件导出 chat groups、terminal、browser、plan、goal、diff、metrics 和 status。UI store 不可反向写 runtime state。

## 排序重放背压

- server 按 offset 至少一次投递；
- timestamp 仅用于展示，不能替代 offset；
- Event tree 分支遍历按 parent，append 顺序按 offset；
- 客户端队列溢出发送 `resync_required` 并断开慢订阅者；
- history page 使用稳定 cursor，边拉边写不重复/漏项；
- token delta 可丢弃；完整 MessageEvent 必须足以重建；
- WebSocket reconnect 携带 last applied offset；
- 事件压缩不删除审计 log，只影响模型 View 或生成可重建快照。

## 错误与版本

错误字段：`code`、`message`、`retryable`、`details`、`request_id`、`error_id`。

稳定 code：`invalid_request`、`not_found`、`conflict`、`lease_held`、`ownership_lost`、`confirmation_required`、`permission_denied`、`sandbox_denied`、`workspace_unavailable`、`provider_unavailable`、`deadline_exceeded`、`protocol_mismatch`、`internal`。

major 变化包括字段语义、parent/offset 保证、Action/Observation 配对改变。新增可选 event/tool variant 提升 minor。客户端必须保存 unknown 分支。

## 映射约束

- OpenHands SDK 的 event index file 是实现细节；wire 使用显式 offset。
- `ConversationExecutionStatus.FINISHED` 映射当前 run completed，不自动删除 conversation。
- `leaf_event_id=None` 与 deliberate empty head 必须用 `head_is_empty` 区分。
- legacy event 的 `parent_id=None` 可按前一个 event 解释；迁移后新 event 写显式 parent。
- tool call batch 的 shared response id 不代替每个 tool_call_id。
- confirmation 响应引用 request/action id，不通过“再调用 run 即批准”的隐式 UI 契约实现。

持久化事务见 [persistence-recovery.md](persistence-recovery.md)，界面投影见 [experience.md](experience.md)。
