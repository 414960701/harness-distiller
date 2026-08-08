# Permission Policy

## 目录

- [职责](#职责)
- [非目标](#非目标)
- [接口与 Schema](#接口与-schema)
- [规则与状态](#规则与状态)
- [Policy 与 Enforcement 分离](#policy-与-enforcement-分离)
- [四级增量](#四级增量)
- [直接升级与回滚](#直接升级与回滚)
- [失败模式与攻击面](#失败模式与攻击面)
- [可执行验收](#可执行验收)
- [来源与设计综合](#来源与设计综合)

## 职责

Permission Policy 将规范化 action、resource、用户授权、tool 注解、运行模式和组织约束映射为 `allow | deny | ask | amend`。

它返回可解释、可审计、带作用域和期限的决策；真实文件、进程和网络限制由 sandbox/executor enforcement。

## 非目标

- 不亲自打开文件、启动进程或代理网络。
- 不信任模型自报的 read-only、risk 或 reversibility。
- 不用一次批准覆盖审批后改变的参数。
- 不让项目规则覆盖 managed deny。
- 不把“没有 UI”自动解释为 allow。

## 接口与 Schema

```yaml
Action:
  id: string
  tool: string
  effect: read|workspace_write|process|network|external_write|destructive
  normalized_resource: object
  arguments_digest: string
  workspace_revision: string
  actor: object
```

```yaml
Decision:
  outcome: allow|deny|ask|amend
  reason_code: string
  matched_rules: [{id, effect, provenance, priority}]
  scope: once|turn|session|workspace|organization
  expires_at: timestamp|null
  audit_id: string
  amended_action: object|null
```

## 规则与状态

规则来源至少区分 managed、user、project、local 和 runtime_default。

`normalized -> matched -> precedence_resolved -> ask_pending | allowed | denied | amended -> expired`

deny 冲突时默认胜出；managed requirement 不可被低层覆盖。具体 precedence 必须形成版本化、可测试表，不藏在 prompt。

ask resolution 绑定 action id、arguments digest、resource、workspace revision 和 expiry。

## Policy 与 Enforcement 分离

- policy 判断路径 `workspace://root/a` 是否允许写。
- filesystem 在 open 时证明目标仍位于 root。
- policy 判断命令是否可运行。
- sandbox 约束进程真实 syscall、网络和后代。
- policy 判断域名可访问。
- network proxy 在连接、DNS 和 redirect 时 enforcement。

任何 enforcement capability 缺失都会回到 policy 重新决策，而非复用原 allow。

## 四级增量

### runnable / 能跑

按 read/write/process/external write 显式询问，默认 deny 未知工具。

### usable / 能用

path/tool/command/network matcher、作用域、过期、mode 和规则 provenance。

### productive / 顺手

profile、批量批准、风险 amend、headless policy、审计查询和模拟器。

### polished / 好用

组织 requirements、双人审批、策略签名/版本、租户治理和形式化冲突测试。

## 直接升级与回滚

旧布尔 grant 迁移为 once + unknown provenance，不能默认扩大成 workspace scope。

先引入 shadow evaluation 比较新旧 decision，再切换 enforcement；差异按 effect/rule 记录。

回滚 policy engine 时保留 managed deny 与审计；新 matcher 无法解释时 fail closed 或 ask，不降级 allow。

## 失败模式与攻击面

- 参数、path、redirect target 在批准后变化。
- 命令混淆、Unicode、shell expansion 绕过 matcher。
- tool 虚报 effect/read-only。
- project allow 通过 precedence 覆盖 managed deny。
- approval replay、过期、跨 session 或跨 workspace 复用。
- 批量范围过宽，隐藏后续高风险目标。
- 自动风险模型超时或失败后默认 allow。
- headless 环境无限等待 ask 或偷偷 allow。
- 审计理由含 secret 或攻击性终端控制字符。

## 可执行验收

- 修改任一已展示参数后旧 resolution 无效并重新 ask。
- managed deny 与 user/project allow 同时命中，结果稳定 deny 且 provenance 正确。
- 同名工具来自两个 MCP server 时分别授权。
- workspace A 的 grant 不能用于 B，branch/session scope 符合声明。
- approval 过期、replay 和 audit id 重复均被拒绝。
- tool 注解 read-only 但实际 effect external_write 时以 runtime effect 重新决策。
- 无 UI 时 ask 返回结构化 blocked/exit code，不自动 allow。
- enforcement capability 降级后原 allow 失效。

## 来源与设计综合

策略思想参考 capability security、deny/allow ACL、OPA/Rego 等公开系统；统一 Action/Decision schema 和 precedence 是设计综合。

- OPA policy language：https://www.openpolicyagent.org/docs/policy-language
- NIST access control overview：https://csrc.nist.gov/projects/attribute-based-access-control
- OWASP authorization guidance：https://cheatsheetseries.owasp.org/cheatsheets/Authorization_Cheat_Sheet.html

完整 command/event envelope 见 [../implementation/policy-execution.md](../implementation/policy-execution.md) 与 [../implementation/protocol.md](../implementation/protocol.md)，本文维护领域规则而不复制实现文档。

产品特有 mode 和规则语法应在产品 dossier 中做 adapter，不能污染共享 policy 核心语义。
