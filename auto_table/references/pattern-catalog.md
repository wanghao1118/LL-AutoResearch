# Top-conference main-table pattern catalog

This catalog records reusable structure, not visual imitation. The papers were checked against their published/author PDF tables and official proceedings metadata.

## 1. Dense benchmark matrix — BERT

- Paper: [BERT: Pre-training of Deep Bidirectional Transformers for Language Understanding](https://aclanthology.org/N19-1423/) — NAACL 2019, Best Long Paper.
- Observed table: Table 1, GLUE test results.
- Structure: `System` rows; one column per task; training-set size appears as a second header line; `Average` is the final summary column.
- Data expression: metrics differ by task (F1, correlation, accuracy) but share a compact numeric grid; the caption defines each metric rather than bloating headers.
- Reusable lesson: use `benchmark-wide`; reserve the final column for a clearly defined aggregate, and put per-task metadata directly beneath task names only when it changes interpretation.

## 2. Hierarchical model/method/budget — LoRA

- Paper: [LoRA: Low-Rank Adaptation of Large Language Models](https://openreview.net/forum?id=nZeVKeeFYf9) — ICLR 2022.
- Observed table: Table 2, GLUE comparison.
- Structure: a combined model/method region, explicit `# Trainable Parameters`, then task columns; horizontal spacing separates RoBERTa-base, RoBERTa-large, and DeBERTa-XXL blocks.
- Data expression: mean ± spread for reproduced runs, point estimates for published baselines, and `*`/`†` provenance/protocol markers explained in the caption.
- Reusable lesson: use `hierarchical-method-budget`; never encode the parameter budget only inside a method name, and visibly distinguish source/protocol differences.

## 3. Transposed benchmark scan — Vision Transformer

- Paper: [An Image is Worth 16x16 Words](https://openreview.net/forum?id=YicbFdNTTy) — ICLR 2021.
- Observed table: Table 2, state-of-the-art image classification comparison.
- Structure: datasets are rows, five focal systems are columns; model name and pre-training data are combined in column headers; compute is a final cost row.
- Data expression: mean ± SD for most reproduced results, point values for external baselines, em dash for unavailable results, and a dedicated compute unit row.
- Reusable lesson: use `transposed-benchmark` when many benchmarks are compared across few systems. Missing cells must remain visible, and cost may occupy a semantically distinct final row.

## 4. Quality and cost as parallel evidence — Transformer

- Paper: [Attention Is All You Need](https://papers.neurips.cc/paper_files/paper/2017/hash/3f5ee243547dee91fbd053c1c4a845aa-Abstract.html) — NeurIPS 2017.
- Observed table: Table 2, machine translation quality and training cost.
- Structure: methods in rows; top-level column groups `BLEU` and `Training Cost (FLOPs)`; language pairs form the second header level; ensemble baselines form a separate row block; proposed models are placed last.
- Data expression: intentional blanks where a paper did not report a language pair/cost; no invented aggregate score between quality and compute.
- Reusable lesson: use `quality-efficiency` with `metric → dataset` headers and preserve missingness. Separate single models, ensembles, and proposed systems because they are not the same comparison regime.

## 5. Performance plus realized speedup — FlashAttention

- Paper: [FlashAttention: Fast and Memory-Efficient Exact Attention with IO-Awareness](https://papers.neurips.cc/paper_files/paper/2022/hash/67d57c32e20fd0a7a302cb81d36e40d5-Abstract-Conference.html) — NeurIPS 2022.
- Observed tables: Tables 2–3, GPT-2 and Long Range Arena.
- Structure: implementation identity is separate from perplexity/accuracy, wall-clock time, and normalized speedup; task columns lead to `Avg` and then `Speedup`.
- Data expression: cost is measured on a declared hardware setup; speedup is shown next to absolute time rather than replacing it.
- Reusable lesson: a relative efficiency field needs its absolute anchor and measurement protocol. Use `quality-efficiency`, and keep quality, absolute cost, and relative speedup as separate metrics.

## 6. Scale fields as first-class descriptors — ResNet

- Paper: [Deep Residual Learning for Image Recognition](https://openaccess.thecvf.com/content_cvpr_2016/html/He_Deep_Residual_Learning_CVPR_2016_paper.html) — CVPR 2016.
- Observed tables: Tables 3, 4, and 6.
- Structure: model family and depth/shortcut variant are encoded in row labels; the CIFAR table explicitly separates `# layers` and `# params`; horizontal rules divide prior methods from residual variants.
- Data expression: error metrics use lower-is-better semantics; selected repeated-run results include mean ± SD while most prior values are point estimates.
- Reusable lesson: use `scaled-variants`; separate family, variant, depth, and parameter count when scale is part of the claim.

## 7. Model scale as evidence columns — MAE

- Paper: [Masked Autoencoders Are Scalable Vision Learners](https://openaccess.thecvf.com/content/CVPR2022/html/He_Masked_Autoencoders_Are_Scalable_Vision_Learners_CVPR_2022_paper.html) — CVPR 2022.
- Observed table: Table 3, ImageNet-1K comparison.
- Structure: methods and pre-training data are left descriptors; ViT-B/L/H/H448 are separate model-scale columns; scratch/supervised rows are visually separated from self-supervised methods.
- Data expression: missing scale evaluations are dashes; best result per scale is underlined; the caption fixes resolution and fine-tuning protocol.
- Reusable lesson: represent scale as a true axis, not a suffix that readers must parse. Use `scaled-variants` or transpose when the number of scales is small.

## 8. Compact regimes and oracle separation — ReAct

- Paper: [ReAct: Synergizing Reasoning and Acting in Language Models](https://openreview.net/forum?id=WE_vluYUL-X) — ICLR 2023.
- Observed table: Table 1, PaLM-540B prompting results.
- Structure: two task columns with metric names in parentheses; prompting regimes are separated by horizontal rules; supervised state-of-the-art is a distinct final block.
- Data expression: compact scalar scores, citation markers attached to external systems, and bold emphasis only within the intended comparison.
- Reusable lesson: use `compact-regime-comparison`; a supervised oracle must not visually blend into prompting baselines.

## 9. Family bands and scoped ranking — ToolArtist

- Paper: [ToolArtist: Tool-Using Unified Multimodal Models for Agentic Image Generation](https://arxiv.org/abs/2608.04436) — arXiv preprint, 2026 (not a conference publication at catalog time).
- Observed table: Table 1, WISE and WorldGenBench-Humanities.
- Structure: full-width gray bands divide proprietary, general image-generation, unified multimodal, and agentic systems; two benchmark blocks each end in an average; the proposed row receives a restrained background shade.
- Data expression: dashes preserve unavailable source values. Bold and underline rank only non-proprietary systems, and ties share the same marker.
- Reusable lesson: use `family-banded-benchmark`; method-family bands, focal-row shading, and scoped numerical ranking are three separate channels.

## 10. Resource identity beside performance — BLIP-2

- Paper: [BLIP-2](https://proceedings.mlr.press/v202/li23q.html) — ICML 2023.
- Observed tables: Tables 1–2, zero-shot vision-language results.
- Structure: trainable parameters, total parameters, and open-source status sit beside benchmark blocks; BLIP-2 variants form a separate proposed-method block.
- Data expression: point estimates and unavailable cells coexist; resource evidence supports the efficiency claim without replacing task scores.
- Reusable lesson: resource and openness fields belong to system identity/evidence, not a method-name suffix.

## 11. Published versus reproduced provenance — LLaVA

- Paper: [Visual Instruction Tuning](https://papers.neurips.cc/paper_files/paper/2023/hash/6dcf277ea32ce3288914faf369fe6de0-Abstract-Conference.html) — NeurIPS 2023.
- Observed table: Table 7, ScienceQA.
- Structure: a full-width separator distinguishes representative literature values from the authors' own experiment runs; category columns lead to an overall score.
- Data expression: a dagger marks text-only GPT-4 evaluated by the authors; the caption defines category abbreviations and provenance.
- Reusable lesson: values with different sources/protocols need visible blocks or fields even when their metric names match.

## 12. Absolute value plus inline gain — ConvNeXt

- Paper: [A ConvNet for the 2020s](https://openaccess.thecvf.com/content/CVPR2022/html/Liu_A_ConvNet_for_the_2020s_CVPR_2022_paper.html) — CVPR 2022.
- Observed table: supplementary Table 12, paired Swin/ConvNeXt throughput comparisons.
- Structure: matched model scales appear as adjacent pairs with image size, FLOPs, throughput, and accuracy.
- Data expression: throughput keeps its absolute value and appends an inline relative gain such as `1943.5 (+47%)`; slash-separated accuracy distinguishes two training-data regimes.
- Reusable lesson: use `auxiliary.delta` only after selecting an explicit matched baseline, and preserve the absolute measurement.

## 13. Dedicated improvement row and test declaration — BirDRec

- Paper: [BirDRec](https://papers.neurips.cc/paper_files/paper/2023/file/08309150af77fc7c79ade0bf8bb6a562-Abstract-Conference.html) — NeurIPS 2023.
- Observed table: Table 3, robust sequential recommendation.
- Structure: dataset blocks contain HR, NDCG, and MRR metrics; a final `Improv.` row reports gain over the runner-up.
- Data expression: the runner-up is marked separately, and the caption declares the relative-improvement baseline and paired test threshold.
- Reusable lesson: a delta may deserve its own evidence row when it is central across many columns; baseline and test semantics belong in the caption.

## 14. Repeated-run value grammar — MGM

- Paper: [Generative Modeling for Multi-task Visual Learning](https://proceedings.mlr.press/v162/bao22c.html) — ICML 2022.
- Observed table: Table 2, NYUv2 and Tiny-Taskonomy.
- Structure: dataset and labeled-data regimes organize several task metrics with mixed directions.
- Data expression: mean ± standard deviation is reported from five runs; arrows disambiguate higher/lower-is-better metrics.
- Reusable lesson: uncertainty type, run count, precision, and direction form one value contract and must be generated together.

## 15. Pairwise preference outcomes — VCB

- Paper: [Don't Forget Your Reward Values](https://aclanthology.org/2024.emnlp-main.976/) — EMNLP 2024.
- Observed tables: Tables 2–5, automatic, human, and out-of-distribution evaluation.
- Structure: datasets group `Win`, `Tie`, and `Lose` instead of compressing preference into a single score.
- Data expression: the evaluation description reports 100 sampled prompts and two annotators for the human study.
- Reusable lesson: preference evidence is distributional; preserve Win/Tie/Lose and disclose sample/annotator counts rather than inventing a scalar average.

## Cross-paper synthesis

The recurring grammar is:

```text
[identity / protocol fields] | [measured evidence blocks] | [optional aggregate or cost]
```

The left region answers “what exactly was run?” The right region answers “what happened?” Multi-level headers encode real experimental dimensions. Row whitespace encodes comparability regimes. Published papers vary in how much methodology they place in captions; Paper2Table adopts the concise end of that range and keeps aggregation, source markers, protocol, metric semantics, and caveats in正文-oriented `context_notes` by default.
