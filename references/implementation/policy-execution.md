# 权限、审批与强制执行

## 两层边界

- Policy Decision Point：回答动作是否 `allow/deny/ask/amend`。
- Policy Enforcement Point：在 OS、容器、代理、文件和进程层真正限制动作。

不得用 prompt、确认框或字符串黑名单冒充 enforcement。

## Action

```yaml
Action:
  actor: {user_id, agent_id, tool_id}
  operation: filesystem.read|filesystem.write|process.exec|network.connect|browser.click|external.send
  resources: [canonical resource]
  data_classification: public|workspace|sensitive|secret
  side_effect: none|local_reversible|local_irreversible|external_reversible|external_irreversible
  normalized_args_hash: sha256
  workspace_id: string
  turn_id: string
```

## 决策顺序

```text
hard deny / managed requirements
-> sandbox capability ceiling
-> user/project rules
-> cached grants scoped to exact action
-> tool annotation and risk classifier
-> allow / ask / amend / deny
```

`deny` 优先。`amend` 只能缩小资源、参数、时长或数据范围。

## Approval Request

界面必须展示：动作、规范化目标、数据范围、风险、可逆性、为什么需要、授权期限。选择包括一次允许、在精确范围允许、拒绝、修改范围。批准后参数或重定向变化必须重新审批。

## Workspace enforcement

所有路径：标准化 → 解析 symlink → 检查所属 root → 打开时再次验证。防 TOCTOU 需要安全打开原语或 descriptor-relative 操作。Git `.git`、技能/配置目录和 secret 路径可在可写 root 内继续保护。

## Process enforcement

结构化 argv 优先；环境变量白名单；限制 cwd、文件、网络、IPC、设备、子进程和资源。取消时杀进程树。sandbox 初始化失败必须 fail closed，除非用户明确选择危险模式。

## Network enforcement

默认 deny。allowlist 规则作用于最终连接目标，处理 DNS、redirect、private IP、localhost、Unix socket 和上游代理。秘密只在授权目标/工具执行时以 handle 解析，禁止进入普通日志和 prompt。

## 等级

- runnable：workspace 写限制、默认断网、显式危险提示；
- usable：OS/容器 sandbox、精确 path/command/tool approval；
- productive：permission profiles、network proxy、worktree/remote executor；
- polished：managed requirements、自动风险审查、租户隔离、审计和策略迁移。

## 验收攻击集

- `../`、symlink swap、大小写绕过、Git pointer；
- shell substitution、alias/config override、子进程逃逸；
- DNS rebinding、redirect 到私网、Unix socket；
- tool 声称 read-only 但产生副作用；
- approval 后参数变化；
- secret 出现在模型请求、stderr、artifact、通知或 trace；
- sandbox 不可用时继续执行；
- 浏览器页面 prompt injection 请求上传工作区文件。

