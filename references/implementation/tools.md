# Tool Runtime 实现合同

## 组成

```text
Discovery -> Catalog -> Selection -> Schema validation -> Normalization
-> Policy -> Executor -> Progress -> Result normalization -> Artifact store
```

Tool implementation 不得直接修改 thread 状态或 UI；只能返回 ToolResult/Artifact，由 orchestrator 追加事件。

## ToolSpec

除 name/description/schema 外，MUST 声明：版本、capability、side effect、idempotency、timeout、concurrency、approval hint、artifact policy。MCP 注解只作为 hint，不能覆盖本地策略。

## 输入规范化

在 policy 前完成：

- path：解析相对 workspace URI、符号链接和大小写；
- command：区分 argv 与 shell string，解析 cwd/env/network intent；
- URL：规范 scheme、host、port、重定向策略；
- file change：计算 base hash、目标 hash 和 hunk；
- external action：列出账号、收件方、数据、可逆性。

PolicyDecision 绑定规范化后的 action hash，不绑定模型原始 JSON 文本。

## 生命周期

```text
draft -> proposed -> authorizing -> approved -> queued -> running
-> completed | failed | cancelled | indeterminate
```

每个状态产生事件。`running` 前持久 intent；副作用结束后持久 receipt/result。executor 崩溃时用 receipt 判断是否可重试。

## 输出

ToolResult 的 model-visible content 有严格大小上限。完整 stdout、截图、文件、网页或表格保存为 artifact：

```yaml
ArtifactRef:
  id: art_1
  uri: artifact://art_1
  mime: text/plain
  size: 120034
  sha256: ...
  preview: bounded string
  created_by: call_7
  retention: session|project|persistent
```

## 并发和锁

读取工具可并行；写工具按规范化资源集合加锁。未知资源范围或 shell 命令默认串行。并行执行结果按原 call 顺序回写模型。Finish/complete 工具触发后，后续未开始动作取消。

## 内置最低工具

完整 coding harness 至少有：

- `workspace.list`, `workspace.search`, `file.read`；
- `patch.apply` 或等价结构化编辑；
- `process.exec`, `process.write`, `process.cancel`；
- `git.status`, `git.diff`；
- `plan.update`；
- `artifact.read`；
- product recipe 指定的 MCP、browser、computer 或 subagent 工具。

## MCP/Plugin/Skill

MCP 负责发现和传输，Tool Runtime 仍负责 schema、policy、timeout、result 和 artifact。Plugin 在隔离边界加载；Skill 只在触发后加载正文，脚本执行走普通 policy/executor。工具名冲突用 namespace 或显式优先级，禁止静默覆盖。

## 验收

- invalid JSON 和 schema mismatch 不进入 executor；
- 同一 keyed call 重试不重复副作用；
- timeout/cancel 后迟到结果被记录但不改变终态；
- 大输出不会突破模型 context；
- 恶意 tool result 不被提升为系统指令；
- MCP server 断线、OAuth 过期和 schema 改变可诊断；
- 两个并行 patch 不会静默覆盖同一文件；
- 工具名冲突必须显式解决。

