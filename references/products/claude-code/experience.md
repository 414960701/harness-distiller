# Claude Code 体验蒸馏

## 证据范围

本篇描述官方文档和公开可观察行为，不推断终端 UI 框架、内部组件树或闭源状态管理实现。

## 核心终端体验

kind: official-doc / behavior

用户在 repository cwd 启动会话，通过自然语言交付任务。Agent 流式输出，执行文件、Bash、MCP 等工具；需要时展示 permission prompt 或问题。用户可 interrupt、steer、排队后续输入，并使用 slash commands 管理模型、context、permissions、hooks、MCP、session 和 checkpoint。

来源：

- https://code.claude.com/docs/en/interactive-mode
- https://code.claude.com/docs/en/commands
- https://code.claude.com/docs/en/terminal-config

## 长任务的人在回路

产品体验的关键不是持续打印 token，而是把阻塞原因外显：

- 等待 permission；
- 等待问题回答；
- background Bash/subagent 仍在运行；
- context 正在 compact；
- 达到目标、失败或被中断；
- 计划和任务依赖状态。

蒸馏 UI 应以事件驱动这些状态，断线恢复后仍能回答“Agent 在做什么、需要我做什么”。

## Permission 与 sandbox 面板

kind: official-doc

/permissions 展示规则和来源；/sandbox 展示 mode、override、resolved config 和 Linux dependency 状态。审批卡应展示规范化命令、影响和允许范围；对 Bash 可提供风险解释，但解释不能自动改变 decision。

来源：

- https://code.claude.com/docs/en/permissions
- https://code.claude.com/docs/en/sandboxing

## Context 与成本可见性

kind: official-doc

/context 用于检查加载内容，status line 可显示 context usage、费用和 git 状态；/compact 手动压缩。体验上应区分模型输出 token、缓存命中、工具输出和剩余窗口，避免把“对话条数”误当上下文大小。

来源：

- https://code.claude.com/docs/en/context-window
- https://code.claude.com/docs/en/statusline
- https://code.claude.com/docs/en/costs

## Session 与 checkpoint

kind: official-doc

会话可 continue、resume、rename、branch；/resume 提供 picker。/rewind 或双击 Esc 进入 checkpoint 操作，可选择恢复 code+conversation 或只恢复 conversation。界面必须清楚区分：branch 创建新 session id，resume 继续旧 transcript，rewind 回到历史点，clear 开新上下文但旧会话仍可恢复。

来源：

- https://code.claude.com/docs/en/sessions
- https://code.claude.com/docs/en/checkpointing

## 多 Agent 体验

kind: official-doc

Subagent 适合隔离探索和噪声；agent teams/agent view 用于多个长期 session。父会话应看到 agent 名称、状态、预算、结果和是否需要输入，而不是把所有子 agent token 混入同一 transcript。

## 多表面

kind: official-doc

- CLI：终端主体验和 headless 模式；
- VS Code：inline diff、mentions、plan review；
- Desktop：并行 session、Git 隔离、terminal/editor、preview；
- Web/cloud：远程 session 与环境；
- Agent SDK：程序化 event stream 和 session 控制。

这些表面的 session history 可能独立，蒸馏产品必须明确哪些状态真正同步，不能暗示不存在的跨端一致性。

来源：

- https://code.claude.com/docs/en/vs-code
- https://code.claude.com/docs/en/desktop
- https://code.claude.com/docs/en/claude-code-on-the-web
- https://code.claude.com/docs/en/agent-sdk/overview

## 体验验收

- 用户在 streaming、tool、approval、background 任一阶段都可安全 interrupt；
- 终端 resize、无颜色、键盘导航和 screen reader 可用；
- permission 来源和 sandbox 状态始终可见；
- resume/branch/rewind/clear 不混淆数据语义；
- context 和费用可解释；
- subagent 只回传所需结果，完整日志按需展开；
- CLI 与 IDE 使用同一公开事件合同，即便存储不同。

