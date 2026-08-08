# OpenCode-like 验收测试

## 目录

- [测试环境](#测试环境)
- [能力登记](#能力登记)
- [runnable](#runnable)
- [usable](#usable)
- [productive](#productive)
- [polished](#polished)
- [故障与升级](#故障与升级)
- [出厂判定](#出厂判定)

## 测试环境

创建临时 Git repo：`src/math.ts` 有失败测试，另含未提交用户修改、`.env`、大输出、图片、root 外 sentinel、symlink。scripted provider A/B 能产生 text/reasoning/tool delta、坏 JSON、429、5xx、overflow、断流、重复 call。fake MCP 含 stdio/HTTP/OAuth、故障重启和同名工具；fake LSP 含 diagnostics/symbol 与 crash。SQLite、fake clock、deterministic ID、process recorder、HTTP/SSE client 和 UI reducer snapshot 全部采集。

每个用例断言 workspace hash、进程、DB、HTTP、event seq、message/part/tool terminal、stdout/stderr。测试不依赖付费 provider、OpenCode 账号或托管 share。

## 能力登记

| capability ID | 等级 | executable oracle |
|---|---|---|
| `architecture.local-server-client` | runnable | 独立 client 只经 HTTP/SSE 完成 session；client crash/restart 后 resume |
| `surface.minimal-tui` | runnable | snapshot/event fixture 驱动 transcript/composer/tool/approval/cancel/error 交互 |
| `protocol.session-message-parts` | runnable | schema/state/property test + delta loss replay |
| `providers.normalized-stream` | runnable | A/B provider golden trace 等价 |
| `tools.workspace-loop` | runnable | 临时 repo 读改测与路径/参数拒绝 |
| `permissions.pattern-rules` | usable | rule 矩阵与 request/reply 集成 |
| `persistence.sqlite-resume` | usable | 多 crash point resume/no duplicate effect |
| `extensions.mcp-runtime` | usable | transport/OAuth/namespace/permission/failure fixture |
| `context.session-compaction` | usable | overflow/prune/summary/tail fixture |
| `protocol.openapi-sse-sdk` | productive | OpenAPI generated diff + SSE gap/resync |
| `workspace.pty-lsp` | productive | PTY offset/idempotency/process tree + LSP crash |
| `surfaces.tui-web-desktop` | productive | shared reducer golden state 与 E2E command parity |
| `sessions.parent-worktree` | productive | 两 child/worktree 并发隔离 |
| `protocol.durable-event-replay` | polished | projection rebuild/fault injection/version migration |
| `security.sandboxed-server` | polished | real backend auth/path/network/process escape suite |
| `sharing.policy-controlled-sync` | polished | fake share server sync/unshare/disable/redaction |

## runnable

### `architecture.local-server-client`

等级：`runnable`。

启动 server 随机端口，用独立进程 client 创建 session、提交 prompt、订阅终态。kill client 而 server 继续，再启 client list/resume。Oracle：同一 session/message ID 和 transcript；client 包不 import DB、provider、workspace execute；server 退出后 client 明确 disconnected。

### `surface.minimal-tui`

等级：`runnable`。

用同一 HTTP snapshot + event fixture 驱动最小 TUI：输入 prompt、观察 text/tool card、处理 approve/reject、触发 cancel，并注入 server disconnect 与 typed terminal error。Oracle：所有动作只发 server command；composer admission 后才固定 message ID；tool/approval/cancel/terminal 状态与 headless projection 等价；断线时禁止假提交；client 包不导入 DB、provider 或 executor。

### `protocol.session-message-parts`

等级：`runnable`。

让 fixture 产生 reasoning、text、tool pending/running/completed、finish。随机丢/重复 delta，再送 ended/snapshot。Oracle：最终 text/tool output 相同；非法 running→pending、双 terminal、跨 session part 被 schema/reducer 拒绝；terminal 后无新 part。

### `providers.normalized-stream`

等级：`runnable`。

Provider A 使用完整 tool JSON，B 使用 input delta 与不同 usage/error 字段。Oracle：归一后 canonical message/parts、call id、result、finish 相同；usage 单位明确；坏 JSON 生成 tool error 且 execute count=0；secret/error body 已脱敏。

### `tools.workspace-loop`

等级：`runnable`。

fixture 依次 read、grep、apply patch、run test。Oracle：测试通过、只改目标文件、每个 call 唯一 result。再测坏 schema、`../../sentinel`、绝对路径、stale hash、多 hunk 第二处失败；全部零目标副作用，sentinel hash 不变。

## usable

### `permissions.pattern-rules`

等级：`usable`。

配置 allow read、ask shell、deny `.env`/root 外，叠加冲突 wildcard。分别 reply once、always、reject、重复/伪造 ID。Oracle：规则优先级与文档一致；once 只执行一次；always scope 精确；reject 回到模型；deny 永不 spawn/open；reply event 恰一次。

### `persistence.sqlite-resume`

等级：`usable`。

在 input admitted、tool intent、文件 rename、receipt committed、terminal commit 后分别 kill -9。Oracle：SQLite integrity；session 可 list/resume；已 completed tool execute count 仍 1；未知副作用标 reconciliation，不自动重跑；event/part terminal 唯一。

### `extensions.mcp-runtime`

等级：`usable`。

连接两个同名 tool 的 MCP，调用 resource/prompt/tool，测试 stdio crash、HTTP timeout、OAuth state 错误和重连。Oracle：工具 namespace 无碰撞；本地 permission 生效；当前 step tool snapshot 不漂移；失败不移除 core tools；token 不进 event/log。

### `context.session-compaction`

等级：`usable`。

注入超过 window 的 12 turns、大 tool output、最近未完成约束和 skill artifact。Oracle：先 prune 再 summary；最近 tail/tool pair/目标保留；token 回到预算；旧 event 可审计；并发新 input 使过期 summary 被丢弃；summary 失败明确降级。

## productive

### `protocol.openapi-sse-sdk`

等级：`productive`。

CI 从 server schema 重生成 SDK 并要求 clean diff。连接 SSE，在 seq 100–110 丢 104 后重连。Oracle：client 检测 gap 并 snapshot/after 补齐，无重复 tool card；unknown additive event 被忽略，breaking version 被 capability handshake 拒绝。

### `workspace.pty-lsp`

等级：`productive`。

启动交互命令，两次 input/resize 含重复 request id，流 1MB 后 cancel；打开 TS 文件触发 LSP diagnostics，再 kill LSP。Oracle：输入只写一次、offset 单调、进程树结束、exit 准确；LSP 按 root 唯一启动，crash 后 read/edit/test 仍成功并显示 degraded。

### `surfaces.tui-web-desktop`

等级：`productive`。

向共享 reducer 回放 session/text/reasoning/tool/permission/diff/PTY golden trace，并在三个 E2E 表面分别 approve/cancel/switch model。Oracle：canonical view model hash 相同；一个表面的 command 被另两个看到；刷新/重开由 snapshot + events 收敛；renderer 不持有 provider key。

### `sessions.parent-worktree`

等级：`productive`。

父 session 创建两个 child/worktree，同时改相同相对路径、运行长进程和 LSP。Oracle：parentID/base ref 正确；cwd、file hash、branch、process、diagnostic 不串；取消一个不杀另一个；有 dirty/process 时 cleanup 拒绝并标 orphaned。

## polished

### `protocol.durable-event-replay`

等级：`polished`。

记录完整会话后删除 message/status/todo projection，从 durable events 重建；再在 event insert/projector/sequence/broadcast 边界故障。Oracle：重建 hash 等于原值；aggregate seq 连续；事务全有或全无；commit 后断线可补取；旧 event version 迁移可重入。

### `security.sandboxed-server`

等级：`polished`。

启用真实 OS/container backend；从未认证 HTTP/SSE/PTY、跨 workspace ID、tool 尝试 symlink/root 外、读 secret、被禁网络/DNS redirect、daemon/fork bomb/资源耗尽。Oracle：server auth 和内核 enforcement 阻止；sentinel/secret 不泄漏；进程资源回收；sandbox error 不 fallback host。

### `sharing.policy-controlled-sync`

等级：`polished`。

fake share server 记录 create/sync/remove。manual 未点击时零请求；显式 share 后更新 message/part/diff；unshare 网络先失败再成功；managed disabled 下从 CLI/API/env 尝试开启。Oracle：只同步 committed/redacted 数据；队列按 key 合并；secret 不入日志；失败不显示已删除；disabled 始终零出站。

## 故障与升级

补充故障：provider retry-after/cancel、MCP/LSP shutdown、SSE slow consumer、SQLite busy/WAL 损坏、stdout flood、Electron renderer crash、server/client 版本错配、share timeout。每个场景要有 typed terminal、bounded resource 和无重复副作用。

直接 runnable→polished：先保存 DB/workspace/SDK schema 快照，运行五项 runnable；迁移后运行全部 16 项；ID 和低级 transcript 不变。v1 adapter 与 v2 canonical 的 golden projection 一致，关闭高级 flag 后基础 read/edit/shell 仍可用。

## 出厂判定

每一级包含前级所有测试。Capability 只有存在实现路径、测试路径和通过报告才标 `verified`。permission 通过不代表 `security.sandboxed-server`；Electron/Web 可运行不代表 surface parity；生成 OpenAPI 文件不代表 SDK/gap oracle；分享页面可打开不代表 policy-controlled sync。报告保存 commit、平台、provider fixture、sandbox adapter、DB schema、通过数和 waiver；安全越界不可 waiver 为通过。
