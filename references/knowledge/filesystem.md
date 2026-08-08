# Filesystem 工具

## 目录

- [职责](#职责)
- [非目标](#非目标)
- [接口与 Schema](#接口与-schema)
- [操作状态](#操作状态)
- [Policy 与 Enforcement](#policy-与-enforcement)
- [四级增量](#四级增量)
- [直接升级与回滚](#直接升级与回滚)
- [失败模式与攻击面](#失败模式与攻击面)
- [可执行验收](#可执行验收)
- [来源与设计综合](#来源与设计综合)

## 职责

Filesystem 提供有界的 list、read、stat、search、write、move 和 delete，并统一路径授权、编码、换行、大小上限、二进制检测和并发冲突。

所有操作绑定 [workspace.md](workspace.md) 的 snapshot；每次真实 open/rename 时重新 enforcement，而不是信任模型传来的 path。

## 非目标

- 不执行 shell 命令或解释通配符脚本。
- 不决定用户是否批准；决策见 [permission-policy.md](permission-policy.md)。
- 不用“只读工具”注解代替系统调用约束。
- 不静默转换未知编码或覆盖用户并发修改。
- 不承担语义代码重构；结构化修改见 [patch-edit.md](patch-edit.md)。

## 接口与 Schema

```yaml
FileRequest:
  operation: list|read|stat|search|write|move|delete
  workspace_revision: string
  path_uri: workspace://root/relative
  expected_hash: sha256:string|null
  range: {offset, length}|null
  limits: {max_bytes, max_entries, timeout_ms}
```

```yaml
FileResult:
  status: succeeded|failed|denied|conflict|truncated
  canonical_uri: string
  content_ref: inline|artifact|null
  hash_before: string|null
  hash_after: string|null
  encoding: string|null
  changed: boolean
  reason_code: string|null
```

## 操作状态

`received -> normalized -> authorized -> opened -> transferred -> committed | conflicted | failed`

写操作采用 temp write、fsync 和 atomic rename；跨卷或平台不支持时必须报告 weaker_atomicity。

delete 默认移至可恢复区或生成 checkpoint；永久删除需要单独 effect 分类。

## Policy 与 Enforcement

策略输入使用规范化 logical URI、operation、size estimate、target type 和 workspace revision。

executor 使用 dir-fd/openat 类能力或平台等价机制把解析限制在 root；先 check 再普通 open 存在 TOCTOU。

allow 只适用于展示过的 URI、operation 和 revision；move 的 source 与 destination 分别授权。

## 四级增量

### runnable / 能跑

文本 list/read/write、单 root、字节上限和显式 ask。

### usable / 能用

glob/search、原子写、hash compare-and-swap、artifact、编码诊断和 recoverable delete。

### productive / 顺手

watcher、增量 search index、远程 FS adapter、批量 change set 和细粒度审计。

### polished / 好用

配额、敏感路径策略、多租户 object capability、跨平台一致性和持续攻击测试。

## 直接升级与回滚

从 runnable 直升 polished 时，先为历史 write result 补 unknown hash 标记，不能伪造 base hash。

新 CAS 与 artifact schema 以版本化字段增加；旧 client 不识别冲突时禁止写而不是 last-write-wins。

回滚可停用 watcher/index，不回滚 hash 和审计；新编码无法由旧 reader 表示时只读导出。

## 失败模式与攻击面

- `..`、symlink、hardlink、junction、mount crossing 越界。
- stat 后目标交换造成 TOCTOU。
- 稀疏文件或压缩炸弹绕过 size estimate。
- 非 UTF-8 与混合换行被损坏。
- 原子 rename 在网络盘、跨卷或 Windows sharing 下失败。
- 用户同时编辑导致 lost update。
- search/index 返回旧 revision，模型据此错误修改。
- secret 内容进入 tool result、日志或 artifact preview。
- delete/move 的目标类型与审批时不同。

失败返回稳定 reason code 和实际未提交范围；部分批量写必须列出每个 path 状态。

## 可执行验收

- symlink 在 authorize 后交换，外部 sentinel 不被读写。
- expected hash 不匹配时返回 conflict，用户新内容保持不变。
- kill writer 的每个阶段，目标要么旧内容要么完整新内容，不出现半文件。
- 1GB 稀疏/二进制文件受 max_bytes 限制并转 artifact 或拒绝。
- UTF-16、非 UTF-8、CRLF fixture 不被静默转码。
- move 跨两个权限 root 时，任一端 deny 则不提交。
- secret fixture 不出现在普通 event、preview 和 model context。
- search result 携带 revision；文件变化后旧结果触发重新读取。

## 来源与设计综合

原子性与路径约束参考 POSIX rename/openat、Windows file sharing/reparse point 和常见内容寻址存储语义；接口是设计综合。

- POSIX rename：https://pubs.opengroup.org/onlinepubs/9699919799/functions/rename.html
- Linux openat2：https://man7.org/linux/man-pages/man2/openat2.2.html
- Windows file management：https://learn.microsoft.com/en-us/windows/win32/fileio/file-management

通用 tool envelope 见 [../implementation/tools.md](../implementation/tools.md)，持久化与 artifact 见 [../implementation/storage.md](../implementation/storage.md)，本文不复制其完整事件定义。

任何平台无法提供的原子或隔离语义都必须进入 capability report，不能以文档约定冒充 enforcement。
