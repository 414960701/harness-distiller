# Tool Runtime

## 职责与非目标

Tool Runtime 管理 schema、发现、注册、路由、授权、执行、进度、取消、结果归一化和生命周期。
它把模型的工具意图变成受约束的 `ToolInvocation`，但不决定产品 UI、不实现 OS sandbox，也不直接改会话数据库。
ToolSpec 与 handler 分离；工具不能通过返回特殊文本绕过事件、policy 或 context engine。
runtime 不保证所有副作用 exactly-once，但必须识别幂等性和 unknown effect。

## 接口与状态

```text
ToolSpec {
  name, version, input_schema, output_schema?,
  side_effect: none|workspace|external,
  idempotency: safe|keyed|unsafe,
  concurrency: parallel|serial|exclusive,
  permissions[], timeout_default, provenance
}
ToolInvocation { call_id, spec_ref, args, context_ref, idempotency_key? }
ToolResult { call_id, status, output?, artifact_refs[], error?, effect_receipt? }
```

调用状态：`received -> validated -> authorizing -> running -> completed|failed|cancelled|unknown_effect`。
每个逻辑 call id 只能有一个终态 result；progress/delta 不算终态。
registry 按名称与版本唯一，冲突必须明确拒绝或命名空间隔离。

## 执行管线

1. 解析模型参数并限制深度/大小；
2. 解析稳定 spec version 并校验 schema；
3. 规范化路径、命令或远程目标；
4. policy 评估与 durable approval；
5. 选择 executor/sandbox 并记录 effect intent；
6. 执行、发送有界 progress、监听 cancel；
7. 持久化 effect receipt 与 canonical result；
8. 大输出进入 artifact，摘要返回模型。

动态发现只影响下一 model step 的 catalog，不能让一次请求中 schema 漂移。

## 四级增量

| 等级 | 新增能力 | 不变量 |
|---|---|---|
| 能跑 | 本地静态工具、串行、基础 result | spec/handler 分离、call id、单终态 |
| 能用 | schema 校验、MCP、取消、progress、artifact | policy 前置与结构化错误 |
| 顺手 | 并行/后台、惰性发现、缓存、动态工具 | catalog version 与因果链 |
| 好用 | 插件隔离、配额、远程工具、签名与供应链审计 | provenance、最小权限和 effect receipt |

并行只对声明安全且资源不冲突的工具开放，写工具默认串行。

## 直接升级与回滚

升级前为现有工具补 spec version、side effect 和 idempotency 注解。
引入 MCP/插件时先 shadow discovery，再让 catalog capability 显式启用。
直接升级好用按 registry → policy → isolation → remote executor → marketplace 顺序。
回滚插件版本时保留旧 spec reader，活动调用继续绑定启动时版本。
禁用新工具不会删除历史 result；恢复旧 session 时显示 unavailable 而非改名执行。

## 失败模式与安全

- schema 错误：不进入 policy/executor，返回可修复 validation detail；
- handler crash：隔离失败并关闭 call，不拖垮 loop；
- timeout/cancel：终止进程树或远程租约，迟到 result 只作诊断；
- effect 后崩溃：依据 receipt/idempotency key 对账，不盲目重跑；
- 恶意输出：标记不可信、限制大小、不得注入系统权限；
- 工具名投毒：来源、签名、命名空间和用户确认共同约束；
- secret 访问：按 spec 最小暴露，不把主进程环境全量继承；
- cache：仅缓存纯读且输入、workspace revision、权限都匹配的结果。

## 可执行验收

- 畸形参数与超大 JSON 在 executor 前被拒绝；
- 重复 call/idempotency key 只产生一次副作用；
- 两个只读工具可并行，两个写工具按资源锁串行；
- cancel 后进程树停止且恰有一个 cancelled result；
- 工具输出超过限制后生成 artifact，模型只收到摘要；
- MCP 断线不改变当前 catalog version，下一 step 才刷新；
- 插件签名失败、名称冲突和越权 secret 请求均 fail closed；
- handler 在副作用后 crash 时进入 confirmed 或 unknown_effect，不伪装 failed-safe。

## 证据与设计综合

`公开事实`：Codex、AgentScope、MCP SDK 和多种开源 harness 都分离工具 schema、router 与 handler。
`设计综合`：这里的状态与注解是跨产品统一合同，不复制某个工具协议的 wire schema。
本地执行细节见 [shell-process.md](shell-process.md)、[patch-edit.md](patch-edit.md)，权限见 [permission-policy.md](permission-policy.md)，MCP 见 [mcp.md](mcp.md)。
