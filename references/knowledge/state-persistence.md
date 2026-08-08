# State 与持久化

## 职责与非目标

State 层持久化 thread、turn、item、event、checkpoint、配置快照和 lineage，使 crash、升级、fork 与 resume 可预测。
它保存领域事实和可重建投影，不保存 UI 组件对象，也不把数据库当前行当唯一审计源。
它不自行重放副作用、不决定对话内容选择、不用 archive 冒充 delete。
存储后端可以更换，但 id、sequence、因果、终态和迁移语义保持稳定。

## 逻辑 schema

```text
Thread { id, status, workspace_identity, config_digest, head_sequence, schema_version }
Turn { id, thread_id, ordinal, status, input_item_id, final_item_id?, error? }
Item { id, thread_id, turn_id, sequence, type, status, canonical_payload, hash }
Event { id, thread_id, sequence, type, payload, causation_id?, checksum }
Checkpoint { id, thread_id, sequence, context_ref, workspace_ref?, checksum }
Effect { idempotency_key, call_id, intent, state, receipt? }
```

状态源采用 append log/event；SQLite 或等价事务库负责列表、搜索和投影。
每个 frame/row 携带 schema version；canonical payload 用稳定序列化和 checksum。
同一 thread 默认单写者，写租约有 owner、epoch 和 expiry。

## 写入与恢复

写入顺序：验证 head → 追加 durable event/frame → 更新投影/outbox → commit → 广播。
无法跨 log 与数据库原子提交时使用 prepared/indexed marker，恢复以 durable log 为准。
snapshot 记录 last_sequence，加载采用 snapshot + tail events。
尾部半写可隔离到最后有效 frame；中部损坏必须阻止可写恢复。
在途 effect 按 planned/started/confirmed/unknown 分类，不能简单重放。

## 四级增量

| 等级 | 新增能力 | 不变量 |
|---|---|---|
| 能跑 | 内存 + append 会话文件 | 稳定 id、sequence、终态 |
| 能用 | SQLite/事务库、resume、migration | log 可审计、投影可重建 |
| 顺手 | 分页、checkpoint、fork、跨表面同步 | lineage、checksum、effect 状态 |
| 好用 | 多设备/远程、加密、保留、导出、灾备 | 单写者 epoch、兼容与可验证恢复 |

## 直接升级与回滚

先为旧记录补 event id、sequence 和 schema version，再迁移存储后端。
迁移按 N→N+1、幂等、小批次和可恢复 cursor 设计。
直接升级远程状态前先双写/校验，再切换 reader，最后停止旧写入。
回滚应用版本前停止新 schema 写入；无法旧读的数据保持只读并提供导出。
projection migration 可删除重建，canonical log migration 必须先备份和 checksum 校验。
每次升级随机 replay thread，比对 transcript、终态和 head hash。

## 失败模式与安全

- 断电半写：截到最后完整 frame并保留诊断；
- 索引领先：回退或重建，不能覆盖 log；
- 双写者：lease epoch 拒绝 stale writer；
- effect 无 receipt：查询 executor 或转人工复核，不盲目重试；
- migration 中断：从 cursor 幂等续跑，不标记已完成；
- fork artifact 共享：引用计数/可达性避免删除父分支破坏子分支；
- 敏感数据：字段级加密、密钥轮换、日志脱敏和保留政策；
- 恶意导入：校验 schema、大小、hash 与 id 映射，禁止路径注入。

## 可执行验收

- 在每个 append 边界 kill -9，恢复到最后完整事件；
- 删除投影数据库后由 log 重建相同 transcript/head hash；
- 同 migration 连跑三次结果一致，旧版本 reader 行为明确；
- effect 完成后、receipt 前崩溃不重复副作用；
- 两个 writer 竞争只有最新 lease epoch 可以提交；
- fork 后删除父 thread 不破坏子 thread 的 item/artifact；
- 10 万事件通过 snapshot+tail 在 SLO 内恢复且内存有界；
- 修改中部 frame 被 checksum 检测并阻止可写启动。

## 证据与设计综合

`公开事实`：Codex rollout/state、LangGraph checkpoint 和多种事件存储公开实现支持可恢复会话与投影思路。
`设计综合`：本逻辑 schema、写入顺序和 lease 规则是跨产品可靠性合同，不复制具体数据库格式。
协议顺序见 [protocol-events.md](protocol-events.md)，执行 effect 见 [tool-runtime.md](tool-runtime.md)，可靠性细节见 [reliability.md](reliability.md)。
