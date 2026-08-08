# QoderWork 实现级产品索引

## 定位

QoderWork 是以“任务与成品交付”为中心的桌面 Agent 工作台，而不是以源码编辑器为中心的 IDE。公开界面把一次工作建模为独立任务：任务拥有自己的会话、工作目录、workspace/model 选择、附件、Task Monitor 与 artifacts；多个任务可并行运行。

不要把它与 Qoder Desktop 的 Quest/代码工作树能力混为一谈。本目录只蒸馏 QoderWork：本地文件、文档/表格/演示文稿等成品、浏览器与桌面应用连接、记忆、定时任务和工作台体验。

## 证据状态

- `status`: implementation-ready dossier
- `retrieved`: 2026-08-08
- 公开实现：低；未发现可对应生产客户端的完整公开源码。
- 主要证据：Qoder 官方文档与可见产品行为，记为 `official-doc` / `behavior`。
- 内部 Agent loop、进程拓扑、模型路由、索引算法、Secure Work Environment 的隔离技术均未公开；本目录涉及这些内容时记为 `inference`。

## 已确认的产品合同

1. 左侧栏管理 Drafts、Scheduled tasks、Recent、Groups 与扩展；中间是任务会话；运行时右侧出现 Task Monitor。
2. 新任务按“目标 → workspace → model → working folder → send”创建；任务间上下文与 artifacts 隔离。
3. Working Folder 是显式授权的单目录边界；任务可读其全部子目录，跨目录需再次授权；删除请求默认移入系统废纸篓。
4. Task Monitor 展示待办、工具调用、使用过的 Skills/MCP；输出文件以 artifact card 出现在会话中并落到工作目录。
5. Browser Connector 复用 Chromium 登录态并进行结构化网页操作；Computer Use 通过截图与系统辅助功能控制 GUI；App Snapshots 捕获前台应用截图与可读文本。
6. Awareness 维护 `USER.md`、`MEMORY.md`、短期记忆目录与本地搜索索引，并提供备份、恢复与清除。
7. Skills 以 `~/.qoderwork/skills/<name>/SKILL.md` 为核心，可带支持文件；Expert Kits 将快捷命令、数据连接与知识技能打包。
8. Hooks 以确定性脚本介入 Agent 生命周期，可在工具执行前阻断危险操作。

## 推荐阅读顺序

另一个大模型应按以下顺序读取，而不是只读 `recipe.md` 后直接生成代码：

1. [sources.md](sources.md)：先建立事实、行为、公开参考、推断与未知项的证据边界。
2. [product-contract.md](product-contract.md)：锁定需要复刻的外部合同、对象和黑盒 oracle。
3. [experience.md](experience.md)：理解三栏工作台、核心旅程和必须呈现的失败态。
4. [architecture.md](architecture.md)：决定模块与故障域，不把 UI、loop、工具和策略耦合。
5. [protocol-state.md](protocol-state.md)：实现 Task/Step/ToolCall/Artifact schema、事件和三栏投影。
6. [agent-loop.md](agent-loop.md)：实现计划、上下文、能力路由、调度和完成门。
7. [workspace-execution.md](workspace-execution.md)：实现 Working Folder、并发写、worker 与 artifact 管线。
8. [context-tools.md](context-tools.md)：细化上下文来源、Skills/Kits/MCP 与 Awareness 装配。
9. [safety-runtime.md](safety-runtime.md)：施加不可被模型或扩展绕过的安全合同。
10. [persistence-recovery.md](persistence-recovery.md)：补齐 crash、幂等、迁移、清除和定时恢复。
11. [recipe.md](recipe.md)：按四级增量装配，不另造一套等级架构。
12. [acceptance-tests.md](acceptance-tests.md)：用黑盒和 kill-point 证据决定是否可发布。

## 文档职责与去重边界

| 文档 | 唯一事实源 | 不负责 |
|---|---|---|
| `product-contract` | 外部兼容与终态定义 | 内部模块实现 |
| `architecture` | 模块/进程边界与公开实现映射 | 逐事件 schema |
| `protocol-state` | 数据结构、事件、状态机、UI 投影 | 产品视觉细节 |
| `agent-loop` | 计划—执行—观察循环 | 具体文件系统原语 |
| `workspace-execution` | grant、文件、worker、artifact 管线 | 长期记忆排序 |
| `context-tools` | context item 与能力语义 | 权限最终裁决 |
| `safety-runtime` | 风险、策略、secret、隔离 | UI 信息架构 |
| `experience` | 三栏体验、旅程、失败态 | 数据库与事务 |
| `persistence-recovery` | durable state、幂等、恢复、迁移 | 正常态规划算法 |
| `acceptance-tests` | 测试夹具、oracle 与发布门 | 新产品功能声明 |
| `sources` | 证据等级与引用账本 | 用开源参考冒充官方事实 |
| `recipe` | 等级增量与升级顺序 | 重复定义 schema |

## 实现完成的定义

只有同时满足下列条件，才可以声称“能指导复刻完整 QoderWork-like 工作台”：

- Task 是独立 durable aggregate，多个 Task 真并行且上下文不串。
- 三栏由结构化事件投影，不从模型文本猜测 todo 或终态。
- Working Folder 在执行层强制，所有路径入口共用 containment 检查。
- artifact 是带版本、来源、验证和恢复状态的一等对象。
- Browser 与 Computer Use 的路由、权限和接管语义不同。
- Skills、Kits、MCP、Hooks 可追溯且不能扩大底层 grant。
- Awareness 原文、索引、备份、恢复和 Clear Memory 均有可测合同。
- scheduled tasks 有时区、幂等、misfire、能力快照和通知策略。
- 崩溃恢复不会制造 Ready 半成品或重复非幂等外部动作。
- 对每个闭源内部结论都标 `inference` 或 `unknown`。
- 目标等级对应的 [acceptance-tests.md](acceptance-tests.md) 全部通过并保存证据包。

## 官方来源

- [Introduction](https://docs.qoder.com/qoderwork/introduction)
- [Interface Guide](https://docs.qoder.com/qoderwork/ui-overview)
- [New Task](https://docs.qoder.com/qoderwork/new-task)
- [Task Management](https://docs.qoder.com/qoderwork/task-management)
- [Viewing Results / Working Folder](https://docs.qoder.com/qoderwork/file-management)
- [Skills](https://docs.qoder.com/qoderwork/skills)
- [Expert Kits](https://docs.qoder.com/qoderwork/expert-kits)
- [Connectors](https://docs.qoder.com/qoderwork/connectors)
- [Computer Use](https://docs.qoder.com/qoderwork/computer-use)
- [App Snapshots](https://docs.qoder.com/qoderwork/app-snapshots)
- [Awareness](https://docs.qoder.com/qoderwork/memory)
- [Hooks](https://docs.qoder.com/qoderwork/hooks)
- [System Settings](https://docs.qoder.com/qoderwork/settings)
- [Scheduled Tasks](https://docs.qoder.com/qoderwork/scheduled-tasks)

完整证据映射、公开实现参考和未知项见 [sources.md](sources.md)。
