# OpenHands-like Canvas、CLI 与 SDK 体验

## 目录

- [体验原则](#体验原则)
- [Canvas 布局](#canvas-布局)
- [事件卡](#事件卡)
- [Terminal Browser Files Diff](#terminal-browser-files-diff)
- [确认与安全](#确认与安全)
- [连接恢复](#连接恢复)
- [CLI 与 Headless](#cli-与-headless)
- [SDK 体验](#sdk-体验)
- [可访问性与性能](#可访问性与性能)
- [体验验收](#体验验收)

## 体验原则

界面呈现“agent 正在做什么、影响什么、如何控制”，而不是暴露内部 Python 对象。所有视图从 snapshot + canonical event 投影。

- 用户输入立即显示 optimistic message，收到 durable id 后 reconcile；
- agent 状态、工具活动、diff、terminal/browser 互相引用同 action；
- thought 只显示可公开摘要，不展示私有 chain-of-thought；
- 错误给稳定 code、恢复动作和 error id；
- local-host、container、remote 执行模式始终可见；
- stop/pause/approve/reject 不藏在日志文本。

## Canvas 布局

推荐三层：

1. 左栏：workspace/backend、conversation 列表、状态、标签和新任务；
2. 主区：chat/event timeline、输入、model/profile/mode、运行控制；
3. 右区 tabs：changes/files、terminal、browser、plan/goal、runtime/security。

窄屏改为 bottom sheet/tab，但当前 conversation、status 和 stop 始终可达。多 conversation tab 只保留 UI 导航，不产生并发 writer。

创建页先选 workspace/backend，再显示 agent/profile。runtime provisioning 展示阶段；失败保留重试和诊断。

## 事件卡

MessageEvent 显示用户/agent内容；Action+Observation 配成一张 tool card。

连续 grep/read 等低风险事件可折叠为 group，卡片摘要显示 completed/total 和最新动作。等待中的 Action 不能被折叠到不可见。

每张工具卡包含：tool、目标、状态、duration、风险、stdout/diff/artifact、重试/失败。Observation 无匹配 action 时显示 protocol warning，而不是崩溃。

StreamingDelta 临时更新同一 agent message；completed MessageEvent 替换 delta。重连后不重复文本。

## Terminal Browser Files Diff

Terminal 显示 session、cwd、command、stdout/stderr、exit/timeout；用户输入 stdin 走受控命令。大输出虚拟化和下载 artifact。

Browser 显示当前 URL、tab、screenshot/structured state；agent click/type 在 timeline 与浏览器高亮关联。敏感字段不回显。

Files 使用 workspace API lazy load；编辑事件 bump cache revision。Diff 分 staged/unstaged/untracked、binary/rename，提供文件跳转；查看 diff 不修改 git。

Plan/Task tracker 从 planning observation 投影，完成状态可追踪到 action。Goal/stuck/critic 信息与普通 assistant 文案区分。

## 确认与安全

Confirmation 卡片固定显示：规范化 action、workspace/runtime、风险类别、分析器状态、影响目标、一次 approve/reject。

用户批准后卡片进入 resolved，重复点击幂等。参数改变生成新请求。分析器不可用显示 degraded；不通过颜色暗示“安全”。

Security 面板显示 policy、sandbox profile、network、secret scopes 和最近分析日志；只展示 secret 名称，不展示值。

LocalWorkspace 顶部常驻“本机执行”标识；强安全模式不可选择它。

## 连接恢复

WebSocket 状态：connecting、live、reconnecting、resyncing、offline。断线不清空已确认事件。

重连发送 last offset；gap 时暂停 live apply、获取 snapshot/page、再合并。conversation 切换取消旧 subscription，旧 socket 迟到事件因 id scope 被拒绝。

optimistic message 超时转 error，可重试同 idempotency key。发送成功但 echo 丢失时历史补拉完成 reconcile。

server/runtime died 与浏览器网络离线分开显示。恢复失败给“导出历史/诊断”而非无限 spinner。

## CLI 与 Headless

交互 CLI：流式消息、tool 摘要、confirmation prompt、Ctrl-C interrupt、conversation resume。非 TTY 时禁止隐式等待确认。

Headless JSONL 每行一个 versioned envelope；stdout 只输出协议，诊断走 stderr。退出码建议：0 completed，2 invalid config，3 denied/confirmation unavailable，4 failed，5 interrupted，6 ownership lost。

`--resume`、`--workspace`、`--profile`、`--max-budget`、`--jsonl` 和 `--no-interactive` 语义明确。CLI 与 Canvas 对同 fixture 的终态/event digest 等价。

## SDK 体验

最小 API：构造 LLM/Agent/Workspace/Conversation，`send_message`，`run/arun`，订阅 event/token，`interrupt`，`close`。

Context manager 保证 workspace cleanup；同步/异步不能混用导致双 writer。callback 异常被隔离并记录，不中断持久化。

类型提示导出 Action/Observation/Event union；未知扩展可访问 raw payload。测试提供 scripted LLM 和 in-memory workspace/event store。

## 可访问性与性能

- 键盘可完成发送、stop、tab、展开事件和 confirmation；
- 动态状态使用 aria-live，token delta 节流避免读屏轰炸；
- 风险和状态不只依赖颜色；
- terminal/browser 有文本替代；
- 长 timeline 虚拟化，历史分页保留滚动锚点；
- 事件 group 展开不触发全列表重排；
- i18n 文案不进入机器 schema；
- 移动端 stop/approve 至少 44px target。

## 体验验收

- snapshot+events 可重建 chat、status、plan、terminal、browser 和 diff。
- reconnect/duplicate/out-of-order 不重复卡片或消息。
- pending confirmation、running tool 和 failed runtime 清晰可控。
- local 与 sandbox 标签准确，不误导安全能力。
- Canvas、CLI、headless 对同 fixture 有相同 Conversation 终态。
- 10 万事件历史仍能分页和交互；慢客户端不阻塞 runtime。
- 键盘、读屏、窄屏和 i18n 基线测试通过。

界面只证明公开行为，私有 Cloud 体验不从截图推断。来源见 [sources.md](sources.md)。
