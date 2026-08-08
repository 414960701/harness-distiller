# 原位升级工作流

## 1. 建立升级基线

运行 `validate_blueprint.py`、目标测试与产品当前等级黑盒场景。记录 protocol、event、database、ToolSpec、plugin API 和 config 版本；蓝图已漂移时先修复，不盲目升级。

## 2. 计算 capability delta

比较当前和目标等级，展开每个 capability 的依赖。即使 `usable -> polished`，也要展开 productive 的 schema、checkpoint、policy、observability 等依赖，但不要求发布中间版本。

```yaml
upgrade:
  from: usable
  to: polished
  batches:
    - schema
    - protocol
    - runtime
    - policy-executor
    - surfaces
    - cleanup
```

## 3. 设计兼容与回滚

- 数据库：forward migration、旧 reader、备份和 kill-point；
- event：upcaster 或保留旧 reducer；
- protocol：可选字段或 capability negotiation；
- config：旧 key 至少一个迁移边界可读；
- ToolSpec/plugin：版本并存或 adapter；
- workspace：checkpoint、Git/worktree 或 artifact 备份；
- 外部副作用：幂等键或人工确认。

无法安全回滚的步骤必须在执行前说明并请求授权。

## 4. 分批实施

1. schema：新增字段/表和兼容 reader，不立即删除旧字段；
2. protocol：发布新 capability/schema，旧客户端仍可运行；
3. runtime：实现新状态与算法，默认 feature flag 关闭；
4. policy/executor：先启用强制边界，再开放无人值守能力；
5. surface：消费新事件，不旁路 runtime；
6. cleanup：确认遥测和回归后才删除旧路径。

每批有独立 commit/rollback point 和 capability 测试。

## 5. 验证

运行所有低等级回归、新等级合同、产品 acceptance、security、recovery、migration 与 N/N-1 兼容测试。用录制事件验证旧 session 在新 UI 的投影。

## 6. 提交状态

测试通过后才把 capability 从 selected/implemented 改为 verified，并写实现、测试、迁移和证据路径。失败时恢复到批次前 checkpoint，不把部分升级标为完成。

## 常见错误

- 通过重新生成工程“升级”；
- 先改 UI，再补协议；
- 迁移后立即删除旧字段；
- 把自动批准当安全升级；
- 增加 subagent 却没有隔离、取消和预算；
- 升级 context 算法却不重跑低等级正确性集。

