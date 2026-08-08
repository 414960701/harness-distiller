# Aider-like 工作区与执行

## 目录

- [Workspace schema](#workspace-schema)
- [文件授权与应用](#文件授权与应用)
- [Git checkpoint](#git-checkpoint)
- [lint/test feedback](#linttest-feedback)
- [Shell 和命令执行](#shell-和命令执行)
- [失败、取消与降级](#失败取消与降级)
- [等级增量](#等级增量)

## Workspace schema

```yaml
WorkspaceSnapshot:
  root: absolute-path
  git_root: absolute-path|null
  head_sha: string|null
  files:
    relative-path:
      exists: boolean
      sha256: string|null
      mode: integer|null
      git_tracked: boolean
      git_dirty: boolean
      access: editable|read_only|unlisted|ignored
  captured_at: timestamp

ApplyOutcome:
  changeset_id: string
  status: applied|no_change|rejected|conflict|rolled_back|partial_failure
  edited_paths: [relative-path]
  preimage_hashes: object
  postimage_hashes: object
  journal_id: string|null
  errors: [ErrorEnvelope]
```

root 必须在 session 启动时 canonicalize。模型返回的每个路径先拒绝 absolute、NUL、`..` 穿越和 symlink escape，再解析为 root-relative path。read-only 与 ignored path 在 parser 之后、落盘之前由 policy 再判一次。

## 文件授权与应用

授权规则按优先级：

1. root 外、read-only、ignore policy deny：硬拒绝，不提供“一次允许”。
2. 已在 chat files 的普通文件：允许，但 dirty 时建立用户 checkpoint。
3. repo 中未加入的文件：显示 diff preview，询问是否加入并允许编辑。
4. 新文件：询问创建；允许后加入 chat files。
5. delete/rename：即使已加入也要求显式高风险确认，除非配置已预授权。

`--yes` 或 automation grant 可以自动回答 3/4，但审计仍记录 rule 和 actor。read-only 不能被 `--yes` 绕过。

原子应用伪代码：

```python
def apply_changeset(snapshot, edits):
    postimages = simulate_all(snapshot, edits)
    verify_expected_hashes(snapshot)
    journal = begin_journal(snapshot, postimages)
    try:
        for path, bytes_ in postimages:
            write_temp_same_fs(path, bytes_)
            preserve_mode_if_existing(path)
            fsync_and_replace(path)
            journal.mark_applied(path)
        journal.commit()
        return applied(postimages)
    except Exception:
        journal.restore_preimages_reverse_order()
        return rolled_back_or_partial_failure()
```

Git 可以恢复已提交状态，但不能替代 apply transaction：parser 失败、多文件中途写失败和无 Git 模式仍需零/可恢复部分写入。删除文件的 preimage 可存 journal 或 trash，journal 内容受权限保护并在 commit 后清理。

## Git checkpoint

若启用 Git，编辑前记录 `base_head`。目标文件已有 dirty change 且 `dirty_commits=true` 时，先只提交这些用户变更，避免与 AI edit 混合。AI edit 应单独 commit；commit message 可由 weak model根据 diff + history 生成，失败时用确定性 fallback。

```yaml
GitCheckpoint:
  id: string
  kind: user_dirty|agent_edit|lint_followup
  base_sha: string|null
  commit_sha: string|null
  paths: [relative-path]
  message: string
  authored_by_agent: boolean
  created_in_session: boolean
  pushed: boolean|null
```

只有 `agent_edit` 且 `created_in_session=true` 的 hash 加入 `aider_commit_hashes`。commit hooks 是否运行必须显式配置；基线默认可跳过 hook，不能声称 hook 已验证。commit 失败不回滚已成功文件修改，而是标记 `applied_uncommitted` 并强警告 `/undo` 不可保证。

Git unavailable 时仍允许 no-git 模式，但启动公告必须提示恢复能力降低；至少保留 diff preview 和 transaction journal。

## lint/test feedback

lint 接口接受 edited files；内置 linter 可按扩展名路由，用户命令必须能接收文件路径。test 接口执行配置的项目级命令，不自动追加文件名。

```yaml
ValidationRequest:
  kind: lint|test
  command: [string]
  cwd: absolute-path
  paths: [relative-path]
  timeout_ms: integer
  env_allowlist: [string]

ValidationOutcome:
  exit_code: integer|null
  signal: integer|null
  stdout: string
  stderr: string
  duration_ms: integer
  timed_out: boolean
  output_truncated: boolean
```

exit 0 表示验证通过；非零、signal、timeout 分别保留。formatter 可能修改文件且首次返回非零，不能盲目判断“AI 修复失败”：运行后重新 hash，若有变化，把 formatter change 纳入新 checkpoint，并允许配置二次验证。

反馈给模型时包含命令、退出码、经过长度限制的 stdout/stderr 和已编辑文件，不包含完整环境变量。用户拒绝修复时 turn 可以 `completed`，但 `validation.status=failed`，界面不能显示全绿。

## Shell 和命令执行

Aider-like 主要 shell 入口有 `/run`、`/test`、`/git` 和模型建议的 shell commands。每条命令都应在 root cwd 运行、显示完整命令、要求确认；模型建议必须 `explicit_yes_required`，支持同组确认与“永不允许”。重复建议在同轮去重。

CommandRunner 最低要求：argv/shell 模式区分、cwd 固定、timeout、stdout/stderr capture、output limit、process group cancel、exit code。若使用 shell 字符串，审计必须原样显示，不能在日志里渲染成不同命令。

`/git` 是用户直接命令仍有破坏风险；复刻可在 host mode 下允许，但对 reset/clean/checkout 等高风险子命令追加确认。高级 sandbox 模式用隔离 runner 替换实现，不改变 `ValidationOutcome`。

## 失败、取消与降级

| 场景 | 结果 |
|---|---|
| edit path 在响应期间变化 | `workspace_conflict`，零写入，重读上下文 |
| 第二个文件写失败 | journal 逆序恢复；无法恢复则 `partial_failure` 并列出路径 |
| Git detached/no commits | 可 commit 或 no-git 降级；undo 根据 graph 能力判断 |
| lint executable 不存在 | validation failed，`spawn_error`，不进入无限 reflection |
| test timeout | kill process group，保留截断输出和 timed_out |
| 用户 Ctrl-C 在 command | TERM/KILL，turn cancelled 或继续交互 |
| 用户 Ctrl-C 在 apply | 完成原子临界区或回滚后取消 |
| 磁盘满 | rollback journal；禁止宣称 commit 成功 |

## 等级增量

| 等级 | workspace 增量 |
|---|---|
| runnable | root-relative 检查、内存 preview、单文件安全写、手动 Git checkpoint |
| usable | 多文件 journal、auto/dirty commit、lint/test、确认和 cancel/timeout |
| productive | stale hash、mode preservation、formatter detection、structured outcomes、undo provenance |
| polished | 强 sandbox 可选、资源限额、远程 workspace adapter、crash recovery 和故障注入 |

直接升级保持 WorkspaceSnapshot、ApplyOutcome、GitCheckpoint 和 ValidationOutcome schema；新的 runner 或 sandbox 只替换 backend。
