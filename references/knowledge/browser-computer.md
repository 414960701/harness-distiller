# Browser 与 Computer Use

## 目录

- [职责](#职责)
- [非目标](#非目标)
- [接口与 Schema](#接口与-schema)
- [状态与确认](#状态与确认)
- [Policy 与 Enforcement](#policy-与-enforcement)
- [四级增量](#四级增量)
- [直接升级与回滚](#直接升级与回滚)
- [失败模式与攻击面](#失败模式与攻击面)
- [可执行验收](#可执行验收)
- [来源与设计综合](#来源与设计综合)

## 职责

Browser/Computer Use 把网页和桌面视觉操作封装为引用明确 snapshot、窗口和目标的高风险工具，并对导航、输入、下载、上传、交易和系统操作分级。

执行前重新验证目标仍对应审批时的页面/控件；页面文本、DOM、截图和辅助功能树均视为不可信外部内容。

## 非目标

- 不把视觉相似度当稳定身份或授权证明。
- 不绕过登录、验证码、网站条款或系统隐私控制。
- 不自动读取密码管理器、私密窗口或安全输入区域。
- 不把 browser sandbox 等同宿主完整隔离。
- 不承诺任意 GUI 动作可逆。

## 接口与 Schema

```yaml
UISnapshot:
  id: string
  surface: browser|desktop
  window_id: string
  tab_id: string|null
  origin: string|null
  revision: string
  image_ref: string|null
  tree_ref: string|null
  captured_at: timestamp
```

```yaml
UIAction:
  snapshot_id: string
  kind: navigate|click|type|key|upload|download|drag|confirm
  target: {node_id, label, bounds, selector}|null
  value_ref: string|null
  effect: read|local_write|external_write|transaction|credential
  expected_origin: string|null
```

```yaml
UIResult:
  status: succeeded|failed|stale|denied|needs_confirmation|outcome_unknown
  before_snapshot: string
  after_snapshot: string|null
  artifacts: [string]
  observed_effects: [object]
```

## 状态与确认

`observed -> target_resolved -> policy_checked -> freshness_checked -> executing -> observed | stale | unknown`

origin、tab/window identity、目标 bounds/tree node 或页面 revision 变化时返回 stale，不在新目标上猜点击。

交易、消息发送、发布、删除、上传、购买和 credential 动作在最后提交点做二次确认。

## Policy 与 Enforcement

Policy 依据站点/origin、账户、effect、数据分类和可逆性决策；Browser/OS adapter enforce tab/window、下载目录、上传文件和输入字段。

网络 allow 不自动允许页面中的 external write；同一域名不同账户/tenant 也不能共享批准。

secret 通过受限 autofill/handle 注入，模型、DOM dump 和截图不接触明文。

## 四级增量

### runnable / 能跑

显式 URL 的只读导航、snapshot identity、所有写动作人工操作。

### usable / 能用

DOM/可访问树/截图、受控 click/type、origin policy、stale 检查和下载隔离。

### productive / 顺手

会话恢复、上传/download artifact、站点 adapter、受限凭证注入和回放审计。

### polished / 好用

隔离浏览器池、视觉防注入、交易双确认、租户 profile、远程桌面 attestation。

## 直接升级与回滚

从 screenshot 坐标升级 DOM/tree identity 时保留坐标 fallback，但高风险动作必须要求稳定 node + fresh snapshot。

session schema 先记录 origin/profile/account identity，再启用自动写动作；历史 session 缺 identity 时只读恢复。

回滚站点 adapter 时不复用其高信任确认，降级通用模式并重新 ask；未完成交易标 outcome_unknown。

## 失败模式与攻击面

- prompt injection 伪装系统/用户指令。
- overlay、动画、滚动、响应式布局让坐标命中错误目标。
- 同名按钮、iframe、shadow DOM 和跨域嵌套混淆身份。
- 点击前页面跳转或 tab/window 被替换。
- 恶意下载、自动打开和文件名路径逃逸。
- 上传选错 artifact 或泄露 workspace/private file。
- 截图、clipboard、OCR、accessibility tree 泄露密码/隐私。
- 提交后断线导致 outcome_unknown 和重复交易。
- 已登录 profile、cookie、cache 跨租户泄露。

## 可执行验收

- snapshot 后替换同位置按钮，旧 action 返回 stale 且无点击副作用。
- iframe/overlay/同名控件 fixture 只有明确 node/origin 可执行。
- prompt injection 文本不能改变 managed policy 或允许上传 secret。
- download 固定落隔离目录，恶意文件名不能越界或自动执行。
- upload 仅能选已批准 artifact，路径变化或 hash 变化需重批。
- purchase/send/delete 在最后提交点产生 fresh confirmation。
- credential 注入后 model、snapshot、DOM、event、clipboard 均无明文。
- 提交后断线先查询站点状态，不盲目重放 transaction。

## 来源与设计综合

参考 Web origin、CDP/WebDriver、accessibility tree、OS accessibility 和浏览器 profile 隔离公开语义；统一 snapshot/action schema 是设计综合。

- WebDriver：https://www.w3.org/TR/webdriver2/
- Chrome DevTools Protocol：https://chromedevtools.github.io/devtools-protocol/
- Web origin model：https://html.spec.whatwg.org/multipage/browsers.html#concept-origin

网络和 secret 见 [network-secrets.md](network-secrets.md)，工具生命周期见 [../implementation/tools.md](../implementation/tools.md)，surface 事件呈现见 [../implementation/ui.md](../implementation/ui.md)。

产品专属浏览器能力应写 adapter/capability，不应把某网站 selector 或闭源 GUI 结构固化为共享合同。
