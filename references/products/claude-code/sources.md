# Claude Code 来源、证据与推断登记

> 检索快照：2026-08-08。URL 和产品行为会变化；实现前应重新核对官方文档。本文不把公开仓库误称为完整 runtime 源码。

## 目录

- [证据分级](#证据分级)
- [官方核心文档](#官方核心文档)
- [扩展与运行时文档](#扩展与运行时文档)
- [产品表面文档](#产品表面文档)
- [公开仓库](#公开仓库)
- [声明到来源映射](#声明到来源映射)
- [不可证实事项](#不可证实事项)
- [调研复核清单](#调研复核清单)

## 证据分级

### A：官方行为合同

官方文档直接说明的用户可观察能力，可进入 parity contract。

### B：公开仓库证据

公开示例、插件 manifest、hook 和 skill 可证明扩展格式；不能推出闭源主 runtime 架构。

### C：可重复黑盒观察

通过公开 CLI/SDK 在合法使用下观察；必须记录版本、平台、命令和日期。

### D：Inference / design synthesis

为实现相同用户结果而设计的数据结构、模块和算法；不得描述为 Claude Code 内部事实。

### 禁止证据升级

- issue 评论不能自动升级为官方稳定合同。
- 安装包文件名不能证明整体内部架构。
- 公开仓库语言统计不能证明闭源 runtime 的语言。
- UI 截图不能证明跨表面共享数据库或进程。

## 官方核心文档

### 产品与循环

- Overview — https://code.claude.com/docs/en/overview
- How Claude Code works — https://code.claude.com/docs/en/how-claude-code-works
- Documentation index — https://code.claude.com/docs/llms.txt

支持声明：terminal-first coding agent；gather context / take action / verify results；用户 steer/interrupt。

不支持声明：内部状态枚举、loop 类名、私有 system prompt。

### Session 与恢复

- Sessions — https://code.claude.com/docs/en/sessions
- Checkpointing — https://code.claude.com/docs/en/checkpointing

支持声明：continue/resume/rename/branch；本地 transcript；rewind conversation/code/both；外部副作用不由文件 checkpoint 回滚。

注意：内部 JSONL 行格式可能变化，蒸馏实现应提供自己的稳定协议。

### Context、Memory 与 Cache

- Memory — https://code.claude.com/docs/en/memory
- Context window — https://code.claude.com/docs/en/context-window
- Prompt caching — https://code.claude.com/docs/en/prompt-caching
- Costs — https://code.claude.com/docs/en/costs
- Status line — https://code.claude.com/docs/en/statusline

支持声明：CLAUDE.md、rules、auto memory；自动/手动 compact 和 context 可见性；prompt caching 和 usage/cost 展示。

不支持声明：memory 选择算法、compact prompt、cache key、内部 token 分桶。

### 权限与 Sandbox

- Permissions — https://code.claude.com/docs/en/permissions
- Permission modes — https://code.claude.com/docs/en/permission-modes
- Sandboxing — https://code.claude.com/docs/en/sandboxing

支持声明：allow/ask/deny；配置来源与 modes；macOS Seatbelt；Linux/WSL2 bubblewrap、网络代理和可选 seccomp；native Windows 能力差异。

不支持声明：闭源 profile compiler、精确内部 precedence 函数、风险评分模型。

## 扩展与运行时文档

### Agents、Plans 与 Teams

- Subagents — https://code.claude.com/docs/en/sub-agents
- Agents — https://code.claude.com/docs/en/agents
- Agent teams — https://code.claude.com/docs/en/agent-teams
- How it works — https://code.claude.com/docs/en/how-claude-code-works

支持声明：独立 context、prompt、tools、permissions；background/agent view；team collaboration。

不支持声明：scheduler 算法、agent message bus、预算内部默认值。

### MCP、Skills、Hooks 与 Plugins

- MCP — https://code.claude.com/docs/en/mcp
- Skills — https://code.claude.com/docs/en/skills
- Hooks — https://code.claude.com/docs/en/hooks
- Plugins — https://code.claude.com/docs/en/plugins
- Plugin marketplaces — https://code.claude.com/docs/en/plugin-marketplaces

支持声明：公开配置、生命周期、扩展打包和 Agent Skills 兼容范围。

不支持声明：闭源 loader 组件树、插件内部信任实现、私有 marketplace 后端。

## 产品表面文档

### CLI 与 Headless

- Interactive mode — https://code.claude.com/docs/en/interactive-mode
- Commands — https://code.claude.com/docs/en/commands
- Terminal configuration — https://code.claude.com/docs/en/terminal-config
- Headless / CLI reference — 从 https://code.claude.com/docs/llms.txt 定位当前条目

支持声明：interactive streaming、slash commands、non-interactive/programmatic use。

### IDE、Desktop、Web 与 SDK

- VS Code — https://code.claude.com/docs/en/vs-code
- Desktop — https://code.claude.com/docs/en/desktop
- Claude Code on the web — https://code.claude.com/docs/en/claude-code-on-the-web
- Agent SDK overview — https://code.claude.com/docs/en/agent-sdk/overview

支持声明：存在这些产品表面及各自公开功能。

不支持声明：所有表面共享同一 session store、相同发布节奏或内部协议。

## 公开仓库

### anthropics/claude-code

- Repository — https://github.com/anthropics/claude-code
- Plugins — https://github.com/anthropics/claude-code/tree/main/plugins
- Hook examples — https://github.com/anthropics/claude-code/tree/main/examples/hooks
- Plugin dev toolkit — https://github.com/anthropics/claude-code/tree/main/plugins/plugin-dev

可用于：manifest、skills、agents、commands、hooks、MCP 的公开示例和工具链研究。

不可用于：宣称获取完整 Agent loop、context manager、sandbox、TUI 或 session runtime 源码。

许可注意：仓库使用 Anthropic 商业条款；逐文件复用前必须核对许可，不应复制商业代码到生成项目。

### 高星参考实现的使用原则

可选公开实现应从各自官方仓库核对版本与许可，例如 MCP SDK、bubblewrap、OpenTelemetry、SQLite 和终端 UI 库。

星数只用于发现候选，不是安全、维护性或许可合规证明。

本 dossier 不固定第三方版本；生成时必须产生 dependency ledger：repo、commit/tag、license、purpose、替代项。

## 声明到来源映射

| 合同声明 | 证据 | 本目录落点 |
|---|---|---|
| gather/action/verify | How it works | agent-loop.md |
| CLAUDE.md/rules/memory | Memory | context-tools.md |
| compact/context/cache | Context/Prompt caching | persistence-recovery.md |
| allow/ask/deny | Permissions | safety-runtime.md |
| Seatbelt/bubblewrap | Sandboxing | workspace-execution.md |
| plan/tasks | How it works/permission modes | agent-loop.md |
| subagents/teams | Subagents/Agent teams | agent-loop.md |
| resume/branch/JSONL | Sessions | persistence-recovery.md |
| checkpoint/rewind | Checkpointing | persistence-recovery.md |
| hooks/skills/plugins/MCP | 对应扩展文档 + repo | context-tools.md |
| CLI/IDE/Desktop/Web/SDK | 对应 surface 文档 | experience.md |

## 不可证实事项

以下只能标 `inference`，直到出现新的官方/开源证据：

- runtime 实际编程语言和内部模块图。
- 私有 system prompt、tool prompt 和 compact prompt。
- session JSONL 每种内部 record 的稳定 schema。
- prompt cache key、TTL 和切分启发式。
- auto memory 的提取、排序和淘汰算法。
- permission 规则精确内部求值器。
- subagent/team scheduler 和消息传输实现。
- CLI、IDE、Desktop、Web 是否共享进程、数据库或代码库。
- 模型选择、fallback、重试和 token reserve 的私有策略。
- 遥测事件、后端基础设施和 SLO。

若实现者选择 actor、SQLite、JSONL、Seatbelt adapter 或 workflow engine，应写“本实现采用”，不能写“Claude Code 使用”。

## 调研复核清单

每次发布蒸馏 skill 前：

1. 从 `llms.txt` 检查文档路径是否变更。
2. 记录检索日期、产品版本、OS 和账户能力。
3. 对关键行为保存合法黑盒 test transcript，先脱敏。
4. 检查公开仓库 LICENSE、release/tag 和 breaking changes。
5. 把新增声明登记为 A/B/C/D 证据等级。
6. 无来源的内部描述改成 inference 或删除。
7. 更新 acceptance fixture，不用截图代替结构化 oracle。
8. 对不同平台分别核验 sandbox capability。
9. 对 IDE/Desktop/Web 明确 session 是否实际互通。
10. 复核品牌、代码许可和隐私边界。
