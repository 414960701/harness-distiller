# AgentScope-like 分级验收测试

## 测试夹具

实现仓库必须提供 `ScriptedModel`、`FakeTool`、`FakeWorkspaceBackend`、`FakeMCPServer`、`InMemoryBus`、临时持久库与 controllable clock。每个测试捕获 command、event、snapshot、tool execution receipt、filesystem diff 和 trace。测试通过才把 capability 标记 `verified`。

## 通用 oracle

- 每个 reply 恰有一个 `REPLY_START` 与一个 `REPLY_END`，终态不可逆。
- event cursor 单调，snapshot + after_cursor 重建结果与在线投影一致。
- 相同 command idempotency key 不产生第二个 reply；相同 tool call 不产生第二次副作用。
- permission decision、workspace/backend 与 sandbox enforcement 分别记录，不能用其中一个代替另一个。
- 所有错误有 category/retryable/trace id，公开 payload 无 secret。

## runnable（能跑）

1. `agent.react`：scripted model 输出 Read call 后输出 final；断言 reasoning→policy→acting→result→final 顺序，max_iters 时停止。
2. `model.wrapper`：对 text/tool/usage/finish reason 做 provider-neutral 转换；模拟 429 后只按策略重试，取消能终止 stream。
3. `tools.toolkit`：注册、分组、schema 校验、未知工具和 malformed args；只有完整合法 call 能到 executor。
4. `context.manager`：system、history、tool schema、当前输入顺序固定；超预算返回显式 context error，不静默丢消息。
5. 单 LocalWorkspace 标为 `host-process`；越界 root 被 policy/backend 拒绝，但不得声称 OS sandbox。
6. 在 model stream 与 tool 执行中 interrupt；断言单 `interrupted` 终态、无孤儿后台任务。

## usable（能用）

1. `permission.rules`：逐表测试 DEFAULT/ACCEPT_EDITS/EXPLORE/BYPASS/DONT_ASK，deny/ask/allow 顺序、tool check passthrough、args hash 和确认过期；BYPASS 仍显示无 sandbox。
2. `planning.notebook`：create/list/update task，状态仅 pending→in_progress→completed；崩溃恢复 revision 不倒退，用户修改产生 event。
3. `mcp.gateway`：发现 tool、固定 schema snapshot、调用/timeout/断连；server 漂移不改变当前 reply，远端 tool 仍经过 permission。
4. context 压缩覆盖早期 items 后，模型仍能根据 fixture 中的早期约束完成答案；summary 带 covered ids/hash。
5. 大 tool result offload 后 ref 可读且 hash 一致；删除、过期、越权分别结构化失败。
6. 等待 confirmation 时 kill/restart，恢复同 request id；重复 resolve 只提交一次。

## productive（顺手）

1. `middleware.chain`：记录所有 hook 顺序；观测 hook fail-open、安全 hook fail-closed；修改内容带 provenance，timeout 不悬挂 lease。
2. `workspace.resources`：tool/MCP/skill/artifact 进入 capability snapshot；启停 skill 只影响下一 reply；恶意 archive、symlink 和超大文件被拒绝。
3. `rag.pipeline`：ingest→chunk→embed→retrieve fixture 的 citation 可回源；tenant/project filter 生效，删除 source 后不再召回。
4. `memory.long-term`：写入、检索、纠错、删除、expiry；用户 A/session scope 的记忆不能泄漏给用户 B，删除同步清理派生索引。
5. `teams.messaging`：leader 创建两个独立 worker session，消息含 source event id；并发运行不串 context/permission/workspace，重复投递幂等。
6. `service.deployment`：通过 HTTP/stream 提交、订阅、interrupt、resolve；重连 cursor 补发，API 与 SDK snapshot 相同。
7. trace 串起 command→reply→model→permission→tool→event；token、latency、error 指标可按 session/agent 汇总。

## polished（好用）

1. `channels.production`：provider 重复 webhook、乱序、429、断线重连和消息长度上限；无重复 reply/side effect，降级内容保留 request id 与终态。
2. `runtime.distributed-state`：两个 worker 抢同 session，fencing 只允许一个 writer；Redis/bus 断线、TTL 过期、旧 worker 复活都不能双写。
3. 已选择的 sandbox backend 运行 `..`、symlink、process escape、network redirect、secret inheritance、resource exhaustion 测试；失败时不回退 LocalWorkspace。
4. Workspace Manager 重启/reconnect、lease 过期、容器丢失和 unknown effect；只在可证明安全时自动恢复。
5. N-1 schema/event fixture 升级后可读；新客户端降级到旧 protocol 不发送未知关键安全事件。
6. 故障注入覆盖 tool 成功/result commit 前崩溃、event commit/outbox 前后崩溃、artifact pending 与 channel delivery；oracle 为无重复副作用或明确 `effect_unknown`。

## Blueprint capability 闭环

| capability id | 最低等级 | 可执行 oracle |
|---|---|---|
| `agent.react` | runnable | scripted ReAct fixture 的状态、iteration、单终态与取消测试 |
| `model.wrapper` | runnable | 两个 fake provider 的 block/usage/error contract suite |
| `tools.toolkit` | runnable | registry/group/schema/unknown-tool property tests |
| `context.manager` | runnable | deterministic assembly golden + budget/压缩 fixture |
| `permission.rules` | usable | 五 mode × rule precedence × tool-check 决策矩阵 |
| `middleware.chain` | productive | hook 顺序、mutation provenance、fail policy、timeout suite |
| `workspace.resources` | productive | snapshot diff、skill staging、artifact scope/hash tests |
| `planning.notebook` | usable | task transition/revision/recovery tests |
| `rag.pipeline` | productive | citation、scope、delete/reindex retrieval fixture |
| `memory.long-term` | productive | add/search/correct/delete/expiry/tenant isolation fixture |
| `teams.messaging` | productive | multi-session concurrency、dedupe、权限/上下文隔离 test |
| `mcp.gateway` | usable | discovery/schema pin/call/timeout/drift/policy tests |
| `service.deployment` | productive | API-stream parity、cursor reconnect、restart recovery tests |
| `channels.production` | polished | duplicate/out-of-order/rate-limit/reconnect delivery suite |
| `runtime.distributed-state` | polished | dual-worker fencing、bus partition、lease-expiry chaos suite |

本表使用 `scripts/new_blueprint.py` 的 canonical 短 id；若生成物内部加 `agentscope.` 命名空间，必须一一映射，不能以一个“AgentScope 集成测试”笼统覆盖十五项。

## 安全专项 oracle

- Permission ALLOW + host-process backend：结果只能标 policy allowed，不得标 sandboxed。
- EXPLORE 对 write/edit/destructive shell 一律 deny；read-only 识别误判加入回归 fixture。
- 批准后修改 path/command/env 必须产生新 decision。
- MCP/skill/channel 提供的文本不能提升为 system 指令。
- secret 出现在 event、trace、artifact summary 或 channel payload 即测试失败。

## 出厂门禁

运行顺序：schema/golden→unit/state machine→integration→crash/recovery→security→channel/chaos。高等级必须回归全部低等级。任何 flaky safety/recovery test 视为失败；deferred capability 保持 `planned`，不得在 README、蓝图或 UI 标记 verified。
