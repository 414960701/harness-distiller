# Codex 上下文与工具

## 上下文组成

Codex 的模型输入不是简单 messages 数组。公开源码可验证的组成包括：

- developer/system instructions；
- AGENTS.md 与用户指令；
- workspace、cwd、shell、时间等环境上下文；
- collaboration mode、personality、permissions 等 world state；
- 历史 user/assistant/tool items；
- 本轮动态工具、MCP、skills 和插件信息；
- 图片、音频等受模型能力过滤的输入。

ContextManager 同时维护历史和 world-state baseline。稳定状态可按差量注入；压缩、rollback、模型变化或基线失效时必须完整重注入，避免模型只看到一半配置。

源码：

- context manager: https://github.com/openai/codex/tree/92fb33b7583ac909a21efaebcd2fad6e79643a6f/codex-rs/core/src/context_manager
- world state: https://github.com/openai/codex/tree/92fb33b7583ac909a21efaebcd2fad6e79643a6f/codex-rs/core/src/context/world_state
- AGENTS.md loading: https://github.com/openai/codex/blob/92fb33b7583ac909a21efaebcd2fad6e79643a6f/codex-rs/core/src/agents_md.rs

## Token 预算与压缩

压缩包含手动、turn 前自动和 turn 中 inline 路径。关键语义不是“调用一个总结 prompt”，而是：

1. 在确定的 token 阈值触发；
2. 压缩前后发 lifecycle hook/event；
3. 生成 summary item；
4. 保留必要 user messages；
5. 根据压缩发生位置决定初始上下文何时重新注入；
6. 替换模型可见历史但保留可审计 checkpoint；
7. 重算 token usage 后继续当前任务。

源码：https://github.com/openai/codex/blob/92fb33b7583ac909a21efaebcd2fad6e79643a6f/codex-rs/core/src/compact.rs

压缩不变量：

- 不产生孤立 tool call/result；
- 当前用户意图、未完成计划、修改文件、失败命令和待验证项必须进入摘要；
- 原始 rollout 不因压缩被不可逆删除；
- 压缩失败有裁剪或新 thread 建议，不无限递归。

## 工具体系

ToolSpec 描述模型可见 schema；ToolRegistry 绑定 handler；ToolRouter 解析调用并将执行结果归一化为协议 item。执行前后经过审批、sandbox、hook、遥测和 diff tracking。

代表性工具域：

- 文件搜索、读取、apply patch；
- shell/PTY 与 stdin continuation；
- web search、view image；
- plan、review、用户输入；
- MCP、动态工具、skills；
- agent collaboration。

源码：

- router: https://github.com/openai/codex/blob/92fb33b7583ac909a21efaebcd2fad6e79643a6f/codex-rs/core/src/tools/router.rs
- registry: https://github.com/openai/codex/blob/92fb33b7583ac909a21efaebcd2fad6e79643a6f/codex-rs/core/src/tools/registry.rs
- tool handlers: https://github.com/openai/codex/tree/92fb33b7583ac909a21efaebcd2fad6e79643a6f/codex-rs/core/src/tools/handlers

## 计划与子代理

计划是结构化状态并发出 plan delta/update，而非只在聊天中打印 Markdown。子代理由 agent registry、role、control 和 spawn 路径管理，具有独立上下文和状态；父 agent 只接收所需结果和通知。

源码：

- agent control: https://github.com/openai/codex/tree/92fb33b7583ac909a21efaebcd2fad6e79643a6f/codex-rs/core/src/agent/control
- agent registry: https://github.com/openai/codex/blob/92fb33b7583ac909a21efaebcd2fad6e79643a6f/codex-rs/core/src/agent/registry.rs
- multi-agent session: https://github.com/openai/codex/blob/92fb33b7583ac909a21efaebcd2fad6e79643a6f/codex-rs/core/src/session/multi_agents.rs

蒸馏要求：子代理必须有 parent id、独立预算、权限收窄、取消传播、终态和结果回传，不能只是同一上下文里换一段 prompt。

## MCP、Skills 与 Hooks

- MCP 是外部工具/资源协议，连接、OAuth、工具审批和状态均需显式建模。
- Skill 采用按需加载：先暴露小型元数据，命中后读取 SKILL.md 及必要资源。
- Hook 是 lifecycle policy/automation，不应允许任意 hook 绕过 sandbox。

官方来源：

- https://learn.chatgpt.com/docs/extend/mcp?surface=cli
- https://learn.chatgpt.com/docs/build-skills

