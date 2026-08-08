# OpenCode-like 架构

## 目录

- [实际技术栈](#实际技术栈)
- [部署拓扑](#部署拓扑)
- [模块边界](#模块边界)
- [依赖规则](#依赖规则)
- [v1 与 v2](#v1-与-v2)
- [最小代码布局](#最小代码布局)
- [反模式](#反模式)

## 实际技术栈

固定基线是 Bun monorepo，核心语言 TypeScript。Effect 提供 typed effect/layer/schema/stream，SQLite + Drizzle 保存本地状态；OpenAPI/Effect HttpApi 暴露 server；TUI 为 OpenTUI + Solid，Web/Desktop renderer 为 Solid，桌面 host 为 Electron。provider 层同时使用 Vercel AI SDK 与仓库内 `@opencode-ai/llm`。

复刻不必逐个依赖一致，但必须保留：强类型 schema、可组合 service layer、事务状态、server/client 分离、流式事件、多 surface 投影。若用 Python/Go/Rust，要写 adapter parity tests。

## 部署拓扑

```text
TUI / Web / Electron / IDE / SDK
             |
       HTTP + SSE + OpenAPI
             |
     OpenCode-like local server
       |        |        |
 session loop  tools   extensions
       |        |      MCP / LSP
 provider     workspace
       |        |
 model API   files/process/PTY/git
             |
      SQLite + durable events
```

`opencode` 的交互模式可在进程内启动 server 与 TUI，但二者仍通过协议边界协作。`serve` 只启 server；`attach` 连接已有 server。Remote URL 是 server transport，不改变 session 领域模型。

## 模块边界

| 模块 | 职责 | 不得承担 |
|---|---|---|
| schema/protocol | ID、对象、event、HTTP/OpenAPI | DB 查询、工具执行 |
| server | auth、route、location routing、SSE | 直接拼 provider prompt |
| session | prompt admission、single drain、projection | UI 状态 |
| provider | auth/model/options、stream 归一化 | workspace 写入 |
| tool registry | builtin/plugin/MCP schema 和路由 | 绕过 permission |
| permission | allow/ask/deny、pending request | syscall enforcement |
| workspace | path、file、patch、process、PTY、snapshot | provider retry |
| persistence | transaction、event seq、projection、migration | 网络 UI |
| surfaces | command、render、input、resync | 唯一真值 |
| share | 显式远端投影同步 | 默认 session persistence |

## 依赖规则

1. schema/protocol 不依赖具体 TUI、Electron 或 provider SDK。
2. server handler 调用 service interface，不直接 import SQLite table 做业务写。
3. tool execute 接收 immutable `ToolContext`：session/message/call、agent、directory/worktree、permission callback、abort signal。
4. provider stream 只能产生 normalized LLMEvent；processor 决定 Part/Event 更新。
5. event publish 与 durable projection 在一个 transaction 边界；broadcast 在 commit 后。
6. client reducer 只消费 server snapshot/event，刷新页面可完整重建。
7. share subscriber 只读取 committed event，不拦截主循环。

## v1 与 v2

固定代码同时存在：

- v1：`SessionV1.Info + Part[]`、`message.updated`、`message.part.updated/delta`；
- v2：durable `session.next.*` event、`session_message` projection、`/api/session` 和 typed SSE；
- bridge：把 instance location 和 durable sync 投影到旧 GlobalBus。

这是迁移证据，不是要求复刻双内核。推荐 canonical 使用 v2 durable events，写一个 v1 projection adapter 服务现有 TUI/SDK；runnable 阶段也可先使用 v1 object model，但 schema 中预留 event version 与 projection rebuild。不能同时让 v1 与 v2各自执行工具。

## 最小代码布局

```text
src/
  schema/          # IDs, session/message/part/event
  protocol/        # HTTP/OpenAPI/SSE
  server/          # routes, auth, location routing
  session/         # admission, drain, processor, compaction
  provider/        # adapters and fixtures
  tools/           # registry and builtins
  permission/      # policy and pending approvals
  workspace/       # fs, patch, shell, PTY, snapshot
  extensions/      # MCP, LSP, plugins
  storage/         # SQLite, migrations, event store, projectors
  clients/tui/     # event projection only
  clients/web/     # event projection only
```

接口层需要 fake clock、deterministic ID、scripted provider、fake process 和 in-memory/temporary SQLite，保证 acceptance tests 无付费 provider。

## 反模式

- Electron/TUI 直接 import session singleton；
- 把每个 token delta 永久保存但不保存完成态；
- server route 返回内部 Effect/SDK error；
- provider tool callback 直接写文件而不经过 ToolContext；
- MCP server 自己决定宿主 permission；
- 把 SQLite projection 表当成不可重建 event log；
- share 网络失败阻塞本地消息提交；
- 因固定仓库有迁移桥接，就复制两套类型、表和 loop。
