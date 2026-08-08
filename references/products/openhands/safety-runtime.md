# OpenHands-like 安全与 Runtime 规格

## 目录

- [安全边界](#安全边界)
- [风险分析](#风险分析)
- [Confirmation Policy](#confirmation-policy)
- [Enforcement](#enforcement)
- [Secret 与数据](#secret-与数据)
- [Hook Skill Plugin MCP](#hook-skill-plugin-mcp)
- [Server 与租户](#server-与租户)
- [失败模式](#失败模式)
- [安全验收](#安全验收)

## 安全边界

严格分离四层：

1. Tool schema validation：参数形状正确；
2. SecurityAnalyzer：给 action 风险与解释；
3. ConfirmationPolicy：决定 allow/confirm；
4. Workspace enforcement：真正限制文件、进程、网络、资源和 secret。

前 3 层都不能替代第 4 层。用户 approve 只授权策略允许范围内的一次动作，不解除 sandbox ceiling。

不可信输入包括用户内容、仓库、网页、模型、工具输出、MCP、skill、plugin、hook 和恢复数据。

## 风险分析

Risk 至少包含：`level`、`categories`、`targets`、`reason_summary`、`analyzer_id/version`、`confidence`。

类别：filesystem write/delete、process、network、credential、external mutation、privilege、persistence、data exfiltration。

分析器可以是规则、shell AST、LLM 或 ensemble。shell string 先 parse，再分析 pipeline、redirect、subshell、heredoc 和 encoded command；解析失败在安全 profile 按高风险处理。

模型生成的 `security_risk` 只能作为 hint，不能覆盖独立分析器。分析结果与规范化 action digest 绑定，参数改变后重新分析。

## Confirmation Policy

策略建议：

- `NeverConfirm`：仅用于 enforcement 已足够且用户选择的低摩擦模式；
- `AlwaysConfirm`：每个副作用动作确认；
- `ConfirmRisky`：达到阈值或类别命中时确认；
- managed profile：组织 ceiling + 用户偏好，用户不能降低 ceiling。

Request 展示 tool、规范化命令/路径/域名、风险、workspace、影响、可选 scope、expiry。禁止展示 secret 值。

decision：approve once、reject、amend、expire。批量或 session approval 只对结构化 scope digest 生效；命令前缀文本匹配不足以授权 shell。

## Enforcement

Workspace enforcement 负责：

- root/mount/path allowlist 与 symlink-safe open；
- 非 root uid、只读系统层、最小 Linux capabilities；
- CPU/memory/pid/time/output quota；
- network deny/allow，覆盖 DNS、直接 IP、redirect 和 IPv6；
- process tree cancel 与 zombie cleanup；
- credential broker 按 tool/host/action 注入短期 secret；
- artifact 与日志出站扫描；
- remote writer fencing。

LocalWorkspace 无法满足强隔离时标记 `local-unsafe`，polished profile 拒绝启动。

## Secret 与数据

Secret registry 只保存 ref、name、description、scope 和加密值。没有 cipher 时持久化应 redacted/lost，而不是明文。

secret 值禁止进入：system prompt、Event payload、Action display、Observation、trace、telemetry、Canvas store、artifact filename 和 exception。

执行时 broker 根据 action digest 发短期 credential；结束后撤销。masker 同时处理精确值、URL encoded、base64/分块和 header 形式，但脱敏不是防外传的唯一边界。

用户文件和模型内容按数据分类控制远程 provider；遥测默认最小化并提供 consent/disable。

## Hook Skill Plugin MCP

PreToolUse hook 可以 block，但不能 allow 被 policy/enforcement 拒绝的动作。PostToolUse 只观察/补充事件，不能伪造 tool receipt。

Skill/plugin 安装使用固定 ref/digest、来源 allowlist、大小限制和安全解析。plugin hooks、MCP 与 agent definitions 各自带 provenance。

MCP server 获得独立网络/secret scope；tool list changed 不能绕过当前 run capability snapshot。MCP tool result 作为不可信内容，不能注入 system policy。

Client-side tool 只有已绑定 conversation、认证且声明 capability 的客户端能回传结果；断连不自动成功。

## Server 与租户

- REST/WebSocket 同一认证与 authorization；
- conversation、workspace、event、artifact、secret 按 tenant/user 隔离；
- workspace cookie/header 有 audience、expiry 与 CSRF 设计；
- event history 分页也执行资源 authorization；
- lease store 不接受客户端自报 writer token；
- CORS 默认 deny，生产显式 origin；
- error detail、OpenAPI 和健康接口不泄漏路径或 token；
- admin、runtime、user API 分离；
- rate limit 覆盖 create、run、events、WebSocket 和 confirmation。

## 失败模式

- analyzer timeout：managed/safe profile fail closed；
- confirmation client 离线：保持 pending 或 expire-reject；
- sandbox provider down：不回退 local；
- policy service unreachable：缓存签名 ceiling 未过期才可继续；
- secret broker failure：action 不执行；
- lease lost：取消在途并 fence commit；
- hook/plugin crash：隔离、记录、按 profile fail closed/open，不能拖垮 event store；
- malformed persisted event：隔离损坏项，拒绝运行直到修复，不反序列化任意代码。

## 安全验收

- path traversal、symlink race、hardlink、mount alias、Unicode case 绕过；
- shell AST bypass、encoded payload、heredoc、nested interpreter；
- DNS rebinding、redirect、direct IP、IPv6、metadata service；
- env/proc/log/artifact/WebSocket/telemetry secret leak；
- prompt injection 从 repo/web/MCP/skill/tool output 提权；
- confirmation TOCTOU 与 approval replay；
- old lease writer、cross-tenant id guessing、slow WebSocket DoS；
- container escape primitives、privileged flags、docker socket、host mount；
- cancel/timeout 后遗留进程和外部副作用。

通过 [acceptance-tests.md](acceptance-tests.md) 的对应 oracle 前，不得把 `security.defense-in-depth` 标为 verified。
