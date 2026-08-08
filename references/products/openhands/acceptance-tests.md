# OpenHands 实现验收与 Capability Oracle

## 目录

- [判定规则](#判定规则)
- [统一夹具](#统一夹具)
- [runnable](#runnable)
- [usable](#usable)
- [productive](#productive)
- [polished](#polished)
- [跨能力失败注入](#跨能力失败注入)
- [证据产物](#证据产物)
- [发布门禁](#发布门禁)

## 判定规则

本页逐项覆盖 [recipe.md](recipe.md) 的 15 个 canonical capability ID。

`verified` 必须同时满足：生产实现路径存在；下列命令或等价测试可执行；oracle 由 schema、event、digest、receipt 或外部状态判定；失败/安全分支通过；报告记录 build commit、配置、seed 和 artifact。

只展示 UI、只跑 happy path、只链接官方文档或人工称“看起来像”最多标 `implemented-not-verified`。

等级累积：polished 回归 runnable、usable、productive 全部测试。

## 统一夹具

- `scripted-model`：文本、并行 tool、Finish、malformed、429、context overflow；
- `repo-small`：文本、binary、symlink、dirty git、固定测试；
- `repo-large`：触发 output offload 和 condenser；
- `fake-workspace`：可记录 dispatch、receipt、cancel 和 resource key；
- `docker-hostile`：escape、network、secret、fork bomb、output flood；
- `fake-browser`：两 tab、stable element refs、download、stale element；
- `fake-mcp/plugin/skill`：冲突名称、恶意内容、断连；
- `event-projector`：从 snapshot+events 构建 Canvas state；
- `killpoint-runner`：append、receipt、lease、publish、confirmation；
- `tenant-a/tenant-b`：相同 conversation/workspace 名称。

建议命令：

```bash
pytest -q tests/openhands_contract --junitxml=artifacts/openhands.xml
npm test -- --run tests/canvas-contract
python3 scripts/assert_event_projection.py artifacts/events.jsonl
python3 scripts/assert_capabilities.py artifacts/capabilities.json
```

## runnable

### `conversation.event-tree`

等级：`runnable`。

执行：创建 root→A→B；navigate 到 A 后追加 C；切换 B/C；用 legacy parent-null fixture 恢复；刻意制造 duplicate、missing parent 和 cycle。

Oracle：event id 唯一；B/C 是 sibling；active branch 分别为 root-A-B/root-A-C；navigate 不删除事件；deliberate empty head 可恢复；legacy 线性映射正确；损坏图拒绝运行；重放 projection digest 一致。

命令：`pytest -q tests/openhands_contract/test_event_tree.py`。

### `tools.action-observation`

等级：`runnable`。

执行：scripted model 发 terminal、file edit、未知 tool、非法 args、Finish 后附多余 action，并注入 executor exception。

Oracle：每个 ActionEvent 恰有一个 Observation/UserReject/AgentError；tool_call_id 配对；schema 错误不执行；异常不是 success；Finish 后 action 不执行；孤儿在中断恢复时补 typed error；View property validator 全通过。

命令：`pytest -q tests/openhands_contract/test_action_observation.py`。

### `agent.parallel-actions`

等级：`runnable`。

执行：同 response 生成两个只读 action、两个冲突写 action、terminal session action、慢 action 和 cancel。

Oracle：只读可并行；冲突资源确定串行或拒绝；append 结果按原 action 顺序；每个 span/tool id 独立；cancel 后未开始项不派发；迟到结果不覆盖终态；Finish 截断；100 次 seed 的 event digest 稳定。

命令：`pytest -q tests/openhands_contract/test_parallel_actions.py`。

### `workspace.adapter`

等级：`runnable`。

执行：对 FakeWorkspace 和 LocalWorkspace 跑 execute/upload/download/git/pause/resume/close conformance，覆盖 nonzero、timeout、cancel、binary、cwd 和缺能力。

Oracle：结果 typed；exit code/stdout/stderr/timeout 保留；identity 稳定；unsupported 不回退；close 幂等；Local 标 local-host 且 pause/resume no-op；workspace 外路径拒绝；失败闭合 action。

命令：`pytest -q tests/openhands_contract/test_workspace_adapter.py`。

## usable

### `context.condenser`

等级：`usable`。

执行：构造长 branch，边界落在多 action batch、action/result、tool loop 和旧 condensation 内；运行摘要并重启恢复。

Oracle：边界移动到原子边界；摘要记录 covered ids/digest；目标、决策、文件、失败和 pending 保留；原事件未删除；secret 不出现；恢复不再次调用摘要模型；重建 View digest 与在线一致。

命令：`pytest -q tests/openhands_contract/test_condenser.py`。

### `security.confirmation`

等级：`usable`。

执行：Never/Always/Risky 策略覆盖 low/high risk、analyzer failure、approve、reject、duplicate、expiry、参数 TOCTOU 和 hook block。

Oracle：分析绑定 action digest；等待前无副作用；request durable；重复决议幂等；reject 生成模型可见 Observation；参数改变重新确认；hook block 不能批准；approval 不提升 enforcement；safe profile analyzer failure 为 deny/confirm。

命令：`pytest -q tests/openhands_contract/test_confirmation.py`。

### `server.remote-conversation`

等级：`usable`。

执行：通过 REST 创建/发消息/run/pause/history/confirmation；WebSocket 订阅后断线、重复、乱序、慢消费者和重连；进程重启 resume。

Oracle：OpenAPI schema 稳定；mutation 幂等；history cursor 无漏重；snapshot last_offset 正确；reconnect 从 offset 补拉；慢消费者触发 resync 不阻塞 loop；认证覆盖 REST/WS；重启恢复同终态。

命令：`pytest -q tests/openhands_contract/test_agent_server.py`。

### `surface.agent-canvas`

等级：`usable`。

执行：event-projector 输入 message、action/observation、delta、status、confirmation、terminal、diff、unknown event，模拟 conversation 切换和 reconnect。

Oracle：chat/tool group/status/terminal/files-diff 正确；delta 被 completed 替换；event id 去重；不同 conversation 不串流；pending confirmation 可操作；unknown generic card；local-host 标签可见；snapshot+events 与 live UI state hash 一致。

命令：`npm test -- --run tests/canvas-contract/agent-canvas.test.tsx`。

## productive

### `runtime.container`

等级：`productive`。

执行：provision、health、execute、pause/resume、crash、cleanup；限制 CPU/memory/pid/output；测试 host mount、root、docker socket 与 network profile。

Oracle：image digest/runtime id 可追踪；非 root；workspace mount 符合配置；资源限制生效；cleanup 幂等；runtime crash typed；不安全 flags 被拒绝；provider 失败不回退 Local；基础隔离测试通过。

命令：`pytest -q tests/openhands_contract/test_container_runtime.py`。

### `browser.interaction`

等级：`productive`。

执行：navigate/get-state/click/type/scroll/tab/screenshot/download，覆盖 stale ref、跨域 policy、认证字段、cancel 和 runtime replacement。

Oracle：element ref 来自最近 observation；stale 不猜坐标；tab id 隔离；screenshot/content 为 artifact 并带 digest；secret input 不进事件；deny domain 无网络；cancel 清理；runtime generation 变化后旧 handle 失效。

命令：`pytest -q tests/openhands_contract/test_browser.py`。

### `extensions.skills-plugins`

等级：`productive`。

执行：加载多 source 同名 skill/plugin、非法 YAML、超大正文、浮动 ref、MCP tool changed、恶意 hook 和提权指令。

Oracle：固定 precedence；metadata/body 分阶段；安全解析；ref/digest/provenance 记录；tool changed 仅 step 边界生效；恶意内容不能改变 policy ceiling；hook crash 被隔离；uninstall/disable 可回滚；secret 不泄漏。

命令：`pytest -q tests/openhands_contract/test_extensions.py`。

### `subagents.child-conversation`

等级：`productive`。

执行：父 action 启动两个 child，分别采用 shared read-only workspace 与 isolated worktree；覆盖 budget、工具权限、取消、失败、重复 launch 和迟到结果。

Oracle：child 有独立 conversation/event/lease；parent/child lineage 稳定；预算与权限不超过父；workspace mode 明确；launch idempotent；父取消下传；child 结果以 typed observation 回父；迟到结果不提交到已终结父。

命令：`pytest -q tests/openhands_contract/test_child_conversations.py`。

## polished

### `runtime.remote-lease`

等级：`polished`。

执行：两个 server 竞争同 conversation；在 dispatch/receipt/event/outbox/renew 处 kill；lease expiry、网络分区、旧 writer 恢复和 runtime replacement。

Oracle：单 writer；generation 单调；旧 token 无法写 event/receipt/workspace；committed 副作用一次；未知副作用标 unknown_effect；outbox 重发去重；新 writer query receipt 后恢复；replacement 更新 identity 且关闭旧 handle。

命令：`pytest -q tests/openhands_contract/test_remote_lease.py`。

### `security.defense-in-depth`

等级：`polished`。

执行：path traversal/symlink race、shell parser bypass、fork bomb、network DNS/IP/redirect/metadata、secret encoding/exfiltration、prompt injection、approval replay 和 container escape。

Oracle：workspace 外不可读写；进程/资源限制生效；deny network 无外连；secret 不在 prompt/event/log/trace/artifact/WS；approval digest 防 TOCTOU；skill/MCP/web 不能提权；sandbox unavailable fail closed；报告列出 kernel/provider 边界。

命令：`pytest -q tests/openhands_contract/test_defense_in_depth.py`。

### `deployment.multi-tenant`

等级：`polished`。

执行：tenant A/B 使用相同 id/path/name，猜测 conversation/artifact/WS；滚动升级、schema migration、backup/restore、quota、slow client、server/runtime failover。

Oracle：跨租户均 denied 且无存在性泄漏；namespace 覆盖 DB/artifact/secret/runtime；migration 可 dry-run/rollback；restore digest 一致；旧客户端协商；quota/SLO 告警有效；单租户故障不拖垮其他租户。

命令：`pytest -q tests/openhands_contract/test_multitenancy.py`。

## 跨能力失败注入

- LLM stream 断开、429、invalid response、context overflow；
- tool dispatch 前后 crash、迟到 result、重复 tool_call_id；
- Event append/state snapshot/outbox 中断；
- confirmation pending 时 UI/server 重启；
- workspace/container/browser/MCP/child conversation 失联；
- lease renew 延迟、时钟偏差、网络分区；
- event gap/duplicate/cycle/unknown schema；
- malicious repo、web、skill、plugin、hook、tool output。

每个场景断言单一 run 终态、action 闭合、projection 可重建和权限不提升。

## 证据产物

`artifacts/capabilities.json` 对每个 ID 记录：`status`、`implementation_paths`、`test_paths`、`command`、`build_commit`、`artifact_digest`、`verified_at`。

保存 `events.jsonl`、snapshot digest、workspace receipts、security report、JUnit、Canvas snapshot 和 migration report。脱敏检查本身也输出机器报告。

证据路径为空、测试被 skip、使用真实付费 provider 才能通过或报告缺 build commit 时，不得标 verified。

## 发布门禁

- runnable：4/4 overlay 加共享 runnable 全绿；
- usable：前级回归 + 4/4 usable + reconnect/recovery；
- productive：前级回归 + 4/4 productive + container/browser/extension/subagent 安全；
- polished：15/15 + 共享 polished + tenant/escape/killpoint/migration/SLO。

任何高危回归、secret leak、双 writer、重复 committed 副作用或不可重建 UI 都阻断发布。
