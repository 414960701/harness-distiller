# MCP

## 职责与非目标

MCP client 将外部 server 的 tools、resources 和 prompts 接入 harness。
Server 是不可信、可迟到、可升级的能力提供方，不是本地 policy engine。
MCP 注解与描述只能帮助展示和风险提示，不能授予文件、网络、secret 或外发权限。
本页不定义 Skill 工作流或 plugin 安装；见 [Skills 与 Plugins](skills-plugins.md)。

## 连接与 catalog schema

```yaml
McpServer:
  id: string
  transport: stdio|streamable_http
  endpoint_or_command: string
  identity: package_digest|tls_origin
  auth_ref: secret_handle|null
  status: disabled|starting|ready|degraded|reauth|stopped
McpCapability:
  server_id: string
  kind: tool|resource|prompt
  name: string
  schema_digest: string
  annotations: object
  discovered_at: timestamp
```

client 接口至少包括 `discover`, `start`, `list_capabilities`, `call_tool`, `read_resource`, `get_prompt`, `stop`。
每次调用带 task/turn/step、deadline、cancel token、policy decision 和 correlation id。
catalog 使用 `(server_id, kind, name, schema_digest)` 定位，名称冲突不得静默覆盖。

## 生命周期与调用状态

Server 按 `disabled → starting → ready → degraded|reauth → stopped` 转移。
ToolCall 按 `proposed → policy_checked → running → succeeded|failed|cancelled|unknown` 转移。
发现与启动解耦；大 catalog 惰性分页，元数据预算独立于 prompt 预算。
schema 在 TaskRun 启动时快照；运行中变化产生 `schema_changed`，不按旧参数盲调。
stdio 子进程与 HTTP 连接均有 heartbeat、timeout、输出上限和可终止边界。

## 四级增量

### `runnable` 能跑

支持一个本地 stdio server、tools/list 与 tools/call、固定超时和手动配置。

### `usable` 能用

增加 streamable HTTP、resources/prompts、取消、分页、OAuth、重连和 schema validation。

### `productive` 顺手

增加惰性启动、catalog 搜索、按任务能力快照、健康面板、配额、结果 artifact 化。

### `polished` 好用

增加组织 allowlist、包签名/来源、细粒度 RBAC、供应链审计、隔离 worker 与兼容测试。

## 直接升级与回滚

先为旧 server 配置生成稳定 id 与 schema digest，再引入 capability snapshot 和 policy gate。
HTTP/OAuth 与市场安装最后开启；旧明文 token 迁入 secret broker 并轮换。
升级 server 时并存旧新版本跑 catalog/contract tests，成功后切 alias。
回滚恢复旧 server 版本与 schema snapshot，但不重复无 receipt 的外部写调用。

## 权限与安全

- server 进程使用最小 OS、filesystem 和 network 权限。
- OAuth token 按 server/origin/environment 隔离，模型只见 opaque handle。
- tool args 在本地 policy 决策后才发送；高风险外发需目标/数据/影响审批。
- tool result、resource 和 prompt 都标 untrusted data，不能提升指令优先级。
- annotations 不可信；`readOnlyHint` 仍需本地验证与审计。
- Hook/Skill/MCP 叠加时权限取交集，不取并集。

## 失败模式与恢复

断线可对纯读/声明幂等调用重试；外部写无 receipt 时进入 unknown。
OAuth 过期只阻塞该 server/Step，其他任务继续。
schema 变化拒绝旧调用并要求刷新 catalog。
畸形/超大返回截断到 blob，保留诊断而不污染 transcript。
server 崩溃不能拖垮 task store 或 UI；反复崩溃触发 circuit breaker。

## 验收 oracle

1. 两 server 同名 tool 均可显式寻址，不发生覆盖。
2. 运行中 schema 改变时旧参数不被执行。
3. 恶意 `readOnlyHint` 对写调用不降低风险。
4. server 请求 Working Folder 外文件时策略拒绝。
5. OAuth 过期转 reauth，secret 不出现在日志/模型/Hook。
6. 外发后断线恢复不重复提交无幂等保护的动作。

## 来源与设计综合

以 [Model Context Protocol specification](https://modelcontextprotocol.io/specification/) 与 [官方 SDK](https://github.com/modelcontextprotocol) 为协议来源。
具体产品的事件信封、审批 UI、worker 隔离和 receipt 格式由产品 dossier 定义，本页只维护互操作与信任边界。
