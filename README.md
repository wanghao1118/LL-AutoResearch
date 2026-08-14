# AutoDesign

AutoDesign 是一个 **Skill-first 研究工作流**。Codex 通过七个 Skill 完成方法路线、证据设计、实验实现、执行、结果解释与独立审计；仓库中的 Python 只负责状态、命令、结果 cell 完整性和可选远端 GPU 运行。

## 保留内容

```text
.
├── autodesign/                    薄运行包
│   ├── cli.py                     CLI 路由
│   ├── io.py                      JSON 与文本读写
│   ├── runner.py                  本地五阶段命令执行
│   ├── skillflow.py               状态初始化、推进与验证
│   ├── skillresults.py            结果 cell 校验与聚合
│   └── remote_gpu.py              可选 SSH/GPU 执行器
├── skills/                        七个 Prompt-first Skills
├── scripts/
│   ├── install_autodesign_skills.sh
│   ├── uninstall_autodesign_skills.sh
│   └── run_skill_first_demo.sh
├── tests/                         四组核心回归测试
├── assets/input/demo_input.json   最小自然语言输入 fixture
├── configs/                       远端配置示例与本地配置
├── environments/                  远端控制环境
└── docs/                          当前对接记录与可视化
```

旧 AutoSearch/AutoBench 应用、旧 JSON 研究 pipeline、旧结果 tuning Prompt、一次性盲测/迁移脚本和三类验证 fixture 均不属于当前生产路径，已经从本分支删除。历史运行结果和日志位于 gitignored 的 `assets/output/` 与 `assets/logs/`，不会进入分支。

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

安装：

```bash
bash scripts/install_autodesign_skills.sh
```

卸载：

```bash
bash scripts/uninstall_autodesign_skills.sh
```

## 自然语言入口

```text
使用 $run-autodesign 处理 assets/input/demo_input.json，运行目录使用 assets/output/my_run；完成方法路线、证据设计、项目实现、五阶段执行、结果诊断和完整性审计。
```

一个 canonical run 包含：

```text
assets/output/<run>/
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

- 方法路线选择；
- R0 假设与 falsifier；
- evidence plan；
- 项目实现决策；
- 结果解释；
- 完整性审计。

依赖薄运行包的确定性步骤：

- `skillflow.py`：状态初始化、推进和完成验证；
- `skillresults.py`：schedule 与 observed cells 对齐、确定性聚合；
- `runner.py`：本地命令计划；
- `remote_gpu.py`：可选远端 GPU 部署和收集。

通用单阶段记录器已随 executor Skill 自带：

```text
${CODEX_HOME:-$HOME/.codex}/skills/autodesign-executor/scripts/run_stage.py
```

因此剩余代码不会替 Codex 选择方法、模型、baseline、训练范式或论文结论。

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
python3 -m unittest discover -s tests -v
.venv/bin/ruff check .
python3 -m compileall -q autodesign skills scripts tests
bash scripts/run_skill_first_demo.sh assets/output/skill_first_demo
```

## 远端 GPU

```bash
python3 -m autodesign remote-validate configs/remote_gpu.local.json
python3 -m autodesign remote-all configs/remote_gpu.local.json --dry-run
```

远端执行读取 `generated_project/environment.yml`、`command_plan.json` 和 `result_contract.json`。它只运行已经接受的项目，不重新解释研究方案。
