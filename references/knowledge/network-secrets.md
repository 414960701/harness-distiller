# Network 与 Secrets

## 目录

- [职责](#职责)
- [非目标](#非目标)
- [接口与 Schema](#接口与-schema)
- [状态与边界](#状态与边界)
- [Policy 与 Enforcement](#policy-与-enforcement)
- [四级增量](#四级增量)
- [直接升级与回滚](#直接升级与回滚)
- [失败模式与攻击面](#失败模式与攻击面)
- [可执行验收](#可执行验收)
- [来源与设计综合](#来源与设计综合)

## 职责

Network 层把已批准的访问意图落实为 DNS、连接、redirect 和代理级 enforcement；Secrets 层用 opaque handle 向最小执行范围提供凭证。

两者共同阻止“网络已允许”演变成任意出口，也阻止秘密进入 prompt、普通日志、事件、截图或环境快照。

## 非目标

- 不把域名 allow 解释为允许该站点所有写操作。
- 不让模型直接读取 secret 明文再自行放入 header。
- 不仅靠 URL 字符串 matcher 阻止真实连接绕过。
- 不承诺能检测所有加密流量中的数据外泄。
- 不把日志脱敏当运行时访问控制。

## 接口与 Schema

```yaml
NetworkIntent:
  operation: fetch|connect|listen|external_write
  scheme: https|http|ssh|tcp|other
  host: string
  port: integer
  method: string|null
  redirect_policy: same_origin|reapprove|deny
  data_classification: public|workspace|sensitive
```

```yaml
SecretLease:
  handle: secret://provider/name/version
  audience: string
  allowed_process_id: string
  allowed_destinations: [object]
  expires_at: timestamp
  renewable: boolean
```

```yaml
EgressResult:
  status: allowed|denied|failed
  resolved_ips: [string]
  redirects: [string]
  proxy_policy_id: string
  bytes_in: integer
  bytes_out: integer
  secret_handles_used: [string]
```

## 状态与边界

`intent -> policy_decision -> dns_resolution -> route_enforcement -> tls/connect -> redirect_check -> terminal`

DNS 每次解析结果都按 public/private/link-local/loopback 分类；redirect 视为新目标。

Secret 为 `requested -> leased -> injected -> revoked|expired`；只向指定 process/socket 注入，不进入通用 env dump。

## Policy 与 Enforcement

Permission policy 按 logical destination、method、effect 和 data classification 决策。

代理/firewall 在真实连接时按解析 IP、SNI/Host、port、redirect 和租户 enforce；仅 policy allow 不足以开放 raw socket。

secret broker 在 audience 与 destination 都匹配时释放短期凭证；进程不能用 handle 查询明文。

## 四级增量

### runnable / 能跑

默认断网、按次人工放行、secret 默认不进模型和日志。

### usable / 能用

域/端口 allowlist、redirect 复核、环境脱敏、opaque handle、lease expiry。

### productive / 顺手

强制代理、OAuth broker、setup/agent 阶段分离、egress audit、自动轮换。

### polished / 好用

租户 vault、DLP/egress inspection、mTLS workload identity、离线撤销和攻击持续测试。

## 直接升级与回滚

把历史明文 credential 配置迁入 vault 时仅保存新 handle，不把旧值写入 migration log；完成后轮换旧凭证。

网络从 direct 切 proxy 先 shadow 记录目标，再改 preferred，最后 required；高风险租户可直接 hard fail。

回滚 proxy 时不得回到 unrestricted；降级为 deny/ask，并撤销无法 enforce destination 的 lease。

## 失败模式与攻击面

- DNS rebinding、CNAME、redirect、IP literal 和 IPv6 表示绕过。
- localhost、metadata service、private IP 和 Unix socket SSRF。
- TLS SNI、HTTP Host 与实际路由不一致。
- 包管理器、Git helper、浏览器或子进程绕过代理。
- secret 出现在 argv、env、`/proc`、core dump、stderr 或 tool result。
- prompt injection 诱导上传 workspace/secret。
- lease 在 cancel/崩溃后仍有效。
- 日志脱敏只匹配固定格式，编码后 secret 泄漏。
- 跨租户 cache、proxy connection 或 vault handle 混用。

## 可执行验收

- allow 域后 redirect 到未批准域/private IP，连接前被拒并生成新 decision。
- DNS 第一次 public、第二次 private 的 rebinding fixture 不能到达 private sentinel。
- raw socket、Unix socket、IPv6 和 metadata endpoint 绕过均失败。
- secret 不出现在 model request、argv、env dump、event、hook、artifact preview 和 terminal。
- lease 只能被指定 process/destination 使用，复制 handle 到另一进程失败。
- cancel/session end 后 lease 撤销，后续连接不能复用。
- proxy unavailable 且 enforcement required 时网络 fail closed。
- 两租户相同 secret name 得到不同 lease，不能跨租户使用。

## 来源与设计综合

参考 HTTP redirect/DNS/TLS 公开语义、常见 egress proxy、OAuth workload identity 和 secret vault lease 模型；统一 intent/lease schema 是设计综合。

- HTTP Semantics：https://www.rfc-editor.org/rfc/rfc9110
- OAuth 2.0 Security BCP：https://www.rfc-editor.org/rfc/rfc9700
- OWASP SSRF prevention：https://cheatsheetseries.owasp.org/cheatsheets/Server_Side_Request_Forgery_Prevention_Cheat_Sheet.html

决策规则见 [permission-policy.md](permission-policy.md)，系统级网络边界见 [sandbox.md](sandbox.md)，事件脱敏与存储见 [../implementation/storage.md](../implementation/storage.md)。

无法 inspect 的加密或非 HTTP 协议必须在 capability/threat model 中说明，不得宣称完全阻断 exfiltration。
