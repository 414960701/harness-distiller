# Codex 架构蒸馏

## 可验证模块边界

| 边界 | 公开实现职责 | 蒸馏合同 |
|---|---|---|
| core | Session、Turn、上下文、模型采样、工具路由、压缩、agent | 不依赖具体 UI 的可取消 runtime |
| protocol | tool call、event、thread/turn/item 等共享类型 | 带版本的命令、事件、错误和 capability |
| exec | 非交互任务入口 | 同一 runtime 的 headless adapter |
| tui | 终端状态投影与输入 | 只消费事件、提交命令，不持有业务真相 |
| app-server | JSON-RPC/WebSocket 客户端协议 | 多客户端连接、订阅、恢复和 steering |
| rollout/state | 会话日志、索引和恢复状态 | append-first 写入、幂等恢复、可迁移索引 |
| sandbox crates | 平台执行隔离 | policy 决策后的独立 enforcement |

源码入口：

- core session: https://github.com/openai/codex/tree/92fb33b7583ac909a21efaebcd2fad6e79643a6f/codex-rs/core/src/session
- protocol: https://github.com/openai/codex/tree/92fb33b7583ac909a21efaebcd2fad6e79643a6f/codex-rs/protocol
- app-server: https://github.com/openai/codex/tree/92fb33b7583ac909a21efaebcd2fad6e79643a6f/codex-rs/app-server
- TUI: https://github.com/openai/codex/tree/92fb33b7583ac909a21efaebcd2fad6e79643a6f/codex-rs/tui

## 运行拓扑

最小拓扑是 UI adapter 与 runtime 同进程；产品级拓扑允许 CLI、IDE 或桌面客户端连接 app-server。两种拓扑共享同一协议语义：

1. client 创建或恢复 Thread；
2. client 提交 Turn input；
3. runtime 追加 Item，并发出 started、delta、completed 等事件；
4. tool call 进入审批和执行；
5. client 可在运行中 steer、interrupt 或回答请求；
6. turn 进入 completed、failed 或 interrupted 终态。

app-server README 和生成的 v2 schema 显示，协议已经覆盖 thread start/read/resume/fork/rollback、turn start/steer/interrupt、compaction、MCP、permission、skills 和协作状态。

来源：https://github.com/openai/codex/blob/92fb33b7583ac909a21efaebcd2fad6e79643a6f/codex-rs/app-server/README.md

## Agent loop

run_turn 是 turn 内循环，而不是“一次用户消息等于一次模型调用”：

1. 执行预采样压缩检查；
2. 解析用户输入所需的 MCP、附件和动态上下文；
3. 捕获本 step 的一致上下文与工具视图；
4. 发起流式模型请求；
5. 将文本、推理、函数调用等 response item 归一化并落事件；
6. 经 ToolRouter 执行工具，并把结果追加历史；
7. 有待继续的工具结果、steering 或压缩时再次采样；
8. 无工具请求且没有待处理输入时结束。

源码：https://github.com/openai/codex/blob/92fb33b7583ac909a21efaebcd2fad6e79643a6f/codex-rs/core/src/session/turn.rs

本节只保留研究结论；可直接实现的状态机、伪代码、重试、取消与 steering 规范统一见 [agent-loop.md](agent-loop.md)。

## 状态模型

建议保留四层：

- Thread：长期会话与工作区绑定；
- Turn：一次用户意图到明确终态；
- Item：user message、agent message、reasoning、tool call/result、plan、diff、compaction；
- Event：Item 生命周期与状态增量。

恢复时先重放不可变 Item，再用数据库或索引加速列表查询。不要只存 UI 最终文本，也不要让 UI 组件对象成为恢复源。

命令/事件表与 JSON 示例统一见 [protocol-state.md](protocol-state.md)，事务与恢复算法统一见 [persistence-recovery.md](persistence-recovery.md)。

## 架构不变量

- runtime 不导入 TUI/IDE 组件。
- 每个逻辑 tool call 只有一个终态 result，重试复用 causation id。
- 同一 Thread 的持久化默认单写者；并行工作使用子 thread/agent 和隔离 workspace。
- UI 断线重连后可由快照加增量事件重建。
- 协议先于界面演进，新字段向后兼容或通过 capability 协商。
- app-server 的文件、命令辅助接口不得绕过 runtime 的 policy/enforcement。

## 测试证据

Codex 源码包含 core、app-server、exec、TUI 的单元/集成测试，app-server 使用 mock model server 和 rollout fixture；TUI 使用 snapshot 测试。蒸馏实现至少应具备协议合同、模型流 fixture、恢复重放、取消竞态和 UI snapshot。

## 实现交接检查

- core 可以在没有 TUI 的测试进程中完整运行 turn；
- protocol 包不反向依赖 executor 或 surface；
- app-server 仅提交命令并投影事件，不直接修改 thread state；
- state 索引可从 rollout 重建，sandbox adapter 可独立替换；
- 产品合同和模块 API 都能由黑盒 fixture 验证。
