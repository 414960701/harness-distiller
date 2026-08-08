# QoderWork 架构蒸馏

> 本文只负责模块边界与故障域；规范对象见 [product-contract.md](product-contract.md)，精确事件与状态见 [protocol-state.md](protocol-state.md)。所有闭源内部结构均为 `inference`。

## 公开可见架构

以下是产品行为，不是对闭源内部实现的声明：

```text
Desktop shell
├── Sidebar: tasks / groups / schedules / extensions / awareness
├── Task surface: transcript / composer / artifact cards
└── Task Monitor: todo / tool calls / Skills & MCP / progress
        │
        ├── Working Folder: one authorized local directory per task
        ├── Capability layer: Skills / Expert Kits / Connectors / Hooks
        ├── Browser or Computer Use
        └── Awareness files and local search index
```

任务是顶层持久化单元。官方文档确认每个任务独立保存会话历史、Working Folder、workspace/model、附件、Task Monitor 和 artifacts；不同任务可以并行，不互相共享这些状态。[New Task](https://docs.qoder.com/qoderwork/new-task)

## 兼容实现的模块边界

下表是本仓库的 `inference`，目标是复现外部合同，不声称等同 QoderWork 内部代码。

| 模块 | 稳定职责 | 不能偷放的职责 |
|---|---|---|
| `desktop-shell` | 多面板窗口、路由、系统托盘、全局快捷键、通知 | Agent loop 与权限判定 |
| `task-service` | Task/Turn/Step 生命周期、并发调度、取消/恢复 | 直接执行工具 |
| `event-store` | 追加式事件、重放、游标、崩溃恢复 | 大文件 artifact 内容 |
| `artifact-store` | 文件元数据、预览、版本、来源步骤、打开/导出 | 会话事实源 |
| `workspace-service` | Working Folder 授权、路径规范化、废纸篓操作 | 绕过策略层的任意文件访问 |
| `tool-broker` | 工具 schema、调用、流式结果、超时、取消 | 自行决定越权 |
| `policy-engine` | 能力授权、风险、审批、sandbox/host 路由 | UI 提示词 |
| `connector-host` | Browser、系统应用、SaaS、MCP 的凭据与会话 | 将原始凭据送入模型 |
| `memory-service` | Awareness 文件、反思任务、检索索引、备份恢复 | 覆盖原始会话历史 |
| `capability-registry` | Skills、Kits、Hooks、Connectors 的发现与版本 | 隐式安装未经同意的扩展 |

## 建议状态模型

```text
Workspace 1─* Task 1─* Turn 1─* Step
                    ├─* ToolCall 1─1 PolicyDecision
                    ├─* ArtifactVersion
                    └─* ContextReference
Task 0─1 WorkingFolderGrant
Task *─* CapabilityBinding
```

关键约束：

- `Task` 保存配置快照，后续全局设置变化不能悄悄改变历史任务的可解释性。
- `Step`、`ToolCall` 与 `ArtifactVersion` 使用稳定 ID；UI 不从自由文本推断进度。
- tool result 大对象进入 artifact/blob store，事件只保留引用、摘要、hash 与 MIME。
- 并行任务使用独立执行上下文；共享目录写入需文件锁、乐观版本或任务级独占声明。
- 任务恢复从最后一个已提交事件继续，不能重放非幂等外部动作。

## 进程与故障隔离

兼容实现至少分离 UI 进程与 Agent/runtime 进程。Browser、Computer Use、文档渲染和第三方 MCP 再各自置于可终止的子进程或容器中。一个连接器崩溃只结束对应 ToolCall，不应拖垮任务列表或丢失 transcript。

官方设置描述了可选的 **Secure Work Environment**：任务在本机独立空间运行、不会触碰真实系统，清理 workspace 文件不影响会话与 artifacts。这只证明产品行为目标；隔离原语、镜像格式和进程边界未公开。[System Settings](https://docs.qoder.com/qoderwork/settings)

## 可借鉴的公开实现

Stars 为 2026-08-08 通过 Shields/GitHub 动态数据取得的近似值，只作候选发现：

| 仓库 | Stars | 借鉴点 |
|---|---:|---|
| [OpenHands](https://github.com/All-Hands-AI/OpenHands) | ~83k | runtime service、事件驱动会话、Web UI、终端/浏览器/diff 分面 |
| [Cline](https://github.com/cline/cline) | ~66k | IDE/CLI Agent、人在回路、MCP、browser、任务持久化 |
| [Continue](https://github.com/continuedev/continue) | ~35k | core 与 VS Code/JetBrains surface 分离、context/tools/policies |
| [browser-use](https://github.com/browser-use/browser-use) | ~108k | 浏览器观察—动作循环与会话封装 |
| [Playwright](https://github.com/microsoft/playwright) | ~94k | 浏览器上下文、定位器、trace、截图与确定性测试 |

复用前必须重新检查许可证、commit、维护状态与安全边界；不要把 Stars 当架构正确性的证明。

## 未公开项

- 模型 provider/router 与提示词编排。
- Task Monitor 的计划生成、动态改写和并行调度算法。
- Secure Work Environment 的 OS/虚拟化实现。
- artifacts 的内部格式、版本与事务协议。
- Awareness 的检索、反思触发与冲突合并算法。
