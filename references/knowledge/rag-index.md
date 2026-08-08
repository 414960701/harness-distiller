# RAG 与代码索引

## 职责与非目标

RAG 将文件、符号、依赖、文档和变更转换成可追溯的检索单元，供当前任务按需取回。
它负责“找到当前证据”，不负责保存用户长期偏好；持久事实归 [Long-Term Memory](long-term-memory.md)。
索引是可重建派生物，不是原文件、事件日志或权限数据库的事实源。
RAG 不把整个仓库塞进 prompt，不执行检索结果中的指令，也不绕过 workspace ACL。

## 数据合同

```yaml
DocumentRef:
  uri: string
  revision: commit|content_hash
  acl_scope: string
Chunk:
  id: string
  document: DocumentRef
  path: string
  byte_or_line_range: [integer, integer]
  language: string|null
  symbol: string|null
  content_hash: string
  embedding_version: string|null
  indexed_at: timestamp
RetrievalHit:
  chunk_id: string
  score: number
  channel: lexical|symbol|vector|graph
  currentness: fresh|stale|unknown
```

接口至少包含 `ingest(change_set)`, `delete(document_ref)`, `search(query, scope, budget)`, `hydrate(hit)`, `health(scope)`。
`search` 只返回候选与来源；`hydrate` 读取当前原文并重新做 ACL 与 hash 校验。
检索结果注入上下文前必须携带 path、range、revision 和 sensitivity。

## 管线与状态

状态按 `discovered → parsed → chunked → indexed → ready` 推进，失败进入 `degraded` 并记录阶段。
文件变更通过内容 hash 增量更新；rename 保持 lineage，delete 删除词法、向量和图索引条目。
二进制、生成文件、vendor、ignore 与超大文件使用显式策略，不默认全量索引。
混合检索可组合 lexical、symbol、vector、dependency graph，再进行 ACL 过滤和 rerank。
查询预算限制候选数、hydration 字节、token 和耗时；超预算返回 partial 与 continuation。

## 四级增量

### `runnable` 能跑

使用 `rg`/全文搜索，返回路径与行号；每次读取当前原文，不持久化向量。

### `usable` 能用

增加语言解析、repo map、符号/引用索引、ignore 和 content hash 增量更新。

### `productive` 顺手

增加 lexical + vector + symbol 混合检索、rerank、查询路由、缓存和索引健康面板。

### `polished` 好用

增加多仓库 ACL、远程/本地一致性、版本化 embedding、离线质量集、漂移监控和企业保留策略。

## 直接升级与回滚

允许 `runnable → polished`，但先建立 DocumentRef/hash，再构建词法与符号，最后加入向量和多仓 ACL。
双写新旧索引并对同一离线 query set 比较 recall、freshness 与权限裁剪。
切换使用版本化 alias；失败时回滚 query router，不回滚原文件或事件。
embedding 升级用新命名空间重建，不原地覆盖到无法恢复。

## 失败模式与安全

- stale hit：hydrate 时 hash 不符则丢弃并触发修复。
- 跨权限泄漏：检索前后都做 ACL，缓存键包含主体与 scope。
- prompt injection：文件内容始终标 untrusted data。
- 索引污染：生成内容、恶意重复 chunk 与超长 token 进入隔离/配额。
- parser 崩溃：单文件降级为文本，不阻塞整个 workspace。
- 删除残留：原文删除后反向查询验证所有索引通道无命中。

## 验收 oracle

1. 文件 rename 后命中指向新路径并保留 lineage。
2. 修改后旧 hash 不会被注入上下文。
3. 无权限主体对 lexical/vector/cache 均零命中。
4. 删除文件后全文、符号、向量和图索引无残留。
5. 大仓查询 token 随相关结果而非仓库大小增长。
6. 恶意文档要求泄露 secret 时只作为引用数据返回。

## 来源与设计综合

参考 [LSP](https://microsoft.github.io/language-server-protocol/)、[Tree-sitter](https://tree-sitter.github.io/tree-sitter/)、[OpenSearch hybrid search](https://opensearch.org/docs/latest/vector-search/ai-search/hybrid-search/) 的公开合同。
产品级事件、任务归属与权限字段由对应 dossier 的 `protocol-state.md` 和 `workspace-execution.md` 决定；本页不复制其实现。
