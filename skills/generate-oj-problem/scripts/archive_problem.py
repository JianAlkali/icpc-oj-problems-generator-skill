#!/usr/bin/env python3
"""Cleanup temporary files and archive a finalized OJ problem package."""

from __future__ import annotations

import argparse
import fnmatch
import shutil
from pathlib import Path


PRESERVE = [
    "description.json",
    "description.draft.json",
    "frozen_spec.md",
    "brute.cpp",
    "slower_solution.cpp",
    "solution.cpp",
    "generator.cpp",
    "checker.cpp",
    "validator.cpp",
    "interactor.cpp",
    "mediator.cpp",
    "stress.cpp",
    "stress.py",
    "provenance.json",
    "sample_requirements.json",
    "tests/*",
    "reports/*",
]

DELETE = [".tmp", "*.diff", "*.log", "*.exe", "a.out", "*.tmp.in", "*.tmp.out"]


def matches(path: Path, patterns: list[str]) -> bool:
    s = path.as_posix()
    return any(fnmatch.fnmatch(s, p) or fnmatch.fnmatch(path.name, p) for p in patterns)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--workdir", default=".")
    ap.add_argument("--archive-root", default="archive")
    ap.add_argument("--slug", default="process")
    ap.add_argument("--finalized", action="store_true", help="Required safety acknowledgement.")
    args = ap.parse_args()

    if not args.finalized:
        raise SystemExit("Refusing to archive before --finalized is supplied.")

    workdir = Path(args.workdir).resolve()
    required = ["description.json", "provenance.json"]
    missing = [p for p in required if not (workdir / p).exists()]
    if not ((workdir / "reports" / "validation_report.json").exists() or (workdir / "reports" / "validation_report.md").exists()):
        missing.append("reports/validation_report.json or reports/validation_report.md")
    if missing:
        raise SystemExit(f"Refusing to archive; missing final files: {missing}")

    for item in list(workdir.iterdir()):
        rel = item.relative_to(workdir)
        if matches(rel, DELETE):
            if item.is_dir():
                shutil.rmtree(item)
            else:
                item.unlink()

    archive_dir = (workdir / args.archive_root / args.slug).resolve()
    archive_dir.mkdir(parents=True, exist_ok=True)
    for path in workdir.rglob("*"):
        if path.is_dir():
            continue
        rel = path.relative_to(workdir)
        if rel.parts and rel.parts[0] in {args.archive_root, "artifacts"}:
            continue
        if matches(rel, PRESERVE):
            target = archive_dir / rel
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(path, target)

    print(f"Archived finalized package to {archive_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
