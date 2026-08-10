#!/usr/bin/env python3
"""Fetch the five preselected fresh-holdout arXiv source packages.

This acquisition step is outside the frozen matcher. It downloads official
e-print archives, extracts them with path/link checks, and records only source
inventory metadata. The matcher later receives generated Introduction/Method
JSON files rather than these source trees.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from step0_fetch_paper_sources import _download, _extract


ROOT = Path(__file__).resolve().parent
PAPER_IDS = ("2303.17651", "2308.09687", "2308.10144", "2305.14992", "2304.09842")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--raw-dir", default="assets/input/source_papers/raw")
    parser.add_argument("--extract-dir", default="assets/input/source_papers/extracted")
    parser.add_argument("--base-url", default="https://export.arxiv.org/e-print")
    parser.add_argument("--timeout", type=int, default=120)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    raw_dir = ROOT / args.raw_dir
    extract_dir = ROOT / args.extract_dir
    raw_dir.mkdir(parents=True, exist_ok=True)
    extract_dir.mkdir(parents=True, exist_ok=True)
    records = []
    for arxiv_id in PAPER_IDS:
        archive = raw_dir / f"{arxiv_id}.src"
        paper_dir = extract_dir / arxiv_id
        downloaded = False
        extracted = False
        if not archive.is_file():
            _download(f"{args.base_url.rstrip('/')}/{arxiv_id}", archive, args.timeout)
            downloaded = True
        if not paper_dir.is_dir() or not any(paper_dir.iterdir()):
            _extract(archive, paper_dir)
            extracted = True
        tex_files = sorted(path.relative_to(paper_dir).as_posix() for path in paper_dir.rglob("*.tex"))
        if not tex_files:
            raise ValueError(f"no TeX source files extracted for {arxiv_id}")
        record = {
            "arxiv_id": arxiv_id,
            "downloaded": downloaded,
            "extracted": extracted,
            "archive_bytes": archive.stat().st_size,
            "tex_file_count": len(tex_files),
            "source_root": paper_dir.relative_to(ROOT).as_posix(),
        }
        records.append(record)
        print(json.dumps(record, ensure_ascii=False))
    inventory = ROOT / "assets/input/fresh_holdout_suite/source_inventory.json"
    inventory.write_text(json.dumps({"papers": records}, ensure_ascii=False, indent=2) + "\n")
    json.loads(inventory.read_text())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
