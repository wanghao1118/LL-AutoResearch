# AutoDesign

AutoDesign 是一个 **Skill-first 研究工作流**，接在上游 AutoSearch 之后：读取 AutoSearch 导出的 **Motivation、Contribution 和 Benchmark**，先完成实验设计，再执行实验。任何支持 Agent Skills 的智能体都可以通过五个 Skill 完成实验设计、实验执行、结果解释与独立审计；仓库中的 Python 薄运行包只负责状态推进、设计契约校验、本地命令执行、结果 cell 完整性校验和目标对比。GPU 与远端机器信息由智能体自己的 `AGENTS.md` 或 `CLAUDE.md` 提供，Python 包不读取 GPU 配置。

模块流程是**先设计，后执行**：

```text
INPUT_READY → EXPERIMENT_DESIGN_READY → IMPLEMENTATION_READY → EXECUTION_COMPLETE
            → RESULT_DIAGNOSIS_READY → INTEGRITY_AUDIT_PASS → COMPLETE
```

## 发布内容

```text
.
├── autodesign/                    状态、设计契约、结果、本地执行薄运行包
├── skills/                        五个 Prompt-first Skills
├── tests/                         设计契约与目标对比的回归测试
├── scripts/
│   └── install_autodesign_skills.sh
├── pyproject.toml
├── README.md
└── LICENSE
```

`assets/` 是运行时本地目录，不进入 Git。输入、日志、生成项目和实验结果可分别放在 `assets/input/`、`assets/logs/` 和 `assets/output/`；也可以把运行目录放在任意可写的绝对路径。

## 五个 Skill

| Skill | 职责 | 主要输出 |
| --- | --- | --- |
| `$run-autodesign` | 两阶段编排、恢复、失效传播和 11 道 gate | `AUTODESIGN_STATE.md` |
| `$autodesign-experiment-design` | 归一化 handoff、选择方法路线、设计四类实验、预写模拟目标 | `experiment_design.md`、`expected_effects.json` |
| `$autodesign-experiment-run` | 按设计生成可运行项目并完成五阶段执行 | `generated_project/`、计划 JSON、`execution_record.json`、`effect_comparison.md` |
| `$autodesign-result-scientist` | 结果完整性与科学诊断 | `result_summary.json`、`result_diagnosis.md`、`result_route.md` |
| `$autodesign-integrity-auditor` | 独立 claim-evidence-execution 审计 | `integrity_audit.md` |

设计与执行之间是硬边界：`$autodesign-experiment-design` 只设计、不实现、不执行；`$autodesign-experiment-run` 只按已接受的设计实现和执行，不重新设计科学问题。

## 四类实验与三类证据

实验设计覆盖四类 **family**，与三类 **evidence class** 正交：

| Family | 作用 |
| --- | --- |
| `main` | 建立效果本身 |
| `ablation` | 把效果归因到具体成分，每次只改一个变量 |
| `case_study` | 用预先定义的选择规则和类别计数（含失败类别）示例化机制 |
| `analysis` | 界定效果的适用范围与边界 |

| Evidence class | 含义 |
| --- | --- |
| `CLAIM_BEARING` | 直接支撑或推翻某个 claim |
| `MECHANISM_PILOT` | 验证机制假设，不单独支撑 claim |
| `ENGINEERING_SMOKE` | 只验证工程可运行性 |

Case study 的选择规则和类别计数必须在**任何结果出现之前**写定，否则属于按结果挑样本，审计判 FAIL。

四类实验并非一律强制齐全，但**缺失必须有论证**：某类实验缺席时，设计文档需在 `## Absent families` 小节下写出 `- <family>: <理由>`，说明该类实验的缺席如何从 contribution 推出（例如贡献是失效规律发现，就没有自有模块可供消融）。`skill-check-design` 只验证一件事——该 family 名下**写了理由**；裸写 `- ablation:` 或只在散文里提到类别名都算没写。机器不评判理由的质量：`- ablation: n/a` 能过机器门，但仍是失败的设计，因为「理由是否从 contribution 推得出来」由设计 Skill 在落笔时判断、并由审计员逐条复核原文。这样切分是为了两头都不失守：既不允许缺席而不作声，也不让机器用字数去给科学论证打分。

## 预写效果与执行后对比

设计阶段为每个 expected cell 预写一个模拟目标，写入 `expected_effects.json`，整个文件的 `value_status` 固定为 `SIMULATED_TARGET`：

```json
{
  "entry_id": "E1-ours-tb10-pass1",
  "experiment_id": "E1",
  "family": "main",
  "evidence_class": "CLAIM_BEARING",
  "claim_ids": ["C3"],
  "variant_id": "ours-32b",
  "benchmark_task_id": "terminal-bench-1.0",
  "metric": "pass@1",
  "simulated_target": 29.1,
  "acceptable_range": [26.0, 32.0],
  "target_basis": "handoff_reported",
  "threshold_reference_variant": "qwen2.5-coder-32b-instruct",
  "decision_threshold": ">= reference + 2.0",
  "on_miss": "iteration",
  "observed_value": null,
  "observed_status": "NOT_EXECUTED"
}
```

