#!/usr/bin/env python3
"""Validate final OJ problem package invariants."""

from __future__ import annotations

import argparse
import ast
import fnmatch
import hashlib
import json
import re
from pathlib import Path


REQUIRED_FIELDS = [
    "title",
    "tags",
    "difficulty",
    "time_limit_s",
    "memory_limit_mb",
    "visible_sample_count",
    "judge_mode",
    "checker_type",
    "description",
    "cases",
]


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def match_any(path: Path, patterns: list[str]) -> bool:
    s = path.as_posix()
    return any(fnmatch.fnmatch(s, p) or fnmatch.fnmatch(path.name, p) for p in patterns)


def validate_sample_requirements(desc: dict, req_path: Path | None) -> list[str]:
    if req_path is None or not req_path.exists():
        return []
    data = load_json(req_path)
    reqs = data.get("requirements", data if isinstance(data, list) else [])
    visible = desc["cases"][: int(desc["visible_sample_count"])]
    errors = []
    for req in reqs:
        if req.get("enabled", True) is False:
            continue
        where = req.get("where", "output")
        min_count = int(req.get("min_count", 1))
        count = 0
        for case in visible:
            text = case.get(where, "")
            if "token" in req and req["token"] in text.split():
                count += 1
            elif "contains" in req and req["contains"] in text:
                count += 1
            elif "regex" in req and re.search(req["regex"], text, re.MULTILINE):
                count += 1
        if count < min_count:
            errors.append(f"visible requirement failed: {req.get('name', req)}")
    return errors


def case_output(case: dict, aliases: set[str]) -> str | None:
    output_value = case.get("output")
    if output_value is not None:
        return output_value
    for alias in aliases:
        if alias in case:
            return case[alias]
    return None


def normalize_case_keys(case: dict, ignored: set[str]) -> set[str]:
    keys = set(case.keys())
    return keys - ignored


def python_timeout_errors(path: Path, workdir: Path) -> list[str]:
    try:
        tree = ast.parse(path.read_text(encoding="utf-8"))
    except SyntaxError:
        return [f"cannot parse python helper: {path.relative_to(workdir)}"]
    errors = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        func = node.func
        is_subprocess_run = (
            isinstance(func, ast.Attribute)
            and func.attr in {"run", "Popen", "call", "check_call", "check_output"}
            and isinstance(func.value, ast.Name)
            and func.value.id == "subprocess"
        )
        if is_subprocess_run and not any(kw.arg == "timeout" for kw in node.keywords):
            errors.append(f"python subprocess call lacks timeout: {path.relative_to(workdir)}:{node.lineno}")
    return errors


def validate_case_provenance(desc: dict, prov_cases: list[dict], workdir: Path, aliases: set[str]) -> list[str]:
    errors = []
    cases = desc.get("cases", [])
    if len(prov_cases) != len(cases):
        errors.append(f"provenance case count {len(prov_cases)} does not match description cases {len(cases)}")
    for idx, (case, pcase) in enumerate(zip(cases, prov_cases), start=1):
        case_id = pcase.get("case_id", f"case {idx}")
        in_file = pcase.get("input_file")
        out_file = pcase.get("output_file")
        output_value = case_output(case, aliases)
        if not in_file or not (workdir / in_file).exists():
            errors.append(f"missing input file for {case_id}: {in_file}")
            continue
        if not out_file or not (workdir / out_file).exists():
            errors.append(f"missing output file for {case_id}: {out_file}")
            continue
        input_text = (workdir / in_file).read_bytes().decode("utf-8")
        output_text = (workdir / out_file).read_bytes().decode("utf-8")
        if case.get("input") != input_text:
            errors.append(f"description input differs from generated file for {case_id}")
        if output_value != output_text:
            errors.append(f"description output differs from generated file for {case_id}")
    return errors


