# QoderWork-like 产品合同

> 本文定义可被另一模型直接实现与验收的外部合同。`confirmed` 表示官方文档确认的行为；`inference` 表示为复现行为而设计的兼容实现，不代表 QoderWork 内部代码。

证据逐条登记在 [sources.md](sources.md)；没有官方来源的内部机制一律不得升级为产品事实。

## 目录

- [产品边界](#1-产品边界)
- [顶层对象](#2-顶层对象)
- [Task 隔离合同](#3-task-隔离合同)
- [三栏状态合同](#4-三栏状态合同)
- [Artifact-first 合同](#5-artifact-first-合同)
- [能力选择合同](#6-能力选择合同)
- [Scheduled task 合同](#7-scheduled-task-合同)
- [终态定义](#8-终态定义)
- [黑盒兼容 oracle](#9-黑盒兼容-oracle)
- [非目标](#10-非目标)

## 1. 产品边界

- `confirmed`：产品是以 Task 和本地成品为中心的桌面 Agent 工作台。
- `confirmed`：Task 独立保存会话、Working Folder、workspace/model、附件、Task Monitor 与 artifacts。
- `confirmed`：多个 Task 可并行运行，用户可从任务列表切换和管理。
- `confirmed`：主界面由 Sidebar、Task conversation、Task Monitor 三个状态区域构成。
- `confirmed`：结果文件以 artifact card 呈现，并可从系统应用打开。
- `confirmed`：Browser、Computer Use、Skills、Expert Kits、MCP、Hooks、Awareness 和 scheduled tasks 属于产品能力面。
- `inference`：实现不要求复制品牌、专有模型、内部提示词或像素级视觉。
- `inference`：兼容目标是同类任务在操作路径、权限边界、状态反馈和交付物上“大差不差”。

## 2. 顶层对象

| 对象 | 必须字段 | 生命周期所有者 | 用户可见性 |
|---|---|---|---|
| `Task` | id、title、status、config snapshot | task service | Sidebar 与主区域 |
| `Turn` | id、task_id、role、content refs | conversation service | transcript |
| `Step` | id、kind、status、attempt | agent runtime | Task Monitor |
| `ToolCall` | id、tool、args digest、decision | tool broker | Task Monitor 详情 |
| `Artifact` | id、path、mime、version、validation | artifact service | artifact card |
| `WorkingFolderGrant` | root、scope、granted_at、revocation | policy engine | composer 与权限页 |
| `Schedule` | trigger、timezone、task template、enabled | scheduler | Scheduled 列表 |
| `AwarenessRecord` | type、content、provenance、status | memory service | Awareness 管理页 |

## 3. Task 隔离合同

1. 每个运行任务拥有独立事件流、上下文缓存、取消令牌和工具调用命名空间。
2. 任务 A 不得读取任务 B 的 transcript、附件、临时文件或未发布 artifact。
3. 共享同一 Working Folder 不等于共享 Task 上下文。
4. 两个任务写同一路径时必须通过版本比较、文件锁或显式独占声明解决冲突。
5. 一个 Task 最多绑定一个 Working Folder；重新绑定生成新 grant，旧 grant 立即失效。
6. 切换 UI 当前任务不得暂停后台运行任务。
7. 任务崩溃不得拖垮 Sidebar、其他任务或 artifact store。
8. 全局设置变化不得静默改写历史任务的配置快照。

## 4. 三栏状态合同

| 区域 | 稳定状态 | 最小内容 | 禁止行为 |
|---|---|---|---|
| Sidebar | draft/scheduled/running/waiting/completed/failed/archived | 标题、状态、最近活动 | 只靠颜色表达状态 |
| Conversation | empty/composing/streaming/settled | turns、composer、artifact cards | 把工具日志伪装成自然语言 |
| Task Monitor | collapsed/planning/executing/attention/terminal | todo、step、tool、能力来源 | 从模型文本猜测进度 |

- Sidebar 是任务导航事实源，不直接驱动运行时状态。
- Conversation 是用户意图与交付物表面，不承担完整审计日志。
- Task Monitor 必须订阅结构化事件，能定位当前 Step、工具、Skill/MCP 和权限等待。
- 三栏使用同一 `task_id` 和单调递增 `event_seq` 消除竞态。

## 5. Artifact-first 合同

- 生成文件先进入 `produced`，格式解析和产品级验证通过后才进入 `ready`。
- card 至少显示名称、类型、版本、大小、落盘位置、来源 Step 和验证状态。
- `ready` 不能仅由文件存在或模型自报完成触发。
- 无效文件仍保留为 `invalid` card，附诊断和可重试动作。
- 覆盖原文件必须产生新版本或可恢复副本。
- artifact 内容不塞入事件流；事件保存 URI、hash、MIME 和摘要。
- 用户打开、导出、重命名或移入废纸篓均生成可审计事件。

## 6. 能力选择合同

- 网页有可靠 DOM/ARIA 时优先 Browser。
- 只有缺少结构化接口或必须操作原生 GUI 时才选择 Computer Use。
- Computer Use 的每个动作绑定目标应用与窗口，焦点漂移即暂停。
- Skill 提供过程知识，Kit 组合能力，MCP 提供外部工具，Hook 提供确定性生命周期约束。
- 任何扩展都不能扩大 Working Folder、secret 或外发权限。
- Awareness 只能作为带来源的 context item，不能覆盖用户本轮指令。

## 7. Scheduled task 合同

- `confirmed`：用户可创建、查看和管理 scheduled tasks。
- `inference`：Schedule 保存时区、触发规则、任务模板、能力快照和通知目标。
- `inference`：无人值守任务只可使用预授权的低/中风险能力。
- `inference`：外发、发布、Computer Use 或新域名访问转为 `waiting_for_approval`。
- 同一 Schedule 的重复触发必须使用幂等键去重。
- 错过触发时间的补跑策略必须明确为 skip、run_once 或 catch_up。

## 8. 终态定义

- `completed`：目标交付物通过验证，所有必需 Step 终结，用户可打开结果。
- `partial`：存在可用交付物，但某些非必要结果失败；需明确列出缺口。
- `failed`：无满足合同的交付物，且自动恢复策略已耗尽。
- `cancelled`：已停止新动作，运行中调用已撤销或进入安全收尾。
- `waiting`：明确指出等待的权限、用户输入、认证或外部条件。

## 9. 黑盒兼容 oracle

1. 同时运行三个任务，切换界面不影响后台进度，任何 transcript 不串线。
2. 拒绝 Working Folder 外读取，即使通过符号链接、`..` 或 Skill 请求。
3. 生成故意损坏的 `.xlsx` 时 card 显示 invalid，而不是 completed。
4. Browser 可完成的表单任务不申请 Screen Recording 或 Accessibility。
5. Computer Use 聚焦错误窗口时动作停止并显示最后观察帧。
6. 清除 Awareness 后，原文、索引和后续检索结果均不再含被删事实。
7. Hook 以阻断码拒绝工具时，ToolCall 与 Task Monitor 显示确定性原因。
8. 定时任务重启后不重复发送已提交的外部消息。

## 10. 非目标

- 不要求复刻 QoderWork 的品牌资产、精确文案、私有模型和商业服务。
- 不把 Qoder Desktop 的代码 Quest、worktree 或 IDE 体验混入本合同。
- 不声明本文的进程、数据库或调度设计是 QoderWork 的真实内部实现。
