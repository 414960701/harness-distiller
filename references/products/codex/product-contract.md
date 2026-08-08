# Codex-like 产品合同

## 目录

1. 文档用途
2. 证据标记
3. 用户可观察合同
4. 核心对象与不变量
5. 表面一致性
6. 性能与可靠性预算
7. 安全合同
8. 非目标
9. 交付定义

## 文档用途

本文把“像 Codex”收敛为可测试的产品行为合同，供实现者、测试者和另一个大模型共同使用。
它描述用户能观察到什么，不复制品牌、私有服务、专有提示词或未公开实现。
详细内部机制分别见 [agent-loop.md](agent-loop.md)、[protocol-state.md](protocol-state.md) 和 [workspace-execution.md](workspace-execution.md)。

## 证据标记

- `公开事实`：可由固定 commit 的公开源码或官方文档验证。
- `设计综合`：为复刻同类能力而给出的推荐实现，不声称与原产品内部完全相同。
- `禁止推断`：无法由公开材料验证，不应写成事实或验收依赖。

## 用户可观察合同

### 启动合同

`公开事实`：公开实现提供交互终端、非交互 exec 和 app-server 等入口，共享核心 runtime。

`设计综合`：任何入口启动时都必须明确以下有效配置：

- 工作目录、工作区根和仓库状态；
- 模型与 provider adapter；
- approval policy 与 sandbox profile；
- 是否允许网络、MCP、skills、hooks 和子代理；
- 会话是新建、恢复还是 fork；
- 协议版本和已协商 capability。

若配置无效，入口必须在创建 turn 前失败，并返回机器可识别错误。

### 任务执行合同

用户提交输入后，系统必须先分配稳定 `thread_id` 与 `turn_id`，再开始模型或工具副作用。
每个 turn 只能进入一个终态：`completed`、`failed`、`interrupted` 或 `cancelled`。
模型可以多次采样并调用多个工具；用户不应被“一条消息等于一次模型调用”限制。
文本、计划、工具活动、命令输出、审批和 diff 必须通过事件逐步可见。
每个逻辑 tool call 恰有一个终态 result；输出 delta 不算终态。
没有待处理工具、steering、压缩或输入时，runtime 才能结束 turn。

### 修改代码合同

读取与搜索不得修改工作区。
文本编辑应优先走结构化 patch；失败必须返回定位信息，不得静默覆盖整文件。
执行命令必须记录规范化命令、cwd、环境策略、sandbox 和退出状态。
系统不得擅自撤销用户原有未提交修改。
变更完成后应尽可能运行与风险成比例的验证，并在最终消息说明未运行项。
大输出可截断模型可见部分，但完整输出应能作为 artifact 查阅。

### 控制合同

`steer` 表示把新输入合入正在运行的 turn，而不是创建平行 turn。
`interrupt` 表示请求当前 turn 尽快停止，不删除已持久化历史。
`cancel tool` 必须向进程树、远程执行租约或子代理向下传播。
输入到达不可安全插入的临界区时，应排队并发出 `queued`，不得丢弃。
审批请求断线后必须可恢复；无人可回答时 headless 模式按显式策略失败。

### 会话合同

用户可以列出、读取和恢复已持久化 thread。
fork 保留原 thread 并创建新标识；rollback 不应偷换成 fork。
conversation rollback 与 workspace rollback 是两个独立能力，界面必须区分。
恢复后 transcript、计划、审批与最终状态必须能由快照加事件重建。
跨版本读取老会话时，要迁移、降级或明确拒绝，不能静默误读。

## 核心对象与不变量

| 对象 | 用户心智模型 | 强制不变量 |
|---|---|---|
| Thread | 一段可恢复的长期任务 | id 稳定；绑定工作区身份；可列出和 fork |
| Turn | 一次意图到终态 | 单终态；可取消；事件有序 |
| Item | 可展示、可审计的内容单元 | 类型明确；生命周期闭合；引用可追踪 |
| Event | 状态变化或增量 | 有序号；可去重；版本化 |
| Tool call | 一次逻辑工具动作 | call id 稳定；一个终态 result |
| Process | 具体 OS/远程执行 | 与逻辑调用分离；可取消；有 exit 状态 |
| Approval | 对动作的授权决定 | scope 明确；deny 优先；不可提升 sandbox |
| Checkpoint | 可恢复一致点 | 能对应 rollout offset 与 workspace 身份 |

同一 thread 默认只有一个持久化写者。
客户端可以有多个，但都通过 runtime command 修改状态。
UI 投影不是业务真相，数据库索引也不是不可变审计源。
模型输出不直接获得权限；所有工具动作都经过 router、policy 和 enforcement。

## 表面一致性

交互 TUI、headless、IDE 和 app-server 必须消费同一 canonical event。
表面可以隐藏不适合展示的字段，但不能改变状态语义。
相同 fixture 在 TUI 与 JSONL 中必须产生等价 item 序列和终态。
headless 使用稳定退出码、stdout/stderr 约定和 JSON/JSONL schema。
客户端重连必须携带最后确认的 event sequence，从下一事件续传。
慢客户端不得阻塞 agent loop；通过有界队列、快照和回放处理背压。

## 性能与可靠性预算

以下为`设计综合`默认 SLO，项目可显式调整：

- 本地 command 接收至 `turn.started`：p95 小于 150 ms；
- runtime 收到模型 delta 至客户端可见：p95 小于 100 ms，不含网络模型延迟；
- interrupt 接收至停止发起新工具：p95 小于 100 ms；
- interrupt 至本地子进程树终止：p95 小于 2 s；
- 10 万事件 thread 的 resume 首屏：使用快照时 p95 小于 2 s；
- 崩溃恢复不得重复已确认的副作用调用；
- event 至少一次投递，客户端按 `event_id` 去重；
- rollout append 在发出完成事件前 durable；
- 单个损坏 artifact 不得导致整个 thread 无法读取。

## 安全合同

approval 决策与 sandbox enforcement 必须是两个模块。
路径在策略判断与执行前都要 canonicalize，并防御 symlink 竞态。
默认 workspace-write 不允许工作区外写入，也不默认允许网络。
模型、仓库说明、工具输出、MCP 和 hook 都是不可信输入，不能提升权限。
danger 模式只能由用户或受管理配置显式启用。
日志、事件和 artifact 必须对 token、密钥和认证头做分层脱敏。
安全能力不可用时必须 fail closed 或明确降级，不能声称仍受保护。

## 非目标

- 不复制 Codex 名称、图标、配色、私有 API、认证和商业服务。
- 不复原或猜测专有 system prompt。
- 不保证逐 token、逐文案或逐像素一致。
- 不将“能运行 shell”误称为完整 coding agent。
- 不用命令黑名单代替 OS/container sandbox。
- 不在 runnable 等级承诺远程执行、企业策略或多客户端协同。
- 不为四个等级维护四套分叉架构；等级是同一合同的增量实现。

## 交付定义

最小可称为 Codex-like 的交付必须同时具备：

1. 可取消的多步 agent loop；
2. thread/turn/item/event 协议与可重放 trace；
3. read、patch、shell 三类工作区工具；
4. approval 与 sandbox 两层控制；
5. 流式 CLI 或 TUI，以及机器可读 headless 输出；
6. 明确的错误、终态和超时；
7. [acceptance-tests.md](acceptance-tests.md) 中 runnable 全部通过。

更高等级按 [recipe.md](recipe.md) 增量升级。
公开事实与源码论断的固定链接集中在 [sources.md](sources.md)。
