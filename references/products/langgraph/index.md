# LangGraph 产品蒸馏索引

## 目录

- [定位](#定位)
- [版本基线](#版本基线)
- [阅读路线](#阅读路线)
- [核心与边界](#核心与边界)
- [复刻目标](#复刻目标)
- [成熟度](#成熟度)

## 定位

LangGraph 是一个面向长生命周期、有状态工作流与 agent 的低层编排运行时。本 dossier 蒸馏的是它可观察、可验证的 durable graph harness：声明状态与 reducer，编译图，由 Pregel 风格 superstep 调度任务，以 checkpoint、pending writes、interrupt 和 stream 支撑恢复与交互。

它不是现成的 Codex/Claude Code 类代码 agent。模型选择、prompt、工具、文件系统、shell、权限、sandbox 和产品 UI 都必须由上层提供。

## 版本基线

- Python 主基线：`langgraph==1.2.10`，tag `1.2.10`，commit `41341457342327166d72fc11952ab28fb61ec0bf`。
- Python checkpoint 同仓库声明版本：`langgraph-checkpoint==4.1.1`。
- JavaScript 交叉基线：`@langchain/langgraph@1.4.9`，commit `5f9915234a5dca861ef01180fde28e52f42c6e15`。
- 两个仓库均为 MIT；详情及固定链接见 [sources.md](sources.md)。
- Python 是本 dossier 的精确实现事实基线；JS 只证明主要概念可跨语言复刻。

## 阅读路线

1. [product-contract.md](product-contract.md)：先冻结行为、非目标和证据边界。
2. [architecture.md](architecture.md)：拆 StateGraph、Pregel、channel、checkpointer、store。
3. [agent-loop.md](agent-loop.md)：实现 superstep、task、retry、取消和终止。
4. [protocol-state.md](protocol-state.md)：定义 thread/turn/item/event 投影及 stream 协议。
5. [persistence-recovery.md](persistence-recovery.md)：实现 checkpoint、pending writes、durability 和 time travel。
6. [context-tools.md](context-tools.md)、[workspace-execution.md](workspace-execution.md)、[safety-runtime.md](safety-runtime.md)：补齐完整 harness 的上层边界。
7. [experience.md](experience.md)：实现 CLI/Web/Studio-like 消费端，而不泄漏运行时私有对象。
8. [recipe.md](recipe.md)：按四等级选择差量能力。
9. [acceptance-tests.md](acceptance-tests.md)：用 executable oracle 判断是否真的复刻。

## 核心与边界

| 层 | 属于 LangGraph core | 需要上层或托管产品补充 |
|---|---|---|
| 图模型 | `StateGraph`、node、edge、branch、`Send`、`Command` | 领域 agent 模板、任务规划策略 |
| 执行 | Pregel superstep、task、channel update、retry/timeout | 进程隔离、容器、remote worker |
| 持久化 | checkpointer 接口、thread/checkpoint namespace、pending writes | 生产数据库部署、租户治理、备份 |
| 交互 | interrupt/resume、state/history/update、stream modes | approval policy、认证、通知、UI |
| 记忆 | checkpoint 的 thread state、独立 `Store` 接口 | embedding/RAG 策略、隐私与保留策略 |
| 工具 | node 可调用任意 runnable/callable | 工具注册、schema、receipt、权限、sandbox |
| 产品 | graph introspection 与结构化 stream | LangSmith Deployment、Studio、计费和 SLO |

不得把 LangChain agent、Deep Agents middleware 或 LangSmith 平台能力标为 LangGraph core。

## 复刻目标

一个合格的 LangGraph-like harness 至少做到：

- 同一状态 schema 的并发写入只通过 channel/reducer 合并；
- 每个 superstep 只看到上一步已提交状态；
- task 的成功写入、错误、interrupt 和 retry 有稳定身份；
- thread + checkpoint namespace + checkpoint id 可寻址历史；
- resume 不会把 checkpoint 当作普通聊天记录重放；
- stream 可从结构化事件投影 UI，而非解析日志文本；
- checkpoint 内 thread state 与 Store 内跨 thread memory 不混淆；
- core 不具备的安全和部署能力明确标记为设计综合。

## 成熟度

本 dossier 为 implementation-grade：13/13 文件齐全；每个产品 overlay capability 在 [acceptance-tests.md](acceptance-tests.md) 中有同 ID 的可执行 oracle。来源存在不等于能力已验证，只有实现路径与测试证据齐全时才能标记 `verified`。
