# OpenCode 证据与版本登记

## 目录

- [版本快照](#版本快照)
- [核心源码](#核心源码)
- [执行与扩展](#执行与扩展)
- [界面与远端边界](#界面与远端边界)
- [测试证据](#测试证据)
- [结论映射](#结论映射)
- [限制](#限制)

## 版本快照

复核日期：2026-08-08。`dev` 与 HEAD 均为 `fe82a1b6ca4f535beb973b0867017e3f639f85ed`，提交标题 `chore: generate`，根许可证为 MIT，`packages/opencode` 版本为 `1.18.15`。

```text
repository: https://github.com/anomalyco/opencode
commit: fe82a1b6ca4f535beb973b0867017e3f639f85ed
docs: https://opencode.ai/docs/
license: MIT
```

所有代码与测试链接固定到该 commit。网站链接只代表当前官方行为说明；若与固定代码冲突，以代码事实和本 dossier 明示的版本边界为准。

## 核心源码

- [根 package.json](https://github.com/anomalyco/opencode/blob/fe82a1b6ca4f535beb973b0867017e3f639f85ed/package.json)（code）：Bun workspace、TypeScript、Effect、Solid、OpenTUI、SQLite/Drizzle 依赖。
- [opencode package](https://github.com/anomalyco/opencode/blob/fe82a1b6ca4f535beb973b0867017e3f639f85ed/packages/opencode/package.json)（code）：主 CLI/runtime 依赖与版本。
- [HTTP server](https://github.com/anomalyco/opencode/blob/fe82a1b6ca4f535beb973b0867017e3f639f85ed/packages/opencode/src/server/server.ts)（code）：路由、认证、中间件与服务组合。
- [v2 protocol session group](https://github.com/anomalyco/opencode/blob/fe82a1b6ca4f535beb973b0867017e3f639f85ed/packages/protocol/src/groups/session.ts)（code）：session create/list/prompt/history 等 HTTP 合同。
- [v2 event SSE group](https://github.com/anomalyco/opencode/blob/fe82a1b6ca4f535beb973b0867017e3f639f85ed/packages/protocol/src/groups/event.ts)（code）：typed SSE event stream。
- [v1 session/message/part schema](https://github.com/anomalyco/opencode/blob/fe82a1b6ca4f535beb973b0867017e3f639f85ed/packages/schema/src/v1/session.ts)（code）：message、part、tool state 与 legacy event。
- [v2 session message schema](https://github.com/anomalyco/opencode/blob/fe82a1b6ca4f535beb973b0867017e3f639f85ed/packages/schema/src/session-message.ts)（code）：projected message union。
- [v2 durable session events](https://github.com/anomalyco/opencode/blob/fe82a1b6ca4f535beb973b0867017e3f639f85ed/packages/schema/src/session-event.ts)（code）：prompt、step、text、reasoning、tool 的事件定义。
- [durable event store](https://github.com/anomalyco/opencode/blob/fe82a1b6ca4f535beb973b0867017e3f639f85ed/packages/core/src/event.ts)（code）：aggregate sequence、事务 publish、replay、claim。
- [session SQL schema](https://github.com/anomalyco/opencode/blob/fe82a1b6ca4f535beb973b0867017e3f639f85ed/packages/core/src/session/sql.ts)（code）：session/message/part、v2 projection、input、context epoch。

## 执行与扩展

- [prompt/loop orchestration](https://github.com/anomalyco/opencode/blob/fe82a1b6ca4f535beb973b0867017e3f639f85ed/packages/opencode/src/session/prompt.ts)（code）：instruction、tools、MCP、LLM、compaction 和 run state。
- [stream processor](https://github.com/anomalyco/opencode/blob/fe82a1b6ca4f535beb973b0867017e3f639f85ed/packages/opencode/src/session/processor.ts)（code）：text/reasoning/tool state、snapshot、doom-loop 和终止。
- [retry policy](https://github.com/anomalyco/opencode/blob/fe82a1b6ca4f535beb973b0867017e3f639f85ed/packages/opencode/src/session/retry.ts)（code）：retry-after、指数退避、错误分类。
- [compaction](https://github.com/anomalyco/opencode/blob/fe82a1b6ca4f535beb973b0867017e3f639f85ed/packages/opencode/src/session/compaction.ts)（code）：tail budget、summary 与旧 tool output prune。
- [provider registry](https://github.com/anomalyco/opencode/blob/fe82a1b6ca4f535beb973b0867017e3f639f85ed/packages/opencode/src/provider/provider.ts)（code）：provider/model/auth/options 归一化。
- [tool registry](https://github.com/anomalyco/opencode/blob/fe82a1b6ca4f535beb973b0867017e3f639f85ed/packages/opencode/src/tool/registry.ts)（code）：builtin/custom/plugin/MCP tool 组装。
- [permission service](https://github.com/anomalyco/opencode/blob/fe82a1b6ca4f535beb973b0867017e3f639f85ed/packages/opencode/src/permission/index.ts)（code）：last matching rule、ask/once/always/reject。
- [MCP service](https://github.com/anomalyco/opencode/blob/fe82a1b6ca4f535beb973b0867017e3f639f85ed/packages/opencode/src/mcp/index.ts)（code）：stdio/HTTP/SSE、OAuth、tool/resource/prompt。
- [LSP service](https://github.com/anomalyco/opencode/blob/fe82a1b6ca4f535beb973b0867017e3f639f85ed/packages/opencode/src/lsp/lsp.ts)（code）：按扩展和 root 惰性启动、diagnostic/symbol API。
- [snapshot service](https://github.com/anomalyco/opencode/blob/fe82a1b6ca4f535beb973b0867017e3f639f85ed/packages/opencode/src/snapshot/index.ts)（code）：修改前后快照、diff/revert 基础。

## 界面与远端边界

- [Server 官方文档](https://opencode.ai/docs/server/)（official-doc）：TUI 是 server client、OpenAPI、SSE、basic auth。
- [SDK 官方文档](https://opencode.ai/docs/sdk/)（official-doc）：类型安全 JS/TS SDK 与 server lifecycle。
- [TUI 官方文档](https://opencode.ai/docs/tui/)（official-doc）：文件引用、命令、session、undo/redo。
- [Web 官方文档](https://opencode.ai/docs/web/)（official-doc）：本地浏览器 server、认证、attach。
- [desktop package](https://github.com/anomalyco/opencode/blob/fe82a1b6ca4f535beb973b0867017e3f639f85ed/packages/desktop/package.json)（code）：当前桌面为 Electron，不是 Tauri。
- [TUI package](https://github.com/anomalyco/opencode/blob/fe82a1b6ca4f535beb973b0867017e3f639f85ed/packages/tui/package.json)（code）：OpenTUI/Solid 客户端。
- [Share 官方文档](https://opencode.ai/docs/share/)（official-doc）：manual/auto/disabled 与公开链接。
- [share sync client](https://github.com/anomalyco/opencode/blob/fe82a1b6ca4f535beb973b0867017e3f639f85ed/packages/opencode/src/share/share-next.ts)（code）：session/message/part/diff/model 队列上传。
- [share SQL](https://github.com/anomalyco/opencode/blob/fe82a1b6ca4f535beb973b0867017e3f639f85ed/packages/core/src/share/sql.ts)（code）：本地 id/secret/url 记录。
- [Enterprise 官方文档](https://opencode.ai/docs/enterprise/)（official-doc）：集中配置、SSO/网关与 share 风险；托管实现未公开。

## 测试证据

- [session loop tests](https://github.com/anomalyco/opencode/tree/fe82a1b6ca4f535beb973b0867017e3f639f85ed/packages/opencode/test/session)（test）：prompt、processor、retry、compaction、message 与 snapshot 竞态。
- [permission tests](https://github.com/anomalyco/opencode/blob/fe82a1b6ca4f535beb973b0867017e3f639f85ed/packages/opencode/test/permission/next.test.ts)（test）：rule precedence 与 reply。
- [MCP lifecycle tests](https://github.com/anomalyco/opencode/blob/fe82a1b6ca4f535beb973b0867017e3f639f85ed/packages/opencode/test/mcp/lifecycle.test.ts)（test）。
- [MCP recovery tests](https://github.com/anomalyco/opencode/blob/fe82a1b6ca4f535beb973b0867017e3f639f85ed/packages/opencode/test/mcp/session-recovery.test.ts)（test）。
- [LSP lifecycle tests](https://github.com/anomalyco/opencode/blob/fe82a1b6ca4f535beb973b0867017e3f639f85ed/packages/opencode/test/lsp/lifecycle.test.ts)（test）。
- [HTTP session tests](https://github.com/anomalyco/opencode/blob/fe82a1b6ca4f535beb973b0867017e3f639f85ed/packages/opencode/test/server/httpapi-session.test.ts)（test）。
- [HTTP event tests](https://github.com/anomalyco/opencode/blob/fe82a1b6ca4f535beb973b0867017e3f639f85ed/packages/opencode/test/server/httpapi-event.test.ts)（test）。
- [tool tests](https://github.com/anomalyco/opencode/tree/fe82a1b6ca4f535beb973b0867017e3f639f85ed/packages/opencode/test/tool)（test）：path、patch、shell、LSP、registry 与 truncation。
- [share tests](https://github.com/anomalyco/opencode/blob/fe82a1b6ca4f535beb973b0867017e3f639f85ed/packages/opencode/test/share/share-next.test.ts)（test）。

## 结论映射

| 结论 | 证据 | 强度 |
|---|---|---|
| OpenCode 是 server-first 多 client | server docs、server code、SDK | code + official-doc |
| 当前核心不是 Go/Tauri | root、opencode、desktop package | code |
| message/part 与 durable v2 同时存在 | schema、SQL、event store | code |
| permission 是应用策略，不是 OS sandbox | permission、tool/path tests | code + inference |
| share 会把会话内容发往远端 | share docs、share-next | code + official-doc |
| LSP/MCP 都是可失败扩展 | services 与 lifecycle tests | code + test |

## 限制

- `dev` 在持续变化；本文只描述固定 commit。
- v2 文件名和 `experimental` 路由显示迁移状态；未来稳定性属于 inference。
- OpenCode Zen/Go、账号、组织、企业和 share 后端不在仓库内，不能推断配额、SLO 或隔离实现。
- 官方“代码不被 OpenCode 存储”不等于 provider 不接收上下文；share 开启后内容明确上传。
- server remote attachment 是协议能力，不自动等于托管 remote executor、租约或 exactly-once。
- tests 证明实现路径，不等于全平台安全认证。
