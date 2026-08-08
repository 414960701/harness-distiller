# Performance 与 Cost

## 职责与目标

在正确性和安全不下降的前提下控制 token、模型调用、tool wall time、索引、存储、网络和并发。优化必须有 trace 和 benchmark 证据。

## Budget

```yaml
Budget:
  max_steps: integer
  max_input_tokens: integer
  max_output_tokens: integer
  max_cost: decimal|null
  deadline: timestamp
  max_parallel_tools: integer
  max_subagents: integer
```

每次 model/tool 前检查剩余预算；接近阈值时压缩、降级或询问，不突然失控。

## 优化顺序

1. 稳定 prompt 前缀与缓存；
2. 减少无关 context/tool schema；
3. 增量文件/符号索引；
4. 大输出 artifact 化；
5. 安全并行独立工具；
6. 模型/工具路由；
7. speculative work，仅在可取消且收益可测时。

## 四级增量

- runnable：最大 steps/token/time；
- usable：usage、cache、compaction、输出上限；
- productive：增量索引、路由、并行、成本画像；
- polished：自适应预算、租户配额、容量规划、成本 SLO。

## 直接升级

先建立基线，再启用优化 feature flag。缓存 key 包含协议、model、tool catalog、稳定指令版本。回滚优化不改变领域事件和 session 可读性。

## 失败模式

压缩丢关键约束、缓存污染、过度并行争用资源、便宜模型路由导致工具误用、token 估算偏差、优化均值但恶化尾延迟。

## 验收

- 冷/热缓存基准；
- 小/中/大仓库与长会话；
- 慢工具/模型和限流；
- 优化前后任务成功与安全指标不下降；
- budget exhausted 给明确终止和恢复建议；
- 关闭 feature flag 可回到稳定基线。

证据：OpenAI prompt caching 文档见 `references/source-registry.md`；其余为设计综合。
