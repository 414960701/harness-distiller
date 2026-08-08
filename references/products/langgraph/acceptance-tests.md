# LangGraph 实现验收与 Capability Oracle

## 目录

- [判定规则](#判定规则)
- [测试夹具](#测试夹具)
- [能力总表](#能力总表)
- [runnable](#runnable)
- [usable](#usable)
- [productive](#productive)
- [polished](#polished)
- [跨能力失败测试](#跨能力失败测试)
- [证据产物](#证据产物)
- [发布门禁](#发布门禁)

## 判定规则

本页逐项覆盖 [recipe.md](recipe.md) 的 15 个 canonical capability ID。每一项必须有实现路径、测试路径、结构化 oracle、失败分支和证据 artifact，才能标记 `verified`。

只复述官方文档、只展示 graph 图、只跑 happy path 或仅有 mock 声明，状态最多为 `implemented-not-verified`。四等级累积；`polished` 必须回归 runnable、usable、productive。

## 测试夹具

- `counter-graph`：LastValue 与 binary reducer、fan-out/join、冲突写；
- `command-graph`：update/goto/Send/parent command 与动态 map-reduce；
- `interrupt-graph`：单/多 interrupt、node 前置副作用 canary；
- `nested-graph`：三层子图、并行同名 child、共享/私有 state；
- `scripted-node`：成功、retryable/fatal error、timeout、cancel、custom/message stream；
- `memory-store`：tenant/subject/thread namespace 与固定 search truth set；
- `fault-saver`：put/put_writes/list/CAS 注入延迟、重复、失败和 killpoint；
- `effect-ledger`：按 idempotency key 统计外部 effect 次数；
- `event-projector`：snapshot + events 重建规范状态；
- `old-checkpoints`：前两版 schema、interrupt、pending writes、subgraph、branch fixtures。

建议命令：

```bash
pytest -q tests/langgraph_contract --junitxml=artifacts/langgraph.xml
python3 scripts/assert_projection.py artifacts/snapshot.json artifacts/events.jsonl
python3 scripts/assert_capabilities.py artifacts/capabilities.json
```

## 能力总表

| capability | 等级 | 主要证据 |
|---|---|---|
| `graph.state-reducers` | `runnable` | channel conformance |
| `runtime.pregel-supersteps` | `runnable` | BSP scheduling trace |
| `control.command-send` | `runnable` | routing state digest |
| `streaming.modes` | `runnable` | typed stream fixture |
| `persistence.checkpoints` | `usable` | history/namespace fixture |
| `interrupts.durable-resume` | `usable` | restart/resume ledger |
| `subgraphs.composition` | `usable` | parent-child lineage |
| `store.cross-thread-memory` | `usable` | namespace isolation |
| `durability.configurable` | `productive` | mode killpoints |
| `recovery.pending-writes` | `productive` | partial task replay |
| `time-travel.branching` | `productive` | branch DAG digest |
| `observability.task-streams` | `productive` | projection conformance |
| `checkpoint.production-store` | `polished` | storage chaos/migration |
| `frontend.snapshot-event-projection` | `polished` | reconnect/gap tests |
| `deployment.operational-boundary` | `polished` | tenant/HA/SLO suite |

## runnable

### `graph.state-reducers`

等级：`runnable`。

执行：对 LastValue、binary aggregate、Topic/custom reducer 注入零/一/多 update，并在同步/异步执行中交换并发 task 完成顺序。

Oracle：LastValue 多写给确定冲突；reducer 输出符合声明顺序合同；同一输入/seed 的 replay state digest 相同；node 不可直接改变共享 snapshot；无效 update 类型结构化失败；checkpoint round-trip 保持 channel 值。

测试路径：`tests/langgraph_contract/test_state_reducers.py`。

### `runtime.pregel-supersteps`

等级：`runnable`。

执行：运行 fan-out→join 图，记录 plan/task/write/update trace，并随机化同一步 task 完成顺序。

Oracle：同一步 task 只见 step-start state；writes 在 update 阶段统一应用；join 在前驱条件满足后运行；channel version/versions-seen 单调；无 task 正常终止；recursion limit、失败、取消分别有稳定终态；迟到 task writes 不提交。

测试路径：`tests/langgraph_contract/test_pregel_supersteps.py`。

### `control.command-send`

等级：`runnable`。

执行：覆盖 `Command(update=...)`、goto 单/多节点、`Send` map-reduce、`Command.PARENT`、未知目标与动态并发。

Oracle：update 经过 reducer；goto 只创建声明目标；Send arg 与全局 state 分离；parent command 只到最近父图；task path/namespace 唯一；未知 node 不产生部分写；取消传播到动态 tasks。

测试路径：`tests/langgraph_contract/test_command_send.py`。

### `streaming.modes`

等级：`runnable`。

执行：请求 values、updates、messages、custom 及多 mode，运行含子图和 token/custom writer 的 scripted graph。

Oracle：每种 mode payload schema 可判；values 是 step 后全投影，updates 是 node/task delta；message delta 有 call/task metadata；custom 不可伪造 core type；多 mode 可无歧义 demux；sync/async 最终 state digest 一致；stream 取消关闭 producer。

测试路径：`tests/langgraph_contract/test_stream_modes.py`。

## usable

### `persistence.checkpoints`

等级：`usable`。

执行：用 conformance saver 创建两个 thread、两个 namespace、多 checkpoint，覆盖 invoke/get/list/update/delete 与进程重启。

Oracle：无 thread id 的 durable run 被拒绝；thread/namespace 隔离；StateSnapshot values/next/tasks/interrupts 正确；history parent/step/source 可追溯；checkpoint id 定位历史而不移动旧 head；sync/async saver 同义；delete scope 不越界。

测试路径：`tests/langgraph_contract/test_checkpoints.py`。

### `interrupts.durable-resume`

等级：`usable`。

执行：在 node 中设置单/多 interrupt，暂停后重启进程，以单值/id mapping resume，并重复、过期、并发提交。

Oracle：interrupt 前 durable checkpoint 存在；id 对同一 task/call position 稳定；node 从头重跑且按顺序消费 resume；重复 request 幂等；expected-head 冲突拒绝；无 checkpointer 的 durable interrupt 配置失败；副作用 canary 仅一次或进入 reconcile。

测试路径：`tests/langgraph_contract/test_interrupt_resume.py`。

### `subgraphs.composition`

等级：`usable`。

执行：构建共享 key、wrapper 映射、并行同名 child、三层 nested graph，分别用 inherit/own/disabled checkpointer。

Oracle：state 只按声明边界共享；每个 child task namespace 唯一；parent snapshot 能定位 child；child interrupt 从 parent 恢复；`Command.PARENT` 合法冒泡；parent cancel 向下传播；disabled checkpoint 不虚假恢复；旧 sibling state 不串线。

测试路径：`tests/langgraph_contract/test_subgraphs.py`。

### `store.cross-thread-memory`

等级：`usable`。

执行：thread A 写 Store memory，thread B 同 tenant/subject 查询，tenant B 与其他 subject 尝试读取；fork checkpoint 后修改 memory。

Oracle：同 namespace 跨 thread 可见；tenant/subject 隔离；checkpoint fork 不复制/回滚全局 Store；mutation 有 version/provenance/TTL；search 对 truth set 确定；Store unavailable 不静默返回空；secret 字段不进入 stream。

测试路径：`tests/langgraph_contract/test_store_memory.py`。

## productive

### `durability.configurable`

等级：`productive`。

执行：对 sync/async/exit 在 input、task update、checkpoint ack、下一 step、正常/interrupt/error exit 注入 killpoint。

Oracle：sync 在下一步前 durable；async 恢复到最后 ack checkpoint 且不声称更新已 durable；exit 中途崩溃按合同丢失进度；每种模式的最后 durable checkpoint 可观测；interrupt profile 不误用 exit；外部 effect count 与 receipt policy 一致。

测试路径：`tests/langgraph_contract/test_durability.py`。

### `recovery.pending-writes`

等级：`productive`。

执行：同一 superstep 三 task 中两个成功、一个失败/interrupt，在 put_writes 前后 kill 后恢复。

Oracle：成功 task 不重复执行；pending write 按 task/write index 去重；失败 attempt writes 丢弃；恢复后的 reducer result 与无故障基线相同；schema/task graph 不兼容时拒绝旧 writes；external effect 依 receipt 而非 pending write 推断。

测试路径：`tests/langgraph_contract/test_pending_writes.py`。

### `time-travel.branching`

等级：`productive`。

执行：从中间/最终/interrupt 前后 checkpoint replay；update_state 后 fork；并行创建两个 branch；对子图做相同行为。

Oracle：旧 checkpoint 不变；branch DAG parent/source 正确；最终点 replay 为 no-op 或明确新 run；interrupt 前 replay 重新触发稳定 interrupt；state patch 经过 reducer/attribution；active head 不按时间误选；外部 effect 默认复用/模拟不重做。

测试路径：`tests/langgraph_contract/test_time_travel.py`。

### `observability.task-streams`

等级：`productive`。

执行：消费 tasks、checkpoints、debug 与 subgraph stream，注入 retry、error、interrupt、cancel 和同名 child。

Oracle：task start/end/error/result/interrupt 可配对；checkpoint event 对应可读取 snapshot；namespace/path 保留父子 lineage；retry attempt 不冒充新业务 task；debug 可关闭并受 redaction；事件投影能解释最终 next/tasks/interrupts；trace 不作为 durable truth。

测试路径：`tests/langgraph_contract/test_task_observability.py`。

## polished

### `checkpoint.production-store`

等级：`polished`。

执行：对真实生产 adapter 做并发 head CAS、事务 rollback、连接中断、failover、加密轮换、旧 schema migration、backup/restore 与 tenant delete。

Oracle：无 lost update；put/put_writes 原子范围符合合同；重复 request 幂等；secret/tenant 隔离；旧数据迁移 digest/lineage 保持；失败 migration 可回滚；restore 后 state/pending writes/event refs 一致；RPO/RTO 达配置阈值。

测试路径：`tests/langgraph_contract/test_production_checkpointer.py`。

### `frontend.snapshot-event-projection`

等级：`polished`。

执行：从 snapshot + values/updates/messages/custom/tasks/checkpoints adapter events 构建 CLI/Web projection，注入重复、乱序、gap、断线和 schema 升级。

Oracle：重复幂等；乱序缓冲；gap 补拉；重连后 projection hash 等于 live canonical state；并行 task/子图/interrupt/branch 无歧义；客户端不 import runtime 私有类；未知扩展前向兼容；redaction canary 不泄露。

测试路径：`tests/langgraph_contract/test_frontend_projection.py`。

### `deployment.operational-boundary`

等级：`polished`。

执行：多实例 service 覆盖 auth、tenant、quota、worker crash/lease、rolling upgrade、backpressure、retention、backup restore 和 SLO load。

Oracle：core 与 Deployment/Studio adapter 可独立替换；tenant 无跨界；worker 接管不重复已 receipt effect；旧/新 schema 协商；取消/interrupt 在 failover 后可恢复；quota/retention 生效；SLO 报告含 p50/p95/p99、错误率、checkpoint lag；托管特性不被标成 OSS core verified。

测试路径：`tests/langgraph_contract/test_deployment_boundary.py`。

## 跨能力失败测试

- reducer 非确定、并发 LastValue 多写、未知 goto/Send target；
- retry timeout、外部 cancel、迟到 write、error handler 再失败；
- checkpoint ack 丢失、pending write 重复、thread head conflict；
- interrupt 顺序变化、恶意 resume、双审批；
- nested child crash、parent crash、`Command.PARENT` 越权；
- Store/checkpointer scope 混淆与跨 tenant search；
- serializer gadget、过大/深层 state、migration 中断；
- stream duplicate/reorder/gap/custom type spoof；
- external commit 未知、sandbox unavailable 和 permission fail-open。

## 证据产物

每次验收保存：build commit、上游基线、语言/runtime、dependency lock、graph/schema digest、seed、durability、saver/Store descriptor、policy/capability snapshot、JUnit、events JSONL、snapshot/history、effect ledger、projection hash、migration/chaos 报告。

`capabilities.json` 对每个 ID 写 `status`、`implementation_path`、`test_path`、`evidence_digest`。缺任一路径不得写 `verified`。

## 发布门禁

- runnable 四项全通过才能称 LangGraph-like runtime。
- usable 四项全通过才能用于可恢复交互工作流。
- productive 四项全通过才能承载长任务与调试/分支。
- polished 三项及所有低级回归全通过才能生产发布。
- 安全、migration、killpoint 或 tenant isolation 任一失败均阻断 polished。
- 平台/Studio 能力必须单列来源与实现，禁止借上游品牌名称替代本地证据。
