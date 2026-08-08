# QoderWork 上下文与工具

> 本文定义 context item 和能力语义；工具执行与 grant 以 [workspace-execution.md](workspace-execution.md) 为准，最终权限裁决以 [safety-runtime.md](safety-runtime.md) 为准。

## 上下文来源

| 来源 | 公开行为 | 建议兼容合同 |
|---|---|---|
| 当前任务 | 每个任务保留独立 transcript、配置与 artifacts | 以 `task_id` 隔离，引用历史 item 而非拼接全文 |
| 直接附件 | `+` 或拖拽添加文件 | 记录来源、hash、MIME、解析器与用户意图 |
| Working Folder | 每任务至多绑定一个显式授权目录，可读其子目录 | 保存 canonical root 与 grant；所有路径先做 containment 检查 |
| App Snapshot | 前台应用截图与可读文本一并进入输入栏 | 截图、AX 文本和应用身份分别带 provenance |
| Skills | `SKILL.md` playbook，可自动匹配、斜杠调用或显式调用 | 元数据常驻，正文与支持文件按需加载 |
| Expert Kits | 快捷命令、数据连接、知识技能组合 | Kit 只绑定 capability，不复制底层实现 |
| Awareness | 用户画像、长短期记忆、本地索引 | 检索结果必须可见、可编辑、可删除、可备份 |
| Connector 结果 | Browser、系统应用、Microsoft 365、SaaS/MCP | 工具结果以结构化 item 回流并标注 server/tool |

来源：[New Task](https://docs.qoder.com/qoderwork/new-task)、[Viewing Results](https://docs.qoder.com/qoderwork/file-management)、[App Snapshots](https://docs.qoder.com/qoderwork/app-snapshots)、[Skills](https://docs.qoder.com/qoderwork/skills)、[Awareness](https://docs.qoder.com/qoderwork/memory)。

## 建议装配顺序

这是 `inference`，用于得到稳定、低成本的行为兼容：

1. 系统策略与当前 workspace 合同。
2. 用户本轮输入、直接附件与 App Snapshot。
3. 当前任务的最近 turns、未完成 todo 与当前 artifacts 摘要。
4. 显式调用的 Skill/Kit；再按描述选择候选 Skill。
5. Working Folder 的目录摘要与按需文件读取，不预塞整个目录。
6. Awareness 检索结果；长期记忆优先于日记式短期摘要。
7. Connector/MCP 工具返回；大结果落 artifact，模型仅取分页或摘要。

每个 context item 至少带 `source`, `uri`, `captured_at`, `content_hash`, `sensitivity`, `token_estimate`。压缩只生成新 summary item，不删除原事件。

## 工具分层

### 文件与成品

- `list/read/search/write/rename/trash` 只在 Working Folder grant 内工作。
- 文档、表格、演示稿通过格式专用 worker 处理，输出先写临时文件、验证后原子替换。
- artifact card 是一等对象：包含 MIME、预览、落盘路径、来源步骤、校验状态与打开动作。

### Browser

官方说明 Browser Connector 支持 Chromium 登录态、导航、点击、表单、结构化抽取与多标签页。兼容实现优先使用 DOM/ARIA/locator，截图用于验证；浏览器 profile 与普通个人 profile 分离。[Connectors](https://docs.qoder.com/qoderwork/connectors)

### Computer Use

官方说明 Computer Use 读取目标窗口、持续截图验证上一步，并操作鼠标键盘和应用切换；网页任务应优先 Browser Automation。兼容实现将其作为高风险后备工具，而不是万能默认工具。[Computer Use](https://docs.qoder.com/qoderwork/computer-use)

### 系统与 SaaS 连接

macOS Apps、Microsoft 365 与市场连接器应统一暴露 typed tool schema，但授权、凭据刷新和撤销由 connector host 持有。模型只看到能力和经过过滤的数据，不得到 OAuth refresh token。

### Skills、MCP 与 Hooks

- Skill：声明式过程知识；官方位置为 `~/.qoderwork/skills/<name>/SKILL.md`，可带支持文件。
- MCP：外部工具协议；server、transport、tool allowlist 和凭据分别管理。
- Hook：确定性生命周期脚本，不交给模型“决定是否执行”。

## 记忆合同

官方 Awareness 将用户画像、`MEMORY.md`、短期记忆目录、本地索引、备份/恢复分开。兼容实现还应加入：

- 写入候选与已确认记忆分层；敏感事实默认不自动持久化。
- 每条记忆保存证据任务、创建者、最后验证时间和冲突状态。
- 用户可逐条编辑/删除，Clear Memory 后索引不可残留旧向量。
- Skill evolution 先产生可审查 diff，不静默改写可执行流程。

## 上下文验收要点

- 两个并行任务不能读取彼此 transcript、附件或未发布 artifact。
- Working Folder 外的符号链接、`..`、大小写与挂载点逃逸均被阻断。
- 同一大目录只检索相关片段，token 用量随相关文件数而非仓库总量增长。
- Task Monitor 能指出某一步使用了哪个 Skill、MCP、文件和记忆。
- Browser 与 Computer Use 的观察结果都可回放到具体步骤。

## 实现交接

- 上下文装配器输入/输出与循环阶段见 [agent-loop.md](agent-loop.md)。
- Skill、Kit、MCP 与 Hook 的能力快照及执行边界见 [workspace-execution.md](workspace-execution.md)。
- Awareness 的清除、备份和索引恢复见 [persistence-recovery.md](persistence-recovery.md)。
- 相应黑盒用例集中在 [acceptance-tests.md](acceptance-tests.md)，本页不另定义一套发布门槛。
