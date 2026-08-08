# LangGraph 持久化、恢复与 Time Travel

## 目录

- [存储模型](#存储模型)
- [事务边界](#事务边界)
- [Pending Writes](#pending-writes)
- [Durability](#durability)
- [Interrupt 恢复](#interrupt-恢复)
- [历史与分支](#历史与分支)
- [子图持久化](#子图持久化)
- [Schema 与迁移](#schema-与迁移)
- [生产恢复](#生产恢复)
- [故障矩阵](#故障矩阵)

## 存储模型

逻辑键：`tenant/application + thread_id + checkpoint_ns + checkpoint_id`。上游 config 核心寻址字段是 thread id、checkpoint namespace 和 checkpoint id；tenant/application 是生产设计综合。

Checkpoint 内容：

- `v`、单调可排序 `id`、RFC3339 timestamp；
- `channel_values` 与 `channel_versions`；
- 每 node 的 `versions_seen`；
- `updated_channels` 与必要的 pending sends；
- metadata：source、step、parents、run id、writes 等；
- tuple 外层的 parent config 与 pending writes。

`StateSnapshot` 是从这些数据计算出的公开读取视图，不应原样作为数据库 schema。

## 事务边界

- `put` 提交 checkpoint 与 metadata/new channel versions。
- `put_writes` 以 checkpoint、task id、write index 保存中间 writes。
- 同一 task/write index 重复写必须幂等或确定覆盖。
- thread head 更新需 CAS/事务，防止并行 resume 丢分支。
- checkpoint blob、pending writes、event/outbox 的原子范围必须文档化。
- Store memory 与 checkpoint 事务默认独立；跨系统原子性需 saga/receipt。
- external tool/executor 更是独立事务域，不能宣称 exactly-once。

## Pending Writes

pending writes 解决一个 superstep 中部分 task 已成功、另一 task 失败/interrupt 后的恢复效率和一致性：

- 成功 task 的 writes 与 task identity 绑定；
- 恢复时已完成 task 可不重跑，并把保存 writes 纳入 update；
- 失败/超时 attempt 的未提交 writes 被丢弃；
- interrupt/error marker 也可作为特殊 write；
- task graph 或 schema 版本变化时必须验证旧 pending writes 兼容；
- 它不记录任意 node 内部外部副作用，后者仍需 receipt/outbox。

## Durability

- `sync`：checkpoint 持久完成后才进入下一 superstep；最强恢复点，吞吐最低。
- `async`：持久化与下一步并行；默认语义，崩溃可能回到更早 durable point。
- `exit`：只在 graph 退出时保存；中途崩溃丢失更多进度，不适合 durable HITL。

durability 是 checkpoint 时机，不是数据库副本数、fsync 保证或外部 effect exactly-once。生产 adapter 必须公布实际 consistency/ack 合同。

## Interrupt 恢复

1. task 调用 `interrupt(value)`；
2. runtime 保存 interrupt 与可恢复 checkpoint/pending writes；
3. thread 状态为 interrupted，并向客户端 surface id/value；
4. 客户端提交 `Command(resume=...)`；
5. runtime 验证 thread/head/request id，将 resume 写入 scratchpad；
6. node 从头重跑，按顺序消费 resume value；
7. update 提交后生成新 checkpoint。

resume 必须绑定 expected head，避免两个审批者同时恢复。过期或重复 resume 返回 conflict/idempotent result。

## 历史与分支

- `get_state_history` 返回 checkpoint lineage，不是 append-only event log 的替代品。
- 从历史 checkpoint invoke 可 replay 后续节点；旧历史必须保留。
- `update_state` 从历史点修改 state 后形成 fork/branch。
- fork metadata 记录 source、parent、actor、reason 与 request id。
- 从最终 checkpoint replay 可为 no-op；从 interrupt 前 checkpoint replay 会再次触发 interrupt。
- time travel 只重建 graph state；外部 effect 默认复用 receipt/模拟，不自动重做。
- branch head 的选择必须显式，不能按“最新时间”跨分支误选。

## 子图持久化

- `checkpointer=None` 继承 parent；`True` 为子图建立持久 state；`False` 禁用。
- checkpoint namespace 包含嵌套 graph/task path，以区分并行或循环调用。
- parent snapshot 的 task.state 可指向 child config 或展开 child snapshot。
- child interrupt 可从 parent surface/resume；父子 checkpoint lineage 都要保留。
- stateful subgraph 在 replay/fork 时如何选 child head 必须与上游 contract tests 对齐。
- parent 删除 thread 时应递归删除 child namespace checkpoint，除非 retention 明确例外。

## Schema 与迁移

- 分开版本化 graph schema、channel checkpoint format、serializer、event envelope。
- state key 新增可有默认；删除/改 reducer 需要显式 migration。
- channel type 变化必须迁移 value、version 与 pending writes。
- migration 先读取副本、校验 digest/lineage，再以新 checkpoint 写入。
- 旧 reader 对未知 metadata 字段前向兼容；未知核心 channel type 应拒绝。
- serializer allowlist 与 encryption key version 同步迁移。
- migration fixtures 覆盖真实历史、interrupt、pending writes、subgraph 和 branch。

## 生产恢复

- PostgreSQL/其他 saver 需 connection pool、transaction、index、retention、backup/PITR。
- 定期恢复演练验证 checkpoint、pending writes、events、artifacts 与 Store 引用一致。
- lease/worker heartbeat 不写进业务 state；worker crash 后安全接管 task。
- event delivery 使用 outbox/sequence；前端 projection 去重。
- 恢复时冻结 capability/model/tool/policy snapshot，或执行显式升级迁移。
- 无法确认 external effect 的 run 不自动推进，进入 reconcile queue。
- RPO/RTO、最大 thread bytes、history depth 和 migration window 都是发布合同。

## 故障矩阵

- node success 前/后 kill；
- `put_writes` 前/后 kill；
- reducer apply 前/后 kill；
- checkpoint put/ack 前/后 kill；
- interrupt emit/ack/resume 前后 kill；
- async durability 落后一或多步；
- subgraph child checkpoint 成功、parent checkpoint 失败；
- external commit 成功、receipt/checkpoint 失败；
- network retry 重复 resume/update/fork；
- migration 中断、旧版本 rollback 与新版本 reader 混跑。

每个 killpoint 的恢复 oracle 包括最终 state digest、task attempts、checkpoint lineage、effect count、pending writes 和 event projection hash。
