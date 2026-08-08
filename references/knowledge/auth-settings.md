# Auth 与 Settings

## 职责与非目标

认证确认主体与会话，Settings 将用户偏好、项目配置、profile、provider 和管理员 requirements 分层解析。
Secrets 与普通设置分库；模型、日志和 UI 不接收 refresh token/原始密钥。
运行时使用不可变 effective config snapshot，避免热更新让历史动作不可解释。
认证成功不等于授权所有资源；RBAC/capability/policy 仍逐动作裁决。

## 配置 schema

```yaml
ConfigValue:
  key: string
  value: json|secret_handle
  source: default|user|profile|project|organization|runtime
  scope: string
  policy: overridable|managed|forbidden
  schema_version: integer
AuthSession:
  id: string
  subject: string
  provider: string
  assurance: string
  scopes: [string]
  status: active|expiring|reauth|required|revoked
  expires_at: timestamp
EffectiveConfigSnapshot:
  id: string
  values_digest: string
  source_map: object
  created_at: timestamp
```

接口：`login`, `logout`, `refresh`, `resolve_config`, `validate`, `snapshot`, `explain_source`, `rotate_secret`。
优先级与管理策略确定性解析；组织 forbidden/managed 项不能被项目或用户层削弱。
配置页面显示 effective value、来源、是否受管与重启/新 Run 生效范围。

## 生命周期与存储

Auth 按 `active → expiring → reauth|required|revoked` 转移；refresh 单飞避免并发风暴。
provider key/OAuth token 存 OS keychain/secret broker，配置只保存 handle。
TaskRun 启动冻结 config/provider/model/capability snapshot；设置变化默认只影响新 Run。
logout 撤销本地 session、停止敏感订阅并清理可撤销缓存，不删除用户任务数据。
多账号数据、cookie、connector 和缓存均按 subject/profile 隔离。

## 四级增量

### `runnable` 能跑

本地单用户、一个 provider key handle、schema 校验和环境变量导入。

### `usable` 能用

增加多 provider、profile、项目配置、来源解释、优先级和安全 logout。

### `productive` 顺手

增加 OAuth、账户切换、配额/限额、跨设备设置同步、token refresh 和配置迁移。

### `polished` 好用

增加 SSO/OIDC、RBAC、managed config、SCIM/设备策略、审计、密钥轮换和灾备。

## 直接升级与回滚

先将明文 secret 迁入 broker，写入成功并验证后再删除旧值并轮换。
把扁平配置转换为带 source/scope/schema 的记录，保存原配置备份与映射报告。
OAuth/SSO 与旧认证并行验证，按账号灰度；切换不自动合并数据主体。
回滚 resolver/auth adapter 时旧 snapshot 可读，managed policy 不因降级被绕过。

## 失败模式与安全

- 优先级混乱：resolver 输出 source map 与冲突原因。
- token 过期：只阻塞相关 provider/connector，安全 reauth。
- refresh 竞态：singleflight + token version，旧响应不能覆盖新 token。
- logout 残留：撤销 session、websocket、download URL 与敏感 cache。
- 多账号串数据：storage/cache/event subscription key 含 subject/profile。
- 管理员收紧：新动作立即遵守；运行中高风险调用重新评估。
- 日志泄密：secret handle 可审计，明文禁止进入模型/日志/通知。

## 验收 oracle

1. 同 key 多层配置可解释 effective value 与来源。
2. 组织 forbidden 设置不能被项目文件覆盖。
3. 并发 refresh 只产生一次有效交换，旧 token 不复活。
4. logout 后旧标签、下载 URL 和连接器调用全部失效。
5. 两账号任务、缓存、provider key 和通知不串线。
6. schema 迁移失败可回滚且明文 secret 不重新落盘。

## 来源与设计综合

认证协议参考 [OpenID Connect Core](https://openid.net/specs/openid-connect-core-1_0.html) 与 [OAuth 2.0 Security Best Current Practice](https://www.rfc-editor.org/rfc/rfc9700.html)。
产品具体设置键、账户 UI 和组织控制由 dossier 定义；共享层维护分层解析、snapshot 与 secret 边界。
