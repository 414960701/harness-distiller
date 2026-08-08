# 上下文装配与压缩

## 目标

在 token、成本、延迟、缓存、安全和可追溯约束下生成一次模型调用的不可变 `ContextSnapshot`。持久事实、工作状态和模型可见上下文必须分开。

## 分层顺序

建议按稳定到动态排序：

1. 系统安全与 runtime 合同；
2. 产品 recipe 和 collaboration mode；
3. Tool schema 与能力说明；
4. sandbox、workspace、时间、环境等稳定世界状态；
5. 用户/组织/项目指令；
6. thread summary、plan、memory；
7. 最近完整消息和 tool call/result；
8. 本轮用户输入；
9. 本轮动态检索和文件片段。

稳定前缀顺序固定。运行时变化追加为新 fragment，不修改旧 fragment，以保留 prompt cache。

## 预算算法

```python
reserve = output_budget + tool_result_reserve + safety_margin
available = model_context_limit - reserve

include(all_required_instructions)
include(tool_specs_selected_for_step)
include(latest_user_input)
include(active_plan_and_pending_approvals)
include(recent_atomic_turns_until_budget)
rank_and_include(files + retrieval + memory, remaining_budget)

if required_content_exceeds_budget:
    compact_or_fail_explicitly()
```

每类 fragment 分配 soft/hard budget；不得让一个巨大工具输出挤掉用户目标或安全指令。

## 工具原子性

模型历史中 tool call 与最终 result 必须一起出现。压缩、截断或过滤不能留下孤立 call/result。未完成 call 用明确 synthetic status 表示，不能伪造成功结果。

## Compaction

压缩生成新的 `context_summary` item：

```yaml
summary:
  covers_sequence: [10, 230]
  preserved:
    user_goals: []
    decisions: []
    constraints: []
    file_changes: []
    unresolved_errors: []
    pending_plan_steps: []
  source_hashes: []
  model: provider/model
  prompt_version: compact-v2
```

原事件不删除。summary 可替换模型可见 View，但审计和恢复仍能访问原始范围。

## 代码上下文

优先级：用户显式引用 > 当前 diff/诊断 > 符号定义与引用 > repo map > 语义检索 > 最近打开文件。所有索引结果带 commit/content hash；注入前发现 hash 变化应重新读取原文。

## Memory 与 RAG

Memory 保存用户/Agent 跨会话状态；RAG 检索外部事实。两者使用不同 namespace、写入策略、过期、权限和引用。自动写 memory SHOULD 先产生候选和 provenance，不把任意 tool/web 文本直接提升为长期事实。

## 安全

workspace 文件、网页、tool result 属于不可信数据。标注 trust，避免把其中伪造的“系统指令”提升层级。秘密在进入 context 前脱敏；opaque secret handle 只交给 executor。

## 验收

- 100k+ token 历史经过压缩仍保留目标、约束、变更和未决错误；
- tool call/result 原子性永不破坏；
- 项目指令冲突按 scope/层级确定解析；
- 同一稳定请求前缀 hash 不因时间戳或动态 cwd 位置变化而失效；
- 索引过期不会注入错误文件版本；
- 恶意 README 不能覆盖系统策略；
- memory 清除后原文和索引均不可检索。

