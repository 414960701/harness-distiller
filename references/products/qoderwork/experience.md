# QoderWork 体验蒸馏

> 本文是 UI/UX 规范；三栏的字段与事件投影以 [protocol-state.md](protocol-state.md) 为准，完成定义以 [product-contract.md](product-contract.md) 为准。

## 信息架构

官方桌面布局可压缩为三栏：

```text
┌──────────────────┬────────────────────────────────┬──────────────────┐
│ Sidebar          │ Task conversation              │ Task Monitor     │
│ New Task         │ transcript                     │ live todo        │
│ Extensions       │ artifact cards                 │ tool calls       │
│ Awareness        │                                │ Skills / MCP     │
│ Draft/Scheduled  │ composer                       │ progress         │
│ Recent/Groups    │ workspace model folder + voice │                  │
└──────────────────┴────────────────────────────────┴──────────────────┘
```

右栏只在运行或检查过程时展开；左栏可折叠。这个布局的核心不是“看代码”，而是同时回答三个问题：我委派了什么、Agent 正在做什么、交付物在哪里。

来源：[Interface Guide](https://docs.qoder.com/qoderwork/ui-overview)。

## 核心旅程

### 1. 创建任务

1. 点击 New Task 或空白 composer。
2. 用 outcome / format / constraints 描述交付物。
3. 选择 General、Design、Slides 或 Writing workspace。
4. 选择模型等级，必要时绑定 Working Folder。
5. 发送后立即进入 Running，右侧 Task Monitor 展示进度。

草稿自动保存；无关工作应新建任务，同一交付物的迭代留在原任务。[New Task](https://docs.qoder.com/qoderwork/new-task)

### 2. 管理长期任务

任务列表支持 Drafts、Scheduled、Recent 和自定义 Groups；搜索覆盖标题与会话内容；单任务可 Rename、Pin、Group、导出 Markdown、Archive。Archive 保留会话和 artifacts，区别于不可逆删除。[Task Management](https://docs.qoder.com/qoderwork/task-management)

### 3. 交付本地成品

Working Folder 授权后，Agent 原地读写；结果以 artifact card 出现在会话中，可打开系统文件。用户不需要理解中间工具链，但应能从 Task Monitor 追溯它读了什么、调用了什么、生成了什么。

### 4. 跨应用工作

- 网页优先 Browser：结构化、快、可定位。
- 只有缺少 API/DOM 能力时才启用 Computer Use。
- App Snapshots 解决“把眼前内容快速加入上下文”，默认先进入 composer 供用户审阅，而不是自动发送。

### 5. 安装能力

Extension 区把 Expert Kits、Skills、Connectors 与相关市场集中管理。安装、授权、启用、停用和更新必须是不同状态；对 Skill 还应显示触发方式和支持文件，对 Connector 显示数据范围与账号。

## 体验原则

- **任务先于聊天**：Task 是可恢复、可搜索、可归档、带交付物的工作单元。
- **成品先于日志**：artifact card 显眼，冗长工具输出折叠但可展开。
- **并行但不混淆**：每个任务显示 workspace、folder、model、状态和最近活动；通知可直接跳回请求注意的任务。
- **能力可见**：Task Monitor 显示使用的 Skill/MCP/connector，避免“魔法完成”。
- **高风险渐进披露**：普通文件处理低摩擦；登录态、外发、Computer Use 和系统权限在动作点解释。
- **可接管**：暂停、取消、追加指令、打开 artifact、恢复归档均有明确入口。

## 必须设计的失败态

| 情形 | UI 行为 |
|---|---|
| Working Folder 被移动/撤权 | 任务保持，标记 folder unavailable，允许重新绑定但不自动扩大范围 |
| Tool/connector 认证失效 | 对应 Step 显示 re-auth，其他无关步骤可继续 |
| Computer Use 焦点漂移 | 暂停并展示最后截图、目标窗口与待执行动作 |
| Artifact 生成后校验失败 | card 标为 invalid，保留诊断，不伪装成成功交付 |
| 应用退出或崩溃 | 重启后恢复 transcript 与已提交 Step；非幂等动作不自动重放 |
| 并行写冲突 | 在 Task Monitor 显示冲突文件和合并选择 |

## 无障碍与可观察性

- 三栏均支持键盘聚焦、屏幕阅读器标题与状态 live region。
- Running/Waiting/Failed/Completed 不能只靠颜色区分。
- 工具调用显示开始、耗时、取消、重试、权限和产物；默认不暴露隐藏推理。
- 全局 QuickPick、通知与语音输入是加速入口，不可成为完成关键动作的唯一入口。

## 蒸馏边界

不复制 QoderWork 品牌、图标、文案或专有模型名。行为兼容关注任务管理、三栏工作台、artifact-first、授权连接器、Awareness 与可接管执行。
