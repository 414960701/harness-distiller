# Claude Code 安全与执行运行时

## 权限系统：公开行为规格

kind: official-doc

官方权限规则使用 allow、ask、deny，作用于工具及匹配条件。只读工具、Bash 和文件修改的默认审批行为不同；规则可来自 managed、user、project 和 local scope。组织/managed 约束必须拥有更高优先级。

来源：https://code.claude.com/docs/en/permissions

蒸馏时将 PermissionDecision 设计为：action、rule provenance、scope、normalized target、reason、expiry。永久或项目级 grant 必须保存规范化模式，不能保存模型原始说明。

## Permission modes

kind: official-doc

产品支持 default、plan、accept edits、bypass permissions、auto 等模式，具体可用性随账户和版本变化。恢复 session 时，高风险临时模式不应静默恢复；官方 sessions 文档明确 plan 和 bypassPermissions 不按普通状态恢复。

来源：

- https://code.claude.com/docs/en/permission-modes
- https://code.claude.com/docs/en/sessions

## Bash sandbox：公开行为规格

kind: official-doc

官方说明：

- macOS 使用 Seatbelt；
- Linux/WSL2 使用 bubblewrap 做文件隔离、socat 代理网络，可选 seccomp 增强 Unix socket 限制；
- native Windows 不支持该 Bash sandbox，应在 WSL2 使用；
- 默认工作目录和 session temp 可写；
- 文件系统与网络是独立层；
- sandboxed command 可自动批准，也可继续走常规权限；
- unsandboxed fallback 是显式 escape hatch，可被关闭；
- sandbox 不可用时可配置 hard fail。

来源：https://code.claude.com/docs/en/sandboxing

这些是外部合同。profile 编译、进程管理、代理实现的内部源码不可见。

## 蒸馏 enforcement 设计

kind: inference / design synthesis

具体 workspace identity、path normalization、process schema、profile compile、network/secrets 和 worktree 隔离统一见 [workspace-execution.md](workspace-execution.md)。

替代实现可用 Seatbelt、bubblewrap、容器或远程 microVM；只要 capability 和威胁模型透明，不要求复制 Claude 内部代码，也不能把软提示词标成 hard sandbox。

## Hooks 与安全

kind: official-doc + public-repo

PreToolUse、PermissionRequest 等 hooks 可作确定性组织策略，但 hook 本身是代码，也可能有副作用。hook 运行环境、timeout、exit code、输入输出 schema、失败模式和日志脱敏必须显式。项目 hook 不能覆盖 managed deny，也不能取得超过父进程的权限。

来源：

- https://code.claude.com/docs/en/hooks
- https://github.com/anthropics/claude-code/tree/main/examples/hooks

## Workspace trust、网络与 MCP

仓库中的 CLAUDE.md、skills、hooks 和 MCP 配置均属于潜在不可信输入。首次加载项目级可执行配置前需要 trust gate；MCP 工具按 server/tool 独立授权，远程内容视为 prompt-injection 来源。网络写操作和外部系统 mutation 不因“在 sandbox 内”自动安全。

## Checkpoint 与恢复

kind: official-doc

Checkpoint 在用户 prompt 前跟踪编辑工具产生的文件状态，可通过 rewind 恢复 conversation、code 或两者；其用途是可逆性，不是安全隔离。Shell、外部 API、数据库或 git push 等副作用不能靠文件 checkpoint 撤销。

来源：https://code.claude.com/docs/en/checkpointing

## 安全验收

- allow/ask/deny precedence 和 managed lock；
- path traversal、symlink、工作区外写、secret read；
- 默认网络拒绝、允许域、TLS proxy 故障；
- sandbox unavailable hard-fail；
- unsandboxed fallback 必须再次授权；
- 恶意 CLAUDE.md/skill/hook/MCP 不得提升权限；
- resume 不恢复 bypass grant；
- checkpoint 文档明确不能回滚外部副作用。

完整攻击 fixture、平台矩阵和 oracle 只在 [acceptance-tests.md](acceptance-tests.md) 维护，本节作为行为摘要。
