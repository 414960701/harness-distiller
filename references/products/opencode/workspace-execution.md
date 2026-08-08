# OpenCode-like Workspace 与执行

## 目录

- [Location 合同](#location-合同)
- [文件工具](#文件工具)
- [Shell 与 PTY](#shell-与-pty)
- [Snapshot、diff 与 revert](#snapshotdiff-与-revert)
- [Worktree 与并发](#worktree-与并发)
- [执行记录](#执行记录)
- [失败处理](#失败处理)
- [验收门禁](#验收门禁)

## Location 合同

每个 session 绑定 `project/workspace/directory/worktree`。server middleware 从 session 解出 location，并在 Effect/service scope 注入；tool 不接收客户端随意传入的 cwd。所有路径先 canonicalize，再验证处于允许 root；相对路径在 directory 下解析。

workspace adapter 提供 `contains(path)`、read/stat/list/search、atomic write、process/PTY、snapshot/diff/revert。local 是默认 adapter；remote adapter 必须暴露相同 receipt，不可让 session loop 特判 SSH/container。

## 文件工具

- `read`：支持 offset/limit、文本编码、行号、binary/media 标识和最大字节。
- `glob/grep`：使用受控 root、ignore、limit、timeout，结果排序确定。
- `edit`：old string 唯一匹配或带 expected hash；多处匹配拒绝。
- `write`：新建/覆盖区分，先 permission；临时文件 + fsync/rename 原子替换。
- `apply_patch`：解析所有 hunks、先 simulate，任一失败则零写入。

写工具返回 changed paths、before/after hash、diff preview、bytes 和 artifact reference。symlink 在检查后到 open/rename 的竞态必须以 dirfd/realpath recheck 或 sandbox 处理。

## Shell 与 PTY

短命令 shell 返回 stdout、stderr、exit code、signal、duration、truncated。命令必须作为原始字符串与解析后的 permission patterns 一起记录；实际执行的 command hash 与批准值一致。

PTY 是有状态资源：

```yaml
Pty:
  id: string
  session_id: string|null
  cwd: absolute-path
  command: [string]
  pid: integer
  offset: integer
  status: running|exited|killed
  exit_code: integer|null
```

output chunk 带递增 offset；input/resize 带 request id 防重复。cancel 终止 process group/tree，不只杀 shell parent。历史 output 有环形缓冲/持久 artifact，client gap 可按 offset 补取或显示截断。

## Snapshot、diff 与 revert

模型 step 前捕获 workspace snapshot/ref；写后计算 diff 与 files。snapshot 不等于复制整个 repo，可用 Git tree/object、内容寻址对象或平台 snapshot。关键是：before ref 不变、diff 可验证、revert 只影响该 step 的 agent change。

revert message 时先检查当前 workspace 是否与 recorded after hash 一致；若用户随后修改同文件，返回 conflict 并提供 preview，禁止粗暴 checkout。redo 从保存的 forward patch 或 snapshot 恢复，同样检查 precondition。

## Worktree 与并发

productive 级可创建独立 Git worktree/workspace：记录 base ref、path、branch、owner session 和 cleanup state。session cwd、process env、LSP root、file watcher、snapshot 与 diff 全部使用该 location。

同 workspace 默认 single writer；read-only session 可并发。跨 workspace 并行允许，但 share/provider/cache 等全局服务不能混淆 location。cleanup 仅删除由系统创建且无未回收进程/用户 dirty 的 worktree。

## 执行记录

副作用工具记录：intent id、session/message/call、schema input hash、permission decision、location、start/end、process/file receipt、result hash。恢复时按 receipt 判断 completed/unknown，不根据 UI card 猜测。

远端 adapter 必须支持 idempotency key 查询：断线后先 `get_receipt(intent_id)`，不得直接重新执行。local runnable 可将不可重放的 running tool 标为 interrupted，但必须明确需要人工核对。

## 失败处理

| 故障 | 结果 |
|---|---|
| 路径越界/symlink escape | permission/enforcement error，零副作用 |
| stale hash | workspace conflict，重新读取 |
| patch 中间失败 | transaction rollback 或全部零写入 |
| command timeout | kill process tree，保存 partial output 与 timed_out |
| PTY client 断线 | 按 policy 保持或终止，状态仍在 server |
| snapshot unavailable | 禁止声称可安全 revert，继续前提示 |
| worktree cleanup 失败 | 标 orphaned，可重试，不删用户数据 |
| remote receipt unknown | paused/needs-reconciliation，不自动重跑 |

## 验收门禁

临时 repo 测 read→patch→test；覆盖绝对路径、`..`、Unicode、symlink swap、stale file、多 hunk 失败、stdout flood、stdin/resize duplicate、孙进程取消、dirty revert、两个 worktree 同名文件。每个失败断言目标 hash、进程树和 event terminal。

固定源码依据见 [sources.md](sources.md) 的 tool、snapshot、server PTY 与 workspace tests；remote receipt 是 `inference`。
