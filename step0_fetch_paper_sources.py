#!/usr/bin/env python3
"""Fetch and unpack the official arXiv sources required by blind fixtures.

Overall logic:
1. Check whether every Introduction/Method source file needed by the fixture
   builder already exists and skip complete papers.
2. Reuse a local ``.src`` archive when present; otherwise download the official
   arXiv e-print package into the ignored raw-source directory.
3. Extract each package into its paper-specific ignored directory and verify all
   expected source files before reporting success.

The source trees are preparation inputs only. The blind worker in
``step2_run_blind_matching.py`` never receives them.
"""

from __future__ import annotations

import argparse
import json
import tarfile
import urllib.request
from pathlib import Path


ROOT = Path(__file__).resolve().parent


PAPER_SOURCES = {
    "2210.03629": [
        "iclr2023/text/intro.tex",
        "iclr2023/text/method.tex",
    ],
    "2303.11366": ["main.tex"],
    "2405.15793": [
        "sections/01_intro.tex",
        "sections/02_aci.tex",
        "sections/03_sweagent.tex",
        "sections/04_experiments.tex",
    ],
    "2310.04406": ["main.tex"],
    "2305.11738": [
        "sections/1_intro.tex",
        "sections/3_method.tex",
        "sections/experiments/qa.tex",
        "sections/experiments/program.tex",
        "sections/experiments/toxicity.tex",
    ],
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--raw-dir", default="assets/input/source_papers/raw")
    parser.add_argument("--extract-dir", default="assets/input/source_papers/extracted")
    parser.add_argument("--base-url", default="https://export.arxiv.org/e-print")
    parser.add_argument("--timeout", type=int, default=90)
    return parser.parse_args()


def _download(url: str, destination: Path, timeout: int) -> None:
    """Download one source archive atomically to avoid retaining partial data."""

    request = urllib.request.Request(url, headers={"User-Agent": "Auto-Bench research fixture builder"})
    temporary = destination.with_suffix(destination.suffix + ".part")
    with urllib.request.urlopen(request, timeout=timeout) as response:
        temporary.write_bytes(response.read())
    temporary.replace(destination)


def _extract(archive_path: Path, destination: Path) -> None:
    """Extract one arXiv tar package while keeping every member under its paper directory."""

    destination.mkdir(parents=True, exist_ok=True)
    destination_root = destination.resolve()
    with tarfile.open(archive_path, mode="r:*") as archive:
        members = archive.getmembers()
        for member in members:
            target = (destination / member.name).resolve()
            if target != destination_root and destination_root not in target.parents:
                raise ValueError(f"archive member leaves destination: {member.name}")
            if member.issym() or member.islnk():
                raise ValueError(f"archive member is a link: {member.name}")
        for member in members:
            archive.extract(member, destination)


def main() -> int:
    args = parse_args()
    raw_dir = ROOT / args.raw_dir
    extract_dir = ROOT / args.extract_dir
    raw_dir.mkdir(parents=True, exist_ok=True)
    extract_dir.mkdir(parents=True, exist_ok=True)

    for arxiv_id, required_paths in PAPER_SOURCES.items():
        paper_dir = extract_dir / arxiv_id
        required = [paper_dir / relative_path for relative_path in required_paths]
        downloaded = False
        extracted = False
        if not all(path.is_file() for path in required):
            archive_path = raw_dir / f"{arxiv_id}.src"
            if not archive_path.is_file():
                _download(f"{args.base_url.rstrip('/')}/{arxiv_id}", archive_path, args.timeout)
                downloaded = True
            _extract(archive_path, paper_dir)
            extracted = True
        missing = [path.relative_to(extract_dir).as_posix() for path in required if not path.is_file()]
        if missing:
            raise ValueError(f"missing required source files for {arxiv_id}: {missing}")
        print(
            json.dumps(
                {
                    "arxiv_id": arxiv_id,
                    "downloaded": downloaded,
                    "extracted": extracted,
                    "required_files": [path.relative_to(extract_dir).as_posix() for path in required],
                },
                ensure_ascii=False,
            )
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
