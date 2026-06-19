# Strictness Rules

## Ambiguity Freeze

Before writing final problem files, resolve and freeze:

- Whether input uses `T`.
- Whether Markdown and LaTeX are supported in the target platform.
- Judge mode, checker type, product mode, and checker/interactor/mediator source requirements.
- Difficulty scale and exact difficulty value/mapping.
- Exact constraints and sum constraints.
- Graph direction, multiedge/self-loop policy, connectivity, indexing, and ordering.
- Query count, query types, valid parameters, updates vs offline semantics, and output per query.
- Tie-breaking, modulo, precision, impossible cases, and empty structures.

After freezing, do not silently change these decisions. If a contradiction appears, update `frozen_spec.md`, discard generated cases, and restart validation.

## Timeout Discipline

Every runtime-uncertain command must be run with an explicit wall-clock upper bound before launch. This includes:

- `generator all`, `generator big`, `generator boundary+big`, and any custom generator mode.
- Any brute, slower solution, official solution, checker, or validator invocation on generated data.
- Stress loops, exhaustive loops, formal case generation, and archive-time verification.

Use `timeout_policy` from `config/defaults.json` unless the frozen spec records stricter limits. If a command times out, stop immediately, save the input/log, and treat it as validation failure. Do not leave a long-running process unattended and do not continue by guessing that it would eventually finish.

## Program Input Discipline

Never run an executable directly when its source contains stdin reads such as `cin >>`, `scanf`, `getchar`, or `getline(cin)` unless an input file/stdin payload and a timeout are supplied. Prefer `scripts/safe_run.py`.

Forbidden:

```bash
./solution
```

Allowed:

```bash
python <skill>/scripts/safe_run.py --cmd ./solution --source solution.cpp --input-file tests/01.in --timeout 30
```

## No Manual Samples

Manual sample construction is forbidden. A case is valid only if:

1. Its input file was created by `generator.cpp` with recorded mode and arguments.
2. Its output file was created by the verified `solution.cpp`.
3. `provenance.json` records SHA-256 for both files.
4. The `description.json` case content byte-for-byte matches those files.

Do not type a small example into JSON. Do not use a sample from the statement unless the generator can reproduce it and provenance records that reproduction.

If a human-proposed small input is truly needed, save it as a candidate file only. It must pass `validator.cpp` when present, then `solution.cpp` must generate its output, and provenance must mark `source: manual_candidate_validated`. It still must not be manually typed into `description.json`.

## Visible Sample Coverage

Visible samples are not arbitrary first cases. Select them by filtering generated cases:

- If `n=1` can trigger special handling and `n>1` is valid, at least one visible sample must have `n>1`.
- If both `YES` and `NO` can appear, visible samples must include both.
- If the task has multiple output branches, include representative visible cases when generated candidates exist.

Use `scripts/select_visible_samples.py` with a problem-specific `sample_requirements.json`. If no generated case satisfies a required visible-sample condition, generate more cases; do not hand-fill a sample.

## Complete `all`

`all` must cover the declared small domain completely. It is not a collection of cute examples.

- Arrays: enumerate every length and every value vector in the small value domain.
- Permutations: enumerate every permutation for each small `n`.
- Trees: use a deterministic ID scheme. Prefer labeled trees via Prüfer sequences when vertex labels matter; use ordered rooted shapes only when the input truly ignores labels.
- Graphs: enumerate edge masks over the correct edge universe.
- Queries: for every base object, enumerate all legal query tuples and all legal query sequences/permutations for the small query limit.

When full Cartesian coverage is too large, shrink the small domain until full coverage fits. Do not sample.

## Structure ID Examples

Use deterministic IDs so `generator all 1 2 3 ...` means exact objects:

- Single vertex tree: ID 1.
- Two labeled vertices: ID 2.
- For labeled trees with `n >= 2`, map IDs through Prüfer sequences in lexicographic order. This distinguishes `1-2-3` from `1-3-2`.
- For undirected simple graphs, map ID to an edge bitmask over `(1,2),(1,3),...,(n-1,n)`.
- For directed simple graphs, map ID to a bitmask over ordered pairs `(i,j), i != j`.

`scripts/all_dictionary.py` provides these mappings and can be copied into or called by generators.

## Validation Gates

The final package is invalid unless all required gates pass:

```text
COMPILE: PASS
ALL: PASS
BOUNDARY: PASS
RAND(... rounds): PASS
TIMEOUTS: PASS
VISIBLE_SAMPLES: PASS
SLOWER_SOLUTION: PASS
FINAL_VERDICT: VERIFIED
```

If any gate fails, keep the counterexample and stop. Do not produce `description.json` with final cases.

## Product And Archive Separation

Do not treat process files as final deliverables. After validation:

- Put uploadable/distributable files in `artifacts/`.
- Put process evidence in `archive/`.
- Use `product_policy.mode` to choose AOJ one-file JSON or split-file output.
- Re-read checkpoint `product-archive` immediately before materializing or archiving.
