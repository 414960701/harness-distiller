# Notifications 与用户输入

## 职责与非目标

输入系统区分新 turn、turn 内 steering、阻塞式 elicitation、风险 approval 和异步 notification。
这些类型有不同生命周期，不能把迟到回复或通知点击当作当前任务的新指令。
Notification 是状态提示/deep link，不是唯一交互入口，也不携带完整敏感内容。
输入路由不自行扩大权限；approval 只针对展示的具体动作与有效期。

## 请求 schema

```yaml
InputRequest:
  id: string
  task_id: string
  kind: steering|elicitation|approval
  prompt: string
  response_schema: object|null
  action_digest: string|null
  status: open|answered|expired|cancelled|superseded
  deadline: timestamp|null
  default_on_timeout: deny|cancel|continue_without
Notification:
  id: string
  task_id: string
  event_id: string
  category: completed|failed|attention|approval|schedule
  dedupe_key: string
  sensitivity: public|private
```

接口：`request_input`, `answer(request_id, expected_status)`, `steer(run_id)`, `notify`, `ack`, `route`。
所有响应带 correlation id、actor、received_at 和客户端 id。
approval 绑定标准化 action digest；参数改变即原批准失效。

## 生命周期与投影

Request 由事件投影到 Task Monitor、composer 或 modal；服务端状态是事实源。
重复点击按 request_id 幂等；过期/已回答返回当前状态，不把内容转给下一请求。
steering 进入当前 Run 输入队列；是否能中断当前工具由工具取消能力决定。
新 turn 在当前 Run 终止后开启新 correlation；若产品允许并行则创建明确新 Run。
notification deep link 打开 task/event，随后刷新真实状态而非显示旧 payload。

## 四级增量

### `runnable` 能跑

只在 turn 结束接受新输入，风险动作同步询问，完成后显示应用内状态。

### `usable` 能用

增加 typed approval/elicitation、deadline、schema validation、幂等响应和 Task attention。

### `productive` 顺手

增加 steering、输入队列、桌面通知、后台回传、语音/快捷输入和静默时段。

### `polished` 好用

增加跨设备路由、去重、升级策略、合规保留、组织值班、无障碍与通知隐私。

## 直接升级与回滚

先为旧 modal 生成 InputRequest id/status/action digest，再接异步通知与跨设备。
steering 上线前建立 run/cancel/queue 语义，避免把所有输入拼进当前 prompt。
通知通道按 feature flag 开启，失败始终保留应用内 attention。
回滚外部通知不删除 open request；迟到渠道响应仍由服务端过期校验。

## 失败模式与安全

- 重复点击：idempotency + expected status，只处理一次。
- 迟到输入：过期/被 supersede 后拒绝，不挪作新 turn。
- approval 换参：action digest 不符重新询问。
- 通知泄密：锁屏只显示通用文案，敏感详情进应用后鉴权。
- 离线：队列带 deadline，重连先同步状态再发送。
- notification fatigue：去重、静默时段、优先级和速率限制。

## 验收 oracle

1. 同一 approval 两设备同时点击只执行一次。
2. approval 展示后修改目标/附件会使原请求失效。
3. 过期 elicitation 回复不进入后续新 Turn。
4. steering 与 cancel 竞态有确定结果并记录事件顺序。
5. 锁屏通知不含文件名、prompt、secret 或客户数据。
6. 通知服务不可用时应用内 attention 仍可完成工作流。

## 来源与设计综合

参考 [Web Notifications](https://notifications.spec.whatwg.org/) 与 [CloudEvents](https://cloudevents.io/) 的标识/路由思路。
具体桌面渠道、UI 文案和 Task Monitor 位置由产品 dossier 定义；共享层规定请求关联、时效和隐私。
