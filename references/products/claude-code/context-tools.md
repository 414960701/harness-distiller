# Claude Code 上下文与工具

## 事实、证据与推断

| 能力 | 可确认事实 | 内部实现状态 |
|---|---|---|
| CLAUDE.md | user/project/组织等范围的持久指令 | 加载器内部不可见 |
| .claude/rules | 可按路径组织规则 | 匹配和缓存细节不可见 |
| auto memory | Claude 自动维护跨 session 学习 | 选择、写入算法不可见 |
| context window | 工具结果、文件、指令和对话占用上下文 | 内部数据结构不可见 |
| compact | 自动或手动总结以释放窗口 | 精确 prompt/算法不可见 |
| prompt caching | 产品自动管理缓存 | cache key 构造不可见 |
| subagent | 独立 context、prompt、tools、permissions | scheduler 内部不可见 |

## 指令与记忆

kind: official-doc

官方区分：

- CLAUDE.md：用户编写的项目、用户或组织指令；
- .claude/rules/：更细的规则组织；
- auto memory：Agent 根据纠正和偏好积累的 repository memory。

CLAUDE.md 和 memory 是模型上下文，不是强制安全策略。要阻止动作，应使用 permission 或 PreToolUse hook。

来源：https://code.claude.com/docs/en/memory

蒸馏实现应给每个 context fragment 记录 origin、scope、priority、loaded_at、token count 和 trust。仓库内指令属于不可信项目输入，不能改变 managed policy。

## Context budget 与 compact

kind: official-doc + inference

官方确认 context 会随对话、文件、tool output 和扩展内容增长，并支持自动压缩、/compact、/context 和 prompt caching。官方没有公开完整压缩算法。

来源：

- https://code.claude.com/docs/en/context-window
- https://code.claude.com/docs/en/prompt-caching
- https://code.claude.com/docs/en/costs

本文只确认 compact/cache 的公开边界。具体预算 schema、summary provenance、cache partition 和崩溃恢复统一见 [persistence-recovery.md](persistence-recovery.md)。

其中数据结构属于本仓库设计，不声称等于 Claude 内部实现；验收以“目标、失败、变更和验证状态不丢失”为用户结果。

## 工具与计划

kind: official-doc / behavior

公开行为包括读取/搜索文件、编辑、Bash、提问、计划、任务、Web/MCP 等；实际可见工具受版本、表面、模型、permission mode 和插件影响。生成器应使用 capability registry，不硬编码永久工具列表。

Plan mode 是权限与交互模式：先研究和规划，限制修改；它不应只是 system prompt 中的一句话。计划/任务应有结构化状态、依赖和终态，UI 可独立渲染。

来源：

- https://code.claude.com/docs/en/how-claude-code-works
- https://code.claude.com/docs/en/permission-modes

## Subagent 与 Agent Teams

kind: official-doc

Subagent 具有独立 context window、自定义 system prompt、特定工具和独立权限，并返回总结；官方还区分 background agents、agent view 和可互相通信的 agent teams。

来源：

- https://code.claude.com/docs/en/sub-agents
- https://code.claude.com/docs/en/agents
- https://code.claude.com/docs/en/agent-teams

蒸馏合同：parent id、agent definition、context boundary、permission narrowing、foreground/background、cancel、status、result artifact、成本和超时都必须显式。

具体 capability envelope、状态转移和取消传播见 [agent-loop.md](agent-loop.md)，本篇不维护第二套调度协议。

## MCP、Skills、Hooks、Plugins

kind: official-doc + public-repo

- MCP：外部 tools/resources/prompts 与 OAuth/transport。
- Skills：按需加载的 SKILL.md，可带 supporting files；遵循 Agent Skills 标准并含产品扩展。
- Hooks：session、turn、tool、permission、subagent、compact、worktree 等 lifecycle。
- Plugins：打包 skills、agents、hooks、MCP server 和 manifest。

来源：

- https://code.claude.com/docs/en/mcp
- https://code.claude.com/docs/en/skills
- https://code.claude.com/docs/en/hooks
- https://code.claude.com/docs/en/plugins
- https://github.com/anthropics/claude-code/tree/main/plugins/plugin-dev
