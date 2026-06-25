# Project Architecture

Use this layout for each generated problem package:

```text
problem-slug/
  artifacts/
    package.json            # platform-neutral package
    problem.json            # aoj_json mode
    aoj/problem.json        # alkalibase-aoj platform output
    statement.md            # split_files mode
    metadata.json           # split_files mode
    tests/                  # split_files mode
    sources/                # split_files mode
  archive/
    process/                # archived evidence
  frozen_spec.md
  description.draft.json
  description.json
  brute.cpp
  slower_solution.cpp
  solution.cpp
  generator.cpp
  checker.cpp              # optional
  validator.cpp            # optional
  tests/
    01_all_small.in
    01_all_small.out
    02_boundary.in
    02_boundary.out
    ...
  reports/
    validation_report.md
    testpoints.md
  provenance.json
  sample_requirements.json   # optional, for visible sample filtering
  .tmp/                    # deleted after finalization
```

Final results are split into two directories in the original problem root:

- `artifacts/`: deliverables for upload or distribution.
- `archive/`: process evidence, validation reports, source programs, provenance, and final process JSON.

## File Roles

- `frozen_spec.md`: resolved choices before generation. If this changes, restart draft and validation.
- `description.draft.json`: statement and constraints with `cases: []`.
- `description.json`: final generated cases only.
- `generator.cpp`: supports `all`, `boundary`, `rand`, `big`, `boundary+big`.
- `provenance.json`: machine-readable trace for every sample and hidden case.
- `artifacts/package.json`: platform-neutral package for adapters and migrations.
- `artifacts/problem.json`: legacy AOJ one-file product when `product_policy.mode` is `aoj_json`.
- `artifacts/aoj/problem.json`: AOJ platform adapter output for `alkalibase-aoj`.
- `artifacts/statement.md`, `artifacts/metadata.json`, `artifacts/tests/*.in|*.out`, `artifacts/sources/*`: split-file product when `product_policy.mode` is `split_files`.
- `reports/validation_report.md`: compile, all, boundary, rand, slower-solution status.
- `reports/testpoints.md`: explains mode, args, scale, and target bug class for each case.

## Suggested Command Flow

```bash
python <skill>/scripts/stress.py --workdir . --rounds 10000 --timeout 30
python <skill>/scripts/generate_cases.py --workdir . --draft description.draft.json --out description.json --visible 2 --timeout 60 --case all --case boundary --case rand:1 --case big --case boundary+big
python <skill>/scripts/select_visible_samples.py --workdir . --description description.json --requirements sample_requirements.json
python <skill>/scripts/validate_package.py --workdir . --config <skill>/config/defaults.json --sample-requirements sample_requirements.json
python <skill>/scripts/materialize_product.py --workdir . --config <skill>/config/defaults.json --mode aoj_json --platform-adapter <skill>/config/platforms/alkalibase-aoj.json
python <skill>/scripts/validate_package.py --workdir . --config <skill>/config/defaults.json --sample-requirements sample_requirements.json --require-artifacts
python <skill>/scripts/archive_problem.py --workdir . --config <skill>/config/defaults.json --archive-root archive --slug process --finalized
python <skill>/scripts/validate_package.py --workdir . --config <skill>/config/defaults.json --sample-requirements sample_requirements.json --require-artifacts --finalized
```
