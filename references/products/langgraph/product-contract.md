# LangGraph 产品合同

## 目录

- [产品承诺](#产品承诺)
- [核心行为](#核心行为)
- [状态与执行合同](#状态与执行合同)
- [持久交互合同](#持久交互合同)
- [非目标](#非目标)
- [设计综合](#设计综合)
- [证据与完成定义](#证据与完成定义)

## 产品承诺

输入一个类型化状态、节点和边，编译得到可调用、可流式消费、可暂停恢复、可检查历史的图运行时。调用者能用显式 `thread_id` 选择持久会话，用 checkpoint id 定位历史，用 `Command` 更新/跳转/恢复，并以 reducer 合并并发写入。

产品价值是“durable orchestration primitive”，不是替用户决定 agent persona、模型、工具、权限或 UI。

## 核心行为

- `StateGraph` 构建期收集 state/input/output/context schema、node、edge、branch。
- compile 后得到 Pregel runtime；未编译 builder 不直接执行。
- 每个 channel 定义值如何从 update 演进；无 reducer 的 LastValue 并发多写应失败。
- superstep 分 Plan、Execution、Update；同一步 task 对彼此更新不可见。
- 节点可以返回 state update 或 `Command(update/goto/graph/resume)`。
- `Send` 为下一步创建带自定义输入的动态 task，适合 map-reduce。
- 没有下一 task、达到显式终点、interrupt、错误或取消时进入可判定终止状态。
- retry 只重跑选定 task，不能让失败尝试写入污染已提交状态。

## 状态与执行合同

- state 字段对应 channel；reducer 决定零、一或多 update 的合并。
- 输入 schema、内部 state schema 与输出 schema可以不同。
- context 是本次 run 的不可持久依赖输入，不应偷偷写入 thread state。
- `Runtime` 可注入 context、Store、stream writer 和 previous value。
- task identity 至少包含 name、id、path；子图需要 checkpoint namespace lineage。
- stream mode 至少支持 values、updates、messages、custom、checkpoints、tasks、debug 的明确子集。
- 同一运行的 sync/async API 必须有相同状态语义；调度时序可不同。
- recursion/superstep limit、node timeout、retry exhaustion 都产生机器可读失败。

## 持久交互合同

- checkpointer 以 thread id、checkpoint namespace、checkpoint id 寻址快照。
- checkpoint 保存 channel values/version、每节点 seen version、metadata 与必要的 pending sends。
- `CheckpointTuple.pending_writes` 保存当前 checkpoint 后尚未形成下一 checkpoint 的 task writes。
- `get_state` 返回 values、next、config、metadata、parent、tasks、interrupts 的快照。
- `get_state_history` 顺序与分页行为必须固定并可测试。
- interrupt 首次调用暂停；resume 后节点从头执行，interrupt 顺序必须稳定。
- `Command(resume=...)` 可按 interrupt id 映射或恢复下一个 interrupt。
- `update_state` 创建可追溯新 checkpoint；time travel 形成 replay/fork，而不是原地篡改历史。
- Store 的跨 thread memory 与 checkpointer 的 thread state 是两个命名和生命周期不同的系统。

## 非目标

- 不承诺内置 LLM、prompt、tool calling、RAG 或 coding agent。
- 不承诺 shell、workspace、patch、Git、artifact 或 sandbox。
- 不承诺 approval/permission policy；interrupt 只是暂停原语。
- 不承诺外部副作用 exactly-once；pending writes 只能避免已成功纯 task 的部分重复。
- 不承诺任意 Python 对象都能安全序列化；生产环境应限制 serializer 类型。
- 不承诺 Studio、LangSmith tracing、Deployment、remote graph 或云控制面属于 OSS core。
- 不把 LangChain agent 与 Deep Agents 的上层能力算入本产品合同。

## 设计综合

要生成“完整 LangGraph-like harness”，在不改 core 语义的前提下增加：

- 规范化 thread/turn/item/event envelope，供 CLI/Web 重建视图；
- tool effect receipt、idempotency key、outbox 与 `indeterminate` 状态；
- workspace 和 shell executor 的独立 policy/sandbox；
- approval policy 在调用节点之前执行，并用 interrupt 持久等待；
- checkpointer 生产适配器的 CAS、租户隔离、加密、备份与迁移；
- snapshot + ordered events 的前端投影，不直接暴露 Python private state；
- deployment readiness、SLO、容量、恢复演练和版本协商。

这些是设计综合，验收时必须与“上游兼容行为”分栏报告。

## 证据与完成定义

- 实现事实必须引用 [sources.md](sources.md) 的固定 commit。
- 行为证据优先采用上游 tests，再用本地 contract tests 覆盖语言无关 oracle。
- capability 只有同时存在生产实现路径和测试路径才可标 `verified`。
- runnable 必须证明 reducer、superstep、Command/Send 与 stream。
- usable 必须证明 checkpoint、interrupt、subgraph 与 Store scope。
- productive 必须证明 durability、pending writes、time travel 和 task observability。
- polished 必须证明生产 checkpointer、UI 投影与 deployment 边界。
- 所有等级必须覆盖错误、取消、恢复和迁移，不得只展示 happy path。
