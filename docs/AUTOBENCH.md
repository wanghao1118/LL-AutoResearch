# AutoBench Module

AutoBench 是 **AutoResearch 系统中的 AutoBench 模块**。它不是独立 Skill，也不是另一个
AutoSearch 系统。

## 目标

AutoSearch 已经从论文集合中形成 `WeaknessCard` 和 Gap 证据链。AutoBench 接着回答：

1. 这个 Weakness 是否已有现成 Benchmark 能证明？
2. 如果有，哪些 Benchmark 可用，各自能证明哪些评估维度？
3. 如果只覆盖一部分，还缺哪些维度，如何基于最接近的 Benchmark 改造？
4. 如果没有现成 Benchmark，需要构造哪些新数据、划分和指标？

## 系统位置

```text
AutoResearch
├── AutoSearch
│   ├── topic / papers / paper cards
│   ├── field map / MOC
│   └── gaps / weakness cards
└── AutoBench
    ├── required evaluation dimensions
    ├── paper-grounded benchmark candidates
    ├── coverage decision
    └── reuse / adaptation / construction plan
```

入口代码：

- `src/autoresearch/autobench.py`：维度提取、候选匹配、三类路由和 Markdown 输出。
- `src/autoresearch/pipeline.py`：AutoSearch 完成 Weakness 后自动运行 AutoBench。
- `src/autoresearch/cli.py`：`autoresearch bench <artifact_path>` 可对已有运行重新计算。
- `src/autoresearch/dashboard.py`：AutoBench 看板页签。

## 输入与证据边界

AutoBench 只使用当前 AutoResearch 运行中已经收集的内容：

- `weakness_cards`：Weakness 与尚未覆盖的部分。
- `gaps`：Gap Evidence Chain 中的 `missing_dimensions`。
- `paper_cards`：论文题名、任务、数据集、指标、URL 和逐字段证据。
- `domain_profile`：与 Weakness 明确相关的能力维度。

候选 Benchmark 必须来自当前论文集合，而不是由系统凭空推荐。每个候选都会记录来源论文、
URL、章节、指标、能证明的维度和覆盖比例。Introduction/Method 证据优先；若当前论文卡片没有
这两类章节，产物会明确标为 `other_paper_section` 或 `structured_paper_card`。

## 决策规则

### `existing_benchmark`

- 候选组合覆盖全部所需维度。
- 至少一个候选明确给出数据集、指标和论文 URL。
- 路由：`direct_benchmark_reuse`。

### `partial_benchmark`

- 至少一个论文 Benchmark 能证明部分维度。
- 仍存在未覆盖维度，或候选缺少完整数据集/指标定义。
- 路由：`base_benchmark_adaptation`。

### `no_existing_benchmark`

- 当前论文集合没有候选能覆盖所需维度。
- 路由：`new_benchmark_construction`。

## 产物

- `search_result.json`：包含完整 `autobench` 字段。
- `autobench.json`：机器可读的 AutoBench 独立结果。
- `autobench.md`：逐 Weakness 的论文来源、Benchmark、覆盖与缺失维度。
- `dashboard.html#autobench`：可视化结果。

## 使用

新搜索会自动运行 AutoBench：

```bash
autoresearch search "GUI agent failure recovery" --profile gui-agent
```

已有 AutoSearch 产物可单独重算：

```bash
autoresearch bench outputs/gui-agent-failure-recovery
```
