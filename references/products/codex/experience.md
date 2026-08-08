# Codex 体验蒸馏

## 表面组合

Codex 体验由共享 runtime 上的多个 adapter 组成：

- 交互 CLI/TUI：主任务流、审批、计划、diff、会话控制；
- exec/headless：脚本和 CI 中的单次任务、结构化输出和退出码；
- app-server client：IDE、桌面或其他长期连接客户端；
- remote/cloud 表面：延续相同 thread/turn/item 心智模型。

产品体验不应让某个界面拥有额外的隐藏执行语义。CLI 能恢复的 session，IDE 也应能从协议读取；headless 的失败要与 TUI 显示的失败使用相同错误分类。

## 主交互流

1. 启动时明确 cwd、仓库、模型、权限与 sandbox profile。
2. 用户提交任务后立即产生稳定 turn id 和 running 状态。
3. 文本、reasoning 摘要、tool call、命令输出和 diff 分区域流式呈现。
4. 审批卡说明动作、原因、影响范围和 grant scope。
5. 用户可在模型工作时 steering、排队后续输入或 interrupt。
6. 结束时给出改动、验证、未完成项、费用/用量和可执行下一步。

## TUI 信息架构

建议最小区域：

- transcript：user/agent message 与折叠的 reasoning；
- activity：工具、命令、subagent、MCP 状态；
- plan：当前步骤和终态；
- diff/review：文件级与 hunk 级变化；
- composer：多行输入、附件、slash command、steering；
- status line：模型、cwd、branch、sandbox、context usage。

源码：https://github.com/openai/codex/tree/92fb33b7583ac909a21efaebcd2fad6e79643a6f/codex-rs/tui

## 审批体验

审批不是简单 yes/no。至少提供：

- allow once；
- allow for session 或保存受限规则；
- deny，并把原因返回 agent；
- 显示规范化命令、目标路径、网络域和是否脱离 sandbox；
- 键盘可操作，断线后仍可恢复待审批状态。

## 会话体验

支持 list、resume、fork、rollback、archive、rename 等操作时，界面应区分：

- conversation rollback：丢弃后续对话状态；
- code rollback：恢复文件或 checkpoint；
- fork：保留原 thread，产生新 id；
- interrupt：终止当前 turn，不删除历史。

切换模型、权限或工作区后，应通过事件明确记录配置差异，避免恢复时“看起来相同、实际不同”。

## Headless 合同

非交互模式必须有稳定退出码、stdout/stderr 分离、JSON/JSONL 事件或 output schema、超时和取消。机器消费者不应解析彩色 TUI 文本。涉及审批且无人回答时应失败或按显式 policy 处理，不能永久挂起。

来源：

- https://github.com/openai/codex/blob/92fb33b7583ac909a21efaebcd2fad6e79643a6f/docs/exec.md
- https://learn.chatgpt.com/docs/codex/cli

## 体验验收

- 1000 个增量事件下界面不丢状态、不重复 tool card；
- resize、窄终端、无颜色、键盘和 screen reader 兼容；
- 重连后恢复 streaming/approval/plan；
- 大输出折叠但可展开或导出；
- 用户 interrupt 在 UI 立即反馈，并最终与 runtime 终态一致；
- headless 与 TUI 对同一 fixture 产生等价 item 序列。

## 降级与空状态

无 TTY 时交互入口应自动切换为纯文本或明确要求 headless 参数，不能输出不可解析控制码。
终端不支持真彩色、鼠标或图片时，信息仍须通过文本、符号和 artifact 链接表达。
模型、MCP 或远程 executor 离线时，界面显示可操作错误、重试范围和已保留状态。
首次启动、没有历史 thread、空 diff 和无活动 plan 都应有明确空状态，而不是空白区域。
客户端版本过旧时展示协议不兼容与升级路径，不用无限重连掩盖错误。
所有降级只改变呈现或可用 capability，不改变 canonical event 的终态语义。

实现协议与重连细节见 [protocol-state.md](protocol-state.md)，完整界面黑盒门禁见 [acceptance-tests.md](acceptance-tests.md)。
