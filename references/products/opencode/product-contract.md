# OpenCode-like 产品合同

## 目录

- [用户承诺](#用户承诺)
- [领域对象](#领域对象)
- [行为合同](#行为合同)
- [失败语义](#失败语义)
- [非目标](#非目标)
- [证据判定](#证据判定)

## 用户承诺

用户在项目目录启动一个本地 coding agent，可从 TUI、Web、Desktop、IDE 或 SDK 创建 session、发送 prompt、观察流式 reasoning/text/tool、处理权限问题、取消或恢复。多个 client 看到同一 server 真值；客户端断线不应把已持久化 session 变成另一条历史。

默认执行发生在用户机器和选定 workspace。产品调用用户配置的模型 provider；只有显式 share 才把会话投影同步到分享服务。若实现增加远端执行，必须另建 execution location 合同。

## 领域对象

```yaml
Session:
  id: stable-id
  project_id: stable-id
  workspace_id: stable-id|null
  parent_id: session-id|null
  directory: absolute-path
  title: string
  agent: string|null
  model: provider/model/variant|null
  status: idle|busy|retry|awaiting_permission|cancelled|failed
  created_at: timestamp
  updated_at: timestamp
```

```yaml
Message:
  id: stable-id
  session_id: session-id
  role_or_type: user|assistant|system|shell|compaction|agent-switched|model-switched
  parts: [Part]

Part:
  id: stable-id
  type: text|reasoning|file|tool|step-start|step-finish|snapshot|patch|retry|compaction|subtask
  state: typed-payload

ToolState:
  status: pending|running|completed|error
  input: object
  output: object|null
  started_at: timestamp|null
  ended_at: timestamp|null
```

Event envelope 至少含 `id,type,data,location`；durable event 另含 `aggregateID,seq,version`。delta 可 live-only，但 completed payload 必须足以校正丢 delta 的 client。

## 行为合同

### Server 与 client

1. runtime 先启动 server，再让 TUI/其他表面使用同一 API。
2. server 默认绑定 loopback；非 loopback 必须提示认证风险。
3. OpenAPI schema 是 SDK 与 route 的共同合同，不能手写两份漂移类型。
4. snapshot/list endpoint 提供初始状态，SSE 提供之后的变化；gap 必须 resync。
5. client 只能发 command/request，不能直写 SQLite 或伪造 tool completion。

### Session 与循环

1. 同一 session 只有一个 foreground drain；第二个 prompt 按 delivery 规则排队、steer 或冲突。
2. 每个 step 固定 model、agent、tool schema 和 system/context snapshot。
3. tool call 从 pending 到 running，再唯一进入 completed/error。
4. provider retry 不得重复已经完成的本地副作用。
5. cancel 终止模型流、未完成命令与派生后台任务，并产生确定终态。
6. context overflow 触发 compaction 或明确失败，不静默删除最新用户约束。

### 工具与 workspace

1. root/directory 是执行权威；所有相对路径由 server 解析。
2. edit/write/apply-patch 在写前检查路径、权限和 stale input。
3. shell/PTY 的 cwd、env、pid、offset、exit 和 cancel 可观察。
4. MCP tool 与 plugin/custom tool 也走 tool state、permission、截断和事件路径。
5. LSP 失败只能降级诊断/符号能力，不能阻止基础 read/edit/shell。

### Permission 与 share

1. permission rule action 为 allow/ask/deny，按匹配优先级确定，deny 不可由模型覆盖。
2. `once` 只解决一个 request；`always` 产生可审计 scope，不等于全局 root 授权。
3. permission 只决定是否尝试执行；sandbox 决定 syscall 是否能越界，两者必须分开。
4. share 默认 manual；disabled 时 UI、API、环境变量都不能绕过。
5. unshare 要清除远端可访问性并更新本地记录；网络失败不能先显示成功。

## 失败语义

| 故障 | 必须结果 | 禁止结果 |
|---|---|---|
| provider 429/5xx | 有上限、尊重 retry-after 的重试 | 无限循环或重复工具 |
| provider stream 断开 | assistant failed/retry，保留已完成 part | completed 假象 |
| tool schema 错误 | tool error 回馈模型 | 猜参数执行 |
| permission reject | rejected result，session 可继续 | 以空输出伪成功 |
| client 断线 | server 继续或按策略 cancel，重连 resync | UI 状态成为真源 |
| SQLite 写失败 | 当前转移失败且可诊断 | 事件已发但状态未提交 |
| MCP/LSP 退出 | 分类错误、可重连、核心工具可用 | 整个 server 崩溃 |
| share 上传失败 | 本地仍可用，share 未成功 | 泄露 secret 或假 URL |

## 非目标

- 不复制 OpenCode 名称、图标、提示词或托管账号系统。
- 不把当前 v1/v2 迁移的重复模块照搬成永久架构。
- 不宣称实现 OpenCode Zen/Go、企业 SSO 或 share 后端。
- 不把 remote client connection 说成 remote execution。
- 不把 permission prompt、路径字符串检查或 Electron renderer isolation 说成 OS sandbox。
- 不要求 Go、Rust 或 Tauri；固定基线事实是 TypeScript/Bun/Effect 与 Electron。

## 证据判定

产品事实见 [sources.md](sources.md)。canonical event、idempotency receipt、gap resync 和迁移门禁是为可复刻性增加的 `inference`。只做 chat UI + shell、只包 SDK、或每个表面各自维护会话，都不满足本合同。
