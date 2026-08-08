# 新建 Harness 工作流

## 1. 固化蓝图

从仓库根目录运行：

```bash
python3 <skill>/scripts/new_blueprint.py \
  --target . \
  --recipe codex \
  --level usable \
  --surfaces headless,cli
```

补齐生成的 `.harness-distill/blueprint.yaml`，记录运行栈、provider、安全模型和分发方式。

## 2. 选择知识模块

先按产品 `index.md` 读取 13 篇 dossier 中指定的前置顺序，至少加载 `product-contract.md`、`recipe.md`、`acceptance-tests.md` 与 `sources.md`。再读取 `references/implementation/index.md` 路由的实现规范。以产品 `recipe.md` 的 `required` 为基线，根据 surface、执行环境和等级展开依赖。任何未选模块都必须是明确 non-goal，不能因遗漏而消失。

## 3. 做 vertical slice

实现一个真实场景：读取仓库文件，模型提出补丁，策略允许或请求审批，执行器写入，事件流展示 diff，状态层保存 turn。runnable 要求 trace 可重放；usable 起再要求进程崩溃后恢复并避免重复副作用。不要用 mock 工具结果作为完成证据。

严格按 `references/implementation/delivery.md` 的 Phase 1–3 顺序：Phase 1 建 schema 与 event store，Phase 2 先交付 model/loop/read 的只读切片，Phase 3 再用 patch/process/policy 把同一切片闭合为读改测。不要把“先验证只读切片”误解为最终不实现 patch，也不要先生成完整 UI 和几十个工具。

## 4. 扩展能力

按依赖顺序扩展 context、plan、MCP、Git、worktree、subagent 和更多 surface。每新增能力同时添加：

- protocol schema；
- policy classification；
- cancellation/timeout；
- persisted event；
- UI projection；
- contract 与 scenario test。

## 5. 验收

运行蓝图验证、静态检查、单元测试、合同测试、场景测试、安全测试和恢复 kill-point。用 recipe 的 `product-contract.md` 与 `acceptance-tests.md` 验证公开行为相似度，不用截图相似度代替底层完整性。每项 verified capability 写回实现与测试路径。
