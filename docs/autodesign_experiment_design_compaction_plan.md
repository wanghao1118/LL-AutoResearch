# AutoDesign Experiment Design Skill 精简与增强方案

## 目标

先消除 `autodesign-experiment-design` 主入口与 `references/design-contract.md` 的重复，再以“替换现有规则”而非“追加章节”的方式吸收 EXP38 Sol Case 4 与 Luna Case 3 暴露的设计缺口。

成功标准：

- `SKILL.md` 从当前约 2,274 words 压缩至约 1,200–1,500 words；数字是方向性预算，不能以删除科学边界换取达标。
- 设计 Skill 与其必读 references 的总文本从约 5,400 words 压缩至约 3,000–3,500 words。
- 保留 scientific locks、高影响选择 R0、证据类别、simulated-target 边界、结构 PASS 与科学 readiness 分离等现有不变量。
- 不增加实验 family、最低表格数量、新状态层级或通用评分表。
- 新规则能识别 Case 4 的 external baseline / R0 reference-cell 缺口，以及 Case 3 的 constructor–teacher capacity 混杂。

## 修改范围

主要修改：

- `skills/autodesign-experiment-design/SKILL.md`
- `skills/autodesign-experiment-design/references/design-contract.md`

按需修改：

- 与新增字段直接相关的 AutoDesign schema、checker 和对应测试。

默认不修改：

- `autodesign-experiment-run`
- `autodesign-result-scientist`
- `autodesign-integrity-auditor`
- `run-autodesign`

只有在链接、状态名称或 artifact contract 被本次修改直接破坏时，才做最小一致性修正。不得把 Auditor 的执行完整性、结果 provenance 或最终 claim 审计复制回 Design Skill。

## 第一阶段：精简

### 1. 建立 Keep / Merge / Move / Delete 清单

逐段比较 `SKILL.md`、`design-contract.md` 与现有 checker：

- **Keep in SKILL.md**：会改变科学决策的核心不变量。
- **Merge**：在主入口重复出现的 route、R0、experiment card、table 和 readiness 规则。
- **Move to contract**：字段 schema、完整输出章节、placeholder、ID 和 JSON 细节。
- **Delete**：Codex 已具备的通用建议、不会改变决定的解释、与 Auditor 重复的末端检查。

### 2. 将 SKILL.md 收敛为四个核心段落

1. Input locks and scope：Motivation / Contribution / Benchmark、scientific locks、autonomous choices。
2. Route and R0：方法路线、高影响选择、角色闭合、R0 gate。
3. Claim-bearing evidence：main / ablation / case study / analysis 的证据职责及 claim contract。
4. Artifacts and readiness：输出、simulated target、AutoWriting handoff、结构与科学状态边界。

### 3. Contract 只保留规范，不重复科学论述

`design-contract.md` 保留：

- artifact 字段与允许值；
- experiment / execution cell / aggregate / paper cell / decision effect 的身份关系；
- table shell 与 result placeholder 格式；
- `expected_effects.json` schema；
- coverage audit 的机器可读要求。

主 Skill 与 contract 对同一规则只保留一个权威表述。

## 第二阶段：嵌入四项改进

### 1. Baseline 双角色闭合

用一条规则替换现有 baseline 列表式要求：

- `causal_reference`：除目标 intervention 外保持关键轴 matched，用于估计方法效应。
- `contextual_baseline`：领域内可识别的独立外部系统，用于论文定位。

同一 baseline 可以兼任，但必须分别证明两个角色；缺少任一角色时记录 evidence gap，不得仅凭“存在 baseline”判定设计完整。

### 2. R0 单变量隔离与 reference-cell 闭合

升级现有 R0 规则：

- 候选比较只改变登记的高影响选择；teacher/backbone、数据、预算及其他 outcome-impacting axes 保持 matched，或拆成独立对照。
- selection / kill rule 引用的每个 cell 必须进入 execution-cell inventory，拥有预算、命令、输出和指标，并计入总成本。

### 3. Claim Contract

把现有 estimand、falsifier 与 `on_miss` 规则合并为一个最小合同：

```text
research_question
intervention
matched_reference
primary_metric
literal_falsifier
claim_collapse
```

每个 `CLAIM_BEARING` 实验回答一个主要问题。结果不满足 falsifier 时，必须明确缩小或撤回哪条 claim；不得用追加解释把所有结果转成支持证据。

### 4. Failure taxonomy 共用

Case Study 与对应 quantitative analysis 引用同一份预注册 taxonomy：

- 结果前冻结类别与抽样规则；
- 同时覆盖 recovered、unrecovered 与 side-effect cases；
- case panel 是定量 error/recovery finding 的实例，不是独立挑选的故事。

只有 Contribution 涉及 failure/recovery 行为时才要求该 taxonomy，不能把它强制到不适用的 Idea。

## 第三阶段：最小校验

只在现有 artifact 已有足够结构化信息时增加以下跨字段检查：

1. `causal_reference` 与 `contextual_baseline` 两个角色是否闭合。
2. R0 selection / kill rule 引用的 cell 是否全部注册并进入成本清单。
3. Case Study 与对应 quantitative analysis 的 taxonomy 引用是否一致。

teacher capacity 是否真正 matched、estimand 是否科学有效等语义判断继续由设计者和 Auditor 判断；不要建立复杂评分系统或防御性脚手架。

## 验证计划

1. 记录修改前后 `SKILL.md` 和 references 的 line / word / byte 数。
2. 运行 Skill 结构校验：

   ```bash
   python3 "${CODEX_HOME}/skills/.system/skill-creator/scripts/quick_validate.py" skills/autodesign-experiment-design
   ```

3. 若修改 checker，运行直接相关的 pytest；不得用全量无关测试代替目标验证。
4. 对现有 EXP38 产物做回归阅读：
   - Sol Case 4 应暴露缺少独立 contextual baseline，以及 kill rule 引用的 reference cells 未完整注册/计费。
   - Luna Case 3 应暴露 controlled/natural constructor 与 teacher capacity 同时变化。
   - 两个 Case 不应因为表格和 expected effects 数量充足而被误判为 scientific-ready。
5. 确认没有新增固定实验数量、EXP38 benchmark 名称、teacher 尺寸或 reflection 专属规则。

## 同步与交付

1. 先修改仓库源文件，保留当前工作树中已有变更，不覆盖或回滚无关内容。
2. 使用现有安装脚本同步到 Codex Skills：

   ```bash
   bash scripts/install_autodesign_skills.sh "${CODEX_HOME}/skills"
   ```

3. 对仓库版本与 `${CODEX_HOME}/skills/autodesign-experiment-design/` 做内容比对，并在安装目录再次运行 `quick_validate.py`。
4. 最终报告修改文件、压缩前后体量、嵌入的四项规则、测试结果和仍需真实盲测验证的边界。
5. 不推送远端；除非用户另行要求，不提交包含其他未提交修改的 Git commit。
