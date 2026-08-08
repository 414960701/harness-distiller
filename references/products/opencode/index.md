# OpenCode 产品蒸馏索引

## 范围与结论

本目录把 `anomalyco/opencode` 蒸馏成另一模型可以实施、测试和升级的 OpenCode-like harness 规范。固定研究基线是 `fe82a1b6ca4f535beb973b0867017e3f639f85ed`，提交日期 2026-08-08，许可证 MIT；证据入口见 [sources.md](sources.md)。

该基线的实际主栈是 TypeScript、Bun、Effect、SQLite/Drizzle；TUI 使用 OpenTUI + Solid，浏览器界面使用 Solid，桌面包使用 Electron。仓库没有以 Go 作为核心 runtime，也没有当前 Tauri 桌面实现。不得根据旧文章或历史版本把栈写反。

OpenCode 的辨识度来自 server-first 本地 agent：CLI/TUI、Web、Desktop、IDE 与 SDK 通过 HTTP/OpenAPI 和 SSE 共享 session runtime；模型输出被投影为 message/part/tool-state；本地工具、permission、MCP、LSP、PTY 和 workspace 均由服务端执行。固定基线同时保留 v1 message/part API 并建设 durable v2 session event/projection，因此复刻时要选一个 canonical 内核，再提供兼容投影，不能照抄两套循环。

## 阅读顺序

1. [sources.md](sources.md)：固定提交、许可证、源码与测试证据。
2. [product-contract.md](product-contract.md)：用户行为、领域对象、边界与失败语义。
3. [architecture.md](architecture.md)：client/server、模块、依赖方向与 v1/v2 迁移。
4. [agent-loop.md](agent-loop.md)：session drain、多步模型循环、重试、取消和压缩。
5. [protocol-state.md](protocol-state.md)：session/message/part/event、SSE、snapshot + events。
6. [context-tools.md](context-tools.md)：provider、instruction、tool registry、MCP、LSP 和 compaction。
7. [workspace-execution.md](workspace-execution.md)：文件、patch、shell、PTY、snapshot、worktree。
8. [safety-runtime.md](safety-runtime.md)：permission、server auth、路径与真实 sandbox 边界。
9. [persistence-recovery.md](persistence-recovery.md)：SQLite、durable event、projection、恢复和迁移。
10. [experience.md](experience.md)：TUI、Web、Electron、IDE、SDK 与 headless 表面。
11. [recipe.md](recipe.md)：四级能力与 canonical overlay。
12. [acceptance-tests.md](acceptance-tests.md)：每个 overlay 的 executable oracle。

## 实现完成定义

实现只有满足以下条件才可称为 OpenCode-like：

- TUI 是 server client，不持有唯一会话真值；同一 server 可被 SDK/Web 客户端观察；
- session、message、part/tool-state 使用稳定 ID，增量事件可由完成态校正；
- provider adapter 归一化文本、reasoning、tool call/result、usage、错误和重试提示；
- read/grep/glob/edit/write/apply-patch/shell 至少构成读改测闭环；
- tool schema 在每个 step 冻结，permission 在执行前判定，拒绝作为有类型结果返回；
- runnable 至少把 canonical event trace 落盘并可重放；usable 起由 SQLite 保存 session/message/part，resume 后不伪造已完成 tool result；
- MCP 工具与本地工具经过同一注册、权限和结果截断边界；
- LSP 是可关闭、按文件惰性启动的辅助层，不是文件真源；
- Web/TUI 对 snapshot + event fixture 得到相同最终 transcript；
- share 明确是把会话数据同步到远端服务，默认手动且可以强制禁用。

## 产品边界

| 能力 | 固定基线事实 | 蒸馏要求 |
|---|---|---|
| 核心拓扑 | 本地 server + 多 client | 一个 runtime，多投影，不复制业务循环 |
| 协议 | OpenAPI、SSE；v1 与 v2 迁移并存 | canonical event 模型 + 版本化兼容 adapter |
| 模型 | 多 provider，Vercel AI SDK 与自有 LLM 包 | provider-neutral contract + scripted fixture |
| 状态 | SQLite/Drizzle + durable event/projection 演进 | 事务、序号、迁移和重放有 oracle |
| 执行 | 本地主机文件/进程/PTY | permission 不等于 OS sandbox |
| UI | OpenTUI/Solid、Web/Solid、Electron、IDE | 所有表面消费协议，不直写状态库 |
| 远端 | 可连接 server；share 会上传公开会话 | remote execution 与 share 必须分开建模 |

## 证据标签

- `code`：固定 commit 的公开源码。
- `test`：固定 commit 的自动化测试。
- `official-doc`：随仓库发布或 opencode.ai 的官方文档。
- `inference`：为稳定复刻而做的设计综合，不能声称为原字段或官方路线。

滚动中的 v2、OpenCode 托管模型/账号、企业控制面和 share 后端实现均不得超出公开证据推断。
