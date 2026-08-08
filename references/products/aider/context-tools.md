# Aider-like 上下文、repo map 与 edit formats

## 目录

- [上下文分层](#上下文分层)
- [repo map 数据管线](#repo-map-数据管线)
- [tree-sitter 与 PageRank](#tree-sitter-与-pagerank)
- [token 预算与降级](#token-预算与降级)
- [历史总结](#历史总结)
- [edit format 合同](#edit-format-合同)
- [四级优化](#四级优化)

## 上下文分层

Aider-like 不把整个仓库当作一个 prompt。ContextCompiler 应按稳定优先级组合：

1. system prompt、format 指令和 fences；
2. format examples；
3. 已完成历史 `done_messages`，必要时为 summary；
4. repo map；
5. read-only 文件完整内容；
6. chat files 的最新完整内容；
7. 当前对话 `cur_messages`；
8. 新用户消息。

文件内容比旧 assistant 叙述更接近真值。编辑完成后，把当前消息后移并在下一轮重新读取文件，避免模型继续依赖旧版本。每个 chunk 记录来源、token 数、hash、是否可裁剪和敏感等级。

```yaml
ContextChunk:
  id: string
  kind: system|example|history|repo_map|read_only_file|chat_file|current
  source: string|null
  content_sha256: string
  tokens: integer
  priority: integer
  truncatable: boolean
  access: instruction|read_only|editable|null
```

不要仅以 XML/Markdown 标签表达 access；真正写权限仍由 workspace policy 强制。

## repo map 数据管线

输入是 Git tracked files（排除 ignore）、当前 chat files、用户消息提到的文件/identifier、语言 parser registry 和 token budget。输出是按相关性选择的文件/符号定义树，而不是向量检索全文。

```text
tracked files
 -> language detection
 -> tree-sitter query captures
 -> Tag(file, name, def|ref, line)
 -> file dependency multigraph
 -> personalized PageRank
 -> ranked definitions/files
 -> TreeContext around lines of interest
 -> binary search/select under token budget
```

tag cache key 至少包含 canonical path、mtime 或 content hash、parser/query version。公开实现使用 `.aider.tags.cache.vN` 和 mtime；生产复刻更适合 content hash + parser version，避免时间戳回退。cache 只是性能层，任何损坏都必须可重建。

## tree-sitter 与 PageRank

tree-sitter query 把 capture 名 `name.definition.*` 归为 def，把 `name.reference.*` 归为 ref。某语言 query 只有 defs 而没有 refs 时，可用 Pygments/lexer 的 Name tokens 补 ref；无 parser 时退化为文件路径，不伪造符号。

构图伪代码：

```python
for tag in tags:
    if tag.kind == "def": defines[tag.name].add(tag.file)
    else: references[tag.name].append(tag.file)

for ident in intersection(defines, references):
    multiplier = 1.0
    if ident in mentioned_idents: multiplier *= 10
    if descriptive_identifier(ident): multiplier *= 10
    if ident.startswith("_"): multiplier *= 0.1
    if len(defines[ident]) > 5: multiplier *= 0.1
    for source, count in Counter(references[ident]).items():
        for target in defines[ident]:
            chat_boost = 50 if source in chat_files else 1
            graph.add_edge(source, target,
              weight=multiplier * chat_boost * sqrt(count), ident=ident)
rank = pagerank(graph, personalization=focus_files)
```

PageRank 分数再沿出边分配到 `(defining_file, ident)`，从高到低选择 definition lines。用户提到的文件、路径 component 和 identifier 进入 personalization。定义太普遍应降权，长而具辨识度的 snake/kebab/camel identifier 可升权。

渲染时用 AST-aware TreeContext 展开 definition 的父作用域和必要上下文；不同文件按 path 分组。单行截断用于防止 minified 文件破坏预算，但必须标记 truncation。相同文件与 lines-of-interest、mtime 的结果可缓存。

## token 预算与降级

默认 map 预算可以约 1k tokens；没有 chat files 时可乘 `map_mul_no_files` 扩大，但要给模型上下文预留固定 padding。选择过程不能只按字符截断 AST：先生成不同候选规模，找到不超过预算的最大树，或逐项加入 ranked tags 并精确计 token。

ContextCompiler 的裁剪顺序：

1. 去除低 rank repo map 条目；
2. summary 老历史并保留最新尾部；
3. 提示用户 drop 不必要 chat files；
4. 缩减 examples/可选说明；
5. 若仍超限，拒绝发送并提供 token report。

不可裁剪：当前用户消息、当前 edit format 核心语法、最新 chat file 真值、明确安全约束。repo map RecursionError、parser crash 或过大仓库时可禁用 map，输出 `repo_map.degraded`；不得让主会话崩溃。

## 历史总结

公开 `ChatSummary` 的策略值得保留：超过 soft limit 后，保留接近半预算的最近 tail，确保 head 在 assistant 边界结束；用 weak model 总结 head；summary + tail 仍过大则递归，深度有限；weak model 失败再尝试 main model。

```python
def summarize(messages, max_tokens):
    if tokens(messages) <= max_tokens: return messages
    head, tail = split_keep_recent_half(messages)
    if head_too_small_or_depth_exceeded(): return summarize_all(messages)
    summary = weak_then_main(head)
    return summary + tail if fits(summary, tail) else recurse(summary + tail)
```

summary 必须覆盖用户目标、已做决定、已编辑文件、未解决错误和重要约束，但不能替代文件内容。输出作为一条带固定 prefix 的 user message，并补 assistant `Ok.` 以维持角色交替。后台总结提交前比较原消息列表 hash；已变化则丢弃结果。

切换 edit format 时，旧 assistant 回复可能示范错误语法；因此应总结旧 done history，或至少移除旧格式示例，再构造新 Coder。summary 失败可以保留原历史并警告，不能清空会话。

## edit format 合同

| format | 模型输出 | 优点 | 关键风险 |
|---|---|---|---|
| whole | path + 完整新文件 | parser 简单、能跑稳定 | token 高、易覆盖并发修改 |
| diff | SEARCH/REPLACE blocks | 小输出、上下文锚定 | 搜索 0/多次匹配 |
| diff-fenced | path 放在 fence 内 | 适配特定模型 fencing | fence/parser 分歧 |
| udiff | 简化 unified diff | 紧凑、减少懒惰省略 | hunk 定位和偏移 |
| editor-diff/whole | 相同 edit 语法、简化 prompt | architect 后专注落盘 | 依赖 proposal 完整性 |
| patch | add/update/delete actions | 结构清晰 | 路径/section parser 复杂 |

统一接口：

```yaml
ParsedEdit:
  path: relative-path
  format: string
  operation: create|replace|delete|whole-file
  before: string|null
  after: string|null
  occurrence: integer|null
  source_span: {start: integer, end: integer}
```

search/replace 的 `before` 必须唯一匹配，除非协议显式给 occurrence；whole file 必须带当前 expected hash；udiff/patch 不允许路径穿越。多个 edits 先在内存按顺序应用同一 post-image，任何块失败则整个 ChangeSet 零写入。parser 应输出精确诊断：missing fence、unknown path、no match、ambiguous match、overlapping edit、invalid encoding。

模型默认 format 来自 metadata/benchmark，可由用户覆盖。不要把格式“自动修好”到无法审计；有限的空白容错可以，但要保留 normalization report。

## 四级优化

| 等级 | context/edit 增量 |
|---|---|
| runnable | 显式 chat files、whole 或严格 diff、token 计数、parse-before-write |
| usable | repo map、tag cache、history summary、多 format、read-only files、mention 建议 |
| productive | personalized PageRank、增量 hash cache、精确预算、architect editor formats、prompt cache |
| polished | parser property tests、跨语言 query quality、stale snapshot、可观测 context manifest、检索评测 |

直接升级复用 `ContextChunk`、`ParsedEdit` 和 cache key；低等级字段可以为空，但不能换 schema。验收重点见 [acceptance-tests.md](acceptance-tests.md)。
