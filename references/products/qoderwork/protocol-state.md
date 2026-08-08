# QoderWork-like 协议与状态

> 本文为 `inference` 实现协议。QoderWork 未公开生产客户端的事件 schema、存储引擎或进程间协议。

## 目录

- [设计原则](#设计原则)
- [标识与信封](#标识与信封)
- [核心 schema](#核心-schema)
- [事件表](#事件表)
- [状态机](#状态机)
- [三栏投影](#三栏投影)
- [命令与幂等](#命令与幂等)
- [版本演进](#版本演进)
- [黑盒 oracle](#黑盒-oracle)

## 设计原则

协议以追加式事件为事实源，数据库行和 UI view model 都是可重建投影。
所有用户可见进度来自事件，不解析模型自然语言。
大文件、截图和完整工具结果放 blob/artifact store，事件只留引用。
每个 Task 的序号单调递增；跨任务只依赖时间戳时不得推断因果。
命令、事件和外部动作都具有稳定 idempotency key。

## 标识与信封

```json
{
  "event_id": "evt_01...",
  "event_type": "StepStarted.v1",
  "task_id": "task_01...",
  "run_id": "run_01...",
  "seq": 42,
  "causation_id": "cmd_01...",
  "correlation_id": "turn_01...",
  "occurred_at": "2026-08-08T10:20:30.123Z",
  "actor": {"kind": "runtime", "id": "agent-main"},
  "payload": {},
  "sensitivity": "internal",
  "schema_version": 1
}
```

`seq` 在同一 Task 内唯一，提交使用 compare-and-swap expected sequence。
`causation_id` 定位产生事件的命令，`correlation_id` 串联一次用户委派。
UI 接到跳号时必须补拉事件，不猜测中间状态。

## 核心 schema

对接通用 harness 协议时，QoderWork-like 的 `Task` 可映射为其他系统所称的 `thread`，但本产品 UI 与存储合同始终使用 Task；不要同时创建两个顶层聚合。
Conversation 中的最小追加单元可抽象为 `Item`：Turn、artifact card、approval card 都是带 `item_id` 的可排序投影，真实执行事实仍来自 event。

```yaml
Task:
  id: string
  title: string
  status: draft|queued|running|waiting|partial|completed|failed|cancelled|archived
  config_snapshot_id: string
  active_run_id: string|null
  last_seq: integer
  created_at: timestamp
  updated_at: timestamp
Step:
  id: string
  task_id: string
  goal: string
  kind: plan|research|tool|transform|validate|deliver
  deps: [step_id]
  status: queued|ready|running|validating|blocked|succeeded|failed|cancelled|superseded
  attempt: integer
  expected_outputs: [OutputSpec]
ToolCall:
  id: string
  step_id: string
  provider: builtin|connector|mcp|computer_use
  tool_name: string
  args_ref: blob_ref
  policy_decision_id: string
  status: proposed|awaiting_approval|running|succeeded|failed|cancelled|unknown
Artifact:
  id: string
  task_id: string
  version: integer
  uri: string
  sha256: string
  mime: string
  source_step_id: string
  validation: pending|valid|invalid|stale
```

## 权限与能力 schema

```yaml
WorkingFolderGrant:
  id: string
  task_id: string
  canonical_root: string
  device_identity: string
  operations: [read, create, update, rename, trash]
  granted_at: timestamp
  expires_at: timestamp|null
  revoked_at: timestamp|null
CapabilityBinding:
  id: string
  task_id: string
  kind: skill|kit|mcp|connector|hook
  name: string
  version: string
  config_digest: string
PolicyDecision:
  id: string
  action_digest: string
  verdict: allow|deny|ask
  risk: low|medium|high|forbidden
  reasons: [string]
  grant_refs: [string]
```

## 事件表

| 事件 | 必需 payload | 主要投影 |
|---|---|---|
| `TaskCreated` | title、config_snapshot | Sidebar |
| `TaskRunStarted` | run_id、lease | Sidebar/Monitor |
| `TurnAppended` | role、content_refs | Conversation |
| `PlanCommitted` | step graph | Task Monitor |
| `PlanRevised` | revision、mapping | Task Monitor |
| `StepStarted` | step_id、attempt | Task Monitor |
| `ToolCallProposed` | call_id、tool、args digest | Monitor detail |
| `PolicyDecided` | decision_id、verdict | Monitor/approval |
| `ToolCallObserved` | result_ref、receipt | Monitor detail |
| `ArtifactProduced` | artifact metadata | Conversation card |
| `ArtifactValidated` | validator、diagnostics | Conversation card |
| `StepBlocked` | blocker、recovery actions | 三栏 |
| `TaskStatusChanged` | from、to、reason | 三栏 |
| `ScheduleTriggered` | schedule_id、dedupe key | Scheduled/Sidebar |
| `MemoryChanged` | record_id、operation | Awareness |

## 状态机

Task 的允许转换：

```text
draft → queued → running → completed
                    ├→ waiting → running
                    ├→ partial
                    ├→ failed
                    └→ cancelled
terminal → archived → terminal
```

`archived` 是可逆的可见性状态，不删除任务事实。
`completed` 不得回到 running；追加需求应创建新 Turn 和新 Run。
恢复 `failed` 创建新 Run，旧 Run 保持终态。
ToolCall 在进程崩溃后若无可靠 receipt，先标为 `unknown`，不得直接判 failed 或重放。

## 三栏投影

SidebarView 读取 Task、Schedule、Group 与最近事件时间。
ConversationView 读取 Turn 与 Artifact；工具详情通过引用按需加载。
MonitorView 读取 Plan/Step/ToolCall/PolicyDecision 的事件投影。
三个投影均携带 `projected_through_seq`。
若 Conversation 到 seq 80、Monitor 只到 seq 78，UI 显示同步中而不展示矛盾终态。
通知包含 task_id、event_id 和 deep link，点击后定位具体 Step 或 approval。

## 命令与幂等

客户端命令至少包括 `CreateTask`, `AppendTurn`, `BindFolder`, `StartRun`, `CancelRun`, `ApproveCall`, `RetryStep`, `ArchiveTask`。
命令带 `command_id`, `expected_seq`, `client_instance_id`。
服务端记录已处理 command_id，相同命令重试返回原结果。
外部写操作带 `action_key = hash(task, step, attempt, normalized_target, intent)`。
邮件、发布、支付和表单提交必须保存 provider receipt。
Scheduled trigger 使用 `schedule_id + intended_fire_time` 去重。

## 版本演进

- 事件类型使用名字加 major 版本，如 `ArtifactProduced.v1`。
- 新增可选字段不改 major；删除或改语义必须新增类型版本。
- reducer 能读取至少两个历史 major，并提供离线迁移器。
- TaskConfigSnapshot 永不原地更新，设置变更创建新 snapshot。
- capability 版本在 TaskRun 启动时固定，避免运行中 Skill 热更新改变结果。
- 未知事件必须可跳过并保留，不能导致整个任务不可读。

## 失败恢复

事件提交和本地文件原子替换之间使用 outbox/intent record 协调。
artifact blob 先写临时区并校验 hash，再提交 ArtifactProduced。
UI 断线按最后 seq 补拉；重复事件按 event_id 去重。
runtime lease 到期后，recovery worker 只能接管无活跃心跳的 Run。
非幂等 ToolCall 先查询 receipt；无法判定时进入 `waiting_user_resolution`。

## 黑盒 oracle

1. 人为打乱 WebSocket 事件顺序，三栏最终仍与事件重放一致。
2. 重复发送同一 CreateTask 命令只生成一个 Task。
3. 在 ArtifactProduced 前杀进程，不出现 Ready card 或半文件。
4. 在外部发送成功后、receipt 入库前杀进程，恢复后不自动重发。
5. 老版本事件流经迁移后保持 transcript、artifacts 与终态。
6. 归档再恢复不改变 last_seq 之前的事实。
7. 一个任务事件损坏不阻止其他任务加载。
8. UI 的 completed 状态始终能定位对应 CompletionGate 事件。
