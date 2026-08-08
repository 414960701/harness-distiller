# AgentScope-like 产品合同

## 目标行为

生成物应让用户配置一个 Agent，选择 model、tools、workspace、permission mode、middleware、RAG/LTM 和 plan 能力，然后以 SDK 或服务运行。相同 runtime 可被本地界面、Agent Team 和 Channel 消费，运行中能流式看到 message/event、审批、tool result、压缩与终态。

## 核心实体合同

| 实体 | 必需字段 | 行为不变量 | 证据 |
|---|---|---|---|
| `AgentDefinition` | id, name, model_ref, tool_refs, middleware_refs, configs | 配置版本固定到一次 run | code + inference |
| `Session` | id, agent_id, owner_id, state_version | 同 session 最多一个活跃 reply writer | app bus code |
| `Reply` | id, session_id, iteration, status, finished_reason | 只有一个终态 | event/state code |
| `Msg` | id, role, content_blocks, metadata | block 顺序稳定，tool call/result 可关联 | message code |
| `Event` | id, type, created_at, metadata, causal ids | append 后不可原地改语义 | event code + inference |
| `CapabilitySnapshot` | tools, mcps, skills, workspace, policy, hash | reply 内不可静默漂移 | inference |
| `WorkspaceLease` | id, backend, isolation, owner, expires_at | 执行只消费有效 lease | manager code + inference |

## 可观察行为

1. `run(session, input)` 产生 `REPLY_START`，随后是零到多个 model/block/tool/HITL event，最后恰有一个 `REPLY_END`。
2. 模型请求工具后，参数先完整组装与 schema 校验，再进入 permission engine；ASK 必须等待关联 confirm result。
3. 工具结果以 typed block 回到 context；若仍需推理，loop 继续，否则提交 assistant message。
4. 达到 `max_iters`、用户中断、错误和正常完成都有不同 `finished_reason`，不伪装成成功文本。
5. context 压缩保留摘要与覆盖范围；offload 保留 artifact ref、hash、scope 和缺失失败。
6. service 重连按 event cursor 补发；channel 只转换输入/输出，不改变 permission decision。
7. team worker 有独立 session、permission/context/workspace scope；共享资源必须显式声明。

## API 最小面

```text
create_agent(definition) -> agent_id
create_session(agent_id, owner_id, workspace_request) -> session_id
submit_input(session_id, message, idempotency_key) -> reply_id
stream_events(session_id, after_cursor) -> Event*
resolve_confirmation(request_id, choice, rules?) -> accepted
interrupt(session_id, reply_id, reason) -> accepted
get_snapshot(session_id) -> SessionSnapshot
resume(session_id, expected_version) -> reply_id | idle
```

字段名可等价改写，但 idempotency、cursor、expected_version 和 causal id 不得省略。

## 能力等级

| 等级 | 产品承诺 |
|---|---|
| `runnable` | 单 Agent、单 model、静态 tools、LocalWorkspace、基础事件、可中断 ReAct loop |
| `usable` | 压缩/offload、plan、完整 permission rules/HITL、MCP、持久 session/reply 恢复 |
| `productive` | middleware、RAG/LTM、skills、team、trace、workspace manager 与 channel adapter |
| `polished` | 经验证的 sandbox backend、分布式互斥/恢复、兼容协议、配额、SLO 与安全回归 |

等级是同一对象模型的增量优化；从 runnable 直升 polished 通过 migration 和 capability 开关完成，不允许平行重写 runtime。

## 质量与 SLO

- 单进程 runnable：scripted model 测试中每次 reply 都有单终态，取消延迟小于测试 timeout。
- usable：进程在任一 event append 后崩溃，恢复不得重复已提交 tool side effect。
- productive：两个 worker 并发时 session/event/context 不串流，渠道断线后 cursor 补发无重复展示。
- polished：为 model、tool、bus、storage、workspace 分别定义 timeout/error budget；所有跨服务请求可用 trace id 定位。

数值应由生成项目根据部署目标写入 ADR；本 dossier 不冒充官方线上 SLO。

## 安全合同

- Permission 是 policy decision；Workspace 是资源/执行抽象；Sandbox 是可选 enforcement。三者必须分别显示状态。
- `BYPASS` 只表示跳过部分 permission prompt，不表示执行安全。
- LocalWorkspace 默认继承宿主进程权限，只能标 `host-process`。
- 远端 MCP tool 也必须经过本地 schema、identity、policy、timeout 与审计。
- credential 不进入 model-visible context、event payload 或 channel 文本。

## 非目标

- 不复刻 AgentScope 商标、视觉、提示词和云端私有服务。
- 不保证所有模型 provider 的 tool/thinking/structured output 完全等价。
- 不用目录名称推断生产可靠性，不把 Redis、Docker 或 Kubernetes 的存在当成安全证明。
- 不把 RAG 与长期记忆合并成一张无 provenance 的向量表。
- 不承诺任意 channel 支持完整富交互；能力必须经 capability negotiation。

## 证据与验收

公开事实来源见 [sources.md](sources.md)，设计实现见后续专题。最终行为只由 [acceptance-tests.md](acceptance-tests.md) 的 oracle 验证；README 声称、类型检查通过或单次 demo 成功均不能替代黑盒、恢复和安全测试。
