# 共享参考架构

## 核心原则

Harness 不是一个 `while(tool_calls)` 循环，而是受策略约束、可恢复、可观察的事件驱动状态机。模型提出意图；策略层决定是否允许；执行层在强制边界内完成；状态层提交事件；界面只投影事件。

```text
Surface -> Command API -> Turn Orchestrator -> Model Adapter
                         |        |             |
                         |        v             v
                         |    Context Engine  Tool Intent
                         |                      |
                         v                      v
                      Event Log <- Tool Runtime/Policy -> Executor/Sandbox
                         |
                         v
                 State projections / UI / traces
```

## 九个稳定边界

1. **Protocol**: 版本化 command/event/error；支持 capability negotiation。
2. **Turn orchestrator**: 明确状态机、预算、取消、重试、最大步数和终止原因。
3. **Model adapter**: 统一消息、流、工具调用、推理/缓存/多模态能力，不抹平提供商限制。
4. **Context engine**: 分层装配指令、仓库、检索、记忆和历史；给每层预算与来源。
5. **Tool runtime**: schema、注册、路由、并发、幂等、结果归一化和生命周期事件。
6. **Policy**: 纯决策或可审计决策服务，返回 allow/deny/ask/amend。
7. **Executor**: workspace、进程、文件、网络和 sandbox 的强制实现。
8. **State**: thread/turn/item/event/checkpoint 的单写者持久化与迁移。
9. **Surface adapters**: CLI/TUI/IDE/Desktop/Web 通过协议消费状态，不直接抓 runtime 对象。

## 建造顺序

```text
protocol -> state skeleton -> model adapter -> orchestrator -> one read tool
-> policy -> executor -> one edit tool -> streamed surface -> recovery
-> context/compaction -> plugin tools -> extra surfaces -> advanced optimization
```

先做可执行的 vertical slice，再扩展 35 个知识模块。若先做大量工具，后补事件、权限和恢复，通常需要重写。

## 关键数据模型

- `Thread`: 长期会话身份、配置快照和 lineage。
- `Turn`: 一个用户目标的运行边界；只有明确终态。
- `Item`: 用户消息、agent 消息、reasoning 摘要、tool call/result、file change、approval、plan 等可呈现单元。
- `Event`: 事实追加记录，带 sequence、causation、correlation 和 schema version。
- `Projection`: UI 或查询模型，可丢弃重建。
- `Checkpoint`: 上下文、workspace/git、状态 schema 的恢复锚点。

## 失败语义

所有异常映射为稳定错误类型：`invalid_input`, `model_error`, `tool_error`, `policy_denied`, `approval_rejected`, `sandbox_violation`, `cancelled`, `timeout`, `budget_exhausted`, `protocol_error`, `internal_error`。原始 provider 错误只能作为受控 detail，不可成为跨层合同。

## 缓存与上下文

保持稳定 prompt 前缀：系统指令、工具 schema、sandbox 与环境说明顺序固定；把动态用户输入和运行时变化追加在后。压缩生成新 item，不原地改写历史，从而同时支持缓存、审计和恢复。

## 权限与沙箱

Policy Decision Point 与 Policy Enforcement Point 必须分离。审批只是授权，不能替代 OS/容器 sandbox；字符串命令分类只是输入，不能替代系统调用、路径、网络和进程边界。

