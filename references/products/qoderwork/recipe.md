# QoderWork 产品配方

## 目录

- [配方目标](#配方目标)
- [共享能力差量](#共享能力差量)
- [产品配置草案](#产品配置草案)
- [实现装配顺序](#实现装配顺序)
- [四级实现](#四级实现)
- [直接升级](#直接升级)
- [反伪装验收](#反伪装验收)
- [证据与更优实现](#证据与更优实现)

## 配方目标

在共享 harness 上增加“桌面任务工作台”差量：用户可以委派多个相互隔离的任务，监控过程，授权本地目录与连接器，并获得可打开、可追溯的成品。配方不复刻闭源提示词或内部实现。

本页只定义装配顺序和等级差量。实现前先冻结 [product-contract.md](product-contract.md)，schema 直接采用 [protocol-state.md](protocol-state.md)，执行细节采用 [agent-loop.md](agent-loop.md) 与 [workspace-execution.md](workspace-execution.md)，不要从本配方摘要反推另一套协议。

生成文档、表格、演示文稿、PDF 或网页 artifact 前，必须读取 [Artifact 语义验证](../../implementation/artifact-validation.md)，并在目标项目锁定实际 parser/renderer 版本；不能用“文件存在”作为 Ready 判定。

## 共享能力差量

| 产品差量 | 依赖的共享知识 | QoderWork 默认 |
|---|---|---|
| Task 作为顶层工作单元 | `protocol-events`, `state-persistence`, `desktop-web` | 独立 transcript/config/folder/artifacts，可并行 |
| 三栏工作台 | `desktop-web`, `notifications-input`, `observability` | Sidebar + conversation + Task Monitor |
| Working Folder | `workspace`, `filesystem`, `permission-policy` | 每任务一个显式 grant，删除进废纸篓 |
| Artifact-first | `protocol-events`, `diff-review`, `testing` | 文件 card、预览、校验、来源 Step |
| Browser / Computer Use | `browser-computer`, `sandbox`, `network-secrets` | Browser 优先，Computer Use 高风险后备 |
| Awareness | `long-term-memory`, `rag-index`, `state-persistence` | 用户画像、长短期记忆、本地索引、备份恢复 |
| Skills / Kits / MCP | `skills-plugins`, `mcp`, `instructions-prompts` | playbook、组合能力、外部工具分层 |
| Hooks | `middleware-hooks`, `permission-policy` | 确定性生命周期脚本，可阻断 pre-tool |
| Scheduled / IM | `deployment-update`, `notifications-input`, `auth-settings` | 后台触发、状态通知、来源可审计 |

## 产品配置草案

```yaml
profile: qoderwork
surface: desktop-workbench
task:
  isolation: strict
  parallel: true
workspace:
  one_working_folder_per_task: true
  delete_mode: trash
artifacts:
  first_class: true
  validate_before_ready: true
tools:
  browser_preferred_over_computer_use: true
memory:
  user_managed: true
extensions:
  skills: true
  mcp: true
  hooks: true
```

字段名是本仓库设计，不是 QoderWork 的公开配置格式。

## 实现装配顺序

1. 先落 Task/Turn/Step/ToolCall/Artifact 与事件信封，建立三栏空投影。
2. 接入单 Task Agent loop、取消令牌、Task Monitor 和完成门。
3. 实现 WorkingFolderGrant、统一 path resolver、原子写与 artifact validator。
4. 将单任务扩展为 TaskRun 调度器；加入资源预算、path lease 与冲突 UI。
5. 接入 Browser，再以显式高风险降级加入 Computer Use。
6. 接入 Skills、Kits、MCP、Hooks，并固定每个 Run 的 capability snapshot。
7. 接入 Awareness 原文、检索、管理、备份、恢复与 Clear Memory oracle。
8. 接入 scheduled tasks 的时区、dedupe、misfire、无人值守授权和通知。
9. 执行 crash matrix、prompt-injection、secret canary、无障碍和迁移测试。

每完成一步都运行 [acceptance-tests.md](acceptance-tests.md) 中对应等级；如果某步只能靠模型自然语言伪装状态，则不能进入下一步。

## 四级实现

### `runnable`：能跑

实现：单桌面窗口、单任务 Agent loop、单 Working Folder、文件读取/写入、命令或格式 worker、流式 transcript、基础审批、一个 artifact card、取消与烟雾测试。

界面验收：左侧 New Task；中间 composer/transcript；运行时出现最小 Task Monitor；完成后 card 能打开真实落盘文件。

任务验收：在授权目录读取两个 Markdown，生成带来源的合并文档；越出目录被拒绝；要求删除时进入废纸篓。

### `usable`：能用

增加：Task/Turn/Step 持久化、Draft/Recent、标题和全文搜索、Rename/Pin/Archive、多个并行任务、workspace/model picker、附件、结构化 Task Monitor、artifact 预览与语义校验、Browser、Skill、MCP、连接器显式授权、重试/恢复，以及可验证的本地隔离 worker/sandbox capability probe。若隔离不可用，执行工具必须 fail closed 或明确降为只读，不能仅靠 Working Folder 提示词。

界面验收：三个并行任务状态不串；重启应用后 transcript、todo、工具记录和 artifacts 完整；Archive 可恢复且不删除成品。

任务验收：浏览登录后的测试站点提取表格，生成 `.xlsx`，记录网页来源；认证失效只阻塞对应 Step。

### `productive`：顺手

增加：Awareness 长短期记忆与本地索引、Expert Kits、App Snapshots、Computer Use、scheduled tasks、桌面通知、Hooks、增量 context、artifact 版本、文件冲突检测、后台资源与成本控制。

界面验收：用户能查看/编辑/清除每条记忆；App Snapshot 先进入 composer；Computer Use 展示目标窗口、动作与截图；Hook 阻断原因出现在对应 ToolCall。

任务验收：从前台应用快照提取错误，Browser 复现，修改 Working Folder 内文件并生成验证截图；并行任务竞争同一文件时出现冲突处理。

### `polished`：好用

增加：把 usable 的真实隔离边界硬化为跨平台 OS/容器 enforcement 矩阵，并加入按 origin/domain 的网络策略、secret broker 与全链路脱敏、细粒度 capability grants、外发/发布二次确认、检查点与崩溃恢复、连接器企业治理、审计导出、SLO、无障碍、国际化、自动更新与数据迁移。

界面验收：权限页能解释谁可访问什么、何时过期；高风险动作显示目标/数据/影响；所有任务状态支持键盘与屏幕阅读器；升级后旧任务可读可恢复。

任务验收：恶意网页提示 Agent 上传本地文件时被策略阻断；敏感值不出现在模型请求、日志、截图 OCR、artifact 或通知；runtime 崩溃后不重复发送外部消息。

## 直接升级

允许 `usable → polished`，但升级器必须展开依赖并依序完成：

1. 迁移 Task/Turn/Step 与 artifact schema，保留兼容读取。
2. 将现有路径记录转换成 WorkingFolderGrant，无法证明授权的路径置为只读待确认。
3. 在 tool broker 前加入 PolicyDecision；旧自动授权不直接继承到 Computer Use/外部写工具。
4. 把明文 connector 凭据迁移到 secret broker 并轮换 token。
5. 启用 sandbox/network policy，再开放 scheduled 与无人值守运行。
6. 重建 Awareness 索引，验证 Clear Memory 不残留旧内容。
7. 运行 `runnable`、`usable`、`productive` 与 `polished` 的全部合同测试。

## 反伪装验收

- Task Monitor 必须来自结构化事件，不是把模型文字渲染成 todo。
- Working Folder 必须由执行层做 canonical containment，不是系统提示词约束。
- Secure Work Environment 必须有可验证的隔离测试，不是单独临时目录。
- Artifact “Ready” 必须经过格式解析/打开验证，不是只检查文件存在。
- Awareness 清除必须删除原文与索引，不是隐藏 UI。
- Browser 与 Computer Use 必须有不同权限和优先级，不能共享一个无限制“点击工具”。

## 证据与更优实现

行为对齐以 [Interface Guide](https://docs.qoder.com/qoderwork/ui-overview)、[New Task](https://docs.qoder.com/qoderwork/new-task)、[Viewing Results](https://docs.qoder.com/qoderwork/file-management)、[Connectors](https://docs.qoder.com/qoderwork/connectors)、[Awareness](https://docs.qoder.com/qoderwork/memory)、[Hooks](https://docs.qoder.com/qoderwork/hooks) 为准。公开资料未说明的底层部分采用本仓库共享安全合同；当更强的隔离、审计或恢复与表面行为不冲突时，优先实现更强方案。

逐条声明、访问日期、未知项和公开参考实现统一维护在 [sources.md](sources.md)，不要在等级升级时把 `inference` 提升为官方事实。
