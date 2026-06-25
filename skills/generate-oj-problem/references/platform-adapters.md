# Platform Adapters

Treat AOJ as one target platform, not as the universal problem format. Always keep a platform-neutral package available, then materialize platform-specific artifacts from it.

## Universal Package

`artifacts/package.json` is the stable interchange package. It should contain:

- `schema_version`
- `platform`
- `title`, `tags`, `difficulty`, limits, statement, and visible sample count
- `judge`: `mode`, `checker_type`, source fields, and platform contracts
- `cases`: normalized `input` and `output`
- `artifacts`: the selected platform output paths

Do not hand-edit `package.json`; generate it from `description.json` with `scripts/materialize_product.py`.

## Adapter Config

Place platform configs under `config/platforms/`. The first supported adapter is `config/platforms/alkalibase-aoj.json`.

Adapters define:

- runner language, compile command, and sandbox name
- custom checker argv and exit-code contract
- interactive argv, bidirectional communication, verdict environment variable, and verdict JSON contract
- protocol mediator argv, second-input delivery rule, and exit-code contract
- platform artifact paths

## Migration Rule

When targeting another OJ, add a new adapter config and materializer branch. Do not change generator, provenance, visible-sample selection, or package validation rules unless the universal package schema itself changes.

Keep legacy AOJ output (`artifacts/problem.json`) until all consuming tools have switched to the platform-specific path (`artifacts/aoj/problem.json`) or the universal package.