def validate_artifacts(desc: dict, config: dict, workdir: Path, aliases: set[str]) -> list[str]:
    errors = []
    product = config.get("product_policy", {})
    artifacts = workdir / product.get("artifacts_dir", "artifacts")
    mode = product.get("mode", "aoj_json")
    if mode == "aoj_json":
        path = artifacts / product.get("aoj_json", {}).get("output_file", "problem.json")
        if not path.exists():
            return ["missing AOJ artifact JSON"]
        artifact = load_json(path)
        if artifact.get("cases") != [{"input": c.get("input", ""), "output": case_output(c, aliases) or ""} for c in desc.get("cases", [])]:
            errors.append("AOJ artifact cases differ from description.json")
    if mode == "split_files":
        split = product.get("split_files", {})
        for rel in [
            split.get("statement_file", "statement.md"),
            split.get("metadata_file", "metadata.json"),
        ]:
            if not (artifacts / rel).exists():
                errors.append(f"missing split artifact: {rel}")
        tests = artifacts / split.get("tests_dir", "tests")
        for idx, case in enumerate(desc.get("cases", []), start=1):
            stem = f"{idx:02d}"
            in_path = tests / f"{stem}.in"
            out_path = tests / f"{stem}.out"
            if not in_path.exists() or not out_path.exists():
                errors.append(f"missing split test artifact: {stem}.in/.out")
                continue
            if in_path.read_bytes().decode("utf-8") != case.get("input"):
                errors.append(f"split input artifact differs for case {idx}")
            if out_path.read_bytes().decode("utf-8") != (case_output(case, aliases) or ""):
                errors.append(f"split output artifact differs for case {idx}")
    return errors


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--workdir", default=".")
    ap.add_argument("--config", default=None)
    ap.add_argument("--description", default="description.json")
    ap.add_argument("--provenance", default="provenance.json")
    ap.add_argument("--sample-requirements", default=None)
    ap.add_argument("--require-artifacts", action="store_true")
    ap.add_argument("--finalized", action="store_true", help="Also enforce cleanup and preserved-file policy.")
    args = ap.parse_args()

    workdir = Path(args.workdir).resolve()
    desc = load_json(workdir / args.description)
    config = load_json(Path(args.config)) if args.config else {}
    errors: list[str] = []

    schema = config.get("authoring_schema_policy", {})
    missing_fields = [field for field in schema.get("required_common_fields", REQUIRED_FIELDS) if field not in desc]
    if missing_fields:
        errors.append(f"description missing required fields: {missing_fields}")
    if config.get("difficulty_policy", {}).get("description_json_output", {}).get("type") == "integer":
        if not isinstance(desc.get("difficulty"), int):
            errors.append("difficulty must be an integer under current difficulty_policy")
    if not isinstance(desc.get("title"), str) or not desc["title"].strip():
        errors.append("title must be a non-empty string")
    tags_type = schema.get("tags_type", "array")
    if tags_type == "array":
        if not isinstance(desc.get("tags"), list) or not all(isinstance(x, str) and x for x in desc.get("tags", [])):
            errors.append("tags must be a non-empty string array under AOJ schema")
    elif not isinstance(desc.get("tags"), str):
        errors.append("tags must be a comma-separated string")
    if not isinstance(desc.get("time_limit_s"), (int, float)) or desc["time_limit_s"] <= 0:
        errors.append("time_limit_s must be a positive number")
    if not isinstance(desc.get("memory_limit_mb"), int) or desc["memory_limit_mb"] <= 0:
        errors.append("memory_limit_mb must be a positive integer")
    if not isinstance(desc.get("description"), str) or not desc["description"].strip():
        errors.append("description must be a non-empty string")
    judge_mode = desc.get("judge_mode", "batch")
    checker_type = desc.get("checker_type", "token")
    if judge_mode not in schema.get("judge_modes", ["batch", "interactive", "protocol"]):
        errors.append(f"invalid judge_mode: {judge_mode}")
    if checker_type not in schema.get("checker_types", ["token", "exact", "custom"]):
        errors.append(f"invalid checker_type: {checker_type}")
    if checker_type == "custom" and not desc.get("checker_source"):
        errors.append("checker_type custom requires non-empty checker_source")
    if judge_mode == "interactive" and not desc.get("interactor_source"):
        errors.append("interactive mode requires non-empty interactor_source")
    if judge_mode == "protocol" and not desc.get("mediator_source"):
        errors.append("protocol mode requires non-empty mediator_source")

    allowed_case_keys = set(config.get("sample_policy", {}).get("case_object_allowed_keys", ["input", "output"]))
    ignored_case_keys = set(config.get("sample_policy", {}).get("case_object_ignored_keys", ["id"]))
    aliases = set(schema.get("legacy_output_aliases", []))
    for i, case in enumerate(desc.get("cases", []), start=1):
        effective = normalize_case_keys(case, ignored_case_keys)
        if "output" not in effective and effective & aliases:
            effective = (effective - aliases) | {"output"}
        if effective != allowed_case_keys:
            errors.append(f"case {i} keys must be {sorted(allowed_case_keys)}; ignored keys: {sorted(ignored_case_keys)}")
        output_value = case_output(case, aliases)
        if not isinstance(case.get("input"), str) or not isinstance(output_value, str):
            errors.append(f"case {i} input/output must be strings")

    visible_count = desc.get("visible_sample_count")
    if not isinstance(visible_count, int) or visible_count < 0 or visible_count > len(desc.get("cases", [])):
        errors.append("visible_sample_count must be an integer within cases length")

    prov_path = workdir / args.provenance
    if prov_path.exists():
        prov = load_json(prov_path)
        prov_cases = prov if isinstance(prov, list) else prov.get("cases", [])
        errors.extend(validate_case_provenance(desc, prov_cases, workdir, aliases))
        for pcase in prov_cases:
            for key in config.get("sample_policy", {}).get("provenance_fields", []):
                if key not in pcase:
                    errors.append(f"provenance case {pcase.get('case_id')} missing {key}")
            in_file = pcase.get("input_file")
            out_file = pcase.get("output_file")
            if in_file and (workdir / in_file).exists() and pcase.get("input_sha256") != sha256_bytes((workdir / in_file).read_bytes()):
                errors.append(f"input hash mismatch for {pcase.get('case_id')}")
            if out_file and (workdir / out_file).exists() and pcase.get("output_sha256") != sha256_bytes((workdir / out_file).read_bytes()):
                errors.append(f"output hash mismatch for {pcase.get('case_id')}")
    else:
        errors.append("missing provenance.json")

    if args.require_artifacts:
        errors.extend(validate_artifacts(desc, config, workdir, aliases))

    req_path = (workdir / args.sample_requirements) if args.sample_requirements else None
    errors.extend(validate_sample_requirements(desc, req_path))

    for path in workdir.rglob("*"):
        if path.is_file() and path.suffix == ".py":
            errors.extend(python_timeout_errors(path, workdir))

    if args.finalized:
        delete_globs = config.get("cleanup_policy", {}).get("delete_globs", [])
        preserve_globs = config.get("cleanup_policy", {}).get("preserve_globs", [])
        forbid_unpreserved = config.get("cleanup_policy", {}).get("forbid_unpreserved_files_after_finalization", False)
        for path in workdir.rglob("*"):
            if not path.is_file():
                continue
            rel = path.relative_to(workdir)
            if match_any(rel, delete_globs):
                errors.append(f"temporary/deletable artifact remains: {rel}")
            if forbid_unpreserved and not match_any(rel, preserve_globs) and not match_any(rel, delete_globs):
                errors.append(f"unpreserved artifact remains in final package: {rel}")

    if errors:
        print("PACKAGE_VALIDATION: FAIL")
        for err in errors:
            print(f"- {err}")
        raise SystemExit(1)
    print("PACKAGE_VALIDATION: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
