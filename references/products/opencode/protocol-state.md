# OpenCode-like 协议与状态

## 目录

- [协议目标](#协议目标)
- [canonical 对象](#canonical-对象)
- [事件信封](#事件信封)
- [事件集合](#事件集合)
- [HTTP 与 SSE](#http-与-sse)
- [客户端投影](#客户端投影)
- [兼容与迁移](#兼容与迁移)
- [不变量](#不变量)

## 协议目标

协议要让 TUI、Web、Electron、IDE 和 SDK 在不访问 runtime 内存的情况下完成：创建/list/resume session，提交 prompt，观察 message/part/tool/event，处理 permission/question，控制 PTY，取消和重连。

固定代码有 v1 session/message/part 事件与 v2 durable `session.next.*`。蒸馏实现选择一个 canonical schema；推荐 v2 event-sourced core，向 v1 `WithParts` 生成兼容 projection。

与共享 harness 术语的映射固定为：OpenCode `session` 对应 thread；一次 admitted prompt 到 terminal 对应 turn；`message`、`part`、permission 与 PTY card 都是 item；每次状态变化是 event。产品文档继续使用 OpenCode 原名，跨产品蓝图使用这组映射，不能再造第三套实体。

## canonical 对象

| 对象 | 标识与关键字段 | 权威来源 |
|---|---|---|
| Project | id, worktree, vcs | DB + workspace scan |
| Workspace | id, project, directory, status | DB/control plane |
| Session | id, parent, location, agent, model, status | DB projection |
| Input | id, session, prompt, delivery, admitted_seq | durable input/event |
| Message | id, session, type/role, created | durable event projection |
| Part | id, message, type, state | durable event projection |
| Permission | id, session, permission, patterns, reply | event + pending state |
| PTY | id, cwd, command, offset, status | runtime + event snapshot |
| Event | id, type, data, location, durable metadata | append store |

thread/turn/item 的兼容 ID 必须引用原 session/input/message/part ID，不复制对象。一个 turn 可以包含多个 provider step，但只能归属一个 admitted input。

所有 ID 由 server 生成或验证前缀/唯一性。客户端提供 id 仅用于幂等提交，不得覆盖其他 session 对象。

## 事件信封

```json
{
  "id": "evt_...",
  "type": "session.next.tool.ended",
  "data": {"sessionID": "ses_..."},
  "location": {"directory": "/repo", "workspaceID": "wsp_..."},
  "durable": {"aggregateID": "ses_...", "seq": 17, "version": 1},
  "metadata": {"traceID": "..."}
}
```

durable `seq` 在 aggregate 内从固定起点严格递增；live delta 可以没有 durable 字段。任何 durable event 必须先 commit 再广播。事件 payload 不携带 secret、provider key 或未截断超大输出。

## 事件集合

最小集合：

- `session.created|updated|deleted|status.changed`；
- `session.input.admitted|promoted`；
- `session.agent.switched|model.switched|moved`；
- `session.step.started|ended|failed`；
- `session.text.started|delta|ended`；
- `session.reasoning.started|delta|ended`；
- `session.tool.started|running|ended|failed`；
- `session.compaction.completed`；
- `permission.asked|replied`、`question.asked|replied`；
- `pty.created|output|exited|deleted`；
- `mcp.status.changed`、`lsp.status.changed`；
- `server.connected` 和 capability/version handshake。

完整 ended event 包含最终 text/reasoning/tool output 或其 artifact ref；客户端丢失 delta 后仍可收敛。

## HTTP 与 SSE

最低 routes：health/version/capabilities，project/workspace，session CRUD/list/history/prompt/cancel，message page，permission reply，tool metadata，MCP/LSP status，PTY create/input/resize/delete，SSE event，OpenAPI document。

list 使用 cursor，不用易漂移的 offset。SSE 支持 `after`/Last-Event-ID 或让 client 带每个 aggregate 最后 seq；检测 gap 返回 `resync_required`。basic auth 可满足本地 usable，公网 productive 需 TLS、token scope 和 origin policy。

## 客户端投影

启动流程固定：

1. 获取 capabilities/schema version；
2. 订阅 SSE 并建立 buffer；
3. 获取 session/message/permission/PTY snapshot；
4. 以 snapshot watermark 丢弃重复 event；
5. 按 aggregate seq 应用 buffer；
6. 遇 gap、unknown breaking version 或 reducer 错误则重新 snapshot。

Text delta 只追加到匹配 part；Text ended 替换完整值。Tool ended 替换 running card。删除/回滚由显式 event 处理，不能让 UI 猜 DB 状态。

## 兼容与迁移

协议版本不是 app version。新增字段须 optional/default；新增 event type 可被旧 client 忽略；改变语义或移除字段要升 capability/version。v1 adapter 把 canonical Message/Part 投影成 `WithParts` 和旧事件，不反向驱动执行。

OpenAPI SDK 在 CI 由 schema 生成并 diff；generated client 与 server commit 成对发布。滚动中的 OpenCode v2 行为只能作为固定代码事实，不能承诺其未来字段稳定。

## 不变量

- 每个 session/message/part 归属唯一；
- 每个 tool call terminal 恰一次；
- event seq 不回退、不重复占位；
- snapshot watermark 之后的 event 不丢；
- terminal 后不出现同 step 新 delta/tool；
- permission reply 只解决存在的 request；
- UI 从 snapshot + events 可重建同一 transcript；
- share/telemetry event 不改变本地 loop 结果。

协议源码与测试入口见 [sources.md](sources.md)。
