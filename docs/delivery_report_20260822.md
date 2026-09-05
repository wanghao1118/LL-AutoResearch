# exp31_autoresearch（AutoDesign）交付文档

> 初次交付：2026-08-22　|　发布整理：2026-09-05　|　当前分支：`autodesign`　|　版本：autodesign v0.4.0

---

## 1. 交付概要（TL;DR）

**AutoDesign 是一个 Skill-first 的研究工作流系统**，定位为上游 AutoSearch（研究缺口发现）与 AutoWriting（论文写作）之间的中间层：读取 AutoSearch 导出的 Motivation / Contribution / Benchmark 三项输入，先完成论文级**实验设计**，通过 R0 低成本门控后推进**实现、执行、结果诊断和独立完整性审计**。

核心架构决策是「**科学判断归 Agent Skills，确定性检查归 Python 薄运行包**」：

- 五个 Prompt-first Skills 承担全部科学推理（路线选择、实验设计、结果解释、审计）；
- Python 包（`autodesign`，零第三方依赖）只负责状态推进、设计契约校验、本地命令执行、结果 cell 完整性校验和目标对比；
- GPU / SSH 等机器资源不进 Python 包，由使用者写在智能体自己的 `AGENTS.md` / `CLAUDE.md` 中。

**当前可交付状态**：63 个回归测试全部通过（0.06s）；Skill 契约已完成压缩重构；存在一批未提交的工作树变更（结构校验与科学 readiness 分离，详见 §7），建议验收后提交。

---

## 2. 项目定位与设计理念

### 2.1 在整体流水线中的位置

```text
AutoSearch（上游，他人开发）          AutoDesign（本仓）                AutoWriting（下游）
Motivation/Contribution/Benchmark → 设计 → [写作交接] → 执行 → 诊断 → 审计 → 条件式草稿/结果回填
```

### 2.2 状态机

```text
INPUT_READY ─┬→ EXPERIMENT_DESIGN_READY → IMPLEMENTATION_READY → EXECUTION_COMPLETE
             └→ WAITING_FOR_R0 → R0_PASSED → EXPERIMENT_DESIGN_READY
                                  └──→ AutoWriting（条件式草稿）
            → RESULT_DIAGNOSIS_READY → INTEGRITY_AUDIT_PASS → COMPLETE
```

关键原则：

1. **设计与执行硬边界**：Design Skill 只设计、不实现不执行；Run Skill 只按已接受的设计实现执行，不重新设计科学问题。
2. **先设计，发布写作交接，再执行**：AutoWriting 不属于 AutoDesign 状态机，不阻塞实验，可在实验运行期间并行写稳定章节。
3. **模拟目标与观测结果严格隔离**：预写的 simulated target 只用于决策阈值对比，不得进入 `reports/`、不得冒充观测值、执行后不得修改。
4. **机器不评判科学质量**：机器 gate 只查结构与契约；理由是否成立由设计 Skill 落笔时判断、由审计员逐条复核。

### 2.3 为什么 Skill-first（有盲测数据支撑）

2026-08-14 的 STeP 盲测路由对比（`assets/output/step_blind_route_comparison.md`）：同一冻结输入，Route A（只用两个 planning Skills + 契约）vs Route B（legacy GPT request + JSON schema）：

| 指标 | Route A (Skill-first) | Route B (Legacy schema) |
| --- | --- | --- |
| 最终设计状态 | PASS | 修复两轮后仍 FAIL |
| Codex 轮次 / tokens | 1 轮 / 54,039 | 3 轮 / 154,035（2.85×）|
| 授权输入体积 | 19,572 B | 93,777 B |
| 科学路线 / 实验 cards | 3 / 9 | 2 / 4（对象过载）|
| 校验错误轮次轨迹 | 0 | 21 → 8 → 12 |

结论：Route B 的失败是 schema/validator 耦合失败而非科学推理缺失——因此确定加码方向是 Skill 化，而不是给研究决策写更多代码。

---

## 3. 发布内容清单

