# Input Layout

- `blind_cases/`: matcher-visible anonymized Introduction and Method JSON.
- `blind_gold/`: source paper title/link, experiment-derived benchmark labels,
  benchmark roles, and evidence sections opened only after matching finishes.
- `source_papers/`: official source packages and arXiv metadata used to build the
  fixtures. Run `python3 step0_fetch_paper_sources.py` to populate them;
  raw/extracted source trees remain local and are ignored by Git.
- `untouched_holdout_cases/` and `untouched_holdout_gold/`: first frozen LATS
  case and its isolated literature gold.
- `untouched_holdout_2_cases/` and `untouched_holdout_2_gold/`: CRITIC case
  frozen before the holdout-001-driven matcher revision, plus isolated gold.

The gold-free runner copies neither `blind_gold/` nor `source_papers/` into its
temporary worker directory. The post-run literature audit intentionally reveals
these fields to the researcher for direct paper-versus-recommendation checking.
