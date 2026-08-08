# Codex-like 工作区与执行器

## 目录

1. 模块边界
2. 工作区身份
3. 文件读取与搜索
4. Patch 执行
5. Shell 与 PTY
6. Executor 生命周期
7. Git 与 worktree
8. Sandbox 接入
9. 输出和 artifact
10. 失败与取消
11. 实现验收

## 模块边界

`公开事实`：公开 workspace 将 core tools、apply-patch、shell-command、PTY、sandbox 和 exec 拆为不同模块。
`设计综合`：本实现把模型可见工具、策略判断和 OS 执行器分为三层：

```text
ToolSpec/Router -> Policy + Approval -> Executor + Sandbox Adapter
```

router 不拼接 shell 字符串；executor 不决定业务授权；sandbox 不解释用户意图。
所有执行入口，包括 app-server 辅助命令，都必须穿过相同 policy boundary。

## 工作区身份

Workspace 不能只保存一个字符串路径，应至少包含：

```text
WorkspaceIdentity {
  requested_path, canonical_root, device_or_volume,
  repository_root?, git_common_dir?, worktree_id?,
  initial_head?, trust_level, writable_roots[]
}
```

启动时解析真实路径并拒绝不存在或不允许的 root。
每次写入前重新验证目标父目录，防止检查后替换 symlink。
相对路径一律基于显式 cwd 解析，再检查是否位于 writable root。
不得把进程继承的 cwd 当成可信默认值。
工作区身份变化要产生事件并使上下文 baseline 失效。

## 文件读取与搜索

读取工具返回规范化路径、内容、编码、截断信息和内容摘要。
二进制文件默认只返回元数据，除非有专门媒体工具。
搜索优先使用结构化参数：query、glob、root、max_results、context_lines。
遍历遵守 ignore 规则，但安全检查不依赖 `.gitignore`。
超大文件采用范围读取并返回总行数或字节数。
读取发生变化的文件时，结果携带 revision/hash，供 patch 做乐观并发检查。

## Patch 执行

`公开事实`：公开仓库有独立 apply-patch parser 与 core handler/runtime。
`设计综合`：patch 请求应包含 base revision、目标文件和结构化 hunk。

Patch pipeline：

1. 解析语法并限制文件数量、hunk 数和总字节；
2. 规范化所有路径；
3. 拒绝绝对路径、父级穿越和越界 symlink；
4. 对照 base hash 检测并发修改；
5. 在内存或临时文件中应用并验证上下文；
6. 生成预览 diff 和风险分类；
7. 执行 policy/approval；
8. 使用同目录临时文件、fsync 和原子 rename 提交；
9. 记录 before/after hash 与 workspace revision；
10. 发出 tool result 与 diff updated 事件。

新增、修改、删除、重命名应是明确操作，不从空内容猜测。
部分 hunk 失败时默认整次 patch 不提交；若支持部分提交必须在协议中显式声明。
patch 失败返回最小定位上下文，模型可据此重新读取，不能无界重试。
文件权限和换行风格默认保留，除非 patch 明确改变。

## Shell 与 PTY

shell invocation 至少包含 argv 或受控 shell script、cwd、env delta、timeout、tty、output limit。
能够用 argv 表达时优先 argv；需要管道、重定向、通配符时才交给显式 shell。
展示给用户的 command view 必须与实际执行语义一致。
环境变量采用 allowlist + delta，不默认把主进程所有 secret 传入。

PTY handle 与逻辑 tool call 分离：

```text
ProcessHandle {
  process_id, call_id, pid_or_remote_id,
  process_group, stdin_offset, output_offsets,
  started_at, deadline, state
}
```

`write_stdin` 必须引用 process id，并保证 offset 或 request id 去重。
resize 仅对 PTY 有效；普通 pipe 返回明确 unsupported。
stdout/stderr 分通道；PTY 合并流时必须标注 merged。
退出码、signal、timeout 和 cancellation 是不同终态原因。