```text
exp31_autoresearch/
├── autodesign/                     # Python 薄运行包（v0.4.0，零依赖）
│   ├── __init__.py / __main__.py   #   入口
│   ├── cli.py                      #   七个子命令的 argparse 装配
│   ├── skillflow.py    (16.8 KB)   #   状态初始化/推进/完成验证
│   ├── effects.py      (24.9 KB)   #   设计契约校验 skill-check-design + 观测-目标对比 skill-compare-effects
│   ├── skillresults.py ( 6.9 KB)   #   schedule 与 observed cells 对齐、确定性聚合
│   ├── runner.py       (12.1 KB)   #   本地命令计划执行（五阶段，支持前缀续跑）
│   └── io.py                       #   IO 小工具
├── skills/                         # 五个 Prompt-first Skills（含 agents/openai.yaml、references、脚本）
│   ├── run-autodesign/             #   两阶段编排（SKILL.md 127 行 + autodesign-flow.md 123 行）
│   ├── autodesign-experiment-design/  # 实验设计（91 行 + design-contract.md 142 行 + handoff 契约 82 行）
│   ├── autodesign-experiment-run/  #   五阶段执行（95 行 + run-contract.md 91 行 + run_stage.py 182 行）
│   ├── autodesign-result-scientist/#   结果诊断（49 行 + diagnosis-contract.md 79 行 + tuning prompt 184 行）
│   └── autodesign-integrity-auditor/#  独立审计（40 行 + audit-contract.md 26 行）
├── tests/                          # test_effects.py (25.6 KB) + test_skillflow.py (4.5 KB)，63 个用例
├── scripts/install_autodesign_skills.sh  # Skill 安装脚本（智能体无关，只接收目标目录）
├── docs/                           # 设计 Skill 精简方案（compaction plan）+ 本交付文档
├── assets/{input,logs,output}/     # 运行时本地目录（135+ 日志、40+ 输出产物），不入 Git
├── pyproject.toml                  # requires-python >= 3.9，dependencies = []，dev = pytest/ruff
├── README.md                       # 主文档（约 16 KB，随最新契约同步更新）
└── LICENSE                         # MIT
```

历史遗留目录：`.venv`、`.pytest_cache`、`.ruff_cache`、`build/`、`autodesign.egg-info/`、`draft_3000fa52_folder/`（一份演示用的 presentation 决策 JSON + mermaid 流程图草稿）。这些不属于发布核心。

---

## 4. 五个 Skill 职责表

| Skill | 职责 | 主要输出 |
| --- | --- | --- |
| `$run-autodesign` | 两阶段编排、断点恢复、AutoWriting 交接、失效传播、11 道 gate | `AUTODESIGN_STATE.md` |
| `$autodesign-experiment-design` | 归一化 handoff、方法路线选择、四类实验设计与论文表格、预写决策效果、发布写作交接 | `experiment_design.md`、`expected_effects.json` |
| `$autodesign-experiment-run` | 按设计生成可运行项目并完成五阶段执行 | `generated_project/`、计划 JSON、`execution_record.json`、`effect_comparison.md` |
| `$autodesign-result-scientist` | 结果完整性与科学诊断 | `result_summary.json`、`result_diagnosis.md`、`result_route.md` |
| `$autodesign-integrity-auditor` | 独立 claim-evidence-execution 三角审计 | `integrity_audit.md` |

一次 canonical run 在运行目录产出 16 类文件（`AUTODESIGN_STATE.md`、`input_brief.md`、`experiment_design.md`、`expected_effects.json`、可选 `r0_plan.md`/`r0_record.json`、`generated_project/`、`command_plan.json`、`experiment_schedule.json`、`result_contract.json`、`execution_record.json`、`result_summary.json`、`effect_comparison.md`、`result_diagnosis.md`、`result_route.md`、`integrity_audit.md`、`reports/`）。Markdown 存研究推理，JSON 只存机器必须精确读取的事实。

---

## 5. 核心机制与不变量

### 5.1 四类实验 family × 三类证据 class（正交）

