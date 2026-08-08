# LangGraph 体验与界面投影

## 目录

- [体验目标](#体验目标)
- [核心操作](#核心操作)
- [CLI](#cli)
- [Web 与 Studio-like](#web-与-studio-like)
- [状态投影](#状态投影)
- [Interrupt 体验](#interrupt-体验)
- [Time Travel 体验](#time-travel-体验)
- [错误与恢复](#错误与恢复)
- [无障碍与性能](#无障碍与性能)
- [验收](#验收)

## 体验目标

用户应看到 graph、run、task、state、checkpoint、interrupt 和 branch 的关系，而不是 Python traceback 或 reducer 私有结构。CLI/Web 是同一协议的两个 projection；断线后都能从 snapshot + events 恢复。

Studio-like 只表示可视化开发体验，不暗示复刻 LangSmith Studio 的闭源实现或托管控制面。

## 核心操作

- 创建/选择 thread，提交 input 或 `Command`；
- 实时查看当前 superstep、并行 tasks、子图 namespace；
- 切换 values/updates/messages/custom/checkpoints/tasks stream；
- 查看 state、next、pending tasks、interrupts 与 checkpoint metadata；
- 对 interrupt approve/respond/edit/reject（后两者属于上层 policy）；
- 浏览 history，比较 checkpoint，replay 或 fork；
- 查看 Store memory 与 thread state 的不同 scope；
- 取消 run，观察 task/child/executor 终止；
- 导出结构化 trace、state digest 和验收 artifact。

## CLI

建议命令面：

```text
harness graph inspect <graph>
harness run start --thread T --input input.json --stream updates,tasks
harness run watch <run>
harness state get --thread T [--checkpoint C] [--subgraphs]
harness interrupt list --thread T
harness interrupt resume I --request request.json --expect-head C
harness history list --thread T
harness history fork --checkpoint C --patch patch.json
harness run cancel <run>
```

stdout 用 JSONL/人类视图可选；stderr 只放诊断；exit code 区分 completed/interrupted/failed/cancelled/conflict。

## Web 与 Studio-like

- graph panel 显示 node/edge/branch/subgraph，不把动态 `Send` 伪装为静态 edge；
- run timeline 按 superstep 分组，并列显示同一步 task；
- state inspector 显示 channel 值、reducer 类型、最近 writer 和版本；
- checkpoint navigator 显示 parent/branch tree，而非单一线性列表；
- interrupt inbox 显示风险、请求参数、来源 task、expiry 和 expected head；
- stream console 可按 mode/namespace/task 筛选并显示 sequence gap；
- artifact/tool panel 来自设计综合层，不混入 core graph state；
- deployment/tenant/admin 页与开发 Studio 表面分离。

## 状态投影

1. 读取 thread/run snapshot，记录 `last_sequence` 与 projection schema；
2. 建立 event stream，从 `last_sequence + 1` 应用；
3. 重复 event 按 event id 去重；
4. 乱序暂存，sequence gap 超时后补拉；
5. checkpoint event 更新 durable badge，但不擅自标外部 effect durable；
6. disconnect 后重新取 snapshot 或 gap range；
7. 最终 projection hash 与服务端规范 state 对比。

前端不得直接 import Python TypedDict、channel class 或 checkpointer row schema。

## Interrupt 体验

- interrupt 状态必须区别于 failure 与普通“等待模型”。
- 显示 interrupt id、task/node、checkpoint、payload schema、policy version。
- resume 请求带 client request id 和 expected checkpoint head。
- 多 interrupt 支持按 id 提交 mapping，不按 UI 列表位置猜测。
- amended 参数显示 canonical diff，提交后重新授权。
- 重复提交显示已处理结果；head conflict 提示刷新，不静默覆盖。
- 审批之后 node 会从头运行，UI 应提示潜在副作用与幂等保障。

## Time Travel 体验

- history 是树/DAG，明确 current head、parent、fork source。
- diff 按 channel/reducer 展示，不只做文本 JSON diff。
- replay、fork、update state 三种动作在确认页解释副作用策略。
- 默认禁止自动重做 non-idempotent 外部 action。
- child graph history 可从 parent task 展开，并保留 namespace breadcrumb。
- 新 branch 完成不删除旧 checkpoint；可显式切换 active head。
- 导出包含 graph/build version、checkpoint lineage、policy 和 capability snapshot。

## 错误与恢复

- node error 显示 task、attempt、exception kind 与 handler outcome。
- persistence error 与 node error 分开；async durability 显示最后 durable checkpoint。
- cancel 显示传播进度及仍需 reconcile 的 external action。
- `indeterminate` 提供 receipt/status 查询或人工处理，不显示普通 retry。
- serializer/migration incompatibility 显示可读版本和只读恢复选项。
- sequence gap、projection mismatch 触发重新同步，不让用户基于陈旧 state 审批。

## 无障碍与性能

- task 状态不只靠颜色；所有 graph 操作支持键盘和文本列表替代。
- 大 state 默认字段摘要/分页，binary/large output 走 artifact。
- 高频 token/custom event 可批处理，但 task/checkpoint/interrupt 事件不丢。
- graph 大于阈值时按子图折叠与虚拟化渲染。
- 时间、step、sequence、checkpoint id 同时展示，避免时间排序误导分支。
- redaction 后仍保留字段存在、类型和 digest，便于诊断。

## 验收

- CLI JSONL 与 Web 对同一 fixture 产生相同 run 终态。
- snapshot + duplicate/out-of-order/gapped events 重建 hash 与 live state 一致。
- 并行 task、嵌套子图、多 interrupt 和 branch tree 可无歧义显示。
- resume conflict、cancel、persistence failure、`indeterminate` 都有专属交互。
- secret canary 不出现在 UI、导出和可访问性文本。
- 只使用规范协议即可实现客户端，不需要 runtime 私有对象。
