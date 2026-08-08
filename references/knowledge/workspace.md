# Workspace

## 目录

- [职责](#职责)
- [非目标](#非目标)
- [接口与 Schema](#接口与-schema)
- [解析状态](#解析状态)
- [Policy 与 Enforcement](#policy-与-enforcement)
- [四级增量](#四级增量)
- [直接升级与回滚](#直接升级与回滚)
- [失败模式与攻击面](#失败模式与攻击面)
- [可执行验收](#可执行验收)
- [来源与设计综合](#来源与设计综合)

## 职责

Workspace 把启动目录、可读/可写 roots、临时区、忽略规则、项目身份和执行环境解析为一次 turn 的不可变边界快照。

它是路径授权和执行隔离的共同输入：策略层判断“是否允许”，filesystem/shell/sandbox 执行层判断“是否真的越界”。

## 非目标

- 不把 cwd 自动等同于全部可写范围。
- 不执行项目 hook、MCP 或脚本；信任门由扩展运行时处理。
- 不用字符串前缀代替 realpath、卷或 inode 身份。
- 不负责 Git 合并；并行隔离见 [git-worktree.md](git-worktree.md)。
- 不把 CLAUDE.md 等模型指令当权限策略。

## 接口与 Schema

```yaml
WorkspaceSpec:
  requested_cwd: absolute_path
  declared_roots: [absolute_path]
  mode: local|container|remote
  trust_requirement: none|read_only|executable_config
```

```yaml
WorkspaceSnapshot:
  id: string
  revision: string
  cwd_uri: workspace://root/relative
  roots: [{id, canonical_path, volume_identity, access}]
  temp_uri: workspace://temp/session
  ignore_digest: string
  trust_state: unknown|restricted|trusted|revoked
  platform_capabilities: object
```

协议只传 logical URI；绝对路径保留在 executor 侧，避免跨主机泄露和错误映射。

## 解析状态

`requested -> canonicalizing -> identifying -> trust_check -> ready | restricted | rejected`

- canonicalizing 解析 `..`、符号链接、junction 和大小写归一。
- identifying 绑定设备/卷身份，防止同名目录替换。
- trust_check 只决定项目可执行配置是否装载，不扩大 filesystem 权限。
- ready 后 snapshot 不原地改变；环境漂移产生新 revision。

## Policy 与 Enforcement

Permission policy 消费 logical resource、操作类型和 snapshot revision，返回 allow/ask/deny。

Filesystem、shell 和 sandbox 在操作瞬间再次解析真实目标并验证 root；仅有 allow 决策不能保证路径仍安全。

远程 workspace 必须由 remote executor 证明 root 映射，不让客户端绝对路径成为服务器权限依据。

## 四级增量

### runnable / 能跑

单 local root、固定 temp、显式 capability 报告；不支持 hard sandbox 时必须说明。

### usable / 能用

多 root、ignore、canonical identity、trust gate、snapshot revision 和 path URI。

### productive / 顺手

Git worktree、容器和远程映射、watcher 驱动 revision、项目环境发现。

### polished / 好用

组织 workspace profile、跨主机 identity、租户隔离、配额、迁移与平台等价测试。

## 直接升级与回滚

usable 可直接升 polished：先为现有绝对路径生成 logical URI 和 root id，再增加远程映射与组织策略。

旧 session 保留 snapshot 与 mapper version；不能用当前 cwd 重新解释历史路径。

回滚只停用新 mapper/capability，保留 identity 数据；无法安全映射时以 read-only 打开，不猜路径。

## 失败模式与攻击面

- symlink 在审批后、打开前交换造成 TOCTOU。
- 大小写不敏感文件系统让两个显示路径指向同一对象。
- mount/bind/junction 把 root 内路径映射到外部。
- Git file 或嵌套仓库误导项目根发现。
- 恶意 ignore 隐藏敏感或关键验证文件。
- remote client/server mapper 版本不同导致授权错位。
- temp 落在共享、可预测或可被其他用户读取的位置。
- workspace 被移动/替换后继续复用旧 trust grant。

失败默认缩小范围；root 身份变化时撤销可执行配置 trust，不静默继续。

## 可执行验收

- `../outside`、symlink、junction 和大小写变体均不能越出声明 root。
- 审批后交换 symlink，executor 在 open 时仍拒绝。
- 同一 snapshot 的 logical URI 在 local/container/remote 映射到预期对象。
- root 被替换后 revision 改变，旧 permission decision 失效。
- 未 trusted 项目可以只读发现，但 hook/MCP process 未启动。
- session temp 权限仅当前用户/租户可读写，结束后按保留策略清理。
- 多 root 中只授权 root A 写时，root B 的 read 和 write 结果符合独立规则。

## 来源与设计综合

路径解析参考 POSIX `openat`/`realpath`、Windows reparse point 与容器 mount namespace 的公开语义；具体 adapter 为设计综合。

- POSIX open：https://pubs.opengroup.org/onlinepubs/9699919799/functions/open.html
- Windows reparse points：https://learn.microsoft.com/en-us/windows/win32/fileio/reparse-points
- Git worktree：https://git-scm.com/docs/git-worktree

与 [../implementation/policy-execution.md](../implementation/policy-execution.md) 的决策/执行分层、[../implementation/protocol.md](../implementation/protocol.md) 的稳定 URI 合同配套使用。

产品差量应记录在各产品 dossier；不得从任一闭源产品行为推断其内部 workspace 类或 trust 存储。
