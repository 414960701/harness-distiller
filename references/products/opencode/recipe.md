# OpenCode-like 蒸馏配方

## 目录

- [默认蓝图](#默认蓝图)
- [四级矩阵](#四级矩阵)
- [canonical overlay](#canonical-overlay)
- [交付顺序](#交付顺序)
- [直接升级](#直接升级)
- [禁止替代](#禁止替代)

## 默认蓝图

默认 usable 栈选择 TypeScript + Bun/Node、SQLite/Drizzle、HTTP/OpenAPI/SSE；runnable surface 为 headless + 最小 TUI，并允许 append-only JSONL trace + 内存 projection，SQLite resume 从 usable 开始。provider 使用 `provider-neutral-contract` 与 `scripted-fixture`。真实产品差量是 local server/client、session/message/part/tool-state、provider stream normalization、permission、MCP/LSP、PTY、多 surface 和可选 share。

若实现团队不采用 Effect，可用普通 async/service container，但必须保留 typed error、cancellation scope、resource finalizer、stream backpressure 和 transaction boundary。桌面默认 Electron；不因历史资料选择 Tauri，除非用户明确指定替代栈。

## 四级矩阵

| 子系统 | runnable（能跑） | usable（能用） | productive（顺手） | polished（好用） |
|---|---|---|---|---|
| topology | local server + CLI/TUI client | resume/reconnect | 多 surface/SDK | version negotiation/SLO |
| protocol | session/message/part live event | snapshot + cursor | OpenAPI/SSE | durable replay/migration |
| model | one normalized provider | retry/usage/compaction | multi-provider/variant | compatibility eval |
| tools | read/grep/edit/shell | permission/MCP | PTY/LSP/plugin/task | sandbox/remote receipt |
| state | temporary/SQLite basics | SQLite resume | worktree/parent session | event projection recovery |
| UX | transcript/tool card | permission/diff/session list | Web/Electron/IDE | a11y/i18n/load |
| data | share disabled | manual share placeholder | explicit sync | managed policy/redaction |

等级共享同一个 schema、server 和 loop；升级增加字段/adapter/优化，不重建四套产品。

## canonical overlay

以下 capability ID 必须原样进入蓝图和 [acceptance-tests.md](acceptance-tests.md)：

| capability ID | 等级 | 实现路径 | verified oracle |
|---|---|---|---|
| `architecture.local-server-client` | runnable | Server + thin CLI/TUI client | client 无 DB/provider import；重启 client session 仍在 |
| `surface.minimal-tui` | runnable | HTTP snapshot/event transcript renderer | composer、tool、approval、cancel、terminal error 均可操作且不直连 runtime |
| `protocol.session-message-parts` | runnable | typed IDs/schema/event reducer | tool state 合法转移，丢 delta 由 ended 收敛 |
| `providers.normalized-stream` | runnable | ProviderAdapter + scripted fixture | 两种 provider trace 投影相同 canonical parts |
| `tools.workspace-loop` | runnable | registry + read/grep/edit/shell | 完成读改测，越界与坏 schema 零执行 |
| `permissions.pattern-rules` | usable | rule evaluator + pending request | allow/ask/deny、once/always/reject 可执行 |
| `persistence.sqlite-resume` | usable | SQLite session/message/part/intent | crash/resume 不重复 completed tool |
| `extensions.mcp-runtime` | usable | stdio/HTTP MCP adapter | lifecycle、namespace、断线、permission 通过 |
| `context.session-compaction` | usable | prune + summary + tail boundary | overflow 后保留最新约束/tool pair |
| `protocol.openapi-sse-sdk` | productive | generated OpenAPI client + SSE | SDK 类型/route 无漂移，gap 触发 resync |
| `workspace.pty-lsp` | productive | offset PTY + lazy LSP | input 幂等、取消进程树、LSP crash 降级 |
| `surfaces.tui-web-desktop` | productive | shared reducer + Electron host | 三表面对 golden trace 得同 canonical state |
| `sessions.parent-worktree` | productive | parent session + isolated worktree | 两子 session 并行无 cwd/file/process 混写 |
| `protocol.durable-event-replay` | polished | aggregate event store/projectors | 删 projection 可重建，seq/terminal 唯一 |
| `security.sandboxed-server` | polished | auth + OS/container enforcement | 未认证/越界/网络/资源逃逸在真实边界失败 |
| `sharing.policy-controlled-sync` | polished | manual sync + managed disable/unshare | disabled 无请求；sync/unshare/secret/redaction 可验证 |

能力只有实现路径和对应测试路径存在时可标 `verified`；只写 route、UI 或文档保持 `planned/implemented`。

## 交付顺序

1. 建 schema、append-only trace、scripted provider、session drain 与 read/edit/shell vertical slice；runnable 可用 JSONL，usable 再迁入 SQLite/Drizzle。
2. 启 local server，做薄 headless/TUI client，完成 runnable 五项。
3. 加 permission、resume/tool intent、compaction、MCP，完成 usable。
4. 从 schema 生成 SDK，引入 SSE resync、PTY/LSP、parent/worktree、共享 reducer。
5. 用共享 reducer交付 Web 与 Electron/IDE adapter，完成 productive。
6. 将 event store 升 canonical、重建 projection、接真实 sandbox、managed share，完成 polished。

每一步先用 scripted fixture 与临时 repo 验收，再接真实 provider/平台。

## 直接升级

允许 runnable 直接升级 polished，但顺序固定：备份/schema migration → protocol capability → runtime/projector → workspace enforcement → surface → share。保留 session/message/tool ID，新增字段给默认值；先 shadow replay 比较 projection，再切写路径。所有低等级 oracle持续运行。

v1/part 实现升级 durable v2 时采用双读不双写；如果回滚，旧 client 至少只读新 session。sandbox 开启失败不得 fallback host。share managed-disable 在升级前先关闭出站队列。

## 禁止替代

- 把 CLI 内函数调用说成 client/server；
- 只输出 token 文本，不建 message/part/tool-state；
- 用 provider SDK callback 绕过 registry/permission；
- 用 UI 内存或普通 JSON snapshot 冒充可恢复 SQLite/event state；runnable 的 append-only JSONL trace 只承诺审计与重放，不冒充 usable resume；
- MCP 连接成功截图替代 tool lifecycle/permission 测试；
- `kill(shell pid)` 替代 process tree/PTY cancellation；
- Electron renderer sandbox 替代 agent execution sandbox；
- public share link 替代 remote execution 或协同编辑。
