#!/usr/bin/env python3
"""Print one phase checkpoint from references/checkpoints.md."""

from __future__ import annotations

import argparse
import re
from pathlib import Path


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--step", required=True)
    ap.add_argument("--checkpoints", default=None)
    args = ap.parse_args()

    script_dir = Path(__file__).resolve().parent
    default_path = script_dir.parent / "references" / "checkpoints.md"
    path = Path(args.checkpoints).resolve() if args.checkpoints else default_path
    text = path.read_text(encoding="utf-8")
    pattern = re.compile(rf"^## {re.escape(args.step)}\s*$([\s\S]*?)(?=^## |\Z)", re.MULTILINE)
    match = pattern.search(text)
    if not match:
        raise SystemExit(f"Unknown checkpoint step: {args.step}")
    print(f"## {args.step}")
    print(match.group(1).strip())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
