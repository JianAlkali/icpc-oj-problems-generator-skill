#!/usr/bin/env python3
"""Compile and validate an OJ problem package.

Assumes generator.cpp supports: all, boundary, rand, big, boundary+big.
The script compares brute/solution on generated inputs and optionally
compares slower_solution/brute on small modes.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path


def exe_name(name: str) -> str:
    return name + (".exe" if os.name == "nt" else "")


def run(cmd: list[str], cwd: Path, inp: bytes | None = None, timeout: int = 30) -> bytes:
    proc = subprocess.run(
        cmd,
        cwd=cwd,
        input=inp,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=timeout,
    )
    if proc.returncode != 0:
        raise RuntimeError(
            f"command failed: {' '.join(cmd)}\nstdout:\n{proc.stdout.decode(errors='replace')}\nstderr:\n{proc.stderr.decode(errors='replace')}"
        )
    return proc.stdout


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def compile_cpp(workdir: Path, source: str, out: str, std: str) -> None:
    run(["g++", f"-std={std}", "-O2", "-pipe", "-Wall", "-Wextra", source, "-o", out], workdir, timeout=120)


def compare_case(workdir: Path, label: str, input_data: bytes, report_dir: Path, timeout: int) -> None:
    brute = run([str(workdir / exe_name("brute"))], workdir, input_data, timeout)
    sol = run([str(workdir / exe_name("solution"))], workdir, input_data, timeout)
    if brute.strip() != sol.strip():
        report_dir.mkdir(parents=True, exist_ok=True)
        (report_dir / f"{label}.in").write_bytes(input_data)
        (report_dir / f"{label}.brute.out").write_bytes(brute)
        (report_dir / f"{label}.solution.out").write_bytes(sol)
        raise AssertionError(f"{label}: brute != solution, counterexample saved in {report_dir}")


def compare_slower(workdir: Path, label: str, input_data: bytes, report_dir: Path, timeout: int) -> None:
    brute = run([str(workdir / exe_name("brute"))], workdir, input_data, timeout)
    slower = run([str(workdir / exe_name("slower_solution"))], workdir, input_data, timeout)
    if brute.strip() != slower.strip():
        report_dir.mkdir(parents=True, exist_ok=True)
        (report_dir / f"{label}.in").write_bytes(input_data)
        (report_dir / f"{label}.brute.out").write_bytes(brute)
        (report_dir / f"{label}.slower.out").write_bytes(slower)
        raise AssertionError(f"{label}: brute != slower_solution, counterexample saved in {report_dir}")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--workdir", default=".")
    ap.add_argument("--std", default="c++17")
    ap.add_argument("--rounds", type=int, default=10000)
    ap.add_argument("--timeout", type=int, default=30)
    ap.add_argument("--report-dir", default="reports/counterexamples")
    ap.add_argument("--no-compile", action="store_true")
    args = ap.parse_args()

    workdir = Path(args.workdir).resolve()
    report_dir = workdir / args.report_dir

    if not args.no_compile:
        for src, out in [
            ("brute.cpp", exe_name("brute")),
            ("slower_solution.cpp", exe_name("slower_solution")),
            ("solution.cpp", exe_name("solution")),
            ("generator.cpp", exe_name("generator")),
        ]:
            compile_cpp(workdir, src, out, args.std)

    summary: dict[str, object] = {"compile": "PASS", "checks": []}
    summary["timeout_seconds_per_command"] = args.timeout
    summary["timeout_policy"] = "Every generator/solver comparison in this run used subprocess timeouts."

    for mode in ["all", "boundary"]:
        data = run([str(workdir / exe_name("generator")), mode], workdir, timeout=args.timeout)
        compare_case(workdir, mode, data, report_dir, args.timeout)
        compare_slower(workdir, f"slower_{mode}", data, report_dir, args.timeout)
        summary["checks"].append({"mode": mode, "status": "PASS", "input_sha256": sha256(data)})

    for i in range(1, args.rounds + 1):
        data = run([str(workdir / exe_name("generator")), "rand", str(i)], workdir, timeout=args.timeout)
        compare_case(workdir, f"rand_{i}", data, report_dir, args.timeout)
        if i <= min(100, args.rounds):
            compare_slower(workdir, f"slower_rand_{i}", data, report_dir, args.timeout)
        if i % 1000 == 0:
            print(f"RAND {i}: PASS", flush=True)

    summary["checks"].append({"mode": "rand", "rounds": args.rounds, "status": "PASS"})
    summary["final_verdict"] = "VERIFIED"
    out = workdir / "reports" / "validation_report.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    print("COMPILE: PASS")
    print("ALL: PASS")
    print("BOUNDARY: PASS")
    print(f"RAND({args.rounds} rounds): PASS")
    print(f"TIMEOUTS({args.timeout}s per command): PASS")
    print("SLOWER_SOLUTION: PASS")
    print("FINAL_VERDICT: VERIFIED")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"FAILED: {exc}", file=sys.stderr)
        raise
