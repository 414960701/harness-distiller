# CLI 与 TUI

## 职责与非目标

CLI 提供稳定、可脚本化的 command/JSON/退出码；TUI 是任务事件的交互投影和 command client。
终端文本不是状态事实源，重连/恢复必须从 snapshot + event cursor 重建。
TUI 不直接执行越权工具，不从模型文本猜 plan、approval 或 completed。
非交互模式与交互模式调用同一服务合同，只更换输入输出适配器。

## 接口与状态

```yaml
CliRequest:
  command: run|resume|list|inspect|cancel|approve|export
  task_id: string|null
  input: string|json|null
  output_mode: human|json|jsonl
  non_interactive: boolean
TuiViewState:
  task_id: string
  projected_through_seq: integer
  focus: composer|transcript|plan|diff|approval|terminal
  connection: online|reconnecting|offline
  input_queue: [input_id]
```

CLI stdout 只输出请求结果，diagnostic 走 stderr；退出码稳定区分 success、partial、invalid input、permission、cancelled 和 runtime failure。
JSON/JSONL schema 有版本；人类渲染可变化但不可破坏机器输出。
Ctrl-C 第一次请求取消当前 Run，第二次按明确规则退出 client，不杀死无关后台任务。

## 事件投影

TUI pane 订阅 Task/Turn/Step/ToolCall/Artifact/Approval 事件并保存 cursor。
跳号时补拉，重复 event_id 去重，断线显示 stale 状态而非假装实时。
流式文本是同一 item 的 delta，terminal/diff/artifact 是独立 typed item。
窄终端可折叠 pane，但 plan、风险审批和最终 artifact 仍可访问。
粘贴、steering 与新 turn 使用不同 command，避免竞态。

## 四级增量

### `runnable` 能跑

提供非交互 `run`、human 输出、稳定退出码和 Ctrl-C 取消。

### `usable` 能用

增加交互 transcript/composer、resume、plan、approval、diff 和 JSONL 事件输出。

### `productive` 顺手

增加多 pane、后台任务切换、输入队列、搜索、快捷键、artifact 打开和断线续传。

### `polished` 好用

增加远程连接、无障碍、国际化、完整自动化 schema、低带宽模式与兼容矩阵。

## 直接升级与回滚

先把旧 stdout parsing 替换为 typed event adapter，再增加 TUI 投影。
保持原 CLI flags/exit codes 的兼容层，新增 JSON schema 用 version 字段。
多 pane 可通过 feature flag 回退单 pane；服务端事件不随 UI 回滚。
远程连接失败时回退本地/只读状态，不能重放非幂等 command。

## 失败模式与安全

- 非 TTY：自动禁用 ANSI、spinner 与交互询问，缺审批时报明确错误。
- 断连：保留 cursor，重连补事件，command 以 idempotency key 去重。
- 粘贴攻击：多行粘贴预览/确认，不执行终端 escape。
- 多字节宽度：使用 grapheme/terminal width，不按 bytes 截断。
- secret：输入关闭回显，历史与日志脱敏。
- 过期 approval：服务端拒绝，不把迟到按键用于新请求。

## 验收 oracle

1. 80/40 列终端均能完成创建、审批、取消和打开 artifact。
2. 非 TTY JSONL 无 ANSI 且 schema 可解析。
3. 断线重连后 view 与服务端事件重放一致。
4. 重复提交同一 command_id 只产生一次动作。
5. Ctrl-C 不误杀其他后台 Task。
6. RTL/CJK/emoji 不破坏焦点、diff 行号与光标。

## 来源与设计综合

参考 [Command Line Interface Guidelines](https://clig.dev/)、[JSON Lines](https://jsonlines.org/) 和终端事件循环的一般实践。
产品专属快捷键、pane 布局和事件 schema 由 dossier 决定；共享层要求事件投影与机器合同稳定。