## Executor 生命周期

`prepare` 校验参数、生成执行计划和 idempotency key，但不产生副作用。
`authorize` 固化规范化动作、approval 与 sandbox profile。
`spawn` 之后立即持久化 process receipt，再向客户端发 started。
`stream` 产生有序 output chunk，每块带 offset。
`collect` 等待退出并返回资源用量、exit status 和 artifact 引用。
`cleanup` 回收进程组、临时文件、socket 和租约。

本地与远程 executor 实现同一接口。
远程实现额外需要 lease、heartbeat、dedupe key、upload manifest 和 result receipt。
连接断开不能自动重启未知状态命令；先按 idempotency key 查询远端回执。

## Git 与 worktree

所有 git 操作先发现 repository root 和 worktree identity。
读取类命令如 status/diff/log 可按普通 read policy 运行。
checkout、reset、clean、push、force 等按破坏性或外部写动作单独分类。
不得在未经用户要求时覆盖未提交修改。
应用 patch 前后保存 `git status --porcelain` 等价快照，用于区分用户改动与 agent 改动。

并行任务优先创建独立 worktree：

- worktree 目录必须是验证后的专用路径；
- 每个 agent 绑定唯一 branch/worktree id；
- 不跨 worktree 共用 cwd 或 patch revision；
- 完成后先汇报 diff，再由显式流程合并；
- cleanup 前确认没有活动进程和未保存改动；
- 删除 worktree 是独立的可审计动作。

conversation rollback 不等于 `git reset`。
workspace rollback 优先使用 agent 自身 checkpoint/patch journal，避免撤销用户后续改动。

## Sandbox 接入

统一 profile 描述可读根、可写根、网络、环境、进程和设备能力。
macOS、Linux、Windows 或 container adapter 把 profile 编译成平台 enforcement。
编译结果应包含实际可执行能力报告，供 runtime 检测降级。
策略允许不代表 sandbox 放开；sandbox 拒绝也不能由模型重试升级权限。
子进程和孙进程继承边界；取消按进程组或 job object 清理。
网络按默认拒绝和显式域/地址规则实现，并防御 DNS 重绑定。

## 输出和 artifact

模型可见输出必须有 token/byte 上限，并保留开头、结尾和截断原因。
完整大输出写入内容寻址 artifact，记录 hash、size、mime、redaction policy 和 retention。
事件只携带有界 delta 或 artifact ref，不把数百 MB 内容塞入 rollout。
日志输出先脱敏再持久化；原始 secret 不应以“调试需要”为由保存。
artifact 读取仍经过 thread/workspace 权限检查。

## 失败与取消

spawn 前失败可安全重试；spawn 后无回执属于 `unknown_effect`。
unknown effect 恢复时先查询 PID、remote lease 或副作用 receipt。
timeout 先温和终止，再在 grace period 后强杀整个进程组。
cancel 后继续到达的 output 可持久化为 late event，但不得把进程改回 running。
executor crash 不得让 turn 永久等待，应由 watchdog 生成明确失败或复核状态。
disk full、permission changed 和 workspace removed 都要有稳定错误 code。

## 实现验收

- patch 遇到 base hash 变化时不覆盖新内容；
- `../`、绝对路径和 symlink swap 无法越界写入；
- Ctrl-C 终止孙进程且只产生一个工具终态；
- 10 MB stdout 不压垮事件队列，模型收到有界摘要；
- PTY stdin 重复 request id 不重复输入；
- 用户脏工作区在失败、rollback 和 cleanup 后不丢改动；
- 两个 worktree 并行执行互不修改；
- sandbox adapter 不可用时按配置 fail closed；
- remote executor 断线重连不重复已完成副作用。

更完整场景见 [acceptance-tests.md](acceptance-tests.md)，权限设计见 [safety-runtime.md](safety-runtime.md)。
公开源码入口集中在 [sources.md](sources.md)。
