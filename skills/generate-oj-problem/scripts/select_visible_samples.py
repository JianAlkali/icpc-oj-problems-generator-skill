#!/usr/bin/env python3
"""Reorder generated cases so visible samples satisfy coverage requirements.

The first visible_sample_count cases in description.json are treated as visible.
This script never adds non-schema keys to cases.
"""

from __future__ import annotations

import argparse
import itertools
import json
import re
from pathlib import Path


def load_requirements(path: Path | None) -> list[dict]:
    if path is None or not path.exists():
        return []
    data = json.loads(path.read_text(encoding="utf-8"))
    return data.get("requirements", data if isinstance(data, list) else [])


def case_matches(case: dict, req: dict) -> bool:
    where = req.get("where", "output")
    text = case.get(where, "")
    if "token" in req:
        return req["token"] in text.split()
    if "contains" in req:
        return req["contains"] in text
    if "regex" in req:
        return re.search(req["regex"], text, re.MULTILINE) is not None
    raise ValueError(f"requirement {req.get('name', '<unnamed>')} has no token/contains/regex")


def covered(selection: list[dict], requirements: list[dict]) -> tuple[bool, list[str]]:
    missing = []
    for req in requirements:
        if req.get("enabled", True) is False:
            continue
        min_count = int(req.get("min_count", 1))
        count = sum(1 for case in selection if case_matches(case, req))
        if count < min_count:
            missing.append(req.get("name", str(req)))
    return not missing, missing


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--workdir", default=".")
    ap.add_argument("--description", default="description.json")
    ap.add_argument("--requirements", default=None)
    ap.add_argument("--out", default=None)
    args = ap.parse_args()

    workdir = Path(args.workdir).resolve()
    desc_path = workdir / args.description
    desc = json.loads(desc_path.read_text(encoding="utf-8"))
    cases = desc.get("cases", [])
    visible_count = int(desc.get("visible_sample_count", 0))
    requirements = load_requirements((workdir / args.requirements) if args.requirements else None)

    if visible_count < 0 or visible_count > len(cases):
        raise SystemExit("visible_sample_count is invalid")
    if not requirements or visible_count == 0:
        print("No visible-sample requirements to apply.")
        return 0

    # Brute force is fine because visible sample counts are normally tiny.
    for combo in itertools.combinations(range(len(cases)), visible_count):
        selection = [cases[i] for i in combo]
        ok, _ = covered(selection, requirements)
        if ok:
            chosen = set(combo)
            desc["cases"] = selection + [case for i, case in enumerate(cases) if i not in chosen]
            out_path = workdir / (args.out or args.description)
            out_path.write_text(json.dumps(desc, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
            print(f"VISIBLE_SAMPLES: PASS ({', '.join(req.get('name', '<unnamed>') for req in requirements)})")
            return 0

    _, missing = covered(cases[:visible_count], requirements)
    raise SystemExit(f"VISIBLE_SAMPLES: FAIL; no generated visible set satisfies requirements. Missing: {missing}")


if __name__ == "__main__":
    raise SystemExit(main())
