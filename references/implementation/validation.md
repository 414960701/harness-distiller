# 完整性验收矩阵

## 合同层

- 所有 command/event/domain schema 有 golden fixture；
- ToolSpec 输入输出和 capability negotiation 可运行；
- provider adapter 通过同一 contract suite；
- store 支持 create/list/resume/fork/archive/migrate；
- UI projection 对重复/乱序/gap 事件行为确定。

## Agent 场景

1. 只回答不使用工具；
2. 读取文件解释代码；
3. 跨文件编辑并运行测试；
4. 测试失败后修复；
5. 用户中途 steering；
6. context 超限后压缩继续；
7. 工具拒绝后调整方案；
8. 子代理或后台任务返回；
9. 重启恢复；
10. 达到预算后有解释地停止。

## 安全场景

- 路径穿越、symlink、受保护目录；
- shell 注入、Git config/output trick、子进程逃逸；
- 默认断网、域 allowlist、redirect/private IP；
- secret 在 prompt/log/artifact/notification 中脱敏；
- MCP/tool 虚假副作用注解；
- browser prompt injection 与 Computer Use 错目标；
- approval action hash 变化；
- sandbox 初始化失败 fail closed。

## 恢复场景

在以下位置 kill：command 已接收、turn 已开始、model 流中、tool intent 已存、tool 刚完成、result 事务中、event 已存未发布、checkpoint 中。每次重启验证 event 不丢不重、终态唯一、不可逆动作不重复。

## 产品 parity

以产品 `product-contract.md` 和 `acceptance-tests.md` 为准。比较公开行为、信息架构、任务流程、恢复和权限，不比较商标、像素或私有 prompt。闭源行为无法重复时标 `blocked-by-evidence`，不得用推断测试冒充。

## 分级闸门

### runnable

垂直切片、明确终止、workspace 边界、基础 approval、streaming、smoke task。

### usable

真实编码/工作任务、持久化、resume、compaction、diff/artifact、取消重试、主表面、contract/scenario tests。

### productive

worktree/并行/subagents/hooks/index、细粒度权限、checkpoint、observability、eval、多个表面共享协议。

### polished

强 sandbox/network、remote/multi-tenant、managed policy、协议/数据库迁移、供应链、SLO、无障碍、灾备。

## 交付报告

必须输出表：capability、目标等级、状态、实现路径、测试路径、证据、已知差异、下一升级。状态只允许 selected/implemented/verified/deferred/blocked-by-evidence。

