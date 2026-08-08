# Middleware 与 Hooks

## 职责与非目标

Middleware/Hooks 在稳定生命周期点插入日志、策略、上下文、工具包装、格式化和用户自动化。
它们扩展单一 runtime，不得形成不可见的第二套 agent loop、绕过 sandbox 或直接篡改持久化投影。
middleware 适合进程内受信代码；第三方 hook 默认是不可信扩展，边界和权限应不同。
hook 不应依靠 UI 文案或 provider 原始 payload 作为稳定接口。

## Manifest 与执行接口

```text
HookManifest {
  id, version, lifecycle_points[], mode: observe|modify|block,
  priority, timeout_ms, failure_policy,
  permissions[], input_schema, output_schema?, provenance, signature?
}
HookInvocation {
  invocation_id, hook_ref, lifecycle_point,
  subject_ref, redacted_payload, deadline, cancellation_token
}
HookOutcome = Continue | Patch(validated_delta) | Block(reason) | Failed(error)
```

生命周期点至少包括 `turn_started`、`before_model`、`after_model`、`before_tool`、`approval_requested`、`after_tool`、`turn_stopped`。
执行顺序按 policy layer、priority、id 确定，不能依赖注册时竞态。
同一 hook id/version 只注册一次；热更新只影响新 invocation。

## 修改与阻断语义

observe hook 不能返回状态修改。
modify hook 只能修改 lifecycle 明确允许的字段，并经 schema 与 policy 再校验。
block hook 返回稳定 code 和用户安全说明，不能假装工具 result。
after hook 不得追溯改变已经 durable 的副作用；只能追加观察或补偿请求。
通知型 hook 使用 outbox 异步发送，不延长 turn 临界路径。

## 四级增量

| 等级 | 新增能力 | 不变量 |
|---|---|---|
| 能跑 | 进程内 observe hook | 版本化 lifecycle 与确定顺序 |
| 能用 | 配置顺序、超时、modify/block、失败策略 | schema 再校验与诊断事件 |
| 顺手 | 动态插件、条件匹配、异步通知、热重载 | invocation version 固定 |
| 好用 | 签名、隔离、管理员策略、兼容与供应链审计 | 最小权限和不可绕过 enforcement |

## 直接升级与回滚

先冻结 lifecycle payload schema，再开放 modify，最后开放第三方 block。
直接升级好用时，第三方 hook 先 observe-only shadow 运行并比较延迟与决策。
manifest 新字段使用拒绝式默认值；未知权限不自动授予。
回滚插件管理器时停止新 invocation，等待或取消旧版本，保留 outbox 与审计记录。
生命周期 major 不兼容时禁用 hook 并报告，不能拿旧 hook 猜字段。

## 失败模式与安全

- 超时：按 manifest 的 fail-open/fail-closed 处理，但安全/managed policy 强制 fail-closed；
- 崩溃：隔离 hook，runtime 记录失败并继续既定策略；
- 递归触发：携带 hook stack/depth，禁止自触发无限循环；
- 热重载竞态：invocation 固定版本，完成后再卸载；
- 敏感字段：按 manifest 最小化 payload，secret 用 capability handle 而非明文；
- output 注入：Patch 再做 schema、permission 与 size 校验；
- 供应链：来源、hash、签名、权限和更新记录可审计；
- 异步通知重复：outbox delivery id 幂等。

## 可执行验收

- 三个相同 priority hook 按稳定 id 顺序执行；
- observe hook 尝试修改 payload 被拒绝；
- before_tool block 后 executor 没有任何副作用；
- 超时分别验证 fail-open 与 managed fail-closed；
- hook 自触发在 depth limit 结束且 turn 不崩溃；
- 热更新时在途 invocation 继续旧版本，新调用使用新版本；
- 未授权 hook 看不到环境 secret 或工作区外文件；
- 通知 outbox 重复投递只产生一次外部动作。

## 证据与设计综合

`公开事实`：Claude Code hooks、Codex hooks/扩展和常见 middleware 系统都提供生命周期扩展点。
`设计综合`：本 manifest、顺序和隔离语义用于避免跨产品扩展失控，不复刻专有 hook payload。
插件发现见 [skills-plugins.md](skills-plugins.md)，策略见 [permission-policy.md](permission-policy.md)，可观测性见 [observability.md](observability.md)。
