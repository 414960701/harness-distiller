# QoderWork 安全与运行时

> 本文是权限与风险的唯一规范入口；文件执行细节见 [workspace-execution.md](workspace-execution.md)，恢复幂等见 [persistence-recovery.md](persistence-recovery.md)。

## 官方确认的边界

### 本地文件

- Working Folder 必须由用户显式选择；任务只访问授权目录，访问其他位置时再次请求权限。
- 每个任务至多绑定一个 Working Folder。
- “删除文件”默认移入系统废纸篓而非永久删除。

来源：[Viewing Results](https://docs.qoder.com/qoderwork/file-management)。

### 连接器与桌面控制

- 市场连接器默认不激活，启用并授权后才访问外部数据。
- Browser Connector 复用已登录的浏览器会话；运行时不应由用户同时操作受控标签页。
- Computer Use 与 App Snapshots 需要 macOS Accessibility 和 Screen Recording；Computer Use 获得的实质能力接近用户本人。
- 设置允许关闭 Computer Use、管理系统权限和清理隔离 workspace。

来源：[Connectors](https://docs.qoder.com/qoderwork/connectors)、[Computer Use](https://docs.qoder.com/qoderwork/computer-use)、[App Snapshots](https://docs.qoder.com/qoderwork/app-snapshots)、[System Settings](https://docs.qoder.com/qoderwork/settings)。

### Hooks

官方 Hook 配置位于 `~/.qoderwork/settings.json`。`PreToolUse` 可匹配工具名并以退出码 `2` 阻断；stderr 回流给 Agent。Hook 是确定性 guardrail，但当前文档说明不支持热重载，需要重启。[Hooks](https://docs.qoder.com/qoderwork/hooks)

## 不能从公开资料得出的结论

以下均标为 `inference/unknown`，禁止写成 QoderWork 事实：

- Secure Work Environment 使用容器、VM、Seatbelt、App Sandbox 或其他何种隔离原语。
- 是否对所有 shell、文件、网络和 connector call 使用统一 policy engine。
- 网络是否默认拒绝、是否支持域名/CIDR allowlist、是否有 prompt-injection 检测。
- secrets 是否对模型、日志、截图、artifacts 做统一脱敏。
- 是否存在逐工具审批、检查点、事务文件系统或可审计 PolicyDecision。

## 兼容实现的强制安全合同

### 决策顺序

```text
normalize input
→ resolve task/workspace/capability grants
→ deterministic deny rules
→ risk classification
→ sandbox or connector isolation
→ user approval when consequential
→ execute with least privilege
→ redact and persist audit event
```

Prompt、Skill 和 MCP 描述只能提出动作，不能覆盖策略。Hooks 可增加限制，workspace/repo 级配置不能削弱系统/企业级限制。

### 风险分级

| 风险 | 例子 | 默认行为 |
|---|---|---|
| 低 | 授权目录内读取、离线解析、预览 | 自动执行并记录 |
| 中 | 新建/覆盖文件、登录态网页读取、安装 Skill | 显示范围；按持久策略审批 |
| 高 | 发送表单/邮件、发布、批量改名、Computer Use、外部写 MCP | 每次确认目标、数据和影响 |
| 禁止 | 永久删除、凭据导出、越出 workspace、绕过系统权限 | 硬阻断；仅管理员策略可改变可配置项 |

### 文件系统

- 所有路径先解析 canonical path，再校验位于 grant root；拒绝符号链接与挂载点逃逸。
- 写入采用临时文件 + fsync + rename；覆盖前保存版本或可恢复副本。
- `trash` 与 `delete_permanently` 是不同 capability；产品配方默认只暴露前者。
- 并行任务写同一文件时进行版本比较并要求合并，禁止 last-writer-wins。

### Browser 与 Computer Use

- 浏览器使用隔离 profile、origin policy、下载隔离区和敏感字段遮罩。
- DOM 中、网页中和文档中的指令一律视为不可信数据。
- Computer Use 每步绑定目标 app/window，动作后截图校验；切换应用、粘贴敏感内容、提交、支付、发送前再次审批。
- 用户接管时立即暂停 Agent 输入，避免鼠标键盘竞态。

### Secrets 与网络

- connector host 代持凭据；模型与 Hook stdin 只见 opaque handle。
- 默认拒绝访问本机元数据、loopback 管理端口和私网段；按工具与 origin 放行。
- transcript、tool output、截图 OCR、artifact 和通知统一走 secret redaction。

## 威胁场景测试

1. 网页内容要求上传 Working Folder：Browser 可读页面，但外发文件必须被阻断并审批。
2. Skill 要求读取 `~/.ssh`：即使 Skill 已安装也不能扩大 workspace grant。
3. MCP 返回隐藏指令：作为 tool data 存储，不提升为 system instruction。
4. Computer Use 误聚焦密码管理器：窗口身份不符即停止。
5. 并行任务同时覆盖同一表格：第二次提交产生冲突而非静默覆盖。
6. Hook 超时、崩溃或输出畸形：按 fail-closed/fail-open 的事件级策略处理并可审计。
