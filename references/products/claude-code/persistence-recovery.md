# Claude-Code-like 持久化与恢复

> 官方公开了 session、resume、branch 和 checkpoint 等行为，也提示本地 JSONL 内部格式可能变化。本文 schema 与算法均为 `inference`，用于实现等价、稳定且可迁移的行为。

## 目录

- [行为边界](#行为边界)
- [存储布局](#存储布局)
- [JSONL 事件记录](#jsonl-事件记录)
- [索引与 Artifact](#索引与-artifact)
- [Session 操作](#session-操作)
- [Checkpoint 与 Rewind](#checkpoint-与-rewind)
- [Compaction](#compaction)
- [Prompt Cache](#prompt-cache)
- [崩溃与副作用恢复](#崩溃与副作用恢复)
- [迁移、保留与隐私](#迁移保留与隐私)
- [升级与测试](#升级与测试)

## 行为边界

`official-doc`：会话 transcript 可 continue、resume、rename、branch/fork；checkpoint 可恢复 conversation、code 或两者。

`official-doc`：默认本地 transcript 路径和格式可被观察，但内部 JSONL 行格式不是稳定外部 API。

`inference`：蒸馏实现对外暴露 versioned export/event protocol，对内可以 JSONL + SQLite index，也可以事务数据库。

### 不变量

- append 成功的 committed event 不原地改写。
- resume 不执行历史 tool call。
- branch 保留 parent/point 引用但生成新 session id。
- rewind 创建新事实，不删除旧历史。
- compact summary 不替换原 transcript。
- cache miss 只影响成本/延迟，不影响语义正确性。

## 存储布局

```text
state-root/
  manifest.json
  sessions/<session-id>/
    metadata.json
    events-000001.jsonl
    checkpoints.jsonl
    locks/
  artifacts/sha256/<prefix>/<digest>
  indexes/state.sqlite
  migrations/
```

这是推荐布局，不是 Claude Code 的内部目录声明。

`manifest.json` 记录 store version、writer build、encryption/redaction version 和 created_at。

session 路径只使用验证后的 id，不能使用 repository name 原样拼接。

## JSONL 事件记录

### Record

```json
{"store_version":2,"event":{"id":"evt_...","sequence":12,"type":"tool.completed","payload":{}},"checksum":"sha256:..."}
```

- 每行一个完整 record，UTF-8，无跨行 JSON。
- payload 写入前经过 schema validation 和 redaction。
- checksum 覆盖 canonical encoding 的 event。
- writer 在完整行后 flush；关键边界执行 fsync。
- segment 达大小阈值后轮换并写 seal record。
- 启动时截断最后一条不完整尾行，保留诊断副本。

### 提交流程

1. 验证 expected session revision。
2. 分配下一 sequence 和 event id。
3. 写入临时 buffer。
4. append 完整行并 flush/fsync。
5. 更新 SQLite 派生索引。
6. 向订阅者发布 committed event。

索引更新失败不撤销 event；后台可从日志重建索引。

### 并发

- 单 session 一个 writer lease。
- 多 surface command 用 expected revision 和 command id 去重。
- writer 崩溃后 lease 有 fencing token，旧 writer 不能继续提交。
- 远程模式用共识日志或具备同等顺序保证的事务存储。

## 索引与 Artifact

SQLite 只保存可重建投影：session 列表、最后访问、标题、状态、全文检索和 artifact refs。

大 tool output、图片、patch 和测试报告写内容寻址 artifact store。

```yaml
ArtifactRef:
  id: sha256:string
  media_type: string
  bytes: integer
  redaction: string
  encryption: string|null
  retention_class: transient|session|user_saved
```

写 artifact 时先临时文件、校验 digest，再 atomic rename。

事件只保存 artifact ref、摘要和必要 preview。

## Session 操作

### Continue

在当前 workspace 选择最近、未归档且兼容的 session；选择逻辑必须展示，不可误续其他项目。

### Resume

1. 读取 metadata 和 schema versions。
2. 校验 workspace identity 和 trust。
3. 执行只读迁移或创建迁移副本。
4. 从 snapshot + event tail 重建投影。
5. reconcile 未知 outcome 的 side effect。
6. 将临时高风险 mode 重置为安全默认。
7. 产生 `session.resumed`。

### Branch

```yaml
BranchMetadata:
  new_session_id: string
  parent_session_id: string
  parent_sequence: integer
  inherited_item_ids: [string]
  inherited_checkpoint_id: string|null
```

branch 可引用 immutable parent events，避免复制；export 时展开为自包含记录。

### Rename 与 Export

rename 只改变 display metadata，不改变 id 和路径主键。

export 使用稳定、已脱敏 schema，并注明省略的秘密和 transient output。

## Checkpoint 与 Rewind

`official-doc`：checkpoint 在用户 prompt 前追踪编辑工具产生的文件状态，rewind 可选择 conversation、code 或两者。

`inference`：checkpoint manifest 如下。

```yaml
Checkpoint:
  id: string
  session_sequence: integer
  workspace_revision: string
  file_entries:
    - path: string
      before_artifact: string|null
      after_hash: string|null
  conversation_boundary_item_id: string
```

### Rewind conversation

创建 `checkpoint.rewound` 和新的 active head；旧事件保留但不进入当前 context projection。

### Rewind code

- 对每个文件校验当前 hash 是否仍等于 checkpoint 记录的 after_hash。
- 若用户或外部进程后来修改，进入冲突解决，不强制覆盖。
- 恢复前生成 safety checkpoint。
- shell、git push、API、数据库和远程资源不在可恢复范围。

### Rewind both

先准备 code restore plan，再原子提交 conversation head 与可成功恢复的文件集合；部分失败必须明确报告。

## Compaction

`official-doc`：支持自动 compact、`/compact` 和 context 诊断；完整算法/私有 prompt 未公开。

### Summary schema

```yaml
CompactionSummary:
  source_item_range: [string,string]
  user_goals: [string]
  decisions: [string]
  changed_files: [path]
  failed_attempts: [string]
  pending_tasks: [string]
  verification_state: [object]
  artifact_refs: [string]
  generated_by: model_ref
```

- summary 追加为新 item，带 source range 和模型版本。
- compact 前保存不可丢失 checklist。
- old items 仍在 store，可审计、branch 和重新总结。
- summary 失败或质量 gate 不过则继续使用旧 projection。
- 多次 compact 形成 summary DAG，不递归丢掉 provenance。

## Prompt Cache

`official-doc`：产品自动使用 prompt caching；cache key 和内部策略未公开。

`inference`：按不可变 prefix 构建 cache descriptor。

```yaml
CacheDescriptor:
  provider: string
  model: string
  prefix_digest: string
  tool_schema_digest: string
  instruction_digest: string
  trust_partition: string
  expires_at: timestamp
```

- user/project/tenant 之间严格 partition。
- tool schema、system instructions 或 model 改变即失效。
- 不持久保存 provider 返回的秘密 cache handle 到可导出 transcript。
- telemetry 记录 hit/miss、读写 token 和成本，不记录 prompt 原文。

## 崩溃与副作用恢复

### Tool recovery classes

- `pure_read`：可安全重试。
- `workspace_write`：通过 expected revision 判断是否已提交。
- `idempotent_external_write`：使用 idempotency key 查询/重试。
- `non_idempotent_external_write`：结果未知时必须人工 reconcile。
- `process`：检查 pid/lease；不可仅凭未收到 result 判断未执行。

启动恢复将无终态 call 标为 `reconciling`，不能直接重新派发。

模型请求断线如果未形成 committed tool intent，可重新请求；半个 JSON tool call 不提交。

terminal event 使用唯一约束，防止恢复线程与旧 worker 双重完成。

## 迁移、保留与隐私

- 每次 schema 迁移先备份 manifest 和受影响 segment。
- 迁移函数确定性、可重复，并写 migration event。
- reader 支持至少一个前一 major 版本或提供独立升级器。
- retention 按 transcript、artifact、telemetry、memory 分开配置。
- 删除 session 时处理共享 artifact 引用计数。
- 用户可导出、删除 session 和 memory；删除语义说明备份延迟。
- 日志默认不含 API key、OAuth token、完整环境变量和 secret 文件内容。

## 升级与测试

- 能跑：单 JSONL、基础 transcript、进程级锁。
- 能用：索引、resume/branch、artifact、尾行恢复。
- 顺手：checkpoint/rewind、compaction DAG、cache telemetry。
- 好用：远程 writer fencing、在线迁移、加密和保留治理。

Oracle：任意字节位置 kill writer，恢复后日志是已提交前缀且可解析。

Oracle：resume 十次不会重复外部 mutation。

Oracle：branch 后父 session 新事件不出现在子 session projection。

Oracle：rewind 遇用户后续编辑时保持用户内容并报告冲突。

Oracle：compact 前后的 pending task、失败和验证状态等价。

Oracle：cache 全部禁用时输出语义和安全决策不变。
