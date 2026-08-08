# LangGraph 架构蒸馏

## 目录

- [分层](#分层)
- [构建层](#构建层)
- [运行层](#运行层)
- [状态层](#状态层)
- [持久化层](#持久化层)
- [组合层](#组合层)
- [产品外层](#产品外层)
- [复刻约束](#复刻约束)

## 分层

```text
Graph DSL: StateGraph / node / edge / branch / schema
        ↓ compile
Pregel runtime: plan → execute tasks → apply writes → checkpoint
        ↕
Channels/reducers      Checkpointer      Store      Stream
        ↕                    ↕              ↕          ↕
User callables       thread history   cross-thread   consumers
```

架构中心不是聊天消息，而是版本化 channel state 与由版本变化触发的 task。

## 构建层

- `StateGraph` 保存 node specs、edges、waiting edges、branches、schemas 和 managed values。
- node 是 runnable/callable；框架不规定它必须是模型、工具或纯函数。
- 普通 edge 表示前驱完成后触发；conditional edge 根据 path result 选择目标。
- `Send(node,arg)` 动态生成 push task；静态 edge 通常形成 pull task。
- `START`/`END` 是控制 channel/终点标识，不是用户 state key。
- compile 校验未知 node、无效 interrupt node、schema 与 checkpointer 配置。
- 编译结果保留 graph introspection，但 execution 由 Pregel 承担。

## 运行层

- Pregel loop 从 input 或 checkpoint 建立 loop state。
- Plan 根据 channel versions 与 `versions_seen` 选择下一组 task。
- Execution 可并发运行同一 superstep 的 task；它们读取同一个 committed snapshot。
- task writes 暂存在 task-local/write buffer；成功后统一交给 update 阶段。
- Update 按 channel 的 `update(values)` 合并，再增加 channel version。
- runner 处理 retry、timeout、cancel、interrupt 与 parent command bubbling。
- 下一 tick 只能看到前一 tick 已应用的 writes，形成 bulk synchronous parallel 语义。
- 无 task 即完成；interrupt/errors/cancel 形成不同的停止原因。

## 状态层

- `LastValue` 适合每步至多一个 update；并发多写是冲突。
- `BinaryOperatorAggregate` 用用户 reducer 折叠 update；reducer 必须满足业务所需确定性。
- `Topic` 可累积多个值，并可配置去重/跨步累积。
- channel checkpoint/restore 负责自身持久表示，不应由 UI 猜测。
- input/output channels 是外部 API 投影；内部 channels 可包含 branch、task、interrupt 元数据。
- `StateSnapshot` 是读取模型，不等同存储层 `Checkpoint`。
- state schema 演进必须绑定 channel migration 与 serializer allowlist。

## 持久化层

- `BaseCheckpointSaver` 定义 get/list/put/put_writes/delete_thread 及 async 对应面。
- storage key 至少由 thread id、checkpoint namespace、checkpoint id 组成。
- checkpoint 保存 channel values、channel versions、versions seen、updated channels 和 metadata。
- `pending_writes` 按 checkpoint + task 记录，支持失败/interrupt 后恢复成功 task 的结果。
- durability `sync` 在下一步前等待持久化，`async` 与下一步并行，`exit` 仅退出时保存。
- Store 是 namespaced key/value/search 能力，用于跨 thread 数据，不能替代 checkpointer。
- SQLite/Postgres 等 saver 是独立包/适配器；core 只依赖协议。

## 组合层

- 编译图可作为父图 node；父子 state key 可共享，也可通过 wrapper 显式转换。
- 子图 checkpointer 可 `None` 继承、`True` 自有持久 scope、`False` 禁用。
- checkpoint namespace 表示嵌套路径和 task 实例，不能只按 node name 寻址并发子图。
- `Command.PARENT` 把 update/goto 发送给最近父图。
- stream 开启 subgraphs 时必须附 namespace/path，避免相同 node name 冲突。
- parent cancel/interrupt/error 的传播与 child checkpoint 保留策略必须单测。

## 产品外层

- 模型 adapter 与 message reducer 属于 LangChain 集成，不是 Pregel 必需品。
- 工具执行是 node 内逻辑；生产 harness 应将工具协议、receipt 与 policy 独立成层。
- CLI/Web 使用 stream 与 state API，不能持有 runner、channel 或 saver 私有对象。
- Studio 是开发体验；Deployment 是服务运行面；两者不是 OSS runtime 的本地实现依据。
- tracing callback 可观测执行，但 durable truth 仍来自 checkpoint/event storage。

## 复刻约束

- reducer 是状态语义，不能降级为“最后一次 JSON merge”。
- task 并发与 state commit 分离，不能让 node 直接修改共享 dict。
- checkpoint 与 pending writes 必须在一个可解释的一致性模型内。
- interrupt 是 durable control flow，不是抛异常后丢弃堆栈。
- resume 从节点开头重跑，interrupt 前副作用必须移出、幂等或有 receipt。
- Store scope、checkpoint scope、workspace scope、tenant scope 必须分别建模。
- UI 协议使用稳定 envelope；Python/JS 的内部类差异留在 adapter 中。
- 安全、审批和部署增强必须标记“设计综合”，不改写上游 core 事实。
