# Patch 与编辑

## 目录

- [职责](#职责)
- [非目标](#非目标)
- [接口与 Schema](#接口与-schema)
- [状态机](#状态机)
- [应用算法](#应用算法)
- [四级增量](#四级增量)
- [直接升级与回滚](#直接升级与回滚)
- [失败模式与攻击面](#失败模式与攻击面)
- [可执行验收](#可执行验收)
- [来源与设计综合](#来源与设计综合)

## 职责

Patch 层把模型建议表示为带 base revision 的结构化 change set，预览、授权、应用并返回实际 diff。

它区分模型 proposed、runtime applied、用户 manual 和 formatter generated 变化，避免把整份工作区归因给 Agent。

## 非目标

- 不直接决定路径权限或 sandbox 范围。
- 不把模糊 patch 成功当作语义正确。
- 不覆盖 dirty tree 或用户审批后产生的新修改。
- 不以 rewind 承诺回滚 shell、网络或数据库副作用。
- 不替代测试和 [diff-review.md](diff-review.md) 的语义审查。

## 接口与 Schema

```yaml
ChangeSet:
  id: string
  workspace_revision: string
  files:
    - path_uri: string
      base_hash: sha256:string|null
      operation: create|modify|rename|delete
      hunks: [PatchHunk]
  provenance: model|user|formatter|migration
```

```yaml
ApplyResult:
  status: applied|partial|conflict|denied|failed
  per_file: [{path_uri, status, before_hash, after_hash, actual_diff_ref}]
  checkpoint_id: string|null
  diagnostics: [object]
```

## 状态机

`proposed -> validated -> previewed -> authorized -> applying -> applied | partial | conflict | failed`

审批绑定 change set digest；任何 hunk、path 或 base hash 改变都需重新决策。

多文件“事务”必须声明范围：本地临时区可 all-or-nothing，跨卷/远程可能只能 compensating rollback。

## 应用算法

1. 校验 workspace 和 change set schema。
2. canonicalize 每个 URI 并独立 policy evaluate。
3. 比对 base hash 和 dirty state。
4. 在隔离 temp/tree 中模拟 apply。
5. 生成精确 preview 与 digest。
6. 获得授权后再次比对 revision。
7. 提交、重读、计算 actual diff。
8. formatter 产生的额外 diff 独立归因。

## 四级增量

### runnable / 能跑

单文件精确 hunk、base hash、实际 diff 和冲突失败。

### usable / 能用

多文件 change set、preview、rename/delete、checkpoint、部分失败报告。

### productive / 顺手

AST/LSP 辅助、局部接受、formatter provenance、批量 undo 和 IDE 映射。

### polished / 好用

大型 migration、策略审查、协作 revision、远程事务和可验证恢复。

## 直接升级与回滚

旧单文件 patch 可包装为单项 ChangeSet；缺 base hash 的历史提议必须重新读取后确认。

从 usable 直升 polished 时先版本化 change set/diff artifact，再引入 AST 或远程 executor，不能改变精确文本 fallback。

回滚关闭 AST/协作 adapter 时仍可用实际 unified diff；已应用 change 不自动撤销，需显式 checkpoint rewind 或 inverse patch。

## 失败模式与攻击面

- 模糊 hunk 应用到相似但错误的位置。
- 行尾、Unicode normalization 或编码改变造成全文件 diff。
- rename 与 delete 隐藏敏感目标。
- symlink 在 preview 和 apply 之间交换。
- 用户并发编辑导致 lost update。
- formatter 修改未审批文件。
- 多文件提交一半后进程崩溃。
- inverse patch 覆盖用户后续修改。
- patch 内容诱导终端 ANSI/HTML 注入预览界面。

冲突是正常状态，不应通过扩大 fuzz 或覆盖 whole file 自动“修复”。

## 可执行验收

- 修改 hunk 后复用旧 approval，runtime 拒绝 digest mismatch。
- base hash 变化时不应用，用户内容保持。
- CRLF、UTF-16、末尾无换行 fixture 的实际 diff 可解释且无意外转码。
- 两文件 change set 在第二文件失败时符合声明的 transaction mode。
- formatter 触及第三文件时第三文件单独显示并重新授权。
- rename/delete 的 source、destination 和 effect 均进入审批。
- symlink 交换后 root 外 sentinel 不变。
- undo 遇用户后续修改时报告 conflict，不强制覆盖。

## 来源与设计综合

Patch 表示参考 unified diff、Git index 和 LSP WorkspaceEdit 的公开语义；change set digest、事务边界和归因 schema 是设计综合。

- Git diff format：https://git-scm.com/docs/diff-generate-patch
- Git index：https://git-scm.com/docs/git-update-index
- LSP WorkspaceEdit：https://microsoft.github.io/language-server-protocol/specifications/lsp/3.17/specification/#workspaceEdit

底层文件原子性见 [filesystem.md](filesystem.md)，Git 恢复与 dirty tree 见 [git-worktree.md](git-worktree.md)，事件包装见 [../implementation/protocol.md](../implementation/protocol.md)。

生成器可选择文本、AST 或 LSP engine，但必须保留 base revision、实际 diff 和冲突 oracle。
