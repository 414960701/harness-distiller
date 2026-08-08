# Claude-Code-like 协议与状态模型

> 本篇提供 CLI、IDE、Desktop、Web 与 headless 共用的实现协议。全部结构均为 `inference/design synthesis`，不是 Claude Code 私有协议或 JSONL 内部格式。

## 目录

- [设计原则](#设计原则)
- [协议封套](#协议封套)
- [领域标识](#领域标识)
- [Command](#command)
- [Event](#event)
- [Item](#item)
- [状态投影](#状态投影)
- [权限协议](#权限协议)
- [工具协议](#工具协议)
- [后台与多 Agent](#后台与多-agent)
- [版本与兼容](#版本与兼容)
- [升级与测试](#升级与测试)

## 设计原则

- 事实是追加事件，UI 状态是可重建投影。
- Command 表示请求，Event 表示已接受的事实。
- 不把模型 provider 的流式 chunk 当稳定产品协议。
- 不把 `~/.claude/...jsonl` 的内部行格式当集成 API。
- 所有副作用通过 tool call、permission 和 execution event 外显。
- 未知字段可忽略，未知必需事件必须触发 capability error。
- 同一 event id 全局只应用一次。

## 协议封套

```json
{
  "protocol":"harness.events",
  "version":"1.2",
  "id":"evt_01...",
  "session_id":"ses_01...",
  "turn_id":"turn_01...",
  "sequence":42,
  "time":"2026-08-08T12:00:00Z",
  "type":"tool.completed",
  "actor":{"kind":"agent","id":"agent_main"},
  "payload":{},
  "meta":{"trace_id":"...","redaction":"v1"}
}
```

`sequence` 只保证 session 内单调；跨 session 用时间不能推出因果。

服务端先写 durable log，再向 surface 发布 committed event。

## 领域标识

- `workspace_id`：canonical root 与 trust identity 的稳定映射。
- `session_id`：可 resume 的会话单位。
- `thread_id`：若共享框架使用 Thread 抽象，应作为 session 的兼容别名或父级容器，必须在 schema 中固定一种语义。
- `turn_id`：一次用户输入到终态。
- `item_id`：可渲染内容、tool intent 或 observation。
- `tool_call_id`：请求与结果配对。
- `run_id`：main/subagent/background 的执行实例。
- `checkpoint_id`：可恢复的 conversation/code 边界。
- `artifact_id`：大输出、patch、日志或报告的内容寻址引用。
- `command_id`：去重用户或 surface 请求。

标识必须不可从用户输入直接拼接文件路径。

## Command

### 通用结构

```yaml
Command:
  command_id: string
  expected_session_revision: integer|null
  kind: string
  args: object
  actor: UserRef|ClientRef
  capability_token: string|null
```

### 必需命令

- `session.create`
- `session.resume`
- `session.branch`
- `session.rename`
- `turn.submit`
- `turn.steer`
- `turn.interrupt`
- `permission.resolve`
- `mode.change`
- `checkpoint.rewind`
- `agent.cancel`
- `artifact.fetch`

Command 被拒绝也应产生可审计 `command.rejected`，但敏感 token 不写日志。

### 幂等

同一 `command_id` 重试返回第一次结果；参数不同则报 idempotency conflict。

`turn.submit` 在网络超时后可安全重试，不能创建两个 turn。

## Event

### 生命周期事件

- `session.created|resumed|branched|renamed`
- `turn.started|state_changed|completed|failed|cancelled`
- `model.requested|item_delta|item_committed|failed`
- `context.materialized|compaction_started|compaction_completed|compaction_failed`
- `permission.requested|resolved|expired`
- `tool.requested|started|output_delta|completed|failed|cancelled`
- `checkpoint.created|rewound`
- `agent.spawned|state_changed|message|completed|failed|cancelled`
- `hook.started|completed|failed`
- `task.created|updated`

delta 可为短期传输事件；只有 `item_committed` 是可恢复内容事实。

### 终态唯一性

`turn.completed|failed|cancelled` 互斥。event store 使用唯一约束 `(turn_id, terminal=true)`。

迟到工具结果可以记录为 `tool.late_result`，但不能把 cancelled turn 改回 active。

## Item

```yaml
Item:
  id: string
  kind: user_message|assistant_message|tool_call|tool_result|plan|summary|attachment|diagnostic
  role: user|assistant|tool|system|null
  content: [ContentPart]
  provenance: Provenance
  trust: managed|user|workspace|external|model
  created_at: timestamp
  supersedes: string|null
```

### ContentPart

- `text`：UTF-8 文本。
- `json`：有 schema id 的结构化值。
- `artifact_ref`：大对象引用和摘要。
- `file_ref`：path、revision、line range。
- `image_ref`：mime、dimensions、artifact id。
- `redacted`：原因与稳定占位符。

任何 secret 被替换为 `redacted`，原值不得进入 model 或普通事件日志。

### ContextFragment

```json
{"item_id":"i1","origin":"CLAUDE.md","scope":"project","priority":300,"tokens":218,"trust":"workspace","revision":"sha256:..."}
```

fragment 记录装载事实，不表示它能覆盖 policy。

## 状态投影

### SessionView

```yaml
SessionView:
  id: string
  status: idle|active|blocked|completed|archived
  mode: string
  current_turn_id: string|null
  revision: integer
  pending_permissions: [PermissionRequest]
  agents: [AgentView]
  tasks: [Task]
  context_usage: ContextUsage
```

### Reducer 规则

```python
def reduce(view, event):
    if event.id in view.applied_ids: return view
    require(event.sequence == view.last_sequence + 1)
    handler = reducers.get(event.type)
    if not handler: return preserve_unknown(view, event)
    next_view = handler(view, event.payload)
    return next_view.with_revision(event.sequence)
```

缺 sequence 时先补拉日志，不可猜测中间状态。

## 权限协议

```yaml
PermissionRequest:
  id: string
  tool_call_id: string
  action: string
  normalized_target: object
  risk: [string]
  matched_rules: [RuleRef]
  allowed_resolutions: [allow_once,allow_scope,deny]
  expires_at: timestamp
```

```yaml
PermissionDecision:
  outcome: allow|ask|deny
  resolution: allow_once|allow_scope|deny|null
  rule_id: string|null
  provenance: managed|user|project|local|runtime_default
  reason_code: string
```

surface 只能提交 resolution；最终 decision 由 runtime 重算，防止过期或 TOCTOU。

## 工具协议

```yaml
ToolIntent:
  call_id: string
  registry_name: string
  arguments: object
  effect: read|workspace_write|external_write|process
  expected_workspace_revision: string|null
```

```yaml
ToolResult:
  call_id: string
  status: succeeded|failed|cancelled|denied|outcome_unknown
  output: [ContentPart]
  exit_code: integer|null
  changed_paths: [string]
  duration_ms: integer
  truncated: boolean
```

每个 `ToolIntent` 恰好一个 committed `ToolResult`；流式 output 不改变配对规则。

外部写工具必须声明 reconciliation strategy。

## 后台与多 Agent

```yaml
AgentRun:
  id: string
  parent_run_id: string|null
  definition_id: string
  status: queued|running|blocked|completed|failed|cancelled
  budget: object
  capability_envelope: object
  workspace_view: object
```

team message 带 `message_id`、sender、recipients、reply_to 和 artifact refs。

父 session 的 sequence 只保存跨边界摘要；子 run 可以有独立 event stream。

## 版本与兼容

- major：删除/改变既有语义，需要显式 negotiation。
- minor：增加可忽略字段或可选事件。
- schema：每种 payload 单独带 schema id/version。
- client 启动时发送支持的版本和 capabilities。
- server 回应选中版本、必需扩展和降级理由。
- session 文件记录 writer version 和最低 reader version。

不得让旧 client 在不知道 sandbox 状态时显示“已隔离”。

## 升级与测试

- 能跑：进程内 command/event 和 JSONL 日志。
- 能用：稳定 ids、projection、resume、permission round-trip。
- 顺手：多 surface、background/subagent streams、artifact store。
- 好用：远程 relay、offline retry、protocol negotiation、迁移工具。

Oracle：删除所有投影后从 event 0 重建，SessionView 与删除前相同。

Oracle：重复发送每条 event，最终视图不变。

Oracle：交换有因果关系的 sequence 时 reducer 明确拒绝。

Oracle：旧 client 收到未知 optional event 仍可继续；未知 required capability 则停止并解释。

Oracle：CLI、IDE 和 headless 消费同一 fixture，turn、tool、permission 终态一致。
