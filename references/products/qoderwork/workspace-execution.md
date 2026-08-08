# QoderWork-like Workspace 与执行层

> Working Folder 的单目录授权、结果落盘与废纸篓行为是 `confirmed`；下面的 canonical path、lease、worker 和 sandbox 方案是 `inference`。

## 目录

- [Working Folder grant](#1-working-folder-grant)
- [路径解析合同](#2-路径解析合同)
- [文件工具 schema](#3-文件工具-schema)
- [原子写与并发](#4-原子写与并发)
- [Artifact 管线](#5-artifact-管线)
- [执行 worker](#6-执行-worker)
- [Browser 与 Computer Use](#7-browser-与-computer-use)
- [Skills、Kits、MCP 与 Hooks](#8-skillskitsmcp-与-hooks)
- [Scheduled execution](#9-scheduled-execution)
- [黑盒 oracle](#10-黑盒-oracle)

## 1. Working Folder grant

每个 Task 最多绑定一个 Working Folder。
选择目录时记录用户选择的展示路径和执行层解析出的 canonical root。
grant 与 `task_id` 绑定，不是全局“永远允许”。
目录被移动、设备变化、权限撤销或 inode/device identity 不一致时，grant 失效。
重新绑定需要用户操作，不能自动退回父目录或 Home。

```json
{
  "grant_id": "wfg_01...",
  "task_id": "task_01...",
  "display_path": "/Users/me/Reports",
  "canonical_root": "/Users/me/Reports",
  "device_identity": "dev:inode-or-platform-bookmark",
  "operations": ["read", "create", "update", "rename", "trash"],
  "granted_at": "2026-08-08T09:00:00Z",
  "revoked_at": null
}
```

## 2. 路径解析合同

1. 将相对路径拼到 canonical root，而不是当前进程 cwd。
2. 逐段解析 `.`、`..`、符号链接、junction、alias 和大小写规范化。
3. 在打开文件后再次以 file descriptor 验证真实对象仍位于 root。
4. 拒绝跨挂载点逃逸、设备文件、socket、FIFO 和未授权云端占位文件。
5. 防御检查与使用之间的 TOCTOU，优先使用 dirfd/openat 类 API。
6. search、glob、archive 解压和格式 worker 都复用同一 resolver。
7. grant 外路径只返回最小错误，不把敏感目录枚举给模型。

## 3. 文件工具 schema

```yaml
read_file: {path, byte_range?, expected_hash?}
list_directory: {path, cursor?, limit, include_hidden?}
search_files: {query, roots?, globs?, max_results}
write_file: {path, content_ref, expected_old_hash?, mode: create|replace}
rename_path: {from, to, expected_hash?}
trash_path: {path, expected_hash?, reason}
validate_artifact: {artifact_id, validators: [string]}
```

路径参数永远相对 grant root 或由 opaque path handle 表示。
工具结果返回新 hash、字节数、MIME、mtime 和审计引用。
大内容以 blob ref 返回，避免进入 transcript。

## 4. 原子写与并发

写入流程是 `acquire lease → read expected hash → write temp → fsync → validate basic → atomic rename → release lease`。
创建与覆盖是不同 intent；覆盖要求 expected hash 或显式冲突策略。
多个任务共享目录时，lease key 使用 canonical path 和操作类型。
目录 rename/trash 会与所有后代路径 lease 冲突。
只读调用可以并行，但必须观察一致的版本或声明接受最新版本。
last-writer-wins 不能作为默认策略。
冲突事件包含双方 Task、基线 hash、新 hash 和用户可选恢复动作。

## 5. Artifact 管线

```text
tool output
→ quarantine/temp file
→ MIME sniff + malware/basic policy
→ format-specific parse
→ semantic checks
→ preview render
→ atomic publish to Working Folder
→ ArtifactProduced
→ ArtifactValidated(valid|invalid)
```

格式专用 validator 示例：DOCX 用结构解析与渲染，XLSX 打开 workbook 并检查公式错误，PPTX 渲染各页，PDF 做解析和页面渲染。
文本/代码至少检查编码、非空、预期文件名与用户约束。
card 的 Ready 由 validator receipt 决定。
原始生成文件与诊断应可保留，便于修复，不以“验证失败”直接删除证据。

## 6. 执行 worker

建议将 shell、office、browser、computer-use、MCP 分进可终止 worker。
worker 接收 task-scoped capability token，而不是完整用户权限。
token 包含 grant id、允许工具、网络 origin、截止时间和调用次数。
worker stdout/stderr 经大小限制、secret redaction 和结构化封装。
每个调用有 deadline、heartbeat、cancel 和 resource budget。
worker 崩溃只让对应 ToolCall 失败，不影响 UI 与其他 TaskRun。

## 7. Browser 与 Computer Use

Browser 使用隔离 profile/context，保留必要登录态但与个人日常标签页隔开。
优先 DOM、ARIA、locator 和结构化网络响应；截图用于验证和降级观察。
下载先进入隔离区，通过扫描和格式验证后才能发布到 Working Folder。
Computer Use 需要 Screen Recording/Accessibility，按 app/window 绑定观察与动作。
每步记录目标窗口、前置截图、动作、后置截图和焦点验证。
切换应用、提交表单、粘贴敏感值、发送或支付前重新审批。
用户接管鼠标键盘时立即暂停 Agent 输入。

## 8. Skills、Kits、MCP 与 Hooks

Skill loader 只按需加载 `SKILL.md` 与被引用支持文件，记录版本和 hash。
Expert Kit 展开成有版本的快捷命令、数据连接和 Skills 绑定。
MCP server 在独立进程/容器运行，使用 tool allowlist 和独立凭据句柄。
Hook 输入是经过脱敏的结构化事件；PreToolUse 可阻断但不能授予额外权限。
扩展升级不改变已运行 TaskRun 的 capability snapshot。
安装、启用、授权、更新、停用和卸载必须是独立状态。

## 9. Scheduled execution

调度器在 intended fire time 创建普通 TaskRun，而不是特殊隐形进程。
无人值守 run 使用创建 Schedule 时冻结的 capability snapshot。
Working Folder grant 已过期时转 waiting，不自动扩大目录权限。
Browser 登录过期、Computer Use、外发或新 MCP 写操作转为需用户注意。
每次触发记录 schedule_id、时区、planned time、actual time 和 dedupe key。
桌面应用退出时由明确的后台服务承接；若无后台服务，则 UI 必须说明不会运行。

## 10. 黑盒 oracle

1. 符号链接指向 grant 外时 read/write 均硬阻断。
2. 两任务同时覆盖同一文件，至少一个进入 conflict 而非静默获胜。
3. worker 被 kill 后，其他任务继续且 temp file 不冒充 artifact。
4. 损坏 PPTX 无法进入 Ready。
5. Browser 下载恶意文件时停留隔离区。
6. Computer Use 焦点漂移后不发送键盘输入。
7. Skill/MCP 请求 `~/.ssh` 不扩大 Working Folder。
8. scheduled run 使用过期 grant 时进入 waiting 并通知用户。
