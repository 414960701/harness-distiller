# Codex 配方

## 目录

1. 配方目标
2. 必读实现文档
3. 共享能力差量
4. 推荐蓝图默认值
5. 四级实现与验收
6. 直接升级
7. 非目标

## 配方目标

在共享 harness 架构之上增加 Codex 风格差量：Rust 或等价的强类型 headless runtime、thread/turn/item 事件协议、终端优先交互、审批与 sandbox 分层、apply-patch/shell 工具、可恢复 rollout、app-server、多 agent 与扩展机制。

本配方是设计综合，不声称复刻 OpenAI 私有服务或提示词。

## 必读实现文档

生成实现前必须读取以下文档，不能只依据本配方或产品名称自由发挥：

- [product-contract.md](product-contract.md)：确定用户可观察行为和非目标；
- [agent-loop.md](agent-loop.md)：实现 turn actor、多步采样、重试、取消和 steering；
- [protocol-state.md](protocol-state.md)：实现 thread/turn/item/event 与命令事件协议；
- [context-tools.md](context-tools.md)：实现上下文、压缩、工具、MCP、skills 和子代理；
- [workspace-execution.md](workspace-execution.md)：实现 read/patch/shell/PTY/git/worktree executor；
- [safety-runtime.md](safety-runtime.md)：实现 approval 与 sandbox 双层边界；
- [persistence-recovery.md](persistence-recovery.md)：实现 rollout、索引、恢复、迁移和副作用回执；
- [experience.md](experience.md)：实现 TUI、headless 和 app-server 表面；
- [acceptance-tests.md](acceptance-tests.md)：以等级门禁判定完成，不以代码生成结束判定；
- [sources.md](sources.md)：区分公开事实、设计综合和不可验证内容。

`architecture.md` 是上述模块的研究索引；详细实现以对应专题文档为准，避免在多篇中维护互相漂移的伪代码。

## 共享能力差量

| 共享模块 | Codex 默认差量 |
|---|---|
| protocol-events | Item 级 started/delta/completed；turn steering/interrupt；capability negotiation |
| agent-loop | step context 快照；多工具循环；inline compaction；pending input |
| context-engine | world-state baseline/diff；AGENTS.md；模态过滤；可审计压缩 |
| tool-runtime | ToolSpec/Registry/Router；apply patch；持久 shell/PTY；动态与 MCP 工具 |
| permission-policy | allow/ask/deny 与 grant scope；managed constraints |
| sandbox | read-only/workspace-write/danger profile；平台 enforcement adapter |
| state-persistence | append-first rollout + 可重建索引；resume/fork/rollback |
| subagents | registry/role/parent-child/cancel/result；独立上下文和权限 |
| cli-tui | transcript、activity、plan、diff、approval、composer、status |
| deployment-update | interactive、exec、app-server 三入口共享 runtime |

## 推荐蓝图默认值

- recipe: codex
- primary surfaces: tui, headless
- optional surfaces: ide, desktop, sdk
- execution: local；productive 起支持 worktree，polished 起支持 remote
- state: append-only event log + SQLite index
- security: workspace-write + on-request approval
- provider layer: Responses/tool-call 能力归一化，不锁定单一厂商

## 四级实现与验收

### runnable / 能跑

实现：单 thread/turn、一个模型 adapter、read/apply-patch/shell、workspace root、基础 ask、流式 item event、CLI。

验收：

- 给定 fixture，完成读文件、修改、运行测试的闭环；
- tool call/result 一一配对；
- 工作区外写入被拒绝；
- 模型、工具错误和 Ctrl-C 都进入明确终态；
- 事件 trace 可独立重放为最终 transcript。

### usable / 能用

增量：thread/turn/item 持久化、resume、计划、token budget、自动/手动 compaction、结构化 diff、PTY continuation、MCP、TUI。

验收：

- 崩溃后恢复，不重复已完成副作用；
- 长会话压缩后仍保留当前任务、计划和改动；
- approval 拒绝可反馈模型并自然收尾；
- TUI 和 headless 对同一事件 fixture 等价；
- app restart 后可 list/resume thread。

### productive / 顺手

增量：app-server、IDE adapter、worktree、checkpoint/fork/rollback、background command、subagent、skills、hooks、细粒度 permission、observability/eval。

验收：

- 两个客户端重连、订阅和 steering 无重复事件；
- 子代理隔离上下文与权限，取消向下传播；
- 并行 worktree 不互相写文件；
- hook 失败策略明确且不能绕过 sandbox；
- eval 覆盖修 bug、跨文件重构、命令失败恢复和长上下文。

### polished / 好用

增量：平台 OS sandbox、网络域策略、remote runtime、协议协商、数据库迁移、插件生命周期、企业 managed policy、无障碍/国际化、发布更新与 SLO。

验收：

- sandbox 逃逸、symlink、secret 和网络策略安全套件通过；
- 老客户端/老 session 经协商或迁移仍可读；
- remote 断线、租约过期、重复投递不重复副作用；
- 生产指标覆盖 turn 成功率、审批延迟、恢复率、sandbox failure；
- runnable、usable、productive 的全部回归场景继续通过。

## 直接升级

允许 usable 直接升级 polished，但执行顺序固定为：schema migration → protocol capability → runtime/enforcement → surface → cleanup。只修改 capability delta，不重建已有 loop。升级前保留 rollout/checkpoint，新增字段使用兼容默认值，并持续运行较低等级合同测试。

## 非目标

- 不复制 Codex 名称、图标、提示词或认证服务；
- 不把自动批准当成 sandbox；
- 不为四级生成四套互不兼容代码；
- 不用 UI 内存状态代替协议与持久化；
- 不在没有 OS/container enforcement 时宣称 polished 安全等级。
