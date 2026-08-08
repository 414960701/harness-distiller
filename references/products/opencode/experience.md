# OpenCode-like 产品体验

## 目录

- [体验原则](#体验原则)
- [TUI](#tui)
- [Web](#web)
- [Desktop](#desktop)
- [IDE 与 SDK](#ide-与-sdk)
- [Headless 与 server](#headless-与-server)
- [跨表面一致性](#跨表面一致性)
- [可访问性与性能](#可访问性与性能)

## 体验原则

产品以 project/session 为中心，不以聊天窗口进程为中心。用户离开 TUI、刷新 Web 或重启 Electron 后仍能 list/resume；tool、permission、diff、todo、terminal 和 usage 都是 server 状态的投影。

所有表面共享动作语义：new/resume/fork、send/cancel、select agent/model、approve/reject、compact、undo/redo、share/unshare、open file/diff、attach terminal。快捷键与布局可不同，事件和结果不能不同。

## TUI

当前产品使用 OpenTUI + Solid。runnable 的“最小 TUI”至少包含 server 连接状态、单 session transcript、composer/send、流式 text/tool card、approve/reject、cancel 和 typed terminal error；它只能消费 HTTP snapshot/event，不得导入 DB、provider 或 executor。usable 再增加 session list/resume、model/agent selector、status/context usage、diff 与 todo；productive 的完整 TUI 再加入 command palette、PTY/LSP 和跨表面能力。

输入支持 `@file/symbol/reference`、`!shell`、`/command`。slash command 转成 server command，不在 TUI 直接修改 session。streaming delta 节流渲染，ended event 校正全文；隐藏 details 只影响 presentation。

启动 `opencode` 可内嵌启动 server；`attach URL` 连接已有 server。断线显示 last seq 和重连状态，禁止继续让用户误以为 prompt 已提交。

## Web

Web 运行于本地 server，提供 project/session picker、timeline、composer、provider settings、diff/file viewer、terminal、权限与 server status。默认 loopback；暴露局域网时突出 auth 状态。

浏览器 refresh 先 snapshot 再 SSE。多 tab 对同一 session 的 busy/permission/tool card 一致；optimistic prompt 只能在 admitted receipt 后固定 ID，失败要回滚。

## Desktop

固定基线桌面包是 Electron，不是 Tauri。主进程负责 window、更新、native PTY/文件选择和 server lifecycle；renderer 复用 Web/Solid app。IPC 使用 allowlisted typed command，renderer 不获得任意 Node/secret 能力。

Desktop 可发现/启动/连接 server，但 session runtime 不复制到 renderer。自动更新失败不影响已有本地 server；协议 capability handshake 决定 client/server 兼容。

## IDE 与 SDK

IDE 扩展通过 server/SDK：发送当前 file/selection、打开 diff/location、prefill/submit prompt、显示 session 状态。IDE 不直接调用 provider 或执行工具。

SDK 由 OpenAPI 生成 typed client，提供 server lifecycle helper、request API 和 event subscription。生成物带 protocol version；示例和验收使用本地 scripted provider，不能要求登录托管服务。

## Headless 与 server

`serve` 提供稳定 health/OpenAPI/SSE；`run` 接收 prompt 并输出 human 或 JSON/JSONL。机器模式 stdout 只含协议结果，日志到 stderr；退出码区分 success、model/tool failure、permission rejection、cancel、timeout、config/auth。

headless 等待与 async admission 都使用同一 session。Ctrl-C 发送 cancel 并等待 bounded settlement，第二次才强退；不能只关闭 client 留命令孤儿运行。

## 跨表面一致性

使用 golden fixture：session snapshot + text/reasoning/tool/permission/diff/terminal events。TUI、Web、Desktop reducer 输出相同 canonical view model；snapshot test 只比较 presentation。一个表面批准后，其他表面 dialog 关闭并显示同一 reply。

share URL、model cost 和 reasoning visibility 受 capability/policy 控制；不可用能力禁用并说明，不显示会失败的按钮。

| 状态 | 表面必须显示 | 禁止显示 |
|---|---|---|
| retry | 原因、下次时间、cancel | 永久 spinner |
| permission | tool/pattern/scope | 模糊“是否继续” |
| disconnected | server URL、last seq、重连 | 可提交假输入 |
| degraded MCP/LSP | 失效扩展、核心仍可用 | 整体会话失败 |
| failed | typed error、可恢复动作 | completed 勾选 |

## 可访问性与性能

- 无颜色模式仍区分 error/permission/diff；
- keyboard-only 可完成所有 dialog，焦点在流式更新时不跳；
- screen reader 有 tool state 与终态公告，delta 不逐 token 轰炸；
- timeline 虚拟化，10 万 events 内存有界；
- delta 合并帧，ended 必须完整；
- terminal、reasoning、tool output 分区限制尺寸；
- 多语言文案不进入协议 enum/error code。

UI 源码与官方表面证据见 [sources.md](sources.md)。
