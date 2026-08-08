# Diff 与 Review

## 职责与非目标

Review 保存 base、current、proposed 三个版本与稳定 hunk identity，让用户可追踪、评论、接受或拒绝变更。
它不是纯文本美化器，不把 UI 本地编辑当成已提交事实，也不把“测试通过”混同“diff 已接受”。
接受、拒绝、stage、revert 和 comment 都是服务端/执行层 command。
Review 不绕过文件 grant、expected hash、branch protection 或发布权限。

## 数据 schema

```yaml
ReviewSet:
  id: string
  task_id: string
  base_revision: string
  current_revision: string
  proposed_revision: string
  status: open|stale|accepted|partially_accepted|rejected|conflicted
Hunk:
  id: string
  file_identity: string
  base_range: [integer, integer]
  proposed_range: [integer, integer]
  context_hash: string
  status: pending|accepted|rejected|stale
Comment:
  id: string
  anchor: hunk_id|symbol_id|line_fingerprint
  body: string
  status: open|resolved|outdated
```

接口：`create_review`, `refresh`, `accept_hunk`, `reject_hunk`, `comment`, `apply`, `stage`, `revert`, `export`。
command 带 expected current hash；应用后产生新的文件/artifact/event receipt。
rename 使用 file identity/similarity 关联，二进制只展示元数据/专用预览。

## 状态与事件投影

Review panel 由 ReviewCreated/HunkChanged/CommentAdded/ApplySucceeded/ConflictDetected 事件投影。
文件在外部变化时 ReviewSet 进入 stale，先 refresh/rebase 再接受。
评论重映射优先 hunk/context/symbol；无法可靠映射则标 outdated，不猜行号。
大 diff 分页/虚拟化，但 summary、未决 hunk、风险文件与验证状态始终可见。

## 四级增量

### `runnable` 能跑

生成 unified diff，显示 base/current 路径与只读预览。

### `usable` 能用

增加逐 hunk 接受/拒绝、inline comment、expected hash、冲突和 apply receipt。

### `productive` 顺手

增加自动 review、诊断/测试关联、rename、跨文件 summary、stage/revert 与 comment remap。

### `polished` 好用

增加策略 gate、多人协作、PR 同步、代码所有者、超大 diff 虚拟化和审计导出。

## 直接升级与回滚

先为旧 diff 记录 base/current/proposed hash 与 ReviewSet id，再开放 hunk command。
应用引擎先 preview-only，对真实 workspace 使用原子写/事务与备份。
PR/多人协作最后接入，远端状态与本地 ReviewSet 用 external id 对齐。
回滚 UI/自动 review 不删除已提交评论与 receipt；文件 revert 是独立显式 command。

## 失败模式与安全

- 行漂移：context hash 不符时 stale，不应用旧 hunk。
- rename/delete：使用稳定 file identity 并要求确认破坏性动作。
- 二进制/大文件：专用 viewer、大小限制，不生成伪文本 diff。
- 恶意 diff：渲染转义 ANSI/HTML，文件内容标 untrusted。
- 部分 apply：事务或逐文件 receipt，明确 partial/rollback 状态。
- 评论越权：按 repo/review ACL 校验，通知不泄露私有代码。

## 验收 oracle

1. 插入行导致旧 hunk anchor 失配时不能错误应用。
2. rename 后评论可映射到新文件或明确 outdated。
3. 两用户同时接受冲突 hunk 时一个得到 expected-seq 冲突。
4. apply 失败不会让 UI 假装 accepted，文件可恢复。
5. 二进制文件不进入普通 patch parser。
6. Review accepted 与测试验证分别显示，不互相冒充。

## 来源与设计综合

参考 [Git diff format](https://git-scm.com/docs/diff-format) 与 [GitHub review comments](https://docs.github.com/en/rest/pulls/comments) 的公开模型。
产品 dossier 决定事件信封、Workspace 写入与 PR connector；共享层只定义版本、hunk 和 command 语义。
