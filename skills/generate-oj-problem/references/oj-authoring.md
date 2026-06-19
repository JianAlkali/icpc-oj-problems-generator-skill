# AOJ Problem Authoring

All problem JSON files must be UTF-8. Imported server-owned `cases[*].id` may appear in samples and should be ignored by local validation and generation.

## Common Fields

```json
{
  "title": "A + B",
  "tags": ["入门"],
  "difficulty": 100,
  "time_limit_s": 1,
  "memory_limit_mb": 256,
  "visible_sample_count": 1,
  "judge_mode": "batch",
  "checker_type": "token",
  "checker_source": "",
  "interactor_source": "",
  "mediator_source": "",
  "description": "...",
  "cases": [
    {"input": "1 2\n", "output": "3\n"}
  ]
}
```

`cases[*].answer` and `cases[*].expected_output` are accepted by AOJ as aliases, but generated local products should normalize to `output`.

## Batch

`judge_mode: batch`.

Pipeline:

```text
input -> user -> checker(answer) -> AC/WA
```

Checker types:

- `token`: built-in whitespace-insensitive token checker.
- `exact`: built-in exact checker except final trailing newlines.
- `custom`: compile and run `checker_source`.

Custom checker arguments:

```text
argv[1] = input file
argv[2] = user output file
argv[3] = answer file
```

Exit code `0` means AC, `1` means WA, anything else means JE.

## Special Judge

Use `judge_mode: batch` plus `checker_type: custom` and non-empty `checker_source`.

For construction problems, official `output` may be one valid answer or canonical witness, but correctness must be decided by the custom checker.

## Interactive

Use `judge_mode: interactive` and non-empty `interactor_source`.

Pipeline:

```text
input, answer -> (interactor <-> user) -> AC/WA
```

Interactor arguments:

```text
argv[1] = input file
argv[2] = answer file
```

The interactor must write a verdict JSON to the path in `ALKALIBASE_VERDICT_FILE`:

```json
{"status":"AC","detail":"ok"}
```

Allowed statuses are `AC` and `WA`. Timeout, crash, missing/invalid verdict, or invalid status means JE.

## Protocol

Use `judge_mode: protocol` and non-empty `mediator_source`.

Pipeline:

```text
input -> user run1 -> mediator -> user run2 -> checker(answer) -> AC/WA
```

Mediator arguments:

```text
argv[1] = input file
argv[2] = first user output file
argv[3] = second input file path
```

The mediator writes second-run input to stdout or directly to `argv[3]`. Exit code `0` continues; `1` means first output invalid and returns WA; any other code, timeout, or crash means JE.

## Neutral Results

`JU` means judge runner unavailable. `JE` means checker/interactor/mediator/internal judge error. Both are neutral in submission statistics.
