# LangGraph 协议与状态投影

## 目录

- [两套模型](#两套模型)
- [运行时原生状态](#运行时原生状态)
- [Harness 规范模型](#harness-规范模型)
- [事件 Envelope](#事件-envelope)
- [Stream 映射](#stream-映射)
- [Command 协议](#command-协议)
- [顺序与幂等](#顺序与幂等)
- [版本与兼容](#版本与兼容)
- [安全边界](#安全边界)

## 两套模型

LangGraph core 的公开读取模型是 `StateSnapshot` 与多种 stream part；完整产品还需要稳定的 thread/turn/item/event 模型。adapter 应保留原生 graph/task/channel 身份，并隔离 Python/JS 内部类型差异。

不得把一次 graph invocation 简单等同于一条 assistant message。

## 运行时原生状态

`StateSnapshot` 至少包含：

- `values`：当前 channel 输出投影；
- `next`：下一步 node 名称；
- `config`：含 thread/checkpoint namespace/id；
- `metadata`：source、step、writes、parents/run id 等；
- `created_at` 与 `parent_config`；
- `tasks`：task id/name/path/error/interrupt/state/result；
- `interrupts`：当前未解决 interrupt。

存储层 `Checkpoint` 则包含 schema version、id、timestamp、channel values/version、versions seen、updated channels；两者不可混用。

## Harness 规范模型

- **thread**：持久会话，键含 tenant/profile/thread_id；可有多个 run/turn。
- **turn**：一次 invoke/stream/resume/update/fork 请求，含 run_id、base checkpoint、终态。
- **item**：node task、model call、tool call、interrupt、artifact、state patch、subgraph run。
- **event**：item/state 生命周期的 append-only 事实，含 sequence 与 causality。

建议 ID：`thread_id`、`run_id`、`turn_id`、`item_id`、`task_id`、`checkpoint_id`、`checkpoint_ns`、`interrupt_id`、`event_id`。不要用显示名称充当身份。

## 事件 Envelope

```json
{
  "schema_version": "1",
  "thread_id": "th_...",
  "turn_id": "turn_...",
  "run_id": "run_...",
  "sequence": 42,
  "event_id": "ev_...",
  "type": "graph.task.completed",
  "checkpoint_ns": "parent|child:task",
  "task_id": "task_...",
  "caused_by": "ev_...",
  "payload": {},
  "timestamp": "RFC3339",
  "redaction": {"policy": "default"}
}
```

payload 需 schema 化；异常对象、callable、channel 实例不得直接越过进程边界。

## Stream 映射

| 原生 mode | 规范事件 | 用途 |
|---|---|---|
| `values` | `graph.state.snapshot` | 全状态投影/补拉 |
| `updates` | `graph.state.updated` | node/task delta |
| `messages` | `model.message.delta` | token/message 流 |
| `custom` | `item.custom` | 用户定义进度 |
| `checkpoints` | `graph.checkpoint.created` | durable boundary |
| `tasks` | `graph.task.started/completed/failed` | 执行可观测性 |
| `debug` | 以上调试组合 | 开发诊断，不作稳定 UI 协议 |

开启 subgraphs 时事件必须带 namespace/path。一个 stream 可请求多个 mode，consumer 不应靠 tuple 长度猜协议版本。

## Command 协议

- `update`：写入 state channels；进入 reducer，不是任意 JSON 覆盖。
- `goto`：node name、node sequence、`Send` 或 `Send` sequence。
- `graph`：当前 graph、最近 parent；跨任意祖先不是默认合同。
- `resume`：单值恢复下一个 interrupt，或 interrupt id→value mapping。
- `update_state`：由外部创建新 checkpoint，需 `as_node`/task attribution。
- resume/update/fork 请求要有 client request id，网络重试不得重复创建分支。

## 顺序与幂等

- event sequence 在 thread 或 run scope 内单调，scope 必须写入协议。
- `event_id` 用于传输去重；`task_id + write index` 用于 pending write 去重。
- checkpoint id 是持久状态位置，不替代事件 sequence。
- snapshot 带 `last_sequence`；consumer 先装载 snapshot，再应用大于该值的事件。
- sequence gap 触发补拉，不能悄悄跳过。
- duplicate/reordered stream part 经 adapter 后仍得到同一 projection hash。
- external action receipt 与 checkpoint receipt 分开记录。

## 版本与兼容

- envelope、payload、checkpoint storage 各有独立 `schema_version`。
- capability handshake 声明支持的 stream modes、subgraph namespace、interrupt mapping 和 time travel。
- reader 至少支持当前版与上一版；writer 只写当前版。
- checkpoint migration 必须离线/在线可恢复，保留旧版本备份与 digest。
- Python 与 JS adapter 可产生同一规范终态，但不要求内部 checkpoint 二进制互读。
- 未知 event type 按扩展规则保留/忽略，不得导致已有状态回滚。

## 安全边界

- state、event、trace 分别做 secret/PII 分类与 redaction。
- interrupt payload 是不可信 UI 数据，resume payload 是不可信用户输入。
- serializer allowlist 禁止任意对象反序列化执行。
- tenant/thread/namespace 的授权在 storage/query 层强制，不依赖前端过滤。
- custom event 不能伪造 core `graph.*` type。
- debug stream 不应默认进入多租户生产客户端。
