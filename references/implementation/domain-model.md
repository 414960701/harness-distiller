# 领域模型

## 目录

- [身份与版本](#身份与版本)
- [核心对象](#核心对象)
- [Tool 与权限对象](#tool-与权限对象)
- [状态与不变量](#状态与不变量)
- [实现检查](#实现检查)

## 身份与版本

所有持久对象 MUST 使用不可复用的 opaque id。不要把数组下标、文件路径或 provider tool id 当全局身份。

```text
ThreadId, TurnId, ItemId, EventId, ToolCallId, ApprovalId,
ArtifactId, CheckpointId, WorkspaceId, AgentId, TraceId
```

每个序列化对象至少包含：

```yaml
id: opaque
schema_version: integer
created_at: RFC3339 UTC
```

更新型对象增加 `updated_at` 与单调 `revision`；事件使用每 thread 单调 `sequence`。

## 核心对象

### Thread

```yaml
Thread:
  id: ThreadId
  title: string|null
  status: active|archived|deleted
  parent_thread_id: ThreadId|null
  forked_from_turn_id: TurnId|null
  workspace_id: WorkspaceId
  recipe: string
  level: runnable|usable|productive|polished
  config_snapshot_id: string
  current_goal: Goal|null
  created_at: timestamp
  updated_at: timestamp
  revision: integer
```

Thread 保存会话身份和 lineage，不直接内嵌无限 turns。

### Turn

```yaml
Turn:
  id: TurnId
  thread_id: ThreadId
  status: queued|preparing|running|waiting_input|completed|failed|cancelled|indeterminate
  input_item_ids: [ItemId]
  started_at: timestamp|null
  ended_at: timestamp|null
  stop_reason: natural|user_cancelled|policy_denied|error|timeout|budget_exhausted|null
  model_snapshot: object
  tool_catalog_version: string
  context_snapshot_id: string|null
  budget: Budget
  usage: Usage
  error: HarnessError|null
```

`indeterminate` 表示外部动作可能发生但没有可靠结果，MUST 禁止自动重跑。

### Item

Item 是 UI、模型历史与审计可引用的离散单元：

```yaml
Item:
  id: ItemId
  thread_id: ThreadId
  turn_id: TurnId|null
  kind: user_message|agent_message|reasoning_summary|tool_call|tool_result|file_change|approval|plan|artifact|context_summary|system_notice
  status: pending|streaming|completed|failed|cancelled
  payload: tagged-union
  correlation_id: string|null
  created_at: timestamp
  completed_at: timestamp|null
```

模型私有推理不得直接持久化或展示；只保存允许的 reasoning summary。

### Event

```yaml
Event:
  id: EventId
  thread_id: ThreadId
  turn_id: TurnId|null
  sequence: integer
  type: string
  payload: object
  causation_id: EventId|CommandId|null
  correlation_id: TraceId
  schema_version: integer
  created_at: timestamp
```

Event 是事实账本；UI projection 可以删除重建。

### ContextFragment

```yaml
ContextFragment:
  id: string
  kind: instruction|message|file|retrieval|memory|plan|tool_result|summary
  source: URI
  scope: global|user|workspace|thread|turn|agent
  trust: trusted|user|workspace|external
  priority: integer
  token_estimate: integer
  content_ref: string
  content_hash: string
  expires_at: timestamp|null
```

## Tool 与权限对象

### ToolSpec

```yaml
ToolSpec:
  name: string
  version: semver
  description: string
  input_schema: JSON-Schema
  output_schema: JSON-Schema|null
  capabilities: [filesystem.read, filesystem.write, process.exec]
  side_effect: none|local_reversible|local_irreversible|external_reversible|external_irreversible
  idempotency: idempotent|keyed|non_idempotent
  timeout_ms: integer
  concurrency: parallel|serialized|resource_locked
  approval_hint: never|policy|always
```

### ToolCall / ToolResult

```yaml
ToolCall:
  id: ToolCallId
  tool_name: string
  tool_version: string
  normalized_args: object
  args_hash: string
  idempotency_key: string|null
  status: proposed|authorizing|approved|running|completed|failed|cancelled|indeterminate

ToolResult:
  tool_call_id: ToolCallId
  status: success|error|cancelled|indeterminate
  content: bounded-model-visible-content
  artifacts: [ArtifactRef]
  error: HarnessError|null
  metadata: object
```

### PolicyDecision

```yaml
PolicyDecision:
  id: string
  action_hash: string
  outcome: allow|deny|ask|amend
  reason_code: string
  user_message: string
  granted_scope: object|null
  expires_at: timestamp|null
  policy_version: string
```

## 状态与不变量

- INVARIANT：每个 completed/failed/cancelled tool call 恰有一个最终 ToolResult。
- INVARIANT：Turn 只有一个终态，终态后不再接受普通事件。
- INVARIANT：Event sequence 在 thread 内严格递增。
- INVARIANT：未知 schema 字段可保留；未知必需语义触发能力协商失败。
- INVARIANT：approval 绑定规范化 action hash；参数变化必须重新决策。
- INVARIANT：artifact 内容不直接塞入 event；event 只保存引用、hash、mime 和 size。
- INVARIANT：删除 projection 不影响 event 事实；归档不等于删除。
- INVARIANT：fork 复制可见历史边界和 lineage，不复制运行中的进程句柄。

## 实现检查

1. 为每个 tagged union 生成静态类型与 JSON Schema。
2. 用 golden fixtures 验证跨语言序列化。
3. 对 id、sequence、revision、status transition 建数据库约束。
4. 对 ToolCall、Approval、Artifact 建外键或等价一致性检查。
5. 拒绝持久化 provider 原始任意对象；先归一化并脱敏。
6. 为每个破坏性 schema 变更编写迁移和旧 fixture 回放测试。

