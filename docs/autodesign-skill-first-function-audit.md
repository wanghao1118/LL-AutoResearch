# AutoDesign Skill-first 功能对比审计

## 对比对象

`fix/AutoDesign` 与 `codex/autodesign` 两个 Git 引用当前都指向 `e50217d6f1e1ad01360be7515862308ea29d9f2c`，因此 Git 引用本身没有包含两版 AutoDesign 实现。此次功能对比使用：

- 当前 `fix/AutoDesign` 工作树中的 Skill-first 实现；
- `assets/output/delivery/autodesign_source.tar.gz` 中已验证的工程化 AutoDesign 交付快照。

工程化快照包含 `14` 个 Python 文件、`4,331` 行 Python 和 `41` 项通过的回归测试。当前实现包含 `8` 个 Python 文件、`2,175` 行 Python、七个 Skill、`24` 个 Skill 文件和 `21` 项通过的回归测试。

## 功能矩阵

| 功能 | 工程化快照 | 当前 Skill-first | 判断 |
| --- | --- | --- | --- |
| 输入固定字段 | Python schema 归一化 `motivation/contribution/benchmark` | `input_brief.md` 保留固定输入与显式锁 | 保留，研究输入改为 Markdown |
| 方法选择 | 单个设计 Prompt 和大 JSON schema | `autodesign-method-router`，含 route 比较、R0 与 falsifier | 增强，方法空间不再受大 schema 限制 |
| contribution 证据覆盖 | validator 检查四类 evidence 和字段映射 | evidence Skill 的 claim ledger、test axes、falsifier 与最终 auditor | 语义保留；不再用 Python 决定研究设计 |
| 代码物化 | `code_bundle.json` 加固定 materializer | implementer 直接生成真实项目、环境、命令和 result contract | 保留，去掉 bundle 文件格式限制 |
| 本地执行 | smoke、experiment、aggregate | preflight、smoke、experiment、aggregate、collect | 增强为五阶段且支持失败续跑 |
| 远端 GPU | SSH、Conda、GPU 和结果拉取 | 保留控制器并对接 materialized command plan | 保留并覆盖五个项目阶段 |
| 结果完整性 | 按设计 schema 聚合 cells | 按显式 experiment schedule 校验 cells 和 metrics | 保留，且不会自动产生 claim verdict |
| 结果诊断 | 完整 iteration Prompt、JSON diagnosis 和确定性 Prompt 路由 | result-scientist 逐 contribution 诊断并写 `result_route.md` | 保留；研究判断交给 Skill，路由事实显式落盘 |
| 结果微调 Prompt | package template 加 renderer 注入上下文 | 完整 Prompt 位于 result-scientist references，并由 Skill 直接读取本轮工件 | 本轮补齐，源 Prompt 为 `153` 行、`9,508` 字节 |
| tuning/iteration 闭环 | 生成请求后停在 `WAITING_FOR_GPT_RESULT_TUNING` | owner Skill → 实现或证据修复 → 执行 → 摄取 → 重新诊断 | 本轮补齐，当前闭环比旧快照多一步真正执行与复诊 |
| 独立最终审计 | 无独立审计 stage | integrity auditor 检查 claim、运行、聚合、图表和 route closure | 新增 |
| Dashboard/show | Python 生成每次运行的 dashboard | 运行状态使用 Markdown；paper tables/charts 由 Skill 生成 | 有意移除的界面功能，不影响科学执行链 |

## 本轮发现并修复的缺口

### 1. 完整微调 Prompt 没有进入已安装 Skill

此前 result-scientist 只有几条 tuning 摘要，无法保证加载六种策略和完整 JSON 输出。现在完整文件位于：

`skills/autodesign-result-scientist/references/result_tuning_prompt.md`

Skill 只在诊断结果选择 `tuning` 后读取它，并同时读取 input brief、method route、evidence plan、execution record、raw results、result summary 和 contribution diagnosis。

### 2. 诊断后直接进入 audit，缺少 route closure

此前 `RESULT_DIAGNOSIS_READY` 固定指向 integrity auditor，导致 iteration 或 tuning 可能尚未执行就被审计。现在每轮诊断必须生成 `result_route.md`，状态返回 `run-autodesign`；编排器按 owner Skill 执行修复或新实验，再摄取结果并重新诊断。

### 3. tuning 输出和下一轮没有独立工件

现在 tuning 使用 Prompt JSON schema 写入 `result_tuning.json`；任何未执行动作写入 `next_round.md`。最终审计把开放的 iteration 或 execution-required tuning 视为 FAIL，避免把 expected delta 当成 observed result。

## 有意不恢复的旧功能

1. 不恢复 `prepare/accept-design/materialize-code` 的大型 JSON schema；它们正是限制 Codex 方法空间的工程层。
2. 不恢复 Prompt renderer；Skill 直接读取权威运行工件，避免把同一上下文再复制成巨型请求文件。
3. 不复制旧 `result_iteration_prompt.md`。其 contribution 诊断、失败分层、单变量下一轮和阈值要求已经进入 result-scientist；旧文件仍允许改写 claim，与当前“原 contribution/claim 不变”的合同冲突。
4. 不恢复 Python dashboard 和 `show` 命令。需要展示时，由报告工件和可视化 Skill 生成，不再把 UI 作为研究 pipeline 的依赖。

## 结论

从输入、方法路线、R0、证据设计、项目实现、五阶段执行、结果摄取、逐 contribution 诊断、iteration/tuning 闭环、独立审计到 COMPLETE，当前流程没有缺失的科学阶段。

当前剩余的交付状态问题是：`fix/AutoDesign` 与 `codex/autodesign` 仍指向同一个旧提交，Skill-first 工作树尚未形成独立 Git 提交；这不影响本机运行，但在提交前不能仅依靠 Git branch ref 重现两版差异。
