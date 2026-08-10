#!/usr/bin/env python3
"""Fetch official arXiv source packages for the frozen suite003 selection."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from step0_fetch_paper_sources import _download, _extract


ROOT = Path(__file__).resolve().parent
SELECTION = ROOT / "assets/input/fresh_holdout_suite_003/paper_selection.json"
INVENTORY = ROOT / "assets/input/fresh_holdout_suite_003/source_inventory.json"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--raw-dir", default="assets/input/source_papers/raw")
    parser.add_argument("--extract-dir", default="assets/input/source_papers/extracted")
    parser.add_argument("--base-url", default="https://export.arxiv.org/e-print")
    parser.add_argument("--timeout", type=int, default=120)
    return parser.parse_args()


def main() -> int:
    """Acquire and extract sources without opening experiment content."""

    args = parse_args()
    selection = json.loads(SELECTION.read_text(encoding="utf-8"))
    if selection.get("gold_state") != "SEALED_NOT_CONSTRUCTED":
        raise ValueError("suite003 sources must be acquired before gold construction")
    raw_dir = ROOT / args.raw_dir
    extract_dir = ROOT / args.extract_dir
    raw_dir.mkdir(parents=True, exist_ok=True)
    extract_dir.mkdir(parents=True, exist_ok=True)
    records = []
    for paper in selection["papers"]:
        arxiv_id = paper["arxiv_id"]
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
            "case_id": paper["case_id"],
            "arxiv_id": arxiv_id,
            "downloaded": downloaded,
            "extracted": extracted,
            "archive_bytes": archive.stat().st_size,
            "tex_file_count": len(tex_files),
            "source_root": paper_dir.relative_to(ROOT).as_posix(),
            "experiment_sections_inspected": False,
        }
        records.append(record)
        print(json.dumps(record, ensure_ascii=False))
    payload = {
        "schema_version": "1.0",
        "suite_id": selection["suite_id"],
        "acquisition_only": True,
        "experiment_sections_inspected": False,
        "papers": records,
    }
    INVENTORY.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n")
    json.loads(INVENTORY.read_text(encoding="utf-8"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
