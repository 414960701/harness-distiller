# Deep Agents 实现验收与 Capability Oracle

## 目录

- [判定规则](#判定规则)
- [测试夹具](#测试夹具)
- [runnable](#runnable)
- [usable](#usable)
- [productive](#productive)
- [polished](#polished)
- [通用失败与安全](#通用失败与安全)
- [证据产物](#证据产物)
- [发布门禁](#发布门禁)

## 判定规则

本页逐项覆盖 `scripts/new_blueprint.py` 的 Deep Agents overlay capability ID。

`verified` 必须同时满足：

1. capability 有生产实现路径；
2. 下列命令或同等测试可执行；
3. oracle 由结构化状态、事件、digest 或外部 receipt 判定；
4. 失败分支与安全边界也通过；
5. 测试报告记录 build commit、配置、seed 和 artifact。

只展示 UI、只完成 happy path 或只链接官方文档，状态最多是 `implemented-not-verified`。

等级是累积的：`polished` 必须回归 runnable、usable、productive 的所有测试。

## 测试夹具

准备以下可复现 fixture：

- `repo-small`：10 个文本文件、1 个 binary、1 个 symlink、1 个测试命令；
- `repo-large`：可触发 tool result offload 与 context summary；
- `backend-state`、`backend-filesystem`、`backend-store`、`backend-composite`；
- `sandbox-deny-network`：无 host secret、无宿主写权限；
- `fake-model`：脚本化 tool call、失败、重试、最终消息；
- `fake-subagent-server`：Agent Protocol start/check/update/cancel；
- `fake-rag`：固定 corpus、相关性与 citation truth set；
- `killpoint-runner`：在 dispatch/commit/checkpoint/interrupt 处终止；
- `event-projector`：从 snapshot + sequence 重建状态；
- `tenant-a/tenant-b`：相同 logical path 和 thread name。

建议统一命令：

```bash
pytest -q tests/deep_agents_contract --junitxml=artifacts/deep-agents.xml
python3 scripts/assert_event_replay.py artifacts/events.jsonl
python3 scripts/assert_capabilities.py artifacts/capabilities.json
```

具体路径可替换，但输出必须机器可判定。

## runnable

### `middleware.harness-stack`

等级：`runnable`。

执行：构建 agent，导出冻结 middleware descriptor；注入同名 custom middleware 和无效 exclusion。

Oracle：

- 核心顺序为 Skills?、Filesystem、SubAgent?、Summarization、PatchToolCalls、Async?；
- user middleware 位于 core 与 tail 之间；
- 同名项原位替换，不产生重复 hook；
- protected filesystem/subagent middleware 无法被 exclusion 移除；
- turn snapshot 包含 middleware id/version/order；
- hook 异常产生结构化 runtime failure。

命令示例：`pytest -q tests/deep_agents_contract/test_middleware_stack.py`。

### `planning.todo`

等级：`runnable`。

执行：分别构建默认 agent 与显式 `TodoListMiddleware` agent；让 fake model 更新、完成并并发双写 todo。

Oracle：

- 0.7.5-compatible 默认 agent 没有 `write_todos`；
- opt-in 后 tool 与 todos state 出现；
- todo 可按 revision 更新并在 event replay 后一致；
- 同一 model response 的并行双写被拒绝或确定串行；
- final 前所有 todo 为 completed/cancelled 或带阻塞原因；
- Todo 不保存 chain-of-thought。

命令示例：`pytest -q tests/deep_agents_contract/test_todo.py`。

### `filesystem.backend`

等级：`runnable`。

执行：对 StateBackend fixture 运行 ls/read/write/edit/glob/grep；切换到无 execute backend。

Oracle：

- 所有 path 是虚拟 POSIX path；
- read pagination、literal grep、glob 和 edit occurrence 正确；
- 不支持的 execute/delete 不暴露；
- 大结果有 truncated/artifact 标记；
- 错误是结构化 ToolMessage，不以异常文本冒充成功；
- 同一输入的 sync/async 结果语义一致。

命令示例：`pytest -q tests/deep_agents_contract/test_backend.py`。

## usable

### `subagents.isolated`

等级：`usable`。

执行：父 state 放入 messages、todos、structured_response、private field 和普通共享 field，再调用同步 subagent。

Oracle：

- 子 messages 仅含 delegation HumanMessage；
- todos/structured_response/private 不进入子 state；
- 允许的共享 field 可读且按 reducer 合并；
- 父只收到 structured response 或最后非空 AIMessage；
- 未知 subagent_type 不运行任何 graph；
- 父取消向子传播，迟到结果不提交。

命令示例：`pytest -q tests/deep_agents_contract/test_subagent_isolation.py`。

### `permissions.hitl`

等级：`usable`。

执行：创建 allow/deny/interrupt 重叠规则，覆盖 exact、bulk、absolute glob、recursive delete 和 amend。

Oracle：

- 首条匹配生效，无匹配默认 allow；
- denied 文件不在 list/search 结果泄漏；
- interrupt 前 checkpoint durable；
- approve/edit/reject/respond 产生稳定终态；
- amend 后重新做 path policy；
- 无 checkpointer 时配置失败；
- 报告明确 custom/MCP/execute 不在此 capability 覆盖面。

命令示例：`pytest -q tests/deep_agents_contract/test_permissions_hitl.py`。

### `skills.loading`

等级：`usable`。

执行：两个 skill source 含同名 skill、非法 frontmatter、超大文件和恶意指令。

Oracle：

- 后 source 按固定优先级覆盖前 source；
- 元数据与 body 分阶段加载；
- YAML 使用安全解析，无代码执行；
- size/name/description limit 有确定错误或告警；
- skill provenance/version 进入 context trace；
- skill 内容不能提升 tool、permission 或 secret scope。

命令示例：`pytest -q tests/deep_agents_contract/test_skills.py`。

### `memory.cross-session`

等级：`usable`。

执行：使用 StoreBackend namespace 在 thread A 写 memory，thread B 按相同主体读取，tenant B 尝试越权读取。

Oracle：

- 指定 AGENTS.md 在启动时按 source 顺序加载；
- 同 namespace 的跨 thread 内容可见；
- 不同主体/tenant 隔离；
- mutation 有 provenance、actor 和可撤销历史；
- secret 不进入 prompt/trace；
- StateBackend 单独使用时不虚假承诺跨 session。

命令示例：`pytest -q tests/deep_agents_contract/test_memory.py`。

## productive

### `rag.pipeline`

等级：`productive`。

此 capability 是复刻差量，不是 `deepagents==0.7.5` 核心包的内置向量索引。

执行：通过 custom tool/MCP/middleware 接入 fake-rag corpus，测试 retrieve、rerank、引用、陈旧和 prompt injection。

Oracle：

- query、filters、top_k、index version 进入 trace；
- top-k 对 truth set 达到配置阈值；
- 每个事实引用可解析到 source chunk/digest；
- RAG 与 AGENTS.md memory、skills、filesystem grep 分层显示；
- 无结果/陈旧结果确定降级，不伪造引用；
- 检索文本作为不可信数据，不能改写 policy。

命令示例：`pytest -q tests/deep_agents_contract/test_rag.py`。

### `fault-tolerance.replay`

等级：`productive`。

执行：killpoint runner 覆盖 model stream、tool dispatch、external commit、receipt、checkpoint、interrupt、summary、async start。

Oracle：

- 恢复结果与无故障基线 digest 一致；
- committed 副作用仅一次；
- approval request ID 不变；
- unknown external commit 进入 indeterminate；
- message reducer replay 确定；
- outbox 至少一次传输、projection 去重；
- 旧 capability snapshot 被恢复。

命令示例：`pytest -q tests/deep_agents_contract/test_recovery.py`。

### `frontend.streaming`

等级：`productive`。

执行：从 LangGraph messages/updates/tasks/custom stream 归一化事件，模拟断线、重复、乱序和 sequence gap。

Oracle：

- message、tool、todo、approval、subagent、artifact 分别投影；
- snapshot + events 与 live state hash 一致；
- 重复 event 幂等，缺口触发补拉；
- sync child lineage 与 async remote task 可区分；
- 取消在 UI 与 runtime 都到终态；
- frontend 不依赖 Python TypedDict/private state；
- ACP 与 Web projection 的核心终态一致。

命令示例：`pytest -q tests/deep_agents_contract/test_stream_projection.py`。

## polished

### `backend.sandbox`

等级：`polished`。

执行：在 sandbox 运行 shell、进程树、网络、symlink、env secret、timeout 和 output flood 测试。

Oracle：

- host root/secret 不可见；
- network deny 同时阻止 DNS、IP 和 redirect；
- timeout/cancel 清理进程树；
- CPU/memory/output quota 生效；
- nonzero exit_code 机器可读；
- provider 不可用时 fail closed，不回退 LocalShell；
- execute 使用独立 policy，而非 filesystem permissions。

命令示例：`pytest -q tests/deep_agents_contract/test_sandbox.py`。

### `backend.remote`

等级：`polished`。

执行：remote backend 注入延迟、断连、过期 credential、并发 lease、provider migration。

Oracle：

- logical URI 在 provider 切换后不变；
- write 使用 version/etag 防止 lost update；
- retry 仅针对幂等操作或带 receipt 动作；
- credential 不出现在 model/trace；
- cancellation 释放 remote lease；
- provider 不确定提交进入 reconcile/indeterminate；
- local fallback 只能显式配置且不降低安全 profile。

命令示例：`pytest -q tests/deep_agents_contract/test_remote_backend.py`。

### `service.production`

等级：`polished`。

执行：多实例 service 运行 tenant、auth、quota、rolling upgrade、backup restore、retention 和 SLO load test。

Oracle：

- 相同 thread 同时只有一个有效 writer lease；
- authz 绑定 tenant/thread/workspace；
- rate/token/tool/storage quota 全部强制；
- N-1 client 与 N server 可协商；
- rolling upgrade 不丢 turn/approval/event；
- backup restore 的 state/artifact/event digest 一致；
- p95 latency、error rate、recovery time 达到声明 SLO。

命令示例：`pytest -q tests/deep_agents_contract/test_production_service.py`。

### `profiles.managed-permissions`

等级：`polished`。

执行：组织 profile 定义 model/tool/middleware/backend/policy ceiling；项目与用户尝试覆盖。

Oracle：

- profile 有 id/version/signature 和审计来源；
- lower scope 只能收紧，不能扩大 permission ceiling；
- protected middleware 与 policy enforcement 不可排除；
- profile 更新只影响新 turn，旧 turn 使用快照；
- rollback 恢复旧 profile 且不改写历史事件；
- 未签名/过期 profile fail closed；
- managed control plane 不可用时执行明确离线策略。

命令示例：`pytest -q tests/deep_agents_contract/test_managed_profiles.py`。

## 通用失败与安全

- 模型无限 tool loop 达到预算并终止为 `budget_exhausted`。
- cancellation 覆盖 model、tool、sync child、remote task 和 process tree。
- memory、skill、RAG、tool output 的注入无法更改 immutable policy。
- path traversal、symlink、absolute glob、recursive delete 均 fail closed。
- approval 参数 hash 不匹配时不执行。
- remote response、tool result 和 media 不兼容时确定降级。
- logs/events/artifacts 不包含 API key、authorization header 或完整 secret。
- tenant A 无法通过 thread ID、artifact URI、store namespace 访问 tenant B。

## 证据产物

每次验收输出：

```json
{
  "capability_id": "fault-tolerance.replay",
  "level": "productive",
  "status": "verified",
  "build_commit": "...",
  "test_command": "pytest ...",
  "report_uri": "artifact://reports/...",
  "trace_uri": "artifact://traces/...",
  "fixture_digest": "sha256:...",
  "verified_at": "..."
}
```

Capability 清单必须恰好包含 14 项 overlay ID；缺项、拼写差异或只有人工备注都使发布失败。

## 发布门禁

1. `runnable`：3/3 capability verified。
2. `usable`：累计 7/7 verified。
3. `productive`：累计 11/11 verified。
4. `polished`：累计 14/14 verified。
5. 所有低等级回归为绿色。
6. 0 个未解释的 `indeterminate` 副作用。
7. 0 个 secret/tenant escape/sandbox escape 高危失败。
8. schema migration 与 rollback 演练通过。
9. 文档固定 commit、产品版本与测试构建版本一致。
10. 伴生服务能力在 manifest 中标记为 external dependency，而非 OSS core。
