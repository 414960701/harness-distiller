# Long-Term Memory

## 职责与非目标

长期记忆保存跨 turn 仍有价值、可追溯、可撤销的用户或项目事实。
它不是无限聊天摘要、隐藏系统指令、RAG 索引或模型参数更新。
RAG 负责找当前文档证据，见 [RAG 与代码索引](rag-index.md)；Memory 负责“谁在什么 scope 下确认过什么”。
模型可以提议记忆，只有策略允许或用户确认后才能成为 durable record。

## 数据与接口

```yaml
MemoryRecord:
  id: string
  subject: user|project|organization|agent
  scope: string
  kind: preference|fact|constraint|procedure|summary
  content: string
  provenance: [turn_id|artifact_uri]
  status: proposed|confirmed|conflicted|expired|revoked
  confidence: number
  sensitivity: public|internal|sensitive
  created_at: timestamp
  verified_at: timestamp|null
  expires_at: timestamp|null
```

接口：`propose`, `confirm`, `query`, `edit`, `revoke`, `clear_scope`, `export`, `restore`。
`query(subject, task_scope, purpose, budget)` 返回记录、来源、状态与适用范围。
读取时按主体、scope、权限、相关性、新鲜度和冲突过滤；不把 conflicted 事实当确定结论。

## 分层与状态

建议分为 profile（稳定偏好）、durable memory（确认事实）、episodic/short-term（近期摘要）、candidate（待确认）。
原文 store 是事实源，全文/向量索引与摘要缓存可重建。
记录状态按 `proposed → confirmed → expired|revoked`；发现相反证据进入 `conflicted`。
Skill 进化属于可执行配置 diff，不应静默写成记忆；见 [Skills 与 Plugins](skills-plugins.md)。
上下文装配只引用必要记录，并显示“为何命中”和来源任务。

## 四级增量

### `runnable` 能跑

仅加载用户显式维护的项目规则/`MEMORY.md`，无自动写入。

### `usable` 能用

增加结构化记录、显式增删改、scope、来源和每任务检索。

### `productive` 顺手

增加候选提议、去重、冲突、过期、本地全文/向量检索与备份恢复。

### `polished` 好用

增加多设备同步、端到端加密、企业保留、敏感策略、遗忘证明、质量/污染 eval。

## 直接升级与回滚

先将旧自由文本拆为候选记录，保留原文与 hash，不自动标 confirmed。
建立 source-of-truth store 后再构建索引；同步和自动提议最后开启。
升级期间双读对比命中集，敏感或无来源记录默认不迁移。
回滚只关闭自动写入/新索引，保留可导出的原始记录与撤销日志。

## 失败模式与安全

- 错误传播：低置信或冲突记录不自动注入。
- 跨项目泄漏：scope 与主体在存储查询层强制，不靠 prompt。
- 恶意记忆注入：tool/web/file 内容不能直接写 confirmed。
- 删除不彻底：Clear 同时删除原文、摘要、全文和向量索引。
- 过期偏好：读取校验 expires/verified_at，并允许用户纠正。
- secret 持久化：凭据只存 secret broker，Memory 保存 opaque reference 或不保存。

## 验收 oracle

1. 项目 A 的私有事实在项目 B 查询中零命中。
2. 相互矛盾的记录显示冲突与来源，不静默选择。
3. Clear 后全文、向量、缓存、备份队列和后续回答无 canary。
4. 未确认的网页内容不能变成 durable preference。
5. 过期记录不注入新任务，但仍可在审计中查看。
6. 导出/恢复保留来源、状态和 schema 版本，不包含 OAuth token。

## 来源与设计综合

可参考 [NIST Privacy Framework](https://www.nist.gov/privacy-framework) 的数据治理和 [LangGraph persistence](https://docs.langchain.com/oss/python/langgraph/persistence) 的可恢复状态思路。
产品级 Awareness UI、事件和备份体验由各产品 dossier 定义；共享层只规定记录与隐私合同。
