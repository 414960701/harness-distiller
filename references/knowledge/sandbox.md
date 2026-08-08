# Sandbox

## 目录

- [职责](#职责)
- [非目标](#非目标)
- [接口与 Schema](#接口与-schema)
- [状态与执行顺序](#状态与执行顺序)
- [平台 Adapter](#平台-adapter)
- [四级增量](#四级增量)
- [直接升级与回滚](#直接升级与回滚)
- [失败模式与攻击面](#失败模式与攻击面)
- [可执行验收](#可执行验收)
- [来源与设计综合](#来源与设计综合)

## 职责

Sandbox 是执行层的强制边界，限制获准代码实际可访问的文件、网络、进程、系统调用、设备和 IPC。

它消费规范化 execution spec 与 permission decision，但不信任模型、prompt、命令分类、tool annotation 或 UI 状态。

## 非目标

- 不决定用户意图是否合理；这属于 [permission-policy.md](permission-policy.md)。
- 不把容器默认配置自动视为安全隔离。
- 不承诺回滚已经允许的外部副作用。
- 不用 hook、提示词或命令 denylist 冒充 OS enforcement。
- 不宣称所有平台具有相同强度。

## 接口与 Schema

```yaml
SandboxRequest:
  execution_id: string
  platform: string
  readable_roots: [string]
  writable_roots: [string]
  network: {mode: deny|proxy_allowlist|unrestricted, destinations: [object]}
  ipc: {unix_sockets: deny|allowlist}
  resources: {cpu_ms, memory_bytes, pids, wall_ms}
  requirement: required|preferred
```

```yaml
SandboxReport:
  adapter: seatbelt|bubblewrap|container|microvm|none
  filesystem: enforced|partial|none
  network: enforced|proxy_only|none
  syscall: enforced|partial|none
  resource_limits: [string]
  profile_digest: string
  degradations: [string]
```

## 状态与执行顺序

`capability_probe -> profile_compile -> profile_validate -> spawn_confined -> monitor -> teardown`

profile 绑定 workspace revision、规范化路径、网络规则和 executable digest；审批后配置变化必须重编译。

`required` 无法满足时 fail closed；`preferred` 降级需返回 policy 重新 ask，不能静默执行。

## 平台 Adapter

- macOS：Seatbelt 等系统机制，记录实际 profile 能力。
- Linux/WSL2：namespace/bubblewrap、cgroup、seccomp 和网络代理组合。
- Windows：AppContainer、Job Object、WSL2、容器或 VM；单独声明能力。
- remote：容器/microVM 与租户 worker identity；远端必须出具 attested capability report。

列举 adapter 不代表任一产品内部采用；这是公开组件的设计选项。

## 四级增量

### runnable / 能跑

至少限制 workspace 写入、默认断网，并诚实显示 unenforced 项。

### usable / 能用

OS/容器隔离、可配置 roots、process tree、required hard fail 和平台 capability probe。

### productive / 顺手

网络代理、secret broker、profile cache、cgroup/resource limits、remote executor。

### polished / 好用

多租户 microVM、attestation、组织 profile、持续逃逸测试、平台等价/SLO。

## 直接升级与回滚

从软限制升级 hard sandbox 时，先发布 capability-only 模式，再以 preferred 观察，最后对高风险动作改 required。

profile schema 版本化并记录 digest；旧 session resume 时重新 probe，不沿用旧“已隔离”标记。

回滚 adapter 时必须降级 capability 并触发审批；不能为了可用性绕过 managed required。

## 失败模式与攻击面

- symlink、mount、`/proc`、device 或 Unix socket 逃逸。
- namespace 内 root 与宿主高权限映射。
- DNS、代理、redirect 或 raw socket 绕过网络限制。
- 子进程继承未预期 fd、secret 或 capability。
- cgroup/limit 未覆盖孙进程。
- profile cache 使用错误 workspace 或旧路径。
- sandbox helper 自身被替换或版本有漏洞。
- remote 多租户数据残留、镜像投毒和 worker 冒充。
- teardown 失败留下可继续执行的孤儿。

## 可执行验收

- read/write symlink、mount 和 proc/socket escape 均被真实 OS 层拒绝。
- allowlisted 域可达，IP literal、redirect、DNS rebinding 和 raw socket 绕过失败。
- fork bomb 受 pid 配额，内存/CPU 超限有结构化终态。
- helper 不存在或 profile compile 失败时 requirement=required 的 spawn 数为零。
- preferred 降级产生新 ask，批准卡展示具体缺失 enforcement。
- process tree 取消和 teardown 后无持有 workspace write fd 的进程。
- profile cache 的 workspace revision 变化后 miss 并重编译。
- 多租户 fixture 无文件、网络、cache 和日志串租户。

## 来源与设计综合

参考 Apple Sandbox/Seatbelt 可观察接口、bubblewrap、Linux namespaces/cgroups/seccomp、OCI 容器与 microVM 的公开文档；profile schema 是设计综合。

- bubblewrap：https://github.com/containers/bubblewrap
- Linux namespaces：https://man7.org/linux/man-pages/man7/namespaces.7.html
- OCI runtime spec：https://github.com/opencontainers/runtime-spec

决策协议见 [../implementation/policy-execution.md](../implementation/policy-execution.md)，进程生命周期见 [shell-process.md](shell-process.md)，网络与秘密见 [network-secrets.md](network-secrets.md)。

威胁模型和平台 capability 必须随产物交付；仅“命令成功运行在容器”不是隔离证明。