- `target_basis` 取 `handoff_reported`、`published_baseline` 或 `design_estimate`，说明目标值从哪里来；
- `decision_threshold` 支持绝对阈值（`>= 20.0`）和相对阈值（`>= reference + 2.0`，需同时给出 `threshold_reference_variant`）；
- `on_miss` 取 `iteration`、`tuning` 或 `stop`，预先决定未达标时的路由；
- `case_study` 用 `required_categories` 计数代替单一目标值；`analysis` 可用 `expected_shape`（`monotonic_increasing`、`monotonic_decreasing`、`saturating`、`non_monotonic`、`flat`）表达曲线形状预期。

执行并摄取结果后，`skill-compare-effects` 逐格对比观测值与目标值，把 `observed_value`、`observed_status`、`threshold_outcome` 写回 `expected_effects.json`，并生成 `effect_comparison.md`。阈值结果只有三种：`MET`、`MISSED`、`NOT_EVALUABLE`（相对阈值缺参考变体、case-study 类别需人工计数、形状预期需人工看曲线、该 cell 未执行）。

完整性不变量：模拟目标不得进入 `reports/`，不得被当作观测值，不得在执行后被修改，`MISSED` 行不得被删除，`MET` 本身不等于 claim `SUPPORTED`。

## 安装 Skill

不需要在项目里维护不同智能体的安装路径。直接把下面这段话发给当前智能体：

```text
请安装这个仓库里的 AutoDesign：先把 skills/ 下所有包含 SKILL.md 的目录安装到你自己的用户级 Skills 目录；再执行 python3 -m pip install /absolute/path/to/exp31_autoresearch，以非 editable 方式安装 pyproject.toml 定义的 autodesign Python 包。不要使用 pip install -e。最后切换到该仓库以外的目录，运行 python3 -m autodesign --help 验证。
```

智能体负责选择它自己的 Skills 目录。仓库中的脚本只接收这个目录，不判断智能体种类：

```bash
bash scripts/install_autodesign_skills.sh /absolute/path/to/current-agent/skills
python3 -m pip install .
```

也可以通过 `AGENT_SKILLS_DIR` 传入目标目录。第一步复制 Prompt、references 和 Skill 自带脚本；第二步把 `autodesign` 命令及 Python 模块复制到当前 Python 环境。完成这两步后，运行 AutoDesign 不再依赖本仓库路径。

下载仓库后只需要三类依赖：

1. 把仓库中的五个 Skill 安装到当前智能体的用户级 Skills 目录；
2. 使用 `python3 -m pip install /absolute/path/to/exp31_autoresearch` 非 editable 安装 Python 包；
3. 在当前智能体实际读取的 `AGENTS.md`、`CLAUDE.md` 或等价指令文件中填写自己的 GPU、SSH、目录、环境和资源约束。

前两项完成后可以删除下载的源码目录；第三项属于用户/智能体配置，不放进 Python 文件，也不需要 Python GPU 控制器。

## 自然语言入口

输入契约**不是**固定的结构化 Schema。Skill 的真实入口就是自然语言：在任一已安装 Skill 的智能体对话中说明三项必需输入和运行目录即可。

```text
使用 $run-autodesign。运行目录 /absolute/path/to/my_run。
motivation: 现有 terminal agent 在长程任务上失败后无法自我恢复。
contribution: 提出 oracle-guided 轨迹重标注，让 32B 模型在失败后重规划。
benchmark: terminal-bench 1.0，指标 pass@1。
另外我倾向用 qwen2.5-coder-32b-instruct 作 baseline，只有 2 张 A100，先跑一个低成本 R0。
```

两条输入通道等价有效，都不是降级路径：

- **通道 A**：规范化的 `autosearch_handoff.json`（只有 `motivation`、`contribution`、`benchmark` 必需，`benchmark.primary` 必需）；
- **通道 B**：`/run-autodesign` 后面直接跟自然语言。AutoSearch 由他人独立开发，导出格式可能漂移或以散文形式到达。

用户还可能提供三项之外的更多信息——初步实验计划、倾向的 baseline、相关工作、算力限制、部分设计。这些内容全部原样吸收进 `input_brief.md` 的 `## Additional user-supplied input (literal)`。**不因为 schema 没有对应字段就丢弃用户提供的信息；三项必需输入已在散文中出现时，不要求用户改写成 JSON。**

一个 canonical run 在指定运行目录中生成：

```text
<run_dir>/
├── AUTODESIGN_STATE.md
├── input_brief.md
├── experiment_design.md
├── expected_effects.json
├── r0_plan.md
├── r0_record.json
├── implementation_notes.md
├── generated_project/
├── command_plan.json
├── experiment_schedule.json
├── result_contract.json
├── execution_record.json
├── result_summary.json
├── effect_comparison.md
├── result_diagnosis.md
├── result_route.md
├── integrity_audit.md
└── reports/
```

