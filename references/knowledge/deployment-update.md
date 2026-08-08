# Deployment 与 Update

## 职责

管理 runtime、surface、executor、plugin、数据库和协议的可兼容发布。部署形态可以是本地单进程、桌面 sidecar、IDE host、容器、远程 worker 或多租户服务。

## 版本轴

分别版本化：产品 release、protocol、event schema、database schema、ToolSpec、plugin API、config。不要用一个包版本推断全部兼容性。

## 启动流程

```text
verify binary/signature
-> load config/requirements
-> migrate database
-> initialize secret store
-> initialize sandbox/executor
-> start event store/app-server
-> advertise capabilities/health
-> accept turns
```

关键依赖失败必须 fail closed 或进入明确只读模式。

## 四级增量

- runnable：源码/单包启动、版本输出；
- usable：安装包、config/db migration、health check；
- productive：桌面/扩展更新、remote worker、灰度与 rollback；
- polished：签名、SBOM、租户 rollout、灾备、LTS、合规与供应链策略。

## 直接升级

先部署兼容 reader，再迁移数据，最后启用新 capability。旧客户端通过协商工作或收到明确升级要求。自动更新验证签名和来源，不能在 turn 中途替换 executor。

## 失败模式

数据库迁移中断、client/server 协议不匹配、坏 plugin 阻止启动、自动更新供应链劫持、回滚二进制无法读取新 schema、remote worker 版本漂移。

## 验收

- N-1 客户端与 N 服务端；
- N 客户端与 N-1 服务端能力降级；
- 每个 migration kill/restart；
- 坏插件隔离启动；
- 签名错误拒绝更新；
- remote worker capability 与实际 enforcement 一致；
- rollback 后旧 session 可读或有明确不可逆说明。

证据类型：设计综合；协议与迁移细节见 `references/implementation/protocol.md` 和 `storage.md`。

