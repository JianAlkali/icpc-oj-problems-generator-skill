---
name: generate-oj-problem
description: Generate rigorous ACM/OI/AOJ/OJ programming contest problems from an idea, formula, or rough statement. Use when Codex must create or improve batch, special-judge, interactive, or protocol problem packages with AOJ JSON or split-file artifacts, generated samples only, provenance manifests, validation gates, cleanup, artifacts, and archival.
---

# Generate OJ Problem

## Core Rule

Treat every output sample and hidden case as generated evidence, never as prose. Do not manually type, infer, edit, or "fix" any `input` or `output` in the final product; only copy data produced by the generator and solved/checked by the verified pipeline. Every runtime-uncertain command must have an explicit wall-clock timeout.

## Resources

- Read `config/defaults.json` first. It defines AOJ schema, judge modes, product modes, Markdown/LaTeX support, ambiguity handling, validation, sample selection, cleanup, artifacts, and archive paths.
- Read `references/oj-authoring.md` when choosing `judge_mode`, `checker_type`, `checker_source`, `interactor_source`, or `mediator_source`.
- Read `references/strictness.md` when designing generators, samples, visible samples, validation, or manual candidates.
- Read `references/architecture.md` when creating directories, materializing artifacts, or archiving process evidence.
- Re-read `references/checkpoints.md` before each major phase. If context is tight, run `scripts/show_step.py --step <name>` immediately before the phase.

## Scripts

- `scripts/stress.py`: compile/run/diff validation.
- `scripts/generate_cases.py`: `generator -> solution -> tests -> description.json` with provenance.
- `scripts/materialize_product.py`: write final deliverables under `artifacts/` in `aoj_json` or `split_files` mode.
- `scripts/safe_run.py`: refuse stdin-reading programs without input and require timeout.
- `scripts/select_visible_samples.py`: filter/reorder generated visible samples.
- `scripts/validate_package.py`: schema, provenance, timeout, visible sample, source-field, and artifact checks.
- `scripts/adopt_manual_candidate.py`: convert a human-proposed candidate input into a validated generated-output case.
- `scripts/all_dictionary.py`: deterministic IDs for exhaustive small structures.
- `scripts/archive_problem.py`: cleanup and archive process evidence under `archive/`.

## Workflow

1. `spec`: Load defaults and freeze ambiguity.
   - Choose `judge_mode`: `batch`, `interactive`, or `protocol`.
   - For special judge, use `judge_mode: batch` and `checker_type: custom`.
   - Choose `checker_type`: `token`, `exact`, or `custom`.
   - Choose product mode: `aoj_json` for one AOJ-compatible JSON, or `split_files` for `statement.md`, metadata, tests, and sources.
   - Freeze input/output, objective, constraints, indexing, tie-breaking, query semantics, multi-test policy, difficulty scale, product mode, and pipeline sources before generation.

2. `draft`: Create `description.draft.json`.
   - Use UTF-8 AOJ fields from `authoring_schema_policy`.
   - Include `judge_mode` and `checker_type`.
   - Include `checker_source`, `interactor_source`, and/or `mediator_source` when required. Empty source fields are allowed only when not needed.
   - Set `cases` to `[]`. Do not include final samples or outputs.
   - When Markdown/LaTeX are supported, use them in `description`.

3. `programs`: Implement required programs.
   - Required for normal generated-output tasks: `brute.cpp`, `slower_solution.cpp`, `solution.cpp`, `generator.cpp`.
   - Add `checker.cpp`, `validator.cpp`, `interactor.cpp`, or `mediator.cpp` as required by the chosen pipeline.
   - Custom checker receives `argv[1]=input`, `argv[2]=user output`, `argv[3]=answer`.
   - Interactive interactor receives `argv[1]=input`, `argv[2]=answer` and writes JSON verdict to `ALKALIBASE_VERDICT_FILE`.
   - Protocol mediator receives `argv[1]=input`, `argv[2]=first user output`, `argv[3]=second input file path`.

4. `all`: Implement exhaustive small generation.
   - `all` must be deterministic and complete for the frozen small domain.
   - Queries, graph/tree structures, permutations, and edge cases must follow `references/strictness.md`.

5. `validate`: Compile and validate.
   - Use explicit timeouts for every compile, generator, solver, checker, interactor, mediator, validator, and stress command.
   - Do not generate formal cases until all required gates pass.
   - Stop on counterexample, preserve it, fix code, and restart validation.

6. `cases`: Generate formal cases.
   - Use generated inputs and verified outputs only.
   - Run visible-sample filtering before finalization.
   - If a human-proposed small input is unavoidable, adopt it only through `adopt_manual_candidate.py`.

7. `finalize`: Finalize process JSON and validate package.
   - Keep `description.json`, `tests/`, `provenance.json`, reports, and source files as process evidence.
   - Ignore imported `cases[*].id`; do not depend on it locally.
   - Run `validate_package.py` and fix every failure.

8. `product-archive`: Materialize product and archive.
   - Run `materialize_product.py` to create `artifacts/`.
   - Run `archive_problem.py` to create `archive/`.
   - Final result must have two directories in the problem root: `artifacts/` for deliverables and `archive/` for process/evidence.

## Required Final Report

Include frozen spec summary, judge mode/checker type, product mode, artifact path, archive path, program list, test point table, visible-sample coverage, validation report, timeout limits, and final verdict.

If validation fails, do not output a final problem. Output the failing command, counterexample path, and next fix needed.