| Family | 作用 | 缺席规则 |
| --- | --- | --- |
| `main` | 建立效果本身 | 必须论证缺席如何从 contribution 推出，写入 `## Absent families` |
| `ablation` | 单变量归因到具体成分 | 同上 |
| `case_study` | 预定义选择规则 + 类别计数（含失败类别）示例化机制 | 同上 |
| `analysis` | 界定适用范围与边界 | 同上 |

| Evidence class | 含义 |
| --- | --- |
| `CLAIM_BEARING` | 直接支撑或推翻某条 claim |
| `MECHANISM_PILOT` | 验证机制假设，不单独支撑 claim |
| `ENGINEERING_SMOKE` | 只验证工程可运行性 |

机器 gate（`skill-check-design`）只验证「缺席的 family 名下写了理由」这一件事；裸写 `- ablation:` 或只在散文里提类名算没写。理由质量不由机器打分，由审计员复核原文——既不允许缺席而不作声，也不让机器用字数给科学论证打分。

### 5.2 Decision effect 与目标体系（四类对象分离）

逐 seed execution cell、跨 seed aggregate result、paper result cell、decision effect 四类对象严格分离。只为 decision effect 写模拟目标进只读 `expected_effects.json`（`value_status` 固定 `SIMULATED_TARGET`）；baseline 展示格不生成伪目标。每条 entry 支持：

- `target_basis`: `handoff_reported` / `published_baseline` / `design_estimate`
- `decision_threshold`: 绝对（`>= 20.0`）或相对（`>= reference + 2.0`，需 `threshold_reference_variant`）
- `on_miss`: `iteration` / `tuning` / `stop`（未达标路由预先决定）
- case_study 用 `required_categories` 计数；analysis 用 `expected_shape`（五种曲线形状）

对比结果只有三值：`MET` / `MISSED` / `NOT_EVALUABLE`。不变量：MISSED 行不得删除；MET 不等于 claim `SUPPORTED`；`automatic_claim_verdict` 固定 `NOT_ASSIGNED`（claim 判定永远归人/审计员）。

### 5.3 AutoWriting 提前交接

设计文档末尾 `## AutoWriting handoff`，两种合法配对：`Verdict: PASS` ↔ `handoff_status: ACCEPTED`（可并行写作）；`Verdict: PROVISIONAL_WAITING_FOR_R0` ↔ 同名 status（只写稳定章节，路线相关内容条件式，状态机进入 `WAITING_FOR_R0`）。结果格用 `{{RESULT:<eid>::<vid>::<bid>::<metric>}}` 占位、派生列用 `{{EFFECT:<entry_id>}}`，真实值分别从 `result_summary.json` 和 `effect_comparison.md` 回填。模拟数字只能出现在显眼标记 `DRAFT — SIMULATED TARGETS, NO OBSERVED RESULTS` 的草稿里。

### 5.4 五阶段执行与续跑

`preflight → smoke → experiment → aggregate → collect`。`run-local` 保留已成功且命令计划未变的阶段前缀，从第一个需要重跑的阶段继续；命令计划变更使对应前缀失效。

### 5.5 输入通道

双通道等价有效：通道 A 规范化 `autosearch_handoff.json`（仅 motivation/contribution/benchmark 必需）；通道 B 自然语言直说。用户额外提供的 baseline 倾向、算力限制等全部原样吸收进 `input_brief.md` 的 literal 小节，不因 schema 无字段而丢弃。

---

## 6. CLI 命令一览（七个）

```bash
python3 -m autodesign skill-init <handoff> --output <run_dir>     # 归一化输入，生成 input_brief.md
python3 -m autodesign skill-check-design <run_dir>               # 结构性设计契约 gate
python3 -m autodesign run-local <run_dir> [--stage <stage>]      # 五阶段本地执行
python3 -m autodesign skill-ingest <run_dir> <results.json>      # 结果 cell 完整性与聚合
python3 -m autodesign skill-compare-effects <run_dir>            # 观测 vs 模拟目标
python3 -m autodesign skill-repair-state <run_dir>               # 规范化 AUTODESIGN_STATE.md
python3 -m autodesign skill-advance <run_dir> <stage> --changed-input x --literal-result y
```

