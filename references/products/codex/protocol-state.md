# Codex-like 协议与状态

## 目录

1. 设计目标
2. 信封与版本
3. 对象状态
4. 命令表
5. 事件表
6. JSON 示例
7. 顺序、重放与背压
8. 错误模型
9. 兼容策略

## 设计目标

`公开事实`：公开 app-server 文档和协议源码暴露 thread、turn、item、通知与请求语义。
`设计综合`：本文给出品牌无关的 canonical protocol，适合 JSON-RPC、WebSocket、stdio 或进程内 adapter。
协议只描述命令和事实事件，不让客户端直接改数据库行。

## 信封与版本

命令信封：

```json
{
  "protocolVersion": "1.0",
  "requestId": "req_01",
  "method": "turn.start",
  "params": {},
  "client": {"name": "terminal", "version": "0.1"}
}
```

事件信封：

```json
{
  "protocolVersion": "1.0",
  "eventId": "evt_000042",
  "threadId": "thr_01",
  "turnId": "turn_03",
  "sequence": 42,
  "type": "item.completed",
  "occurredAt": "2026-08-08T10:00:00Z",
  "causationId": "call_07",
  "payload": {}
}
```

`sequence` 在 thread 内单调递增；`eventId` 全局或安装内唯一。
金额、token 和时间字段使用整数或明确单位，避免浮点歧义。
未知字段必须忽略；未知必需 capability 必须拒绝协商。

## 对象状态

Thread 状态：`active`、`archived`、`deleted`；deleted 可以是 tombstone。
Turn 状态：`queued`、`running`、`waiting_approval`、`cancelling`、`completed`、`failed`、`interrupted`。
Item 状态：`started`、`streaming`、`completed`、`failed`、`interrupted`。
Approval 状态：`pending`、`allowed`、`denied`、`expired`、`cancelled`。
Process 状态：`prepared`、`running`、`exited`、`timed_out`、`cancelled`、`unknown_effect`。

终态不可逆；rollback 创建新的状态事实，不修改历史事件。
thread archived 不终止活动 turn，除非产品合同显式规定并发出独立 interrupt。

## 命令表

| 命令 | 关键参数 | 前置条件 | 成功结果 |
|---|---|---|---|
| `initialize` | versions、capabilities | 新连接 | 协商后的版本和能力 |
| `thread.start` | cwd、config、metadata | 配置有效 | thread snapshot |
| `thread.read` | threadId、afterSequence | 可见 thread | snapshot + events |
| `thread.list` | cursor、filter | 已初始化 | 分页摘要 |
| `thread.resume` | threadId | 无活动写者冲突 | runtime attachment |
| `thread.fork` | threadId、atSequence | checkpoint 可读 | 新 thread |
| `thread.rollback` | threadId、checkpoint | 无活动 turn | rollback event |
| `thread.archive` | threadId | 可写 metadata | archived event |
| `turn.start` | threadId、input、options | 无活动前台 turn | turn id |
| `turn.steer` | turnId、input | turn running | accepted/queued |
| `turn.interrupt` | turnId、reason | turn 非终态 | interrupt accepted |
| `approval.resolve` | approvalId、decision、scope | approval pending | resolution event |
| `process.stdin` | processId、bytes | process running | accepted offset |
| `process.resize` | processId、cols、rows | PTY running | applied event |
| `subscription.open` | threadId、afterSequence | thread 可读 | snapshot + stream |
| `subscription.close` | subscriptionId | subscription 存在 | closed |

所有有副作用命令接受 `idempotencyKey`。
同一 key 与相同参数重复提交返回首次结果；参数不同返回 conflict。

## 事件表

