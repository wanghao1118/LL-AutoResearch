# AutoDesign

AutoDesign 是一个 **Skill-first 研究工作流**。Codex 通过七个 Skill 完成方法路线、证据设计、实验实现、执行、结果解释与独立审计；仓库中的 Python 薄运行包只负责状态推进、命令执行、结果 cell 完整性校验和可选的远端 GPU 运行。

## 发布内容

```text
.
├── autodesign/                    状态、结果、本地/远端执行薄运行包
├── skills/                        七个 Prompt-first Skills
├── configs/
│   ├── remote_gpu.example.json    远端 GPU 配置模板
│   └── remote_agent_policy.template.md
├── environments/
│   └── autodesign-gpu.yml         远端控制环境
├── scripts/
│   └── install_autodesign_skills.sh
├── pyproject.toml
├── README.md
└── LICENSE
```

`assets/` 是运行时本地目录，不进入 Git。输入、日志、生成项目和实验结果可分别放在 `assets/input/`、`assets/logs/` 和 `assets/output/`；也可以把运行目录放在任意可写的绝对路径。用户自己的 `configs/remote_gpu.local.json` 和 `configs/remote_agent_policy.local.md` 同样不会进入 Git。

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

在仓库内或其他目录中都可以执行：

```bash
bash /absolute/path/to/exp31_autoresearch/scripts/install_autodesign_skills.sh
```

脚本会从自身位置解析仓库根目录，逐个校验并安装七个 Skill 到 `${CODEX_HOME:-$HOME/.codex}/skills/`。再次执行会用仓库版本覆盖已安装的同名 Skill。

## 自然语言入口

在 Codex 对话中直接说明输入和运行目录，例如：

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
- `runner.py`：本地命令计划执行；
- `remote_gpu.py`：可选远端 GPU 部署、五阶段执行和结果收集。

通用单阶段记录器随 executor Skill 安装到：

```text
${CODEX_HOME:-$HOME/.codex}/skills/autodesign-executor/scripts/run_stage.py
```

薄运行包不会替 Codex 选择方法、模型、baseline、训练范式或论文结论。

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
bash scripts/install_autodesign_skills.sh
```

## 远端 GPU 配置

先从模板创建只属于本机的配置：

```bash
cp configs/remote_gpu.example.json configs/remote_gpu.local.json
cp configs/remote_agent_policy.template.md configs/remote_agent_policy.local.md
```

在 `remote_gpu.local.json` 中填写 SSH、远端根目录、Conda、`git.branch`、运行命令和结果路径；`git.branch` 必须是远端机器将要拉取的已推送分支。GPU 由以下字段绑定：

- `gpu.visible_devices`：允许本次运行看到的 GPU 编号；
- `gpu.required_count`：本次运行要求的 GPU 数量；
- `limits.max_parallel_jobs`：并行任务上限。

远端执行器会依据 `gpu.visible_devices` 导出 `CUDA_VISIBLE_DEVICES` 和 `NVIDIA_VISIBLE_DEVICES`。配置完成后先验证并查看完整 dry-run：

```bash
python3 -m autodesign remote-validate configs/remote_gpu.local.json
python3 -m autodesign remote-all configs/remote_gpu.local.json --dry-run
```

远端执行读取 `generated_project/environment.yml`、`command_plan.json` 和 `result_contract.json`。它只运行已经接受的项目，不重新解释研究方案。
