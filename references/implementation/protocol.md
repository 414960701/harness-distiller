# Command/Event 协议

## 目录

- [传输与握手](#传输与握手)
- [命令](#命令)
- [事件](#事件)
- [流式 Item](#流式-item)
- [错误](#错误)
- [重连与兼容](#重连与兼容)

## 传输与握手

协议与传输分离。`runnable` 可用进程内调用；`usable` SHOULD 支持 stdio JSONL 或本地 socket；远程连接 MUST 使用认证、加密与背压。

生成工程时复制 `assets/contracts/event.schema.json` 与 `assets/contracts/tool-spec.schema.json` 作为 v1 起点；按目标语言生成静态类型，不要手写多份漂移 schema。

首次连接：

```json
{"id":"cmd_1","method":"initialize","params":{"client":{"name":"desktop","version":"1.2.0"},"protocolVersions":[1],"capabilities":["item-deltas","approval-v1"]}}
```

```json
{"id":"cmd_1","result":{"protocolVersion":1,"serverVersion":"0.4.0","capabilities":["item-deltas","approval-v1","thread-fork"]}}
```

初始化前发送其它命令 MUST 返回 `not_initialized`。重复初始化 MUST 可预测失败。

## 命令

最低命令表：

| 命令 | 幂等 | 说明 |
|---|---:|---|
| `thread.create` | keyed | 创建 thread |
| `thread.get/list/archive/fork` | 读或 keyed | 查询、归档、分叉 |
| `turn.start` | keyed | 启动一个 turn |
| `turn.steer` | keyed | 向活动 turn 追加用户输入 |
| `turn.cancel` | keyed | 请求取消 |
| `approval.resolve` | keyed | 同意、拒绝或缩小范围 |
| `process.write` | 否 | 向活动 PTY 写入 |
| `artifact.get` | 读 | 读取 artifact |
| `subscription.open/close` | keyed | 管理事件订阅 |

所有可能重试的写命令带 `idempotencyKey`。同一 key、同一 body 返回原结果；同一 key、不同 body 返回冲突。

`turn.start` 示例：

```json
{
  "id":"cmd_20",
  "method":"turn.start",
  "params":{
    "threadId":"thr_1",
    "input":[{"type":"text","text":"修复失败测试"}],
    "overrides":{"model":"provider/model","cwd":"workspace://root"},
    "idempotencyKey":"9d6d..."
  }
}
```

## 事件

最低事件表：

```text
thread.created / thread.updated / thread.archived
turn.queued / turn.started / turn.status_changed / turn.completed
item.started / item.delta / item.completed
tool.proposed / tool.authorization_started / tool.started / tool.progress / tool.completed
approval.requested / approval.resolved / approval.expired
context.compaction_started / context.compacted
artifact.created / artifact.updated
checkpoint.created
runtime.warning / runtime.error
```

事件 envelope：

```json
{
  "eventId":"evt_301",
  "threadId":"thr_1",
  "turnId":"turn_9",
  "sequence":301,
  "type":"item.delta",
  "schemaVersion":1,
  "causationId":"evt_300",
  "correlationId":"trace_7",
  "createdAt":"2026-08-08T12:00:00Z",
  "payload":{"itemId":"item_4","delta":{"type":"text","text":"正在检查"}}
}
```

## 流式 Item

`item.started` 创建 identity；零个或多个 `item.delta` 追加；恰一个 `item.completed` 给最终内容/hash/status。客户端必须能忽略未知 delta 类型。

Tool 参数流式增量先存为不可执行 draft；只有 schema 校验后的 `tool.proposed` 才能进入 policy。不得执行未闭合 JSON 或 UI 本地拼接参数。

## 错误

统一错误：

```yaml
HarnessError:
  code: invalid_input|not_found|conflict|not_initialized|unsupported_capability|model_error|tool_error|policy_denied|approval_expired|sandbox_violation|cancelled|timeout|budget_exhausted|overloaded|internal_error
  message: safe user-facing text
  retryable: boolean
  retry_after_ms: integer|null
  details: redacted object|null
```

provider、数据库和 OS 原始错误只进入受控 details；不得把秘密、完整环境或任意堆栈发给客户端。

## 重连与兼容

客户端重连流程：

1. 读取 thread snapshot 及 `lastSequence`；
2. 订阅 `afterSequence=lastSequence`；
3. 顺序应用事件并去重 event id；
4. 遇到 sequence gap，停止投影并重新读取 snapshot；
5. 不根据“最后一行文本”猜 turn 状态。

兼容规则：

- 新可选字段可在同协议版本加入；
- 新必需语义通过 capability 协商；
- 删除或改变字段语义必须提升协议版本；
- 服务端至少保存一个旧版本 adapter 或给出明确升级错误；
- golden fixtures 覆盖旧客户端/新服务端和新客户端/旧服务端。
