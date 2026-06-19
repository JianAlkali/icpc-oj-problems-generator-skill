#!/usr/bin/env python3
"""Create final artifacts from the validated process package."""

from __future__ import annotations

import argparse
import json
import shutil
from pathlib import Path


SOURCE_MAP = {
    "checker_source": "checker.cpp",
    "interactor_source": "interactor.cpp",
    "mediator_source": "mediator.cpp",
}


def load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, data) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def normalize_cases(desc: dict) -> dict:
    out = dict(desc)
    cases = []
    for case in out.get("cases", []):
        output = case.get("output", case.get("answer", case.get("expected_output", "")))
        cases.append({"input": case.get("input", ""), "output": output})
    out["cases"] = cases
    return out


def hydrate_source_fields(workdir: Path, desc: dict) -> dict:
    out = dict(desc)
    for field, filename in SOURCE_MAP.items():
        if not out.get(field) and (workdir / filename).exists():
            out[field] = (workdir / filename).read_text(encoding="utf-8")
    return out


def materialize_aoj(workdir: Path, artifacts: Path, desc: dict, output_file: str) -> None:
    write_json(artifacts / output_file, normalize_cases(desc))


def materialize_split(workdir: Path, artifacts: Path, desc: dict, split: dict) -> None:
    statement_file = split.get("statement_file", "statement.md")
    metadata_file = split.get("metadata_file", "metadata.json")
    tests_dir = artifacts / split.get("tests_dir", "tests")
    sources_dir = artifacts / split.get("sources_dir", "sources")
    tests_dir.mkdir(parents=True, exist_ok=True)
    sources_dir.mkdir(parents=True, exist_ok=True)

    (artifacts / statement_file).write_text(desc.get("description", ""), encoding="utf-8")
    metadata = {k: v for k, v in desc.items() if k not in {"description", "cases", *SOURCE_MAP.keys()}}
    write_json(artifacts / metadata_file, metadata)

    for idx, case in enumerate(desc.get("cases", []), start=1):
        stem = f"{idx:02d}"
        output = case.get("output", case.get("answer", case.get("expected_output", "")))
        (tests_dir / f"{stem}.in").write_text(case.get("input", ""), encoding="utf-8")
        (tests_dir / f"{stem}.out").write_text(output, encoding="utf-8")

    for field, filename in SOURCE_MAP.items():
        source = desc.get(field, "")
        if source:
            (sources_dir / filename).write_text(source, encoding="utf-8")
    for filename in ["solution.cpp", "checker.cpp", "interactor.cpp", "mediator.cpp", "validator.cpp"]:
        src = workdir / filename
        if src.exists():
            shutil.copy2(src, sources_dir / filename)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--workdir", default=".")
    ap.add_argument("--config", default=None)
    ap.add_argument("--description", default="description.json")
    ap.add_argument("--mode", choices=["aoj_json", "split_files"], default=None)
    ap.add_argument("--artifacts-dir", default=None)
    ap.add_argument("--clean", action="store_true")
    args = ap.parse_args()

    workdir = Path(args.workdir).resolve()
    config = load_json(Path(args.config)) if args.config else {}
    product = config.get("product_policy", {})
    mode = args.mode or product.get("mode", "aoj_json")
    artifacts = workdir / (args.artifacts_dir or product.get("artifacts_dir", "artifacts"))
    if args.clean and artifacts.exists():
        shutil.rmtree(artifacts)
    artifacts.mkdir(parents=True, exist_ok=True)

    desc = hydrate_source_fields(workdir, load_json(workdir / args.description))
    if mode == "aoj_json":
        materialize_aoj(workdir, artifacts, desc, product.get("aoj_json", {}).get("output_file", "problem.json"))
    else:
        materialize_split(workdir, artifacts, desc, product.get("split_files", {}))
    print(f"ARTIFACTS: {artifacts} ({mode})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