---

## 7. 版本与 Git 状态

- **发布分支**：`autodesign`，由原 `fix/AutoDesign` 改名；`main` 保持为默认分支。
- **远端**：GitHub `origin`；发布后以远端 `autodesign` 分支 SHA 为交付依据。
- **本轮核心变更**：完成「结构校验与科学 readiness 分离」、可选 Benchmark 输入、R0 状态闭环和人工方法修订决策——
  - `effects.py`：coverage verdict 从布尔改为读 `PASS | PROVISIONAL_WAITING_FOR_R0` 双合法值；输出新增 `validation_scope: STRUCTURAL` 与 `declared_design_readiness` 字段；
  - `skillflow.py`：新增 `WAITING_FOR_R0` / `R0_PASSED` 状态推进；
  - `cli.py` / 两个 SKILL.md / references / README：同步措辞；
  - `tests/test_effects.py` 与新增的 `tests/test_skillflow.py` 覆盖 verdict、R0 和人工修订状态分支。
- **APP 前端**：`apps/thainker-autodesign/` 作为普通源码目录纳入同一分支；其原 Sites Git 元数据在仓库外保留备份，依赖、构建目录和运行输出不入库。

### 实验推进历程（按 Round，从提交历史重建）

| Round | 日期 | 主题 | 关键提交 / 动作 | 结论与洞察 |
| --- | --- | --- | --- | --- |
| R1 | 08-07 ~ 08-08 | AutoResearch 起点：缺口发现 | MOC 式 gap discovery、证据链 v2、全文阅读、证据分层评分、中文 dashboard、ECS demo 部署 | 上游能力成型；但纯 LLM 抽卡式 gap 发现不足以保证实验质量 |
| R2 | 08-10 | AutoBench 模块 | `feat: add AutoBench module`、paper seed library + 全文 provider | 开始向 benchmark/实验侧延伸 |
| R3 | 08-14 | **Skill-first 迁移（转折点）** | `migrate AutoDesign to skill-first pipeline`、执行/状态流加固、handoff 补漏、最小发布、移除 Python GPU controller | STeP 盲测证明 Skill 路线 token 省 2.85× 且一次通过；GPU 配置归智能体指令文件，Python 包零依赖 |
| R4 | 08-15 | 对齐 fresh-Idea 研究 | `Align AutoDesign with fresh-Idea research` | 输入不再绑定 AutoSearch 固定导出格式 |
| R5 | 08-17 | 自主性收口 | 高影响自主选择必须走用户决策或双候选 R0 | 防「智能体擅自定路线」 |
| R6 | 08-19 | **design-then-run 重构** | 设计/执行硬边界拆分、absent-family 必须书面论证（随后撤销机器打分）、design-first AutoWriting handoff、CLI 收敛到七命令 | 「先设计再执行」成为骨架；机器只查形式、人审实质 |
| R7 | 08-20 | 契约精简 | result contracts refine；design Skill 契约 compaction（SKILL.md 约 2,274 词 → 目标 1,200–1,500 词，现 91 行） | 吸收 EXP38 Sol Case 4（缺 contextual baseline、kill-rule cell 未注册计费）与 Luna Case 3（constructor–teacher capacity 混杂）两类真实设计缺口，以「替换规则」而非「追加章节」方式嵌入 baseline 双角色闭合、R0 单变量隔离、Claim Contract、failure taxonomy 共用四项改进 |
| R8 | 08-21 ~ 至今 | presentation contract 收紧 + 结构/readiness 分离 | `tighten experiment design presentation contract`（HEAD）；工作树中未提交的结构校验与 `PROVISIONAL_WAITING_FOR_R0` 分离 | 顶层 `status: PASS` 只代表结构可用，科学 readiness 由设计的 coverage verdict 另行声明 |

### 验证产物资产（assets/output，40+ 项）

