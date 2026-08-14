# AutoDesign

AutoDesign 是一个 **Skill-first 研究工作流**。任何支持 Agent Skills 的智能体都可以通过七个 Skill 完成方法路线、证据设计、实验实现、执行、结果解释与独立审计；仓库中的 Python 薄运行包只负责状态推进、本地命令执行和结果 cell 完整性校验。GPU 与远端机器信息由智能体自己的 `AGENTS.md` 或 `CLAUDE.md` 提供，Python 包不读取 GPU 配置。

## 发布内容

```text
.
├── autodesign/                    状态、结果、本地执行薄运行包
├── skills/                        七个 Prompt-first Skills
├── scripts/
│   └── install_autodesign_skills.sh
├── pyproject.toml
├── README.md
└── LICENSE
```

`assets/` 是运行时本地目录，不进入 Git。输入、日志、生成项目和实验结果可分别放在 `assets/input/`、`assets/logs/` 和 `assets/output/`；也可以把运行目录放在任意可写的绝对路径。

## 七个 Skill

| Skill | 职责 | 主要输出 |
| --- | --- | --- |
| `$run-autodesign` | 编排、恢复和失效传播 | `AUTODESIGN_STATE.md` |
| `$autodesign-method-router` | 比较并选择可证伪方法路线 | `method_route.md` |
| `$autodesign-evidence-designer` | claim 到 main、ablation、case、interesting evidence 的映射 | `evidence_plan.md` |
| `$autodesign-implementer` | 生成可运行项目、环境和机器合同 | `generated_project/`、计划 JSON |
| `$autodesign-executor` | 本地或远端五阶段执行 | `execution_record.json` |
| `$autodesign-result-scientist` | 结果完整性与科学诊断 | `result_summary.json`、`result_diagnosis.md` |
| `$autodesign-integrity-auditor` | 独立 claim-evidence-execution 审计 | `integrity_audit.md` |

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

1. 把仓库中的七个 Skill 安装到当前智能体的用户级 Skills 目录；
2. 使用 `python3 -m pip install /absolute/path/to/exp31_autoresearch` 非 editable 安装 Python 包；
3. 在当前智能体实际读取的 `AGENTS.md`、`CLAUDE.md` 或等价指令文件中填写自己的 GPU、SSH、目录、环境和资源约束。

前两项完成后可以删除下载的源码目录；第三项属于用户/智能体配置，不放进 Python 文件，也不需要 Python GPU 控制器。

## 自然语言入口

在任一已安装 Skill 的智能体对话中直接说明输入和运行目录，例如：

```text
使用 $run-autodesign。固定输入为：motivation=<研究动机>；contributions=<贡献列表>；benchmark=<数据集与指标>。运行目录使用 /absolute/path/to/my_run。依次完成方法路线、证据设计、项目实现、五阶段执行、结果诊断和完整性审计。
```

一个 canonical run 在指定运行目录中生成：

```text
<run_dir>/
├── AUTODESIGN_STATE.md
├── input_brief.md
├── method_route.md
├── r0_plan.md
├── r0_record.json
├── evidence_plan.md
├── implementation_notes.md
├── generated_project/
├── command_plan.json
├── experiment_schedule.json
├── result_contract.json
├── execution_record.json
├── result_summary.json
├── result_diagnosis.md
├── integrity_audit.md
└── reports/
```

R0 文件只在路线需要低成本门时出现。Markdown 保存研究推理；JSON 只保存机器必须精确读取的事实。

## 代码依赖边界

不依赖项目 Python 的研究步骤：

- 方法路线选择与 R0 falsifier；
- evidence plan 与项目实现决策；
- 结果解释与完整性审计。

依赖薄运行包的确定性步骤：

- `skillflow.py`：状态初始化、推进和完成验证；
- `skillresults.py`：schedule 与 observed cells 对齐、确定性聚合；
- `runner.py`：本地命令计划执行。

通用单阶段记录器随 executor Skill 安装到所选智能体的 Skills 目录：

```text
<agent_skills_dir>/autodesign-executor/scripts/run_stage.py
```

薄运行包不会替智能体选择方法、模型、baseline、训练范式或论文结论。

## 五阶段执行

```text
preflight → smoke → experiment → aggregate → collect
```

- `preflight`：数据、benchmark、metric 和方法最小语义；
- `smoke`：代表 cell；
- `experiment`：全部计划 cells；
- `aggregate`：统计、表格和图；
- `collect`：权威结果与声明产物。

结果摄取只判断数据是否完整，`automatic_claim_verdict` 固定为 `NOT_ASSIGNED`。

## 本地验证

```bash
python3 -m autodesign --help
python3 -m compileall -q autodesign skills
bash -n scripts/install_autodesign_skills.sh
bash scripts/install_autodesign_skills.sh /absolute/path/to/test-agent/skills
python3 -m pip install .
```

## GPU 与远端执行上下文

把 GPU、SSH、可操作目录和资源约束写入当前智能体实际读取的指令文件：Codex 可写入全局 `~/.codex/AGENTS.md` 或项目根目录 `AGENTS.md`，Claude Code 可写入 `~/.claude/CLAUDE.md` 或项目根目录 `CLAUDE.md`。其他智能体使用它支持的等价指令文件。Python 包不读取 GPU、SSH 或远端目录配置。

可复制以下结构并填写本机信息：

```markdown
## AutoDesign GPU 执行上下文

使用 `$run-autodesign` 或 `$autodesign-executor` 且任务需要 GPU 时，先读取本节；本节是 GPU 与远端目录的来源。

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
