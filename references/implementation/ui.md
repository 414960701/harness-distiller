# UI 状态模型

## 原则

UI 是 command client 与 event projection。它可以缓存 snapshot，不得直接持有 Agent loop 的权威状态。重启或断线后必须用 snapshot + events 重建相同界面。

## 共享投影

```yaml
ThreadView:
  thread: summary
  active_turn: TurnView|null
  timeline: [ItemView]
  plan: PlanView|null
  pending_approvals: [ApprovalView]
  artifacts: [ArtifactView]
  workspace: WorkspaceView
  connection: connected|reconnecting|offline|failed
```

`ItemView` 由 item started/delta/completed 投影；流式 item 重连后以服务端最终 item 为准。

## 通用界面状态

- composer：idle/editing/submitting/disabled；
- turn：queued/running/waiting-input/completed/failed/cancelled；
- tool：proposed/waiting-approval/running/completed/failed；
- diff：loading/current/stale/conflicted/applied/reverted；
- artifact：generating/validating/ready/invalid/missing；
- connection：connected/reconnecting/offline；
- background process：running/waiting-input/exited/unknown。

每个等待状态提供原因、取消或恢复动作；不得无限 spinner。

## CLI/TUI

CLI 提供稳定退出码、JSON/JSONL 输出和非交互模式。TUI 显示 timeline、activity/tool、plan、diff、approval、composer、status。Ctrl-C 第一次请求取消当前 turn，第二次可强制退出但保留恢复记录。非 TTY 自动禁用全屏控制码。

## IDE

编辑器 selection、open files、diagnostics 和 unsaved buffer 是带 revision 的 hint。Agent 应用 change 前比较文档版本。Diff/inline comment 使用编辑器 API；终端命令仍由 runtime executor 管理。workspace trust 未建立时只读。

## Desktop/Web

支持 thread/project 列表、多任务、artifact preview、review、环境选择、通知和认证。清楚显示 local/container/remote 执行位置及数据边界。多标签同时打开时以服务端 revision 处理冲突。

## Approval UI

必须展示规范化动作，而非原始工具描述：目标文件/命令/域名/收件人、数据范围、副作用、授权期限和风险。高风险动作禁止只有模糊“允许”按钮。

## 可访问性

productive 以上要求键盘可操作、焦点顺序、屏幕阅读器标签、非颜色状态、流式更新节流与 reduced motion；polished 要求国际化、时区/数字格式和窄屏/缩放测试。

## 验收

- 用录制 event fixture 在 CLI、TUI、IDE/Web 投影出同一 turn 事实；
- 断线、重连、重复 event、sequence gap；
- 用户在模型流式时 steering；
- approval 过期时按钮不可继续执行；
- diff 基线变化进入 stale/conflict；
- artifact 验证失败不显示 Ready；
- 120/80/40 列终端与 200% 缩放；
- 键盘和屏幕阅读器完成创建任务、审批、取消和打开 artifact。