- 盲测对比：`step_blind_route_comparison.*`、`user_blind_route_comparison.*`（Route A/B，含 Luna 复核版 `*_luna_max`）
- 门控演示：`r0_gate_demo*`、`autodesign_method_route_transaction`、`direction_guard_transaction`
- Idea 类型泛化验证：`idea_type_rl_agent_environment_*`、`idea_type_sft_dpo_*` 全链路日志（init→implementation→execution→ingest→diagnosis→evidence）
- 交付与回滚演练：`delivery/`、`skill_first_refactor_delivery/`（各含 patch、baseline/modified 测试日志、rollback 脚本与验证记录）
- 远端 GPU 链路：`remote_gpu/`、`exp34_remote_gpu*`、`step_worker_real_e2e_v2_remote_gpu`

---

## 8. 安装与快速上手

### 8.1 安装（智能体无关，两步）

```bash
# 1) 把五个 Skill 装进任意智能体的用户级 Skills 目录
bash scripts/install_autodesign_skills.sh /absolute/path/to/current-agent/skills
#    （或通过 AGENT_SKILLS_DIR 环境变量传入）

# 2) 非 editable 安装 Python 包
python3 -m pip install /absolute/path/to/exp31_autoresearch
```

完成后即可删除下载的源码目录；运行时不再依赖本仓库路径。第三步是把 GPU/SSH/目录/环境约束写进当前智能体实际读取的 `AGENTS.md` 或 `CLAUDE.md`（README 提供「AutoDesign GPU 执行上下文」模板，含 SSH、允许根目录、可见 GPU、conda 环境、超时等字段）。

### 8.2 发起一次 run（自然语言即入口）

```text
使用 $run-autodesign。运行目录 /absolute/path/to/my_run。
motivation: 现有 terminal agent 在长程任务上失败后无法自我恢复。
contribution: 提出 oracle-guided 轨迹重标注，让 32B 模型在失败后重规划。
benchmark: terminal-bench 1.0，指标 pass@1。
另外我倾向用 qwen2.5-coder-32b-instruct 作 baseline，只有 2 张 A100，先跑一个低成本 R0。
```

### 8.3 本地验证命令（交付自检清单，均已在本机通过）

```bash
python3 -m autodesign --help                 # OK
python3 -m compileall -q autodesign skills   # OK
python3 -m pytest tests/ -q                  # OK：71 passed（2026-09-05 复测）
bash -n scripts/install_autodesign_skills.sh # OK
python3 -m pip install .                     # OK（v0.4.0）

cd apps/thainker-autodesign
npm test                                     # OK：22 passed（2026-09-05 复测）
npm run lint                                 # OK
npm run build                                # OK
```

---

## 9. 已知边界与风险

1. **机器 gate 的能力上限是设计使然**：`- ablation: n/a` 能过机器门但仍是坏设计——防线在设计 Skill 落笔判断 + 审计员逐条复核，依赖使用者真的跑 `$autodesign-integrity-auditor`，不能省略。
2. **远端 GPU 执行无 Python 控制**：五阶段的远端执行靠智能体自己的 shell/SSH 工具完成；这意味着执行可靠性部分取决于宿主智能体的能力，跨智能体行为可能有差异。
3. **上游格式漂移**：AutoSearch 由他人独立开发，导出可能漂移或以散文到达——通道 B 已兜底，但 handoff 解析质量依赖 Design Skill 的归一化步骤。
4. **框架 ≠ 结果**：本仓库交付的是工作流框架；具体 idea 跑出的真实科学结论必须到相应 run 目录核对，不能从框架能力推断（`docs/summary.md` 中已明确此边界）。

## 10. 后续计划（来自 docs/compaction plan 与工作树现状）

1. 对压缩后的 Design Skill 做 EXP38 回归盲读（Sol Case 4 / Luna Case 3 应被新规则识别，且不因表格数量充足而误判 ready）；
2. 用真实盲测验证新嵌入的四项规则（baseline 双角色闭合、R0 reference-cell 注册计费、claim contract、共享 failure taxonomy）的边界；
3. 后续如需进入默认分支，再通过独立审阅将 `autodesign` 合并回 `main`。
