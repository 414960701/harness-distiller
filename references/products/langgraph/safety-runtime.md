# LangGraph 安全运行时

## 目录

- [安全事实](#安全事实)
- [威胁模型](#威胁模型)
- [Permission 与 Interrupt](#permission-与-interrupt)
- [Sandbox](#sandbox)
- [序列化与存储](#序列化与存储)
- [多租户](#多租户)
- [提示与工具数据](#提示与工具数据)
- [失败关闭](#失败关闭)
- [安全验收](#安全验收)

## 安全事实

LangGraph 的 interrupt 是 durable pause primitive，不是 permission system；callable node 在宿主进程内运行，不是 sandbox；checkpointer/store 协议本身不自动提供租户认证。复刻时必须保留这些边界。

上游提供 serializer/allowlist/encryption 相关构件，但应用仍要选择安全类型、密钥和存储策略。

## 威胁模型

- 不可信 graph input、resume payload、tool output、retrieval 和 memory 内容；
- 恶意或被劫持 node/tool/plugin 读取 secret、网络外传或修改 workspace；
- checkpoint 中的 gadget/object 反序列化；
- tenant/thread/checkpoint namespace 猜测导致越权；
- interrupt amend 后绕过原参数 policy；
- replay/retry 导致付款、删除、发布等副作用重复；
- debug/custom stream 泄露 state、prompt、credential；
- 子图通过 parent command 或 shared Store 提升权限。

## Permission 与 Interrupt

permission engine 在 action dispatch 之前返回 `allow/deny/ask/amend`：

- policy 输入使用规范化 tool id/version、arguments、workspace、actor、risk、scope；
- `ask` 先 durable checkpoint，再 `interrupt` 展示最小必要信息；
- resume 包含 approval request id、decision、actor、expiry 和可选 amended args；
- amend 后重新走 schema、path、network 和 permission policy；
- rule snapshot/version 写入 turn，恢复时不得偷偷改用更宽新规则；
- child graph 继承 ceiling，只能进一步收紧；
- deny 产生终态 item，不伪造 tool success。

## Sandbox

- filesystem root、process、network、DNS、redirect、CPU、memory、time、output 分别限制；
- host env 默认不可见，secret 按 tool/action 最小注入；
- symlink、mount、socket、procfs 与 package manager 都在逃逸测试中；
- cancellation 杀进程树并撤销 credential/lease；
- sandbox provider 不可用时 fail closed，除非 profile 明确允许本地执行；
- graph concurrency limit 不能替代 OS/container resource quota；
- sandbox receipt 与 task/checkpoint lineage 绑定。

## 序列化与存储

- 只允许声明 schema/type；拒绝任意 pickle/object import。
- serializer allowlist 是 defense-in-depth，不是 tenant authorization。
- checkpoint、pending writes、Store、events、artifacts 分别加密并管理 key version。
- secret 不进入 state；若不可避免，字段级加密且 stream/trace 强制 redaction。
- checkpoint migration 在隔离进程读取旧数据，并验证 digest/size/depth。
- list/history/query 都在存储层执行 tenant filter。
- delete thread 覆盖 checkpoint、writes 与索引；Store/外部 artifact 按独立 retention 清理。

## 多租户

- tenant id 从认证上下文得到，不能信任 graph input。
- storage primary key 显式包含 tenant，避免只靠 namespace 字符串拼接。
- thread id、checkpoint id、run id 不可作为授权凭证。
- Store namespace 有 server-side prefix/ACL；semantic search 不跨 tenant 建候选集。
- quota 覆盖 active runs、supersteps、tasks、state bytes、history、stream 和 executor usage。
- Studio/debug 管理权限与普通 invoke 权限分离。
- backup/restore 与 key rotation 保持 tenant 隔离。

## 提示与工具数据

- tool/RAG/memory 内容标记 untrusted data，不能覆盖 system/policy。
- model 建议调用危险工具仍必须通过 deterministic policy。
- custom event type 不可使用保留 `graph.*` namespace。
- exception/trace 在用户 surface 前清除 path、secret、SQL 和 provider credential。
- approval UI 不渲染未转义 HTML/Markdown，参数有 canonical diff。
- final answer 不等于工具执行证据，receipt 才是效果事实。

## 失败关闭

- checkpointer 不可用时，有 durable requirement 的 run 不降级内存模式。
- permission service 超时按风险 policy deny/ask，不默认 allow。
- sandbox/secret broker 不可用时拒绝动作。
- serializer 遇未知 type 拒绝，不回退不安全 codec。
- sequence gap 阻止高风险 UI 决策，先补拉 snapshot/events。
- external commit 状态未知时进入 reconcile/`indeterminate`。
- migration 不通过时保留旧数据只读，不覆盖源 checkpoint。

## 安全验收

- 覆盖绝对/相对/symlink path、进程树、网络重定向与 secret exfiltration。
- deny/ask/amend/expiry/replay 均有黑盒测试。
- 恶意 resume 不能恢复其他 interrupt/thread/tenant。
- 恶意 checkpoint payload 不触发代码执行。
- parent/child permission 与 Store scope 无越权。
- retry/resume/time travel 不重复 non-idempotent action。
- debug/custom/message stream 经 redaction 后不包含 canary secret。
- fail-open 路径为零，例外必须有显式 profile、审计和发布门禁。
