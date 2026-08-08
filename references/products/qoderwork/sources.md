# QoderWork 证据与来源账本

> 检索日期：2026-08-08。QoderWork 生产客户端未见完整公开源码；本 dossier 严格区分 `official-doc`、`behavior`、`public-reference`、`inference` 与 `unknown`。

## 目录

- [证据标签](#1-证据标签)
- [官方文档索引](#2-官方文档索引)
- [声明到来源映射](#3-声明到来源映射)
- [明确属于 inference 的实现](#4-明确属于-inference-的实现)
- [unknown 清单](#5-unknown-清单)
- [可借鉴开源实现](#6-可借鉴开源实现)
- [证据更新流程](#7-证据更新流程)
- [实现者引用规则](#8-实现者引用规则)

## 1. 证据标签

| 标签 | 含义 | 可以支持 | 不能支持 |
|---|---|---|---|
| `official-doc` | Qoder 官方文档明确陈述 | 产品功能与操作合同 | 未描述的内部架构 |
| `behavior` | 公开 UI/可重复黑盒行为 | 用户可见状态和结果 | 数据库、提示词、算法 |
| `public-reference` | 其他开源项目实现 | 一种可行工程方法 | QoderWork 实际采用该方法 |
| `inference` | 为复现外部合同提出的设计 | 兼容实现蓝图 | “官方内部就是如此” |
| `unknown` | 无足够证据 | 明确研究边界 | 肯定或否定结论 |

## 2. 官方文档索引

1. [Introduction](https://docs.qoder.com/qoderwork/introduction)：产品定位与工作类型，标签 `official-doc`。
2. [Interface Guide](https://docs.qoder.com/qoderwork/ui-overview)：Sidebar、任务会话与 Task Monitor，标签 `official-doc/behavior`。
3. [New Task](https://docs.qoder.com/qoderwork/new-task)：任务创建、workspace/model/Working Folder 与任务隔离，标签 `official-doc`。
4. [Task Management](https://docs.qoder.com/qoderwork/task-management)：Draft、Scheduled、Recent、Groups、搜索、归档与导出，标签 `official-doc`。
5. [Viewing Results](https://docs.qoder.com/qoderwork/file-management)：Working Folder、artifact、系统打开与 trash，标签 `official-doc`。
6. [Skills](https://docs.qoder.com/qoderwork/skills)：`SKILL.md`、目录、自动/显式触发与支持文件，标签 `official-doc`。
7. [Expert Kits](https://docs.qoder.com/qoderwork/expert-kits)：快捷命令、数据连接与知识能力组合，标签 `official-doc`。
8. [Connectors](https://docs.qoder.com/qoderwork/connectors)：Browser、市场连接器、启用和授权，标签 `official-doc`。
9. [Computer Use](https://docs.qoder.com/qoderwork/computer-use)：屏幕观察、鼠标键盘、系统权限与 Browser 优先建议，标签 `official-doc`。
10. [App Snapshots](https://docs.qoder.com/qoderwork/app-snapshots)：前台应用截图与可读文本进入 composer，标签 `official-doc`。
11. [Awareness](https://docs.qoder.com/qoderwork/memory)：用户画像、长期/短期记忆、本地索引、备份、恢复和清除，标签 `official-doc`。
12. [Hooks](https://docs.qoder.com/qoderwork/hooks)：配置、PreToolUse、matcher、退出码阻断与重启要求，标签 `official-doc`。
13. [System Settings](https://docs.qoder.com/qoderwork/settings)：Computer Use、系统权限、Secure Work Environment 与清理，标签 `official-doc`。
14. [Scheduled Tasks](https://docs.qoder.com/qoderwork/scheduled-tasks)：计划任务的创建与管理，标签 `official-doc`。

## 3. 声明到来源映射

| 声明 | 来源 | 标签 | 置信度 |
|---|---|---|---|
| Task 是独立持久单元且可并行 | New Task | official-doc | 高 |
| 三栏为 Sidebar/Conversation/Monitor | Interface Guide | official-doc/behavior | 高 |
| Task Monitor 展示 todo、工具、Skills/MCP | Interface Guide/New Task | official-doc | 高 |
| 每 Task 最多一个 Working Folder | Viewing Results | official-doc | 高 |
| 删除默认进入系统废纸篓 | Viewing Results | official-doc | 高 |
| 输出以 artifact card 展示 | Viewing Results | official-doc/behavior | 高 |
| Browser 使用结构化网页自动化 | Connectors | official-doc | 高 |
| 网页优先 Browser 而非 Computer Use | Computer Use | official-doc | 高 |
| Computer Use 需要系统辅助权限 | Computer Use | official-doc | 高 |
| App Snapshot 含截图和可读文本 | App Snapshots | official-doc | 高 |
| Skills 以 `SKILL.md` 为核心 | Skills | official-doc | 高 |
| Expert Kit 组合多类能力 | Expert Kits | official-doc | 高 |
| Hook 可在 PreToolUse 阻断 | Hooks | official-doc | 高 |
| Awareness 可备份、恢复和清除 | Awareness | official-doc | 高 |
| 存在 Scheduled tasks | Scheduled Tasks/Task Management | official-doc | 高 |

## 4. 明确属于 inference 的实现

- 追加式 event store、event envelope 和 reducer 投影。
- UI、runtime、browser、computer-use 与 MCP 的进程隔离方式。
- weighted fair queue、Step DAG 和并行 path lease。
- Working Folder 的 dirfd/openat、device identity 与 canonical resolver。
- ArtifactProduced/ArtifactValidated 两阶段状态和 validator receipt。
- Browser 的 profile/container 结构、下载隔离与 origin policy。
- Awareness 的候选/确认分层、向量索引删除 oracle。
- Schedule 的 dedupe key、misfire policy 与 capability snapshot。
- secret broker、全链路脱敏和网络默认拒绝策略。
- TaskConfigSnapshot、checkpoint、write intent 和 action receipt。

这些设计用于让复刻产品安全、可恢复、可测试；不得在对外文案中写成 QoderWork 官方架构。

## 5. unknown 清单

- QoderWork 使用的模型 provider、router、上下文窗口和 system prompt。
- 计划是否为 DAG、何时重规划、是否存在多 Agent。
- Task Monitor 的真实事件协议与数据库 schema。
- Secure Work Environment 使用 VM、容器、macOS sandbox 还是其他技术。
- Artifact 的内部版本、事务、预览和校验实现。
- Browser 是否共享/导入何种 Chromium profile，凭据如何封装。
- Awareness 的 embedding 模型、排序、反思触发和冲突合并。
- scheduled tasks 在应用退出后的后台承载方式和外发审批策略。
- Skills 自动选择算法、Expert Kit 包格式和内部版本解析。

## 6. 可借鉴开源实现

| 项目 | 链接 | 借鉴点 | 使用边界 |
|---|---|---|---|
| OpenHands | [GitHub](https://github.com/All-Hands-AI/OpenHands) | runtime、事件驱动会话、browser/terminal UI | 核许可证与当前 commit |
| Cline | [GitHub](https://github.com/cline/cline) | 人在回路、MCP、Browser、任务持久化 | IDE 场景需改为桌面工作台 |
| Continue | [GitHub](https://github.com/continuedev/continue) | core/surface 分离、context/tools | 不照搬代码编辑器 IA |
| Open Interpreter | [GitHub](https://github.com/OpenInterpreter/open-interpreter) | 本地 Computer 能力与审批模式 | 加强隔离和桌面状态 |
| browser-use | [GitHub](https://github.com/browser-use/browser-use) | 浏览器观察—动作 loop | 不授予文件/secret 默认权 |
| Playwright | [GitHub](https://github.com/microsoft/playwright) | Browser context、locator、trace | 登录态和下载需独立治理 |
| LangGraph | [GitHub](https://github.com/langchain-ai/langgraph) | durable graph、checkpoint、interrupt | 产品状态仍需自定义合同 |
| Temporal | [GitHub](https://github.com/temporalio/temporal) | durable workflow、retry、schedule | 复杂度较高，可只借合同 |
| MCP SDK | [GitHub](https://github.com/modelcontextprotocol) | typed external tools | server 不天然可信 |

Stars 会变化，不作为选型或正确性的证据。复用任何代码前都应记录 repo、commit、许可证、维护状态与安全审查结果。

## 7. 证据更新流程

1. 每次发布前重新访问官方链接并记录 retrieved date。
2. 把新声明加入“声明到来源映射”，禁止只在正文散落链接。
3. 官方文档与实际行为冲突时，同时保留两条证据并标版本/平台。
4. 只有可重复观察才能从 inference 提升为 behavior。
5. 只有官方明确说明才能提升为 official-doc。
6. 新发现源码时先证明其与生产 QoderWork 的对应关系，不能因仓库名相似就标公开实现。
7. 删除失效来源前保留标题、URL、访问日期和替代来源。

## 8. 实现者引用规则

- 写“QoderWork 支持……”时必须能指向官方来源或公开行为。
- 写“建议实现……”或“兼容实现……”时标 `inference`。
- 不确定处直接写 `unknown`，不要用高星开源项目补成产品事实。
- UI oracle 可要求行为一致，但不能声称底层算法一致。
- 安全实现可以强于公开产品，只要不破坏外部合同，并应标为本仓库加固项。
