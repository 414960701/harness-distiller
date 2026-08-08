# Agent Loop

## 职责与非目标

Agent Loop 把一次用户意图编排为有界、可取消、可恢复的 turn，而不是无界 `while`。
它协调上下文装配、模型采样、工具执行、输入排队和终态提交。
它不实现 provider SDK、具体工具、UI、审批规则或数据库驱动；这些由端口注入。
它不暴露模型私有推理，也不把自然语言“完成了”当作系统终态。

## 状态与接口

建议状态：

```text
queued -> preparing -> model_streaming -> applying_response
  -> authorizing -> executing -> observing -> preparing
  -> compacting -> preparing
  -> completed | failed | cancelled | interrupted
```

```text
TurnRequest { thread_id, input_items, config_ref, budget, deadline }
TurnPorts { context, model, tools, events, state, policy, clock }
TurnControl { steer(input), interrupt(reason), resolve_approval(id, decision) }
TurnResult { turn_id, terminal_status, final_item_id?, error?, usage }
```

每次模型 step 捕获不可变 context snapshot 与 tool catalog version。
同一 turn actor 是状态唯一写者；worker 只能返回带 causation id 的消息。
模型、工具和订阅者错误不得直接越过 actor 写终态。

## 运行规则

1. 持久化 `turn.started` 后才发起模型请求。
2. 消费模型流时先归一化 item，再决定是否执行工具或结束。
3. 工具 result 进入历史后才开始下一模型 step。
4. steering 在安全点合入；写工具临界区只排队，不修改已授权调用。
5. 没有待处理工具、输入、压缩或 follow-up 时才允许正常完成。
6. 终态以 compare-and-set 提交，任何迟到结果不得复活 turn。
7. cancel token 向模型请求、进程、远程租约和子代理传播。

## 四级增量

| 等级 | 新增能力 | 保持不变的合同 |
|---|---|---|
| 能跑 | 单模型、串行工具、最大步数、completed/failed | turn id、单终态、call/result 配对 |
| 能用 | durable turn、分类错误、预算、取消、压缩 | 同一状态机与事件语义 |
| 顺手 | steering、并行只读工具、后台任务、子代理 | actor 单写者与取消树 |
| 好用 | 分布式 lease、优先级、公平调度、灾难恢复 | 幂等命令、因果链与终态不变量 |

等级只增加状态分支和 adapter，不能为每级维护不同 loop。

## 直接升级与回滚

允许从能跑直接升好用，但顺序固定为：事件版本 → durable state → cancel/lease → 并发调度。
升级前用旧 trace 建 golden fixture，并让新 loop 重放出相同 item 与终态。
新增状态必须有旧客户端可理解的投影或 capability gate。
回滚代码前先停止接收新 turn，完成或中断新版本专属状态，再降写入版本。
无法降级读取的 turn 保持只读，不得强行映射成 completed。

## 失败模式与安全

- provider partial stream：关闭未完成 item，按幂等能力决定是否重采样；
- tool 已执行但 result 未落盘：进入 unknown effect，由持久化层对账；
- approval 断线：保持 durable pending 或按 deadline 过期；
- interrupt 与完成竞态：CAS 只接受一个终态；
- input flood：有界队列、背压和明确 rejected/queued 事件；
- 无限工具循环：step、token、时间和费用预算共同终止；
- 恶意工具输出：只作为不可信观察，不可修改 policy 或 loop 配置。

Agent Loop 不能因模型请求而自行提升权限、sandbox 或预算上限。

## 可执行验收

- scripted model 依次发 read、patch、test，产生三个 step 后正常完成；
- 同一 tool call 重复投递时只执行一次并只有一个 result；
- 在 sampling、approval、executing 三阶段 interrupt，终态均唯一；
- 在写工具执行后、result 前 kill，恢复不重复副作用；
- steering 在模型流中与写临界区分别产生 accepted 和 queued；
- 达到任一预算时停止新工具并返回稳定错误 code；
- 随机交错 delta、迟到 result 和 cancel 的 property test 不破坏状态不变量。

## 证据与设计综合

`公开事实`：Codex 的 turn/session 结构、OpenHands 等开源 agent loop 可证明多步采样与工具观察是常见实现。
`设计综合`：上述通用状态名、端口与升级顺序是本 skill 的跨产品合同，不声称对应某一产品私有实现。
产品差量应写入对应 dossier；协议细节见 [protocol-events.md](protocol-events.md)，恢复见 [state-persistence.md](state-persistence.md)，子代理见 [subagents.md](subagents.md)。
