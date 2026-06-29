#!/usr/bin/env python3
"""Smoke-test the batch problem pipeline on a tiny generated package."""

from __future__ import annotations

import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SKILL = ROOT / "skills" / "generate-oj-problem"
SCRIPTS = SKILL / "scripts"
CONFIG = SKILL / "config" / "defaults.json"


def run(cmd: list[str], cwd: Path) -> None:
    subprocess.run(cmd, cwd=cwd, check=True, timeout=120)


def write(path: Path, text: str) -> None:
    path.write_text(text, encoding="utf-8")


def main() -> int:
    if shutil.which("g++") is None:
        print("SKIP: g++ is not available")
        return 0

    with tempfile.TemporaryDirectory(prefix="oj-skill-smoke-") as tmp:
        workdir = Path(tmp)
        desc = {
            "title": "A Plus B",
            "tags": ["入门"],
            "difficulty": 800,
            "time_limit_s": 1,
            "memory_limit_mb": 256,
            "visible_sample_count": 1,
            "judge_mode": "batch",
            "checker_type": "token",
            "checker_source": "",
            "interactor_source": "",
            "mediator_source": "",
            "description": "Given two integers, output their sum.",
            "cases": [],
        }
        write(workdir / "description.draft.json", json.dumps(desc, ensure_ascii=False, indent=2) + "\n")
        write(workdir / "frozen_spec.md", "# Frozen Spec\n\nBatch token A+B smoke fixture.\n")
        write(
            workdir / "generator.cpp",
            r'''
#include <bits/stdc++.h>
using namespace std;
int main(int argc, char** argv) {
  string mode = argc > 1 ? argv[1] : "all";
  if (mode == "all") cout << "1 2\n";
  else if (mode == "boundary") cout << "0 0\n";
  else if (mode == "rand") cout << "5 7\n";
  else if (mode == "big") cout << "1000000000 1000000000\n";
  else if (mode == "boundary+big") cout << "-1000000000 1000000000\n";
  else return 1;
  return 0;
}
'''.lstrip(),
        )
        solution = r'''
#include <bits/stdc++.h>
using namespace std;
int main() {
  long long a, b;
  if (!(cin >> a >> b)) return 0;
  cout << a + b << "\n";
  return 0;
}
'''.lstrip()
        for name in ["solution.cpp", "brute.cpp", "slower_solution.cpp"]:
            write(workdir / name, solution)
        (workdir / "reports").mkdir()
        write(workdir / "reports" / "validation_report.md", "COMPILE: PASS\nFINAL_VERDICT: VERIFIED\n")

        exe_suffix = ".exe" if sys.platform.startswith("win") else ""
        for source in ["generator", "solution", "brute", "slower_solution"]:
            run(["g++", "-std=c++17", "-O2", f"{source}.cpp", "-o", f"{source}{exe_suffix}"], workdir)

        run(
            [
                sys.executable,
                str(SCRIPTS / "generate_cases.py"),
                "--workdir",
                str(workdir),
                "--timeout",
                "10",
                "--visible",
                "1",
                "--case",
                "all",
                "--case",
                "boundary",
            ],
            workdir,
        )
        run([sys.executable, str(SCRIPTS / "validate_package.py"), "--workdir", str(workdir), "--config", str(CONFIG)], workdir)
        run(
            [
                sys.executable,
                str(SCRIPTS / "materialize_product.py"),
                "--workdir",
                str(workdir),
                "--config",
                str(CONFIG),
                "--mode",
                "split_files",
            ],
            workdir,
        )
        run(
            [
                sys.executable,
                str(SCRIPTS / "validate_package.py"),
                "--workdir",
                str(workdir),
                "--config",
                str(CONFIG),
                "--require-artifacts",
            ],
            workdir,
        )
        run(
            [
                sys.executable,
                str(SCRIPTS / "archive_problem.py"),
                "--workdir",
                str(workdir),
                "--config",
                str(CONFIG),
                "--archive-root",
                "archive",
                "--slug",
                "process",
                "--finalized",
            ],
            workdir,
        )
        run(
            [
                sys.executable,
                str(SCRIPTS / "validate_package.py"),
                "--workdir",
                str(workdir),
                "--config",
                str(CONFIG),
                "--require-artifacts",
                "--finalized",
            ],
            workdir,
        )

    print("SMOKE_BATCH_PIPELINE: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
