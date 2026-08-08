# Codex 产品蒸馏索引

## 产品定位

Codex 是以本地工作区为中心、同时支持 CLI、TUI、非交互执行与多种客户端的编码 Agent。它最值得蒸馏的不是终端配色，而是同一 headless runtime 对外提供稳定事件协议，并把模型循环、上下文、工具、策略、强制执行和持久化分层。

本目录研究快照：

- status: researched
- retrieved: 2026-08-08
- repository: https://github.com/openai/codex
- commit: 92fb33b7583ac909a21efaebcd2fad6e79643a6f
- GitHub API stars: 104637（动态值，仅表示查询时快照）
- license: Apache-2.0

## 证据结论

| 结论 | 证据 | 置信度 |
|---|---|---|
| Rust workspace 将 core、protocol、exec、TUI、app-server、sandbox 分开 | code | 高 |
| 一个用户 turn 内可反复采样、执行工具、写回结果，直到自然结束 | code | 高 |
| app-server 用 thread、turn、item 和增量通知为客户端提供协议 | code/protocol | 高 |
| approval policy 与 sandbox enforcement 是两个边界 | code/official-doc | 高 |
| 上下文压缩、子代理、MCP、skills、hooks 均已进入 runtime 或协议 | code | 高 |

## 十二篇专题导航

建议另一个大模型按以下顺序读取，不要只读 `recipe.md` 后直接生成代码：

1. [product-contract.md](product-contract.md)：可观察产品合同、能力边界、SLO 与非目标。
2. [architecture.md](architecture.md)：进程、crate、协议、状态等模块边界的研究摘要。
3. [agent-loop.md](agent-loop.md)：turn actor 状态机、伪代码、重试、取消与 steering。
4. [protocol-state.md](protocol-state.md)：thread/turn/item/event 命令、事件、JSON 与兼容规则。
5. [context-tools.md](context-tools.md)：上下文、压缩、工具、计划、MCP、skills 与子代理。
6. [workspace-execution.md](workspace-execution.md)：文件、patch、shell、PTY、git、worktree 与 executor。
7. [safety-runtime.md](safety-runtime.md)：权限、sandbox、网络和强制执行的研究摘要。
8. [persistence-recovery.md](persistence-recovery.md)：schema、append 事务、恢复、fork、rollback 与迁移。
9. [experience.md](experience.md)：CLI/TUI/headless/app-server 的交互设计。
10. [acceptance-tests.md](acceptance-tests.md)：四级黑盒、安全、故障注入与出厂门禁。
11. [recipe.md](recipe.md)：相对共享架构的差量、四级实现和直接升级路径。
12. [sources.md](sources.md)：固定 commit 源码地图、公开论断与不可验证边界。

其中 `architecture.md`、`context-tools.md`、`safety-runtime.md` 和 `experience.md` 是研究摘要；新增实现文档负责消除代码生成歧义。发生冲突时，以产品合同、协议状态、验收测试的强制不变量为准。

## 适用与边界

适合：终端优先、需要本地执行、希望同一 runtime 支撑多个前端、重视权限和恢复的产品。

不应照搬：OpenAI 品牌、产品名称、私有服务、不可验证提示词、专有认证流程。蒸馏时复现能力合同和状态语义，不做视觉或商标克隆。

## 主要来源

- CLI: https://learn.chatgpt.com/docs/codex/cli
- Security: https://learn.chatgpt.com/docs/security
- MCP: https://learn.chatgpt.com/docs/extend/mcp?surface=cli
- Skills: https://learn.chatgpt.com/docs/build-skills
- Subagents: https://learn.chatgpt.com/docs/agent-configuration/subagents
- Source workspace: https://github.com/openai/codex/tree/92fb33b7583ac909a21efaebcd2fad6e79643a6f/codex-rs
- Repository docs: https://github.com/openai/codex/tree/92fb33b7583ac909a21efaebcd2fad6e79643a6f/docs

逐项固定链接与论断对应关系见 [sources.md](sources.md)。

## 给实现模型的使用约束

实现模型应先选择 `runnable`、`usable`、`productive` 或 `polished` 目标等级，再从产品合同建立 capability checklist。
不要一次生成整个仓库后才测试；按 protocol → loop → executor → persistence → surface 的垂直切片逐步交付。
每完成一个切片，立即运行 [acceptance-tests.md](acceptance-tests.md) 中对应的最小黑盒场景。
所有外部 SDK 都放在 adapter 后面，核心状态机不能依赖某个模型厂商或 UI 框架。
所有示例字段都允许做等价命名，但对象边界、单终态、因果 id、顺序和安全不变量不能省略。
闭源或线上行为不能从品牌相似性推断；无法验证的选择写入项目 ADR，并标记为设计综合。

建议生成仓库至少包含以下顶层模块：

- `protocol`：命令、事件、schema、版本与 golden fixtures；
- `runtime`：thread/turn actor、模型 adapter、context 和 tool router；
- `executor`：文件、patch、shell、PTY、git 和 sandbox adapter；
- `state`：rollout、索引、恢复、迁移和 artifact；
- `surfaces`：CLI/TUI、headless、app-server 或 IDE adapter；
- `tests`：scripted model、fake executor、故障注入和分级验收。

若实现语言不支持进程内 actor，可用单写者 event loop 或串行事务队列实现同样语义。
若目标环境没有强制 sandbox，只能标注受限安全能力，不得通过修改文案把等级提升为 polished。