R0 文件只在路线需要低成本门时出现。Markdown 保存研究推理；JSON 只保存机器必须精确读取的事实。

## 代码依赖边界

不依赖项目 Python 的研究步骤：

- 方法路线选择与 R0 falsifier；
- 四类实验设计、模拟目标取值与项目实现决策；
- 结果解释与完整性审计。

依赖薄运行包的确定性步骤：

- `skillflow.py`：状态初始化、推进和完成验证；
- `effects.py`：设计契约校验（`skill-check-design`）与观测-目标逐格对比（`skill-compare-effects`）；
- `skillresults.py`：schedule 与 observed cells 对齐、确定性聚合；
- `runner.py`：本地命令计划执行。

通用单阶段记录器随 run Skill 安装到所选智能体的 Skills 目录：

```text
<agent_skills_dir>/autodesign-experiment-run/scripts/run_stage.py
```

薄运行包不会替智能体选择方法、模型、baseline、训练范式、目标值或论文结论。`skill-check-design` 只校验设计在结构上可用（schema、目标基准、字面阈值、未达标路由、scheduled cell 是否都有对应 entry），不判断某个目标值在科学上是否合理——那是设计 Skill 的职责。

## 命令一览

```bash
python3 -m autodesign skill-init <handoff> --output <run_dir>   # 归一化输入，生成 input_brief.md
python3 -m autodesign skill-check-design <run_dir>             # 设计契约 gate
python3 -m autodesign run-local <run_dir> [--stage <stage>]    # 五阶段本地执行
python3 -m autodesign skill-ingest <run_dir> <results.json>    # 结果 cell 完整性与聚合
python3 -m autodesign skill-compare-effects <run_dir>          # 观测 vs 模拟目标
python3 -m autodesign skill-status <run_dir>                   # 当前阶段与下一个 Skill
python3 -m autodesign skill-verify <run_dir>                   # 校验当前产物
python3 -m autodesign skill-repair-state <run_dir>             # 规范化 AUTODESIGN_STATE.md
python3 -m autodesign skill-advance <run_dir> <stage> --changed-input <x> --literal-result <y>
```

## 五阶段执行

```text
preflight → smoke → experiment → aggregate → collect
```

- `preflight`：数据、benchmark、metric 和方法最小语义；
- `smoke`：代表 cell；
- `experiment`：全部计划 cells；
- `aggregate`：统计、表格和图；
- `collect`：权威结果与声明产物。

`run-local` 会保留已成功且命令计划未变的阶段前缀并从第一个需要重跑的阶段继续；命令计划变更会使对应前缀失效。结果摄取只判断数据是否完整，`automatic_claim_verdict` 固定为 `NOT_ASSIGNED`。

## 本地验证

```bash
python3 -m autodesign --help
python3 -m compileall -q autodesign skills
python3 -m pytest tests/ -q
bash -n scripts/install_autodesign_skills.sh
bash scripts/install_autodesign_skills.sh /absolute/path/to/test-agent/skills
python3 -m pip install .
```

## GPU 与远端执行上下文

把 GPU、SSH、可操作目录和资源约束写入当前智能体实际读取的指令文件：Codex 可写入全局 `~/.codex/AGENTS.md` 或项目根目录 `AGENTS.md`，Claude Code 可写入 `~/.claude/CLAUDE.md` 或项目根目录 `CLAUDE.md`。其他智能体使用它支持的等价指令文件。Python 包不读取 GPU、SSH 或远端目录配置。

可复制以下结构并填写本机信息：

```markdown
## AutoDesign GPU 执行上下文

使用 `$run-autodesign` 或 `$autodesign-experiment-run` 且任务需要 GPU 时，先读取本节；本节是 GPU 与远端目录的来源。

- SSH：`<user>@<host>:<port>`；认证方式：`<identity-or-default>`
- 允许根目录：`<remote-allowed-root>`
- 同步目录：`<remote-sync-dir>`
- 实验工作目录：`<remote-work-dir>`
- 可见 GPU：`<gpu-indexes>`；`CUDA_VISIBLE_DEVICES` 使用相同列表
- GPU 数量：`<count>`；最大并行任务数：`<max-parallel-jobs>`
- Conda：`<conda-executable>`；环境名：`<environment-name>`
- 单条命令超时：`<seconds>`
- 保留服务器现有进程；日志、checkpoint 和结果均写入允许根目录
```

Skill 读取指令文件中的机器上下文，再读取当前 run 的 `generated_project/environment.yml`、`command_plan.json` 和 `result_contract.json`。机器信息决定在哪里运行；这些 run 产物决定运行什么以及收集什么。智能体直接使用自己的 shell、SSH 和文件传输工具完成远端五阶段流程；仓库不提供 Python GPU 配置或远端控制器。
