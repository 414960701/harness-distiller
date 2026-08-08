# Desktop 与 Web Surface

## 职责与非目标

桌面/Web 客户端管理项目、任务、artifacts、review、环境和认证，并订阅后端结构化事件。
前端是服务端 snapshot + event 的投影，不把浏览器缓存、DOM 或模型文本当事实源。
本地与远程执行的信任边界、数据位置和能力差异必须持续可见。
Surface 不持有 provider refresh token，不自行判定工具权限或完成状态。

## 前端协议

```yaml
SurfaceSession:
  client_id: string
  user_id: string
  protocol_version: string
  auth_context: string
  connection: connecting|online|degraded|offline
TaskProjection:
  task_id: string
  status: string
  projected_through_seq: integer
  unread_attention: integer
  execution_location: local|remote|hybrid
```

接口：`fetch_snapshot`, `subscribe(after_seq)`, `send_command(command_id, expected_seq)`, `upload_attachment`, `open/download artifact`。
命令可重试但必须幂等；event_id 去重，序号跳跃触发补拉。
多标签/多窗口共享服务端状态，draft 可本地保存但发送后由 Turn 事件确认。

## 事件投影与 UI 状态

任务列表投影 Task/Schedule/Attention；主面板投影 Turn/Item/Artifact；Monitor 投影 Step/ToolCall/Approval。
连接断开时所有 view 标 stale，禁止继续显示“实时运行”错觉。
乐观 UI 仅用于可撤销本地动作；外发、审批、删除和运行状态等 command 等服务端确认。
notification deep link 必须携带 task_id/event_id，并在过期时显示真实当前状态。
本地/云 handoff 创建明确 event 和 checkpoint，不在两个执行器同时拥有 lease。

## 四级增量

### `runnable` 能跑

单任务页面、composer/transcript、流式文本、基础 artifact 与运行/失败状态。

### `usable` 能用

增加任务历史、项目、搜索、结构化 plan/tool/approval、artifact 预览和重连。

### `productive` 顺手

增加并行任务、三栏/多 pane、local-cloud handoff、review、离线 draft、桌面通知和快捷输入。

产品 recipe 可以把某项能力提前：QoderWork 的公开 usable 合同要求并行 Task 和三栏 Task Monitor，因此以产品 `recipe.md`/`acceptance-tests.md` 的较早等级为准；共享等级只表示通用默认，不得覆盖产品合同。

### `polished` 好用

增加多租户、多设备、合规、细粒度 RBAC、无障碍、国际化、离线投影和灾备。

## 直接升级与回滚

先定义 versioned snapshot/event/command 协议，再拆分 UI pane。
从单任务升级并行时，所有 local state key 加 task_id/client_id，运行时 lease 留在服务端。
新投影器与旧 API 双读比较 through_seq 和终态，再切 feature flag。
回滚 UI bundle 不回滚事件；未知 event 用通用卡片或只读降级。

## 失败模式与安全

- 网络抖动：cursor 补拉与 command idempotency，禁止盲重发外部动作。
- 多标签竞态：expected_seq 冲突返回并刷新，不 last-write-wins。
- auth 过期：停止敏感订阅/下载并 reauth，不清空未发送 draft。
- 权限收紧：立即刷新 capability，不依赖旧前端缓存。
- XSS/富文本：严格 sanitize，artifact 在隔离 viewer 打开。
- 本地/远程混淆：每个 ToolCall 和 artifact 标 execution location/data residency。

## 验收 oracle

1. 打乱/重复 WebSocket event 后最终投影等于服务端重放。
2. 两标签同时改名产生显式冲突或确定顺序。
3. 离线期间不会伪造 completed，重连后补全事件。
4. auth 撤销后旧标签无法下载 artifact。
5. handoff 后只有一个 executor lease 能发工具调用。
6. 键盘/屏幕阅读器可导航任务、审批和 artifact，状态不只靠颜色。

## 来源与设计综合

参考 [WHATWG WebSocket](https://websockets.spec.whatwg.org/) 与 [WAI-ARIA Authoring Practices](https://www.w3.org/WAI/ARIA/apg/) 的互操作/无障碍合同。
三栏、Task Monitor 等产品专属布局由 dossier 的 `experience.md` 决定；共享层只要求可重建事件投影。
