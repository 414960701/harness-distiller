# Claude Code 配方

## 目录

- [配方声明](#配方声明)
- [实现前置阅读](#实现前置阅读)
- [共享能力差量](#共享能力差量)
- [公开实现替代](#公开实现替代)
- [推荐蓝图默认值](#推荐蓝图默认值)
- [工程构建顺序](#工程构建顺序)
- [四级实现与验收](#四级实现与验收)
- [Behavior parity 验收规则](#behavior-parity-验收规则)
- [直接升级](#直接升级)
- [非目标](#非目标)

## 配方声明

本配方以官方行为规格为兼容目标，以公开、许可证兼容的组件实现；不声称复制 Claude Code 内部架构。完整源码不可见，所有内部模块选择均是 design synthesis。

## 实现前置阅读

- 用 [product-contract.md](product-contract.md) 确定交付边界。
- 用 [sources.md](sources.md) 区分 official-doc、public-repo 与 inference。
- 用 [protocol-state.md](protocol-state.md) 冻结第一版 schema。
- 用 [acceptance-tests.md](acceptance-tests.md) 把选定等级变成发布门槛。

若生成器上下文有限，应优先注入 product-contract、protocol-state、agent-loop、workspace-execution 和 acceptance-tests，而不是只注入产品简介。

## 共享能力差量

| 共享模块 | Claude Code 风格差量 |
|---|---|
| agent-loop | gather/action/verify 自适应循环；steering、interrupt、background work |
| instructions-prompts | CLAUDE.md、scoped rules、trust/provenance；不复制专有 prompt |
| long-term-memory | repository-scoped auto memory，预算和用户可检查/删除 |
| context-engine | /context、自动/manual compact、prompt-cache-aware 预算 |
| planning | plan mode、tasks/goals，修改工具受策略限制 |
| permission-policy | allow/ask/deny、mode、scope、managed precedence |
| sandbox | Bash filesystem/network 隔离；sandbox 与 approval 分层 |
| state-persistence | JSONL 等价 append log；continue/resume/branch/export |
| git-worktree | checkpoint/rewind 与并行 worktree；明确外部副作用不可回滚 |
| subagents | 独立 context/tools/permissions/memory；background 和 teams |
| middleware-hooks | 完整 lifecycle、matcher、command/HTTP/prompt/MCP handler |
| skills-plugins | Agent Skills、plugin manifest、agents/hooks/MCP 打包 |
| surfaces | interactive CLI、headless、IDE，后续 Desktop/Web/SDK |

## 公开实现替代

由于主 runtime 闭源，优先组合：

- 自研稳定 runtime/protocol；
- SQLite 或 append JSONL session store；
- bubblewrap/Seatbelt/container sandbox；
- MCP 官方 SDK；
- Agent Skills 开放规范；
- PTY/OpenTUI 或等价可访问终端组件；
- Git snapshot/worktree；
- OpenTelemetry。

每项记录实际 license 和版本，不因为“行为像 Claude”而复制商业仓库内容。

## 推荐蓝图默认值

- recipe: claude-code
- primary surfaces: cli, headless
- optional surfaces: ide, desktop, web, sdk
- execution: local sandbox；polished 可加 remote/container
- state: append event/session log + query index
- permission mode: default
- project executable config: trust required
- memory: user-controlled, repository scoped, token capped

## 工程构建顺序

1. 建立 versioned ids、Command/Event/Item schema 和 reducer。
2. 用 ScriptedModel 实现 gather/action/verify loop 与 cancel。
3. 接入 workspace read/search/edit 和 revision-safe patch。
4. 接入 permission evaluator，再接平台 sandbox executor。
5. 实现 durable event log、artifact、resume 和 branch。
6. 增加 CLAUDE.md/rules、context budget 和 compact。
7. 增加 Plan/tasks、checkpoint/rewind 和 background process。
8. 增加 subagents/teams，并以 capability envelope 收窄权限。
9. 增加 hooks、skills、plugins 和 MCP trust gate。
10. CLI/headless 稳定后再接 IDE、Desktop/Web 与 SDK adapter。

每一步都跑已完成层的 contract tests；surface 不直接读写 runtime 私有状态。

## 四级实现与验收

### runnable / 能跑

实现：单 Agent loop、read/edit/bash、workspace root、default approval、streamed CLI、基础 transcript。

验收：

- 完成上下文收集、修改、测试和总结闭环；
- Bash 与编辑分别走明确审批；
- interrupt 终止 turn 和子进程；
- transcript 重放得到相同对话/tool 状态；
- 文档明确此级没有强 sandbox 时不能宣称安全隔离。

### usable / 能用

增量：Thread/Turn/Item、resume、plan mode、CLAUDE.md/rules、context budget、auto/manual compact、session picker、MCP、结构化 diff、重试/取消。

验收：

- 长会话压缩后保留任务、失败和验证状态；
- plan mode 不能修改文件，除非通过显式 mode transition；
- resume 不重复副作用；
- MCP server/tool 独立授权；
- /context 等价诊断能解释主要 token 消耗。

### productive / 顺手

增量：auto memory、subagent/background、hooks、skills/plugins、checkpoint/rewind、worktree、IDE、细粒度 permission、prompt cache telemetry、eval。

验收：

- 子代理有独立 context/tools/permissions，父会话只收结果；
- project hook/skill 首次运行受 trust gate；
- rewind 正确区分 code 与 conversation，外部副作用显示警告；
- memory 可查看、编辑、删除并受 token 上限；
- CLI 与 IDE 对同一事件 trace 一致。

### polished / 好用

增量：macOS/Linux/WSL2 强制 sandbox、网络域和 secret policy、agent teams/view、Desktop/Web/remote execution、protocol negotiation、managed policy、迁移、无障碍/国际化、更新和 SLO。

验收：

- sandbox escape、symlink、secret、network、unsandboxed fallback 套件通过；
- managed deny 无法被 project/user/plugin 覆盖；
- team agent 隔离 workspace、预算、权限和取消；
- 老 session/plugin/protocol 经过迁移仍能读取或给出明确错误；
- remote 断线和重复投递不重复外部 mutation；
- 所有低等级合同测试继续通过。

## Behavior parity 验收规则

只把官方文档承诺设为 parity target，例如 resume、checkpoint、permissions、sandbox、subagent 独立上下文和 hook lifecycle。以下不得写成 parity 必须项：私有 prompt、内部类名、未公开压缩算法、调度器、缓存 key、模型路由启发式、遥测后端。

对 inference 的验收应表述为“本实现满足同一用户结果”，并记录可替换实现和替代解释。

## 直接升级

usable 可直接升 polished，但内部依赖仍按 schema → protocol → policy/enforcement → runtime → surface → cleanup 执行。先迁移 session/permission/plugin schema，再启用 sandbox、remote 和团队能力；禁止重建已有 loop 或让新 UI 绕开原协议。

## 非目标

- 不复制 Claude、Anthropic 名称、视觉、提示词或私有 endpoint；
- 不把 anthropics/claude-code 公开仓库描述成完整产品源码；
- 不把 hook 当 sandbox；
- 不把 checkpoint 描述为外部副作用事务回滚；
- 不为四个等级生成四套不兼容架构。
