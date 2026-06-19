# Phase Checkpoints

Before each phase, re-read only that phase's section. This is a context-window guardrail.

## spec

- Load `config/defaults.json`.
- Freeze judge mode, checker type, product mode, statement format support, difficulty scale, multi-test policy, constraints, objective, tie-breaking, query semantics, and pipeline source needs.
- Ask only unresolved high-risk ambiguity required by `ambiguity_policy`.

## draft

- Create UTF-8 `description.draft.json`.
- Use AOJ fields: title, tags array, difficulty, limits, visible_sample_count, judge_mode, checker_type, source fields, description, cases.
- Set `cases` to `[]`.
- Do not include final samples or hand-computed output.

## programs

- Implement generator, solution, brute, slower solution unless the selected problem type proves a different verification shape is needed.
- Implement validator/checker/interactor/mediator when the pipeline needs them.
- Do not run any stdin-reading executable without input and timeout.

## all

- `all` is complete for the declared small domain, not sampled.
- Use deterministic dictionaries for structures.
- Query tasks enumerate complete small query spaces.

## validate

- Compile everything with timeout.
- Validate all, boundary, rand, slower, checker, interactor, mediator, and validator as applicable.
- Stop on first counterexample or timeout.

## cases

- Generate formal cases only after validation passes.
- Official outputs come from verified solution or are accepted by custom checker semantics.
- Filter visible samples from generated cases; do not hand-fill them.

## finalize

- Normalize cases to `input` and `output`; ignore imported `id`.
- Ensure provenance has source, commands, timeout, files, and hashes.
- Run package validation before product materialization.

## product-archive

- Materialize final deliverables under `artifacts/`.
- Archive process evidence under `archive/`.
- Final answer must report both paths.
