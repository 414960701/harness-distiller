# AgentScope Safety 与 Runtime 蒸馏

## 事实：Permission、HITL 与 Workspace

AgentScope 2.0.6dev 为 Permission System 提供 overview、permission mode、permission rule 和 tool check 页面；Agent 另有 human-in-the-loop 与 interrupt 文档：

- https://docs.agentscope.io/versions/2.0.6dev/en/building-blocks/permission-system/overview
- https://docs.agentscope.io/versions/2.0.6dev/en/building-blocks/permission-system/permission-mode
- https://docs.agentscope.io/versions/2.0.6dev/en/building-blocks/permission-system/permission-rule
- https://docs.agentscope.io/versions/2.0.6dev/en/building-blocks/permission-system/tool-check
- https://docs.agentscope.io/versions/2.0.6dev/en/building-blocks/agent/human-in-the-loop
- https://docs.agentscope.io/versions/2.0.6dev/en/building-blocks/agent/interrupt-agent

Workspace 文档区分 overview、manage resources、MCP Gateway 和 run workspace，并有 Workspace Manager 部署页面：

- https://docs.agentscope.io/versions/2.0.6dev/en/building-blocks/workspace/overview
- https://docs.agentscope.io/versions/2.0.6dev/en/building-blocks/workspace/manage-resources
- https://docs.agentscope.io/versions/2.0.6dev/en/building-blocks/workspace/mcp-gateway
- https://docs.agentscope.io/versions/2.0.6dev/en/building-blocks/workspace/run-workspace
- https://docs.agentscope.io/versions/2.0.6dev/en/deploy/workspace-manager

## 源码观察

公开源码将 `permission`、`workspace`、`credential`、`tool`、`mcp`、`state` 与 `exception` 分包：https://github.com/agentscope-ai/agentscope/tree/29b592358c2e983a0d10dd5227316b7a02d8c23a/src/agentscope 。这支持把授权、资源、秘密、调用和错误分别建模；尚不能仅凭目录确认 OS syscall、容器、网络或多租户隔离强度。

## 设计综合：两道安全边界

### 1. Policy Decision Point

把 permission mode 和 rule 编译为共享 `PolicyDecision`：

```text
decision = evaluate(identity, capability, normalized_args,
                    workspace_snapshot, network_target, risk, prior_grant)
```

决策只能为 `allow | deny | ask | amend`，带 reason、scope、expiry、rule id 和 audit id。规则优先级固定为显式 deny 高于 ask，高于 allow；批准绑定规范化参数，不允许工具在批准后替换路径或命令。

### 固定源码决策顺序

以下顺序来自固定 commit 的 [`PermissionEngine`](https://github.com/agentscope-ai/agentscope/blob/29b592358c2e983a0d10dd5227316b7a02d8c23a/src/agentscope/permission/_engine.py)，生成实现不得只写成模糊的 `deny > ask > allow`：

| Mode | 有序决策链 | 最终 fallback |
|---|---|---|
| `DEFAULT` | deny rule → ask rule → read-only fast path → tool `ALLOW/DENY` 或 bypass-immune safety `ASK` → allow rule | `ASK` |
| `ACCEPT_EDITS` | deny rule → ask rule → read-only fast path → tool decision；工作目录内 edit 可由 tool 返回 `ALLOW`，safety `ASK` 不可被 allow rule 覆盖 → allow rule | `ASK` |
| `EXPLORE` | deny rule → ask rule → read-only fast path | 非只读一律 `DENY`；不调用 tool check，也不读 allow rule |
| `BYPASS` | deny rule → ask rule → read-only fast path → tool `ALLOW/DENY`；tool 的普通或 safety `ASK` 均跳过 → allow rule | `ALLOW` |
| `DONT_ASK` | deny rule → ask rule 转 `DENY` → read-only fast path → tool `ALLOW/DENY`，tool safety `ASK` 转 `DENY` → allow rule | `DENY`，永不返回 `ASK` |

Rule match 也必须保持工具语义：Bash 使用命令 pattern，Read/Write/Edit 使用 path glob，其它工具委托 typed matcher。匹配前先规范化命令与路径；approval、规则建议和审计都绑定同一 canonical args hash。

最低决策矩阵至少覆盖：只读调用、工作目录内 edit、目录外 edit、普通命令、危险命令、显式 deny/ask/allow rule、tool `ALLOW/DENY/PASSTHROUGH/ASK`、`bypass_immune` 和无用户场景。测试期望直接来自上表，不能由被测实现自行生成。

### 2. Policy Enforcement Point

Workspace runner 或 executor 消费已批准的 execution spec，并强制 roots、symlink resolution、process/network limits、secret injection 和 resource quota。Permission 的 `allow` 不等于 executor 有能力完成；sandbox 不可用时按安全 profile fail closed。

## Interrupt 与 HITL 状态机

人工输入与审批不是普通工具返回。它们应形成 `waiting_for_input` / `waiting_for_approval` 持久状态，保存 request id、展示参数、有效期和恢复 continuation。中断必须传播 cancellation token，迟到的 model/tool 结果只能记录为 ignored，不得提交副作用。

## 服务化运行

官方提供 Agent Service、Agent Team、渠道和 Workspace Manager 文档：

- https://docs.agentscope.io/versions/2.0.6dev/en/deploy/agent-service
- https://docs.agentscope.io/versions/2.0.6dev/en/deploy/agent-team
- https://docs.agentscope.io/versions/2.0.6dev/en/deploy/channel/overview
- https://docs.agentscope.io/versions/2.0.6dev/en/deploy/channel/routing

蒸馏时把 agent runtime、workspace executor 和 channel adapter 作为不同身份。渠道只能发送版本化 command、订阅脱敏 event；Workspace Manager 不接收模型原始自由文本，只接收规范化 execution spec。

## 安全验收重点

- permission rule 冲突、批准过期、批准后参数变化和无 UI 场景。
- `..`、symlink、嵌套仓库、临时目录、子进程继承与网络重定向。
- MCP Gateway 断连、工具列表变化、凭证轮换与恶意远端工具。
- 中断发生在 model stream、审批等待、工具执行和 artifact 上传的每个阶段。
- 服务重启后等待中的审批可恢复，且不会重复执行已产生外部副作用的 tool call。

## 实现级补充

- 固定源码 mode 为 DEFAULT、ACCEPT_EDITS、EXPLORE、BYPASS、DONT_ASK；每个 mode 都需决策矩阵测试。
- Approval 绑定 actor、request/session/reply/call、规范化参数 hash 与 expiry；无用户时 ASK 不得默认 ALLOW。
- enforcement profile 明示 host-process、fs-restricted、container 或 remote-sandbox，并附已验证测试。
- Credential 只以 secret reference 进入 backend，不得出现在 model context、event、trace 或 channel。
