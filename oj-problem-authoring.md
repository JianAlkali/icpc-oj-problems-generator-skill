# OJ Problem Authoring

All problem JSON files must be UTF-8. Existing problems without pipeline fields are treated as normal batch problems with the built-in token checker.

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
  "description": "...",
  "cases": [
    {"input": "1 2\n", "output": "3\n"}
  ]
}
```

`cases[*].answer` and legacy `cases[*].expected_output` are accepted as aliases of `cases[*].output`.

## Batch Problems

Batch mode runs the user program once for each case:

```text
input -> user -> checker(answer) -> AC/WA
```

Supported `checker_type` values:

- `token`: built-in checker, ignores all whitespace differences.
- `exact`: built-in checker, compares exact text except final trailing newlines.
- `custom`: compile and run `checker_source`.

Custom checker source receives three arguments:

```text
argv[1] = input file
argv[2] = user output file
argv[3] = answer file
```

Exit code `0` means `AC`, exit code `1` means `WA`, any other exit code, timeout, or crash means `JE`.

## Interactive Problems

Interactive mode runs an interactor and the user program as connected processes:

```text
input, answer -> (interactor <-> user) -> AC/WA
```

Use:

```json
{
  "judge_mode": "interactive",
  "interactor_source": "..."
}
```

The interactor receives:

```text
argv[1] = input file
argv[2] = answer file
```

It talks to the user program through standard input/output. It must write a JSON verdict to the file named by the `ALKALIBASE_VERDICT_FILE` environment variable:

```json
{"status":"AC","detail":"ok"}
```

Allowed final statuses are `AC` and `WA`. If the interactor times out, crashes, fails to write a valid verdict, or returns an invalid status, the submission result is `JE`. User program TLE/RE/MLE is still treated as the user's result.

## Protocol Problems

Protocol mode runs the user program twice with a mediator between the runs:

```text
input -> user run1 -> mediator -> user run2 -> checker(answer) -> AC/WA
```

Use:

```json
{
  "judge_mode": "protocol",
  "checker_type": "token",
  "mediator_source": "..."
}
```

The mediator receives:

```text
argv[1] = input file
argv[2] = first user output file
argv[3] = second input file path
```

It should write the second-run input to stdout, or directly to `argv[3]`. Exit code `0` continues to the second user run. Exit code `1` means the first output is invalid and returns `WA`. Any other exit code, timeout, or crash returns `JE`.

The final second-run output is judged by the selected checker.

## Neutral Judge Results

`JU` means the judge runner is unavailable, for example Lima or the runner image cannot start.

`JE` means judge error: checker, interactor, mediator, or internal judge logic failed. `JU`, `JE`, and legacy `judge unavailable` are visible in the submission list but are neutral: they do not count as accepted or failed attempts.
