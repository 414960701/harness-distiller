# OpenHands-like 产品合同

## 目录

- [用途与证据](#用途与证据)
- [用户可观察行为](#用户可观察行为)
- [对象与不变量](#对象与不变量)
- [运行表面](#运行表面)
- [可靠性与安全](#可靠性与安全)
- [非目标](#非目标)
- [交付定义](#交付定义)

## 用途与证据

本文把“复刻 OpenHands”收敛为可测试的行为，不复制名称、商标、私有服务或隐藏提示词。

- `公开事实`：固定 commit 源码或测试可验证；
- `设计综合`：为完整独立产品补出的协议与生产约束；
- `禁止推断`：Cloud 私有实现、内部数据和未公开策略。

逐项证据见 [sources.md](sources.md)。

## 用户可观察行为

### 创建与连接

- 用户可选 workspace、模型/profile、agent、tool preset、confirmation mode 和可选 backend。
- 创建成功后返回稳定 `conversation_id`，并能通过 SDK、REST/WebSocket、Canvas 或 CLI 接入。
- server 在接受新 writer 前获取 conversation lease；冲突必须返回明确错误，不能双跑。
- runtime 尚未就绪时显示阶段与可重试状态，不把空白界面当成功。
- 配置错误在首次模型调用前失败，并输出机器可解析 code。

### 运行任务

- 用户消息追加为 Event 后，Conversation 从 idle 进入 running。
- Agent 可以重复采样；每轮产生零个或多个 ActionEvent，工具回写 ObservationEvent。
- 并行 tool call 按逻辑 action id 配对；事件展示顺序可稳定，实际执行允许并行。
- Finish action、达到预算/迭代上限、stuck、错误、pause 或 interrupt 都进入显式状态。
- 每个 action 恰有一个匹配 observation、拒绝或合成错误，不能留下模型无法继续的孤儿调用。

### 人机确认

- Risk Analyzer 给 action 风险分类；ConfirmationPolicy 决定是否等待。
- 等待时 action 已 durable、未执行，Canvas 显示规范化目标和风险。
- approve、reject 和超时必须闭合请求；拒绝转成模型可见 Observation。
- 更改 confirmation policy 只影响后续决策，不追溯执行已有 action。
- 审批不能扩大 workspace enforcement、网络或 secret 权限。

### 工作区与工具

- workspace 提供命令、上传/下载、git change/diff、pause/resume 的统一 adapter。
- 本地模式明确标注“宿主执行”；容器/远程模式展示隔离 provider 与 runtime id。
- Terminal、FileEditor/apply_patch、glob/grep、browser、planning、MCP、skill/plugin 保留 typed Action/Observation。
- 命令结果包含 stdout、stderr、exit code、timeout；大输出产生截断标记或 artifact。
- 文件与 git diff 必须限定到 workspace identity，不能因 UI 参数绕过 backend 校验。

### 会话与历史

- conversation state 与 event log 可恢复；active branch 由 leaf event 指定。
- navigate 改变活动事件分支；fork 创建新 conversation，不修改父历史。
- condenser 用摘要事件替换模型视图中的旧区间，但原始事件仍可审计。
- UI 历史分页、实时事件和 reconnect 后的补拉合并不得重复卡片。
- 恢复后的模型视图必须保持 tool action/observation 和 condensation 批次原子性。

## 对象与不变量

| 对象 | 作用 | 强制不变量 |
|---|---|---|
| Conversation | 长期任务容器 | id 稳定；同一时刻一个 writer；可恢复/fork |
| Run | 一次 `run/arun` | 有预算与迭代上限；明确停止原因 |
| Event | 不可变事实 | id 唯一；source 明确；parent 可解析 |
| Active branch | 当前模型历史 | leaf 可移动；旧事件不改写 |
| ActionEvent | 模型工具意图 | tool_call_id 稳定；schema 已验证 |
| ObservationEvent | 工具结果 | 引用 action/tool_call；成功失败可区分 |
| View | 给模型的投影 | 可由 active branch 重建；保持工具环原子性 |
| Workspace | 执行边界 | identity 稳定；能力显式；资源可清理 |
| Confirmation | 人机授权 | 风险、目标、decision durable；一次闭合 |
| Lease | writer 所有权 | 有 expiry/fencing；丢失后禁止提交 |

事件是事实源，Canvas Zustand store、聊天分组、browser store、diff 和 terminal 都是投影。

## 运行表面

### SDK

提供构造 Agent、Conversation、Workspace、LLM、Tool 的 typed API；同步与异步入口语义等价。

### Agent Server

提供创建/恢复 conversation、消息、run/pause、事件分页、WebSocket、confirmation、workspace 与 git API。

### Canvas

提供 conversation 列表、chat、工具事件组、terminal、browser、files/diff、模型/profile、settings 和 backend 状态。

### CLI/headless

交互 CLI 消费同一 canonical event；headless 输出 JSONL，退出码与 conversation 终态对应。

任一表面不能直接写 EventLog 或调用宿主 shell；必须走 runtime command/tool router。

## 可靠性与安全

`设计综合`默认门槛：

- command 接收到 state running：本地 p95 < 200 ms；
- Event durable 到 WebSocket 可见：p95 < 150 ms；
- pause/interrupt 接收后不再派发新 action：p95 < 100 ms；
- async interrupt 后本地工具进程树清理：p95 < 2 s；
- 10 万 event conversation 用分页/快照首屏：p95 < 2 s；
- reconnect、重复 event、迟到 observation 不改变最终 projection digest；
- lease 丢失的旧 writer 无权写入；
- secret 不进入事件、日志、遥测或浏览器状态；
- sandbox 不可用时 fail closed 或显式降级为 local-unsafe。

## 非目标

- 不复制 OpenHands 名称、logo、配色或 Cloud 商业 API。
- 不猜测系统提示词、私有 eval 数据或云调度算法。
- 不把旧 monolith 目录当作当前 1.41 SDK 架构。
- 不把本地命令执行、风险提示或用户点击批准称为 sandbox。
- 不要求逐像素、逐文案、逐 token 一致。
- 不为四级成熟度建立四套 fork；所有升级保留同一事件和 workspace contract。
- 不承诺任意模型都能完成软件工程任务；验收使用 scripted model 与固定 fixture。

## 交付定义

`runnable` 至少具备：事件树 Conversation、可取消 agent loop、并行 Action/Observation、workspace adapter、typed tools、SDK 与 headless 表面。

`usable` 再具备：condenser、confirmation/security、持久化恢复、Agent Server、WebSocket 和 Canvas 核心体验。

`productive` 再具备：容器 runtime、browser、skills/plugins/MCP、子会话、观测与 eval。

`polished` 再具备：远程 lease/fencing、强 sandbox、secret/network policy、多租户迁移和全套故障注入。

只有 [acceptance-tests.md](acceptance-tests.md) 对应等级全部通过，capability 才可标记 `verified`。
