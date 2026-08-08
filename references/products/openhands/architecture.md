# OpenHands-like 架构规格

## 目录

- [当前仓库边界](#当前仓库边界)
- [目标拓扑](#目标拓扑)
- [模块职责](#模块职责)
- [进程与数据流](#进程与数据流)
- [依赖规则](#依赖规则)
- [实现接口](#实现接口)
- [部署变体](#部署变体)
- [架构验收](#架构验收)

## 当前仓库边界

`公开事实`：当前 OpenHands 产品族不是一个 monolith。

| 仓库/包 | 当前职责 | 不应承担 |
|---|---|---|
| Agent Canvas | React/Electron UI、backend adapter、事件卡、terminal/browser/diff | Agent loop、shell enforcement |
| `openhands-sdk` | Agent、Conversation、Event、Context、Tool、LLM、security API | Web UI、容器 control plane |
| `openhands-tools` | terminal、file editor、grep/glob、browser、planning 等 | 会话持久化 |
| `openhands-workspace` | Docker、Cloud、Apptainer、Remote API workspace | 模型上下文 |
| `openhands-agent-server` | REST/WebSocket、conversation lifecycle、lease、文件存储 | Canvas 本地 UI 状态 |

历史 `OpenHands/OpenHands` 中旧 Python runtime 设计只能作为 legacy 迁移证据；实现 1.41-like 产品以 SDK repo 为 runtime 基准。

## 目标拓扑

```text
Canvas / CLI / SDK Client
          |
   versioned commands
          v
Agent Server ---- auth / lease / subscription
          |
   Conversation actor
     |      |       |
   Agent  EventLog  Context View/Condenser
     |               |
 Tool Registry <--- Prompt/LLM Adapter
     |
 policy -> confirmation -> executor
     |
 Local / Docker / Remote Workspace
```

进程内 SDK 可以省略 Agent Server，但必须复用相同 Conversation、Event 和 Workspace 语义。

## 模块职责

### protocol

- 定义 command、event、Action、Observation、error、state update；
- 生成 Python/TypeScript schema；
- 保存 unknown variant，不让客户端因新 tool 崩溃；
- 与 transport、数据库和 UI 解耦。

### conversation

- 作为每个 conversation 的单写者；
- 管理 execution status、active leaf、budget、iteration、confirmation；
- 追加事件、构造 View、触发 autosave；
- 提供 run/arun、pause/interrupt、navigate、fork、condense。

### agent

- 初始化 system event 与 tool specs；
- 调用模型并将 response dispatch 为 message/action；
- 并行执行合法 action，稳定合并 observation；
- 处理 Finish、stuck、context overflow 和 typed error。

### context

- 从 active branch 生成模型 View；
- 保证 tool loop、batch 和 condensation 原子性；
- 将静态 prompt 与动态 workspace/secret 描述分层；
- condenser 只改变后续模型投影，不删原事件。

### tool-runtime

- registry 维护 name、schema、executor、risk metadata；
- router 验证 Action discriminated union；
- MCP、client tool、skill/plugin 最终都适配成 ToolDefinition；
- execution receipt 与 Observation 一一对应。

### workspace

- 定义 command/file/git/pause/resume 能力；
- provider 返回 immutable runtime identity 与 capability；
- local 明确为宿主能力；Docker/remote 负责 lifecycle；
- executor 不读取 Canvas store 或 HTTP request object。

### agent-server

- 认证、conversation CRUD、event history、WebSocket、confirmation；
- 获取/续租/释放 lease，lease 丢失后 fence writer；
- 维护 runtime registry 和 workspace session；
- 提供限流、分页、健康和 OpenAPI。

### surfaces

- Canvas/CLI 只提交 command、消费 snapshot+events；
- terminal/browser/files/diff 是 canonical event/workspace API 投影；
- optimistic UI 有本地 pending id，收到 durable event 后 reconcile；
- 断线后清空 transport 状态，但保留 durable projection checkpoint。

## 进程与数据流

启动：client 选择 backend → server provision/attach workspace → 获取 lease → load state/events → 发 snapshot → 订阅增量。

运行：message command → append MessageEvent → status running → build View → LLM → ActionEvent → hooks/security/confirmation → executor → ObservationEvent → 下一 step 或终止。

恢复：验证 workspace identity → 获取新 fencing token → 加载 base state → 扫描 EventLog → 解析 active leaf → 修复可安全修复的 orphan → 重建 View → 从 last ack 续传。

## 依赖规则

- `protocol` 不依赖 SDK 实现、server 或 surface。
- `conversation` 依赖 Agent/Context/Workspace 接口，不依赖 FastAPI/React。
- `tool-runtime` 不直接决定用户授权，也不直接启动未经 enforcement 的命令。
- `workspace provider` 不解析模型响应。
- `agent-server` 不复刻 agent loop；它持有和调度 Conversation。
- `Canvas` 不读取 conversation 文件目录或持久化 Python 对象。
- `eval` 用公共 SDK/协议入口，禁止测试专用后门改变行为。

## 实现接口

```python
class ConversationPort(Protocol):
    def append_user(self, content: Message) -> EventId: ...
    async def run(self, cancel: CancellationToken) -> RunOutcome: ...
    def resolve_confirmation(self, request_id: str, decision: Decision) -> None: ...
    def snapshot(self) -> ConversationSnapshot: ...

class WorkspacePort(Protocol):
    identity: WorkspaceIdentity
    capabilities: frozenset[str]
    async def execute(self, request: CommandRequest) -> CommandReceipt: ...
    async def close(self) -> None: ...

class EventRepository(Protocol):
    def append(self, expected_head: EventId | None, event: Event) -> Offset: ...
    def branch(self, leaf: EventId | None) -> list[Event]: ...
    def scan(self, after: Offset, limit: int) -> Page[Event]: ...
```

所有写接口带 `conversation_id`、`writer_token` 和 `idempotency_key`；本地单进程实现也保留字段，便于原位升级。

## 部署变体

| 变体 | 进程 | 适用 | 限制 |
|---|---|---|---|
| SDK local | 一个 Python 进程 | 测试、嵌入 | 无远程订阅，local 非 sandbox |
| Canvas desktop | Electron + local server/runtime | 个人桌面 | 宿主资源边界需明确 |
| Self-hosted | Web + agent-server + Docker | 团队 | 需外部 durable store/secret |
| Remote runtime | control plane + runtime provider | 大规模/隔离 | 必须 lease、fencing、迁移 |

## 架构验收

- 在不启动 Canvas 的情况下 SDK fixture 可完成完整任务。
- 在不导入 Python private class 的情况下 TypeScript 客户端可投影全部事件。
- Local 与 Docker workspace 跑同一 conformance suite。
- server 崩溃后由 EventLog 和 state 恢复，不依赖内存 store。
- UI 重连后 snapshot+events digest 等于连续在线结果。
- 双 writer 中只有有效 fencing token 能提交事件或副作用 receipt。

实现细节见 [protocol-state.md](protocol-state.md)、[agent-loop.md](agent-loop.md) 与 [persistence-recovery.md](persistence-recovery.md)。
