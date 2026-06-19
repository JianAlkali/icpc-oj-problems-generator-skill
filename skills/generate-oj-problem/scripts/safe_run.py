#!/usr/bin/env python3
"""Run a command with mandatory timeout and stdin discipline."""

from __future__ import annotations

import argparse
import shlex
import subprocess
import sys
from pathlib import Path


READ_PATTERNS = ["cin >>", "scanf(", "getchar(", "getline(cin", "std::getline(cin"]


def source_reads_input(path: Path | None) -> bool:
    if path is None:
        return False
    text = path.read_text(encoding="utf-8", errors="ignore")
    return any(p in text for p in READ_PATTERNS)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--cmd", required=True, help="Command string, e.g. './solution --flag'.")
    ap.add_argument("--source", help="Source file to scan for stdin reads.")
    ap.add_argument("--input-file")
    ap.add_argument("--stdin", dest="stdin_text")
    ap.add_argument("--allow-empty-stdin", action="store_true")
    ap.add_argument("--timeout", type=float, required=True)
    ap.add_argument("--cwd", default=".")
    ap.add_argument("--stdout-file")
    ap.add_argument("--stderr-file")
    args = ap.parse_args()

    if args.timeout <= 0:
        raise SystemExit("--timeout must be positive")

    source = Path(args.source) if args.source else None
    has_input = args.input_file is not None or args.stdin_text is not None or args.allow_empty_stdin
    if source_reads_input(source) and not has_input:
        raise SystemExit(f"Refusing to run {args.cmd}: {source} appears to read stdin but no input was provided.")

    if args.input_file and args.stdin_text is not None:
        raise SystemExit("Use only one of --input-file and --stdin.")
    if args.input_file:
        input_data = Path(args.input_file).read_bytes()
    elif args.stdin_text is not None:
        input_data = args.stdin_text.encode()
    else:
        input_data = b""

    proc = subprocess.run(
        shlex.split(args.cmd),
        cwd=Path(args.cwd),
        input=input_data,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=args.timeout,
    )

    if args.stdout_file:
        Path(args.stdout_file).write_bytes(proc.stdout)
    else:
        sys.stdout.buffer.write(proc.stdout)
    if args.stderr_file:
        Path(args.stderr_file).write_bytes(proc.stderr)
    else:
        sys.stderr.buffer.write(proc.stderr)

    return proc.returncode


if __name__ == "__main__":
    raise SystemExit(main())
