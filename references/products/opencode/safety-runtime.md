# OpenCode-like 安全与运行时边界

## 目录

- [威胁模型](#威胁模型)
- [Permission](#permission)
- [Server 安全](#server-安全)
- [Workspace enforcement](#workspace-enforcement)
- [Provider、MCP 与 LSP](#providermcp-与-lsp)
- [Share 与数据](#share-与数据)
- [等级声明](#等级声明)
- [安全测试](#安全测试)

## 威胁模型

输入可能来自用户 prompt、仓库 instruction、文件内容、模型输出、MCP/tool result、LSP server、plugin、远端 client 和 share URL。它们都不可信。需要保护宿主文件、secret、进程、网络、会话隔离、provider 凭证和其他 workspace。

固定 OpenCode 的 permission service 是应用层授权；本地工具通常仍在 host 进程/文件系统执行。除非蒸馏实现配置了 OS/container/VM enforcement 并通过逃逸测试，不得称为 sandboxed。

## Permission

Rule 为 `{permission, pattern, action: allow|ask|deny}`。匹配要确定：固定实现使用最后匹配规则；蒸馏可以采用 deny precedence，但必须冻结语义、测试多 ruleset 合并并在 UI 显示来源。

ask request 含 id、session、permission、patterns、tool、metadata 和可持久 always patterns。reply：

- `once`：仅 resolve 当前 request；
- `always`：增加当前 scope 的 allow，并自动解决同 session 已 pending 的匹配请求；
- `reject`：返回 rejected/corrected error，并按策略取消同 session pending。

permission 判定发生在工具 schema decode 和规范化之后、执行之前。批准后的 input 变化必须重新 ask。模型、plugin 和 MCP 不能直接调用 reply。

## Server 安全

默认只绑定 `127.0.0.1`。设置非 loopback 或 mDNS 时，若没有密码/token，启动必须强警告或拒绝。Basic Auth 可用于本地可信网络；生产远端使用 TLS、短期 bearer、scope、rate limit、审计与 CSRF/origin 防护。

所有 instance/session routes 校验 location ownership，不能用 query directory 读取任意项目。SSE 订阅也要认证与 session/workspace scope。CORS 只加显式 origin，响应含正确 Vary，不用 `*` + credentials。

## Workspace enforcement

应用层必须做 path normalize、root containment、symlink recheck、read/write permission、command pattern 与环境 allowlist。polished 级增加真实 backend：macOS sandbox/container、Linux namespace/seccomp/container、Windows AppContainer/job/ACL 或 remote microVM。

sandbox policy 独立于 approval：read roots、write roots、network domains、process/resource limits、secret mounts。deny 先于 spawn/open，在内核边界失败；sandbox failure 不能 fallback 到 host execution。

## Provider、MCP 与 LSP

provider key 只在 credential store/runtime adapter，不能进入 prompt、event、log、share。HTTP error body 先 redact。MCP remote URL、headers 和 OAuth token 按 server scope 存储；stdio command 视本地代码执行，需要配置来源和 permission。

MCP/LSP/plugin 可返回恶意路径、ANSI、超大输出、schema、media/data URL。对大小、MIME、JSON depth、tool count、名字、timeout、进程和下载来源设限制。LSP 自动下载在企业 policy 下可禁用。

## Share 与数据

share 是显式出站边界，会同步 session、message、part、diff 和 model。默认 manual；配置/environment/managed policy 的 disabled 为硬禁止。创建前展示公开范围和敏感数据提醒；上传队列只消费 committed redacted data。

share secret 不写日志，公共 URL 与删除 secret 分开。unshare 成功以远端确认作为准则；本地删记录前保留 retry/reconciliation。托管 share 的 retention/CDN/SSO 行为只按官方文档描述，其他内容标 `inference`。

## 等级声明

| 声明 | 最低证据 |
|---|---|
| permission-aware | rule/ask/reply oracle |
| workspace-bounded | path/symlink/stale hash oracle |
| authenticated server | route/SSE auth 与 CORS oracle |
| sandboxed | 真实 OS/container enforcement 逃逸测试 |
| enterprise-managed | 不可被 client 覆盖的签名 policy 与审计 |
| private | share disabled、telemetry/provider 数据流说明 |

Electron renderer sandbox 不等于 agent command sandbox；Docker 安装选项也不等于每个 tool 自动隔离。

## 安全测试

- permission：wildcard/last-match、once/always/reject、重复/伪造 reply；
- 路径：`..`、绝对、symlink swap、Unicode、恶意 Git dir/submodule；
- server：未认证 session/SSE/PTY、跨 workspace IDOR、CORS、CSRF、body flood；
- process：shell injection、恶意 PATH/env、daemon/孙进程、fork bomb、timeout；
- extension：MCP schema bomb、OAuth state、LSP 下载替换、plugin 提权；
- data：provider key/error、`.env`、tool output、event、artifact、share redaction；
- sandbox：网络重定向/DNS、mount、proc、secret、resource escape。

安全失败必须证明目标副作用不存在。实现证据与事实边界见 [sources.md](sources.md)。
