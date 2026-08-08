# Git 与 Worktree

## 目录

- [职责](#职责)
- [非目标](#非目标)
- [接口与 Schema](#接口与-schema)
- [状态与归因](#状态与归因)
- [Worktree 生命周期](#worktree-生命周期)
- [四级增量](#四级增量)
- [直接升级与回滚](#直接升级与回滚)
- [失败模式与攻击面](#失败模式与攻击面)
- [可执行验收](#可执行验收)
- [来源与设计综合](#来源与设计综合)

## 职责

Git 层提供 status、diff、log、blame、branch、worktree、stage、commit 和远程动作的结构化接口，并区分用户改动、Agent change set 和 repository 基线。

Worktree 为并行任务提供文件隔离；它不自动解决权限、网络、秘密和跨分支语义冲突。

## 非目标

- 不把 dirty tree 当干净基线或静默 stash/reset。
- 不默认执行 destructive checkout、clean、force push 或 history rewrite。
- 不把 commit 等同任务验证或安全审核完成。
- 不把 worktree 当 sandbox；进程仍需 [sandbox.md](sandbox.md)。
- 不承诺 Git 能回滚数据库、API 或其他外部副作用。

## 接口与 Schema

```yaml
RepoSnapshot:
  repo_id: string
  worktree_id: string
  git_dir_identity: string
  head: string|null
  branch: string|null
  status_digest: string
  user_dirty_paths: [string]
  agent_change_set_ids: [string]
```

```yaml
GitAction:
  kind: status|diff|stage|commit|branch|worktree_create|merge|push|cleanup
  repo_snapshot: string
  pathspecs: [string]
  expected_head: string|null
  remote: string|null
  destructive: boolean
```

```yaml
GitResult:
  status: succeeded|failed|conflict|denied|outcome_unknown
  head_before: string|null
  head_after: string|null
  actual_paths: [string]
  stdout_ref: string|null
  recovery_ref: string|null
```

## 状态与归因

`discovered -> snapshotted -> action_planned -> authorized -> executing -> verified | conflict | failed`

stage/commit 绑定 expected HEAD、status digest 和 pathspec；变化后旧批准失效。

Agent 首次写前记录 user dirty baseline；actual diff 以 base、user-before、agent-after 三方归因。

## Worktree 生命周期

`allocating -> ready -> active -> handoff|merging -> retained|cleaning -> removed`

- worktree path 由安全 allocator 创建，不能接受模型任意绝对路径。
- 每个任务记录 base commit、branch、owner run 和 lease。
- merge 前重新获取 target branch 和用户变更状态。
- cleanup 前保存未提交 patch/artifact；锁定或未知 ownership 时不删。

## 四级增量

### runnable / 能跑

只读 status/diff/log、repo identity 和 dirty tree 警告。

### usable / 能用

精确 path stage、安全 commit、恢复点、expected HEAD 和结构化冲突。

### productive / 顺手

每任务 worktree、并行分支、handoff、局部接受和自动 patch artifact。

### polished / 好用

远程 PR/push、签名、策略检查、多仓库协调、租约和安全垃圾回收。

## 直接升级与回滚

单 worktree 升并行时先为当前目录登记 main worktree identity 和 user dirty baseline，再创建任务 worktree。

历史 Agent diff 缺 provenance 时标 unknown，不自动纳入 commit；新 stage API 用 pathspec + hash。

回滚并行模式时保留所有未合并 branch/worktree 和 recovery artifact；只停止新分配，不自动删除。

## 失败模式与攻击面

- 用户 dirty change 被 reset、checkout、stash pop 或 commit 混入。
- pathspec、submodule、symlink、LFS filter 扩大实际文件范围。
- unborn branch、detached HEAD 或 replace refs 破坏假设。
- worktree pointer/Git file 指向意外 git dir。
- hook、smudge/clean filter、credential helper 执行任意代码或联网。
- stage 后用户再修改，commit 内容与预览不同。
- force push、远程名/URL 改变或凭证泄漏。
- 并行 agent 修改同一路径产生语义冲突。
- cleanup 删除仍有用户未提交内容的 worktree。

## 可执行验收

- dirty fixture 中 Agent commit 仅含批准 path/hash，用户 hunk 保留未 stage。
- stage 后改变文件或 HEAD，旧 commit approval 失效。
- unborn、detached、submodule、LFS 和 partial stage fixtures 给出正确结构化状态。
- 两 worktree 并行编辑同文件，merge 不 silent last-write-wins。
- malicious hook/filter/helper 在未 trusted 或 sandbox policy 下不执行/联网。
- remote URL 在批准后变化，push 被拒并重新 ask。
- crash/cleanup 前未提交 diff 可从 recovery artifact 恢复。
- worktree lease 未过期或 ownership 未知时 cleanup 不删除目录。

## 来源与设计综合

参考 Git 官方 porcelain/plumbing、index、worktree、submodule 和 hook 的公开语义；RepoSnapshot、lease 与归因 schema 是设计综合。

- Git worktree：https://git-scm.com/docs/git-worktree
- Git status porcelain：https://git-scm.com/docs/git-status
- Git hooks：https://git-scm.com/docs/githooks

文本 change set 见 [patch-edit.md](patch-edit.md)，真实文件边界见 [workspace.md](workspace.md)，远程凭证/网络见 [network-secrets.md](network-secrets.md)。

产品 adapter 可以提供 PR UI 或自动分支命名，但 destructive 和 remote action 仍经过共享 permission/event 合同。
