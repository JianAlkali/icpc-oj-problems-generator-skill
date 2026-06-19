#!/usr/bin/env python3
"""Generate official cases and populate description.json with provenance."""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import os
import subprocess
from pathlib import Path


def exe_name(name: str) -> str:
    return name + (".exe" if os.name == "nt" else "")


def run(cmd: list[str], cwd: Path, inp: bytes | None = None, timeout: int = 60) -> bytes:
    proc = subprocess.run(cmd, cwd=cwd, input=inp, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=timeout)
    if proc.returncode != 0:
        raise RuntimeError(f"command failed: {' '.join(cmd)}\n{proc.stderr.decode(errors='replace')}")
    return proc.stdout


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def parse_case(spec: str) -> tuple[str, list[str]]:
    parts = spec.split(":")
    return parts[0], parts[1:]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--workdir", default=".")
    ap.add_argument("--draft", default="description.draft.json")
    ap.add_argument("--out", default="description.json")
    ap.add_argument("--tests-dir", default="tests")
    ap.add_argument("--provenance", default="provenance.json")
    ap.add_argument("--visible", type=int, default=None)
    ap.add_argument("--timeout", type=int, default=60)
    ap.add_argument("--case", action="append", required=True, help="mode[:arg1[:arg2...]], repeatable")
    args = ap.parse_args()

    workdir = Path(args.workdir).resolve()
    tests_dir = workdir / args.tests_dir
    tests_dir.mkdir(parents=True, exist_ok=True)

    draft_path = workdir / args.draft
    desc = json.loads(draft_path.read_text(encoding="utf-8"))
    if desc.get("cases") not in ([], None):
        raise ValueError("draft description must have empty cases; refusing to merge over existing samples")

    cases = []
    provenance = {
        "created_at_utc": dt.datetime.now(dt.timezone.utc).isoformat(),
        "draft": args.draft,
        "solution_command": [str(workdir / exe_name("solution"))],
        "timeout_seconds_per_command": args.timeout,
        "cases": [],
    }

    for idx, spec in enumerate(args.case, start=1):
        mode, gen_args = parse_case(spec)
        stem = f"{idx:02d}_{mode.replace('+', '_').replace('-', '_')}"
        gen_cmd = [str(workdir / exe_name("generator")), mode, *gen_args]
        input_data = run(gen_cmd, workdir, timeout=args.timeout)
        output_data = run([str(workdir / exe_name("solution"))], workdir, input_data, timeout=args.timeout)
        in_path = tests_dir / f"{stem}.in"
        out_path = tests_dir / f"{stem}.out"
        in_path.write_bytes(input_data)
        out_path.write_bytes(output_data)
        cases.append({"input": input_data.decode("utf-8"), "output": output_data.decode("utf-8")})
        provenance["cases"].append(
            {
                "case_id": stem,
                "source": "generator",
                "generator_command": gen_cmd,
                "generator_mode": mode,
                "generator_args": gen_args,
                "solution_command": [str(workdir / exe_name("solution"))],
                "timeout_seconds": args.timeout,
                "input_file": str(in_path.relative_to(workdir)),
                "output_file": str(out_path.relative_to(workdir)),
                "input_sha256": sha256(input_data),
                "output_sha256": sha256(output_data),
                "created_at_utc": dt.datetime.now(dt.timezone.utc).isoformat(),
            }
        )

    if args.visible is not None:
        desc["visible_sample_count"] = args.visible
    if desc["visible_sample_count"] > len(cases):
        raise ValueError("visible_sample_count exceeds generated case count")
    desc["cases"] = cases

    (workdir / args.out).write_text(json.dumps(desc, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (workdir / args.provenance).write_text(json.dumps(provenance, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Wrote {args.out}, {args.provenance}, and {len(cases)} generated cases.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