| 事件 | 必要 payload | 含义 |
|---|---|---|
| `thread.created` | cwdIdentity、configDigest | thread 已 durable |
| `thread.snapshot` | state、lastSequence | 投影快照，不代替事件 |
| `thread.forked` | parentId、atSequence | 新分支建立 |
| `thread.rolled_back` | checkpoint、workspaceResult | 新有效头建立 |
| `turn.queued` | turnId | 等待前台执行 |
| `turn.started` | inputItemId、budget | runtime 接受执行 |
| `turn.steering_accepted` | inputItemId、mode | 输入已排队或触发重采样 |
| `turn.interrupt_requested` | reason | 已开始取消传播 |
| `turn.completed` | finalItemId、usage | 正常终态 |
| `turn.failed` | error | 失败终态 |
| `turn.interrupted` | reason、effects | 中断终态 |
| `item.started` | item | item 生命周期开始 |
| `item.delta` | itemId、channel、delta | 可丢弃重建的增量 |
| `item.completed` | item | 完整 canonical item |
| `item.failed` | itemId、error | item 失败终态 |
| `tool.approval_requested` | approval | durable 待审批 |
| `tool.approval_resolved` | approvalId、decision | 审批闭合 |
| `process.started` | processId、commandView | 进程实际启动 |
| `process.output_delta` | processId、stream、bytes | stdout/stderr 增量 |
| `process.exited` | processId、exitCode、durationMs | 进程终态 |
| `workspace.diff_updated` | revision、summary | 工作区投影变化 |
| `context.compacted` | before、after、summaryItemId | 上下文头更新 |
| `usage.updated` | token、cost、limits | 资源使用投影 |

Item 类型至少包括：`user_message`、`agent_message`、`reasoning_summary`、`tool_call`、`tool_result`、`plan`、`diff`、`compaction`、`error`。
敏感 reasoning 可只提供摘要；协议不要求暴露私有链式思维。

## JSON 示例

创建 turn：

```json
{
  "protocolVersion": "1.0",
  "requestId": "req_18",
  "method": "turn.start",
  "params": {
    "threadId": "thr_01",
    "input": [{"type": "text", "text": "修复测试失败"}],
    "idempotencyKey": "client-a:18"
  }
}
```

工具 item 完成：

```json
{
  "protocolVersion": "1.0",
  "eventId": "evt_63",
  "threadId": "thr_01",
  "turnId": "turn_03",
  "sequence": 63,
  "type": "item.completed",
  "causationId": "rsp_item_09",
  "payload": {
    "item": {
      "id": "item_12",
      "type": "tool_call",
      "callId": "call_07",
      "tool": "shell",
      "argumentsDigest": "sha256:...",
      "status": "completed"
    }
  }
}
```

审批请求只展示经过规范化和脱敏的动作：

```json
{
  "type": "tool.approval_requested",
  "payload": {
    "approval": {
      "id": "apr_2",
      "callId": "call_07",
      "action": "run command",
      "target": "git push origin feature",
      "risk": ["external_write"],
      "allowedScopes": ["once", "session_prefix"],
      "expiresAt": "2026-08-08T10:05:00Z"
    }
  }
}
```

## 顺序、重放与背压

服务端按 thread sequence 提供至少一次事件投递。
客户端持久化最后应用 sequence，并按 event id 去重。
发现 sequence gap 时暂停投影，调用 `thread.read(afterSequence)` 补洞。
delta 可以在断线后省略，只要 completed item 包含完整 canonical 内容。
快照包含 `lastSequence`；应用快照后只重放更大的 sequence。
慢订阅者队列溢出时发送 `resync_required` 并断开该订阅，不阻塞 runtime。

## 错误模型

错误结构至少包含 `code`、`message`、`retryable`、`details`、`requestId`。
稳定 code：`invalid_request`、`not_found`、`conflict`、`permission_denied`、`sandbox_denied`、`deadline_exceeded`、`provider_unavailable`、`protocol_mismatch`、`internal`。
用户文案可以本地化，机器消费者只依赖 code。
错误 details 不得包含密钥、完整环境变量或未脱敏模型 payload。
命令被接受后发生的失败通过事件终态表达，不用 RPC transport error 代替。

## 兼容策略

连接先协商 major/minor 和 capability 集合。
破坏字段语义、枚举含义或顺序保证时提升 major。
新增可选字段、事件或 capability 时提升 minor。
枚举解析必须保留 unknown 分支，旧客户端遇到未知 item 可显示通用卡片。
写入新 schema 前保存原始 rollout，并让索引迁移可重跑。
协议合同测试使用 golden JSON，禁止因语言序列化器升级发生无意漂移。

对象持久化与恢复见 [persistence-recovery.md](persistence-recovery.md)。
表面体验约束见 [experience.md](experience.md)，公开来源见 [sources.md](sources.md)。
