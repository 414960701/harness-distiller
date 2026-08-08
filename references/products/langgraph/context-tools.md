# LangGraph Context、模型与工具边界

## 目录

- [三类上下文](#三类上下文)
- [模型集成](#模型集成)
- [工具集成](#工具集成)
- [Store 与记忆](#store-与记忆)
- [预算与压缩](#预算与压缩)
- [完整 Harness 增强](#完整-harness-增强)
- [失败合同](#失败合同)
- [测试矩阵](#测试矩阵)

## 三类上下文

- **state**：在 graph channel 中随 superstep 演进；启用 checkpointer 时按 thread 持久化。
- **runtime context**：每次 invocation 注入的不可变依赖，如 user id、DB client 配置；不自动持久化。
- **Store memory**：按 namespace/key 保存，可跨 thread 读取；生命周期不跟 checkpoint 绑定。

还应把 config metadata/tags 与上述三类分开。把 API key 写进 state 会进入 checkpoint；把聊天历史只写入 runtime context 又无法恢复。

## 模型集成

LangGraph core 不拥有 Model 抽象。节点可以调用 LangChain chat model、其他 SDK、本地模型或纯函数。

完整实现应在 node 外再定义 provider-neutral model adapter：

- 输入规范化 messages、tools、response format、sampling 和 cancellation；
- 输出 model item、text/reasoning/tool-call delta、usage 和 finish reason；
- 每次 call 有稳定 call id、attempt 与 provider request id；
- provider retry 与 graph node retry 分层，避免乘法重试；
- token stream 进入 `messages`/规范 event，而最终 message 进入 reducer；
- 不把隐藏 chain-of-thought 写入 state、checkpoint 或 trace。

## 工具集成

LangGraph core 只看到 node/runnable 的输入与返回。即使使用预构建 ToolNode，完整 harness 仍要显式实现：

- tool descriptor：稳定 id/version、JSON Schema、side-effect class；
- invocation：call id、规范化参数、deadline、cancel token；
- result：structured content、error kind、artifact refs、receipt；
- dispatch policy：allow/deny/ask/amend 与 sandbox profile；
- idempotency：effect key、external receipt、reconcile；
- output budget：截断、artifact offload、digest 与 provenance。

工具结果作为 state update 时仍受 channel reducer 约束。

## Store 与记忆

- Store namespace 至少包含 tenant、subject、application/purpose。
- `put/get/search/list_namespaces/delete` 要在 sync/async API 保持同义。
- semantic search 需要显式 embedding/index config；无 embedding 时不虚假承诺 RAG。
- thread A 的 checkpoint 不会自动读取 Store；node 必须通过 `Runtime.store` 查询。
- memory mutation 记录 actor、source、timestamp、TTL、version 和 consent。
- checkpoint fork 不应自动 fork 全局 memory；两者需不同 lineage。
- 生产 Store 要做 tenant isolation、encryption、retention 和 delete audit。

## 预算与压缩

Graph runtime 本身不提供通用 prompt compaction。代码 agent 复刻需新增 context engine：

- 先量化 system/instruction/history/tool/artifact/RAG 各自预算；
- 将不可变 policy 与可压缩工作记忆分层；
- summary 写入显式 channel，并带覆盖范围与 source digest；
- raw artifact 存外部对象存储，state 仅保存引用；
- time travel 时 summary 必须与目标 checkpoint 的来源一致；
- subgraph 只接收声明允许的 context slice；
- 压缩不能删除 pending approval、tool receipt 或失败原因。

## 完整 Harness 增强

推荐节点边界：`context.prepare → model.call → tool.plan → policy.check → tool.execute → state.reduce`。这不是上游固定图，而是一种使权限、receipt 和重放可验证的设计综合。

模型/工具 registry 在 run 开始冻结 capability snapshot；恢复旧 thread 时使用兼容版本或显式迁移，不偷偷绑定最新工具实现。

## 失败合同

- 模型限流：provider retry 达上限后转 node failure，保留 provider request id。
- malformed tool call：不执行，返回 schema validation item。
- tool timeout/cancel：终止进程/请求，迟到结果不提交。
- unknown external commit：标 `indeterminate`，禁止 graph retry 自动重复副作用。
- Store unavailable：按节点声明 fail/skip/degrade，不能静默返回空记忆。
- serializer rejection：结构化说明不允许的 type，不回退不安全 pickle。
- token overflow：压缩或失败，不裁掉 policy 后继续。

## 测试矩阵

- 相同 scripted model 在 sync/async path 得到相同最终 state digest。
- graph retry 与 provider retry 的总 attempt 可上界计算。
- resume 重跑不会重复已 receipt 的 tool action。
- Store 同 subject 跨 thread 可见、跨 tenant 不可见。
- checkpoint fork 不污染旧 branch，也不复制全局 memory。
- 恶意 tool/RAG/memory 文本不能改写 permission policy。
- summary 后 replay 与无压缩基线保留相同 task/receipt lineage。
