# Codex 安全与执行运行时

## 两层安全模型

Codex 最重要的安全设计是把授权决策和执行约束分开：

| 层 | 回答的问题 | 典型输出 |
|---|---|---|
| policy/approval | 这次动作是否允许、是否询问用户 | allow、ask、deny、grant scope |
| sandbox/enforcement | 即使获准，进程实际上能访问什么 | filesystem、network、process boundary |

字符串命令黑名单不能代替 sandbox；sandbox 也不能替代用户对 git push、删除、外部写操作的意图确认。

官方安全说明：https://learn.chatgpt.com/docs/security

## Sandbox 模式

公开源码与文档展示了 read-only、workspace-write、danger-full-access 等能力层级，以及 macOS/Linux/Windows 的平台实现。产品配方应抽象为统一 SandboxProfile，不把平台细节泄漏给 agent loop。

公开实现入口：

- sandboxing abstraction: https://github.com/openai/codex/tree/92fb33b7583ac909a21efaebcd2fad6e79643a6f/codex-rs/sandboxing
- Linux sandbox: https://github.com/openai/codex/tree/92fb33b7583ac909a21efaebcd2fad6e79643a6f/codex-rs/linux-sandbox
- Windows sandbox: https://github.com/openai/codex/tree/92fb33b7583ac909a21efaebcd2fad6e79643a6f/codex-rs/windows-sandbox-rs
- repository sandbox guide: https://github.com/openai/codex/blob/92fb33b7583ac909a21efaebcd2fad6e79643a6f/docs/sandbox.md

强制不变量：

- workspace root 在执行前 canonicalize，防止 symlink 和相对路径逃逸；
- 默认禁止工作区外写入；
- 网络默认关闭或按 profile/domain 开放；
- 子进程继承同一边界；
- danger-full-access 必须是显式配置，不能由模型自行升级；
- sandbox 不可用时不能静默声称已隔离。

## Shell 与进程

Shell 工具需要独立处理命令规范化、PTY、输出流、stdin、resize、timeout、取消和终态。进程 handle 与逻辑 tool call id 分离，断线和重试不得重复启动有副作用的命令。

执行事件至少包括：started、stdout delta、stderr delta、approval requested、exited、timed out、cancelled。超长输出进入 artifact/store，并向模型返回有界摘要及引用。

文件、patch、PTY、git、worktree 与 executor 的可执行规范统一见 [workspace-execution.md](workspace-execution.md)。

## 权限持久化

审批可以只对本次调用、本 turn、本 session 或受限 command prefix 生效。保存授权前必须显示规范化后的目标，而非模型原始字符串。workspace/project 规则和 managed policy 分层合并，deny/组织约束不得被用户层覆盖。

相关源码：

- approvals: https://github.com/openai/codex/blob/92fb33b7583ac909a21efaebcd2fad6e79643a6f/codex-rs/core/src/tools/approvals.rs
- config permissions: https://github.com/openai/codex/tree/92fb33b7583ac909a21efaebcd2fad6e79643a6f/codex-rs/core/src/config
- exec policy: https://github.com/openai/codex/blob/92fb33b7583ac909a21efaebcd2fad6e79643a6f/docs/execpolicy.md

## 状态、恢复与回滚

Thread/turn/item 的 append-first rollout 是审计源；SQLite 或其他数据库适合做索引、列表和派生状态。恢复时要识别：

- 已请求但未执行的 tool call；
- 已执行但结果未持久化的副作用；
- 尚未终止的进程；
- 被中断的 turn；
- rollback 后失效的上下文基线。

副作用工具应使用 idempotency key 或人工复核，绝不能简单重放。

逻辑 schema、append 事务、崩溃分类和迁移步骤统一见 [persistence-recovery.md](persistence-recovery.md)。

## 安全验收

- 路径穿越、symlink、工作区外写入测试；
- 网络默认拒绝和允许域测试；
- approval grant scope 与 deny precedence；
- 取消正在运行的进程并清理子进程；
- 恶意仓库 AGENTS.md/MCP 输出不能提升权限；
- app-server 辅助接口与普通工具使用同一 policy boundary；
- 日志、rollout、遥测不写入 secrets。

安全套件不能只断言返回错误，还要检查文件、进程、网络和远端系统确实没有目标副作用。
平台 adapter 缺失、启动失败或能力报告不完整时，runtime 应 fail closed 或要求用户显式选择降级 profile。
完整故障注入、managed policy 和跨平台用例见 [acceptance-tests.md](acceptance-tests.md)。
公开源码与官方安全论断的固定 commit 映射见 [sources.md](sources.md)。
