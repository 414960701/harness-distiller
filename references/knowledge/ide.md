# IDE Surface

## 职责与非目标

IDE 扩展将 harness 的 Task/Turn/Step、diff、诊断、终端和 approval 投影到编辑器。
它通过稳定协议发 command、订阅事件，不把 extension host 内存当任务事实源。
selection、open files、diagnostics 和未保存 buffer 是带时间戳的 context hint，不是永久事实。
IDE surface 不绕过 workspace trust、编辑器权限、policy 或 review gate。

## 协议与 context schema

```yaml
IdeContextHint:
  window_id: string
  workspace_uri: string
  document_uri: string|null
  version: integer|null
  selection: {start, end}|null
  source: selection|visible_range|open_file|diagnostic
  captured_at: timestamp
IdeViewState:
  task_id: string|null
  projected_through_seq: integer
  panel: chat|plan|diff|artifact|approval
  workspace_trusted: boolean
```

扩展接口包括 `create/resume task`, `append turn`, `attach context`, `apply/reject diff`, `approve`, `cancel`, `open artifact`。
未保存 buffer 使用 document version 与内容 ref；落盘前必须检测版本漂移。
远程 workspace URI 不转换成本机路径，文件操作由对应 remote authority 执行。

## 事件投影与编辑

chat、plan、tool、diff、artifact、approval 都由 typed event 投影。
extension reload 后以 task_id + cursor 恢复，不解析 WebView HTML 或终端文本。
Apply Edit 使用编辑器 WorkspaceEdit/transaction API，并带 expected document version/hash。
Agent 终端使用独立 pseudoterminal/process identity，用户终端不被静默接管。
窗口切换时 context hint 失效或重新捕获，避免把另一 workspace selection 注入当前 Task。

## 四级增量

### `runnable` 能跑

提供命令面板入口，将当前文件/selection 发送给单任务后端并展示文本结果。

### `usable` 能用

增加 chat panel、历史、diff review、terminal、diagnostics 引用、approval 和 resume。

### `productive` 顺手

增加 inline action、后台 Agent、worktree、代码操作、artifact、任务状态栏和多窗口切换。

### `polished` 好用

增加 VS Code/JetBrains 等适配、remote dev、企业策略、无障碍、遥测治理和版本兼容。

## 直接升级与回滚

先抽离 core protocol 与 IDE adapter，确保 CLI/桌面可消费同一事件。
WebView/面板升级用 versioned message schema；新旧 extension/backend 做握手协商。
inline apply 先以 preview-only feature flag 上线，再开放写入。
回滚扩展不回滚任务事件；缺少新 item 类型时降级只读/通用卡片。

## 失败模式与安全

- workspace untrusted：禁用执行/写入，只允许受限解释。
- stale buffer：expected version 不符时显示 diff 冲突。
- 窗口串线：所有 hint 带 window/workspace/task identity。
- extension reload：cursor 恢复，未发送输入留本地 draft。
- protocol mismatch：协商最低兼容版本，不静默丢事件。
- terminal injection：命令预览、控制字符清理与明确 approval。
- remote path：不将远程 secret/文件复制到本机缓存无审计位置。

## 验收 oracle

1. 未保存 buffer 修改后旧 diff 不能静默 apply。
2. 两窗口两 workspace 的 selection 不串到错误 Task。
3. reload 后 plan、approval、artifact 与服务端一致。
4. untrusted workspace 无 shell/写操作。
5. 后端发未知 item 类型时扩展可降级且不崩溃。
6. screen reader/键盘可完成 review 与 approval，状态不只靠颜色。

## 来源与设计综合

参考 [VS Code Extension API](https://code.visualstudio.com/api) 与 [Language Server Protocol](https://microsoft.github.io/language-server-protocol/) 的 client/server 分离。
产品具体编辑器命令、WebView 视觉和 worktree 策略由 dossier 定义；共享层只规定协议、context freshness 与安全编辑。
