# Deep Agents Safety 与 Runtime 蒸馏

## 目录

- [事实：Permission、HITL、Sandbox 与容错](#事实permissionhitlsandbox-与容错)
- [设计综合：四个不同概念](#设计综合四个不同概念)
- [Durable tool call](#durable-tool-call)
- [Middleware 安全](#middleware-安全)
- [补充边界与四级升级](#补充边界与四级升级)
- [安全验收重点](#安全验收重点)

## 事实：Permission、HITL、Sandbox 与容错

Deep Agents 官方文档为 permissions、human-in-the-loop、sandboxes、interpreters、fault tolerance 和 production 分别提供页面：

- https://docs.langchain.com/oss/python/deepagents/permissions
- https://docs.langchain.com/oss/python/deepagents/human-in-the-loop
- https://docs.langchain.com/oss/python/deepagents/sandboxes
- https://docs.langchain.com/oss/python/deepagents/interpreters
- https://docs.langchain.com/oss/python/deepagents/fault-tolerance
- https://docs.langchain.com/oss/python/deepagents/going-to-production

底层 LangGraph 官方文档公开 persistence 与 interrupts：

- https://docs.langchain.com/oss/python/langgraph/persistence
- https://docs.langchain.com/oss/python/langgraph/interrupts

## 源码观察

Deep Agents 仓库公开 `THREAT_MODEL.md`，Python 包公开 `backends`、`middleware`、`profiles` 和 graph 组装代码：

- https://github.com/langchain-ai/deepagents/blob/d60560d695e8c436e11dee96965e7a1447409737/libs/deepagents/THREAT_MODEL.md
- https://github.com/langchain-ai/deepagents/tree/d60560d695e8c436e11dee96965e7a1447409737/libs/deepagents/deepagents

这证明项目显式考虑威胁模型与可插拔运行组件；具体承诺以锁定 commit 的 threat model 内容为准，不能把“支持 sandbox provider”泛化为所有 backend 都强隔离。

## 设计综合：四个不同概念

1. **Permission**：对规范化 action 返回 `allow/deny/ask/amend`。
2. **HITL interrupt**：把等待用户决定保存为可恢复 continuation。
3. **Backend**：文件、artifact 或执行资源的访问抽象。
4. **Sandbox**：强制文件、进程、网络、secret、quota 的 enforcement boundary。

四者可组合但不可互相替代。比如 permission allow 只授予动作意图，sandbox 仍应拒绝超出执行 spec 的系统调用或路径。

## Durable tool call

每个 tool/subagent 调用使用稳定 `call_id` 和幂等键：

```text
requested -> policy_decided -> waiting_approval? -> dispatched
          -> progress* -> committed | failed | cancelled | indeterminate
```

checkpoint 记录 pending node、state version、capability snapshot、approval request 与外部副作用状态。恢复时：纯计算可重放；可幂等副作用用同一 key 重试；无法判定的外部动作进入 `indeterminate` 并要求人工确认，不由模型猜测。

## Middleware 安全

middleware 必须声明生命周期点、是否可变换/阻断、所需 secrets/files、timeout 和 fail-open/fail-closed 策略。第三方 middleware 不继承 agent 全部权限；日志和 trace 默认脱敏。生产等级记录 middleware id/version/order 到 turn 配置快照。

## 安全验收重点

- 危险命令的 allow/deny/ask/amend、审批过期、参数篡改和无前端执行。
- symlink escape、子进程继承、网络重定向、秘密外传、资源耗尽。
- checkpoint 位于工具提交前、提交中、提交后时的恢复与去重。
- 父 agent 取消后，子 agent、model stream 和远程 sandbox 都收到取消；迟到结果不提交。
- sandbox provider 不可用或能力不满足 profile 时 fail closed。
- 恶意 tool/middleware 输出不会修改 policy、稳定系统指令或其他 agent 的 context。

## 补充边界与四级升级

FilesystemPermission 只有 read/write 与 allow/deny/interrupt，首条匹配生效，无匹配默认 allow。它只保护内置 filesystem tools，不保护 execute、custom tool 或 MCP；这些必须进入通用 policy 和 sandbox enforcement。

LocalShellBackend 使用宿主 shell，不是 sandbox；State/FilesystemBackend 的虚拟路径也不是进程、网络或 tenant 隔离。

| 等级 | 安全增量 | Oracle |
|---|---|---|
| `runnable` | schema、timeout、基本 deny | 无越界文件写 |
| `usable` | path permission、HITL、durable resume | approve/edit/reject/respond 正确 |
| `productive` | durable permission/replay、secret provenance | 重复副作用与泄密测试通过 |
| `polished` | 强 sandbox/network policy、tenant/managed profile、审计、SLO | 逃逸、红队、迁移、灾备通过 |

Memory/Skill/remote subagent output 都是可注入的不可信上下文，不能修改 immutable policy 或扩大 permission ceiling。
