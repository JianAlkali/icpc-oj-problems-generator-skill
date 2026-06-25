# Generate OJ Problem Skill

一个用于生成 OJ / ACM / OI 题目的 Codex Skill。它把一个题意灵感转成可验证、可归档、可产出的题目包，默认面向 [AlkaliOJ / AOJ](https://alkalibase.com/oj) JSON 格式，同时支持扩展到其他 OJ 产物格式。

## 使用方式

1. 给支持 Skill 的 Agent 添加本项目中的 `skills/generate-oj-problem`。
2. 直接告诉 AI 你的出题想法，例如：

```text
出一道珂朵莉树板子题，区间第 k 小、区间修改之类都给它整上。
```

3. 等待生成完成。默认 AOJ 产物模式下，会同时生成平台无关包和 AOJ 兼容产物：

```text
artifacts/package.json
artifacts/problem.json
artifacts/aoj/problem.json
```

过程文件、验证报告、源码、数据生成记录等会归档在：

```text
archive/
```

## 支持的题型

- 标准输入输出题
- Special Judge / 特判题
- 交互题
- 通信题 / Protocol 题

其中 AOJ 的特判、交互和通信题的参数读入、执行流程可能与其他 OJ 不一致；标准输入输出题通常更容易迁移。

## 主要特性

- 强制区分过程归档与最终产物。
- 禁止手工填写样例，样例必须可追溯到生成器、标准程序和 hash。
- 对拍、全枚举、边界、随机、大数据等验证步骤都要求显式 timeout。
- 支持展示样例筛选，避免样例只覆盖平凡情况。
- 支持平台无关 `package.json`、AOJ 单 JSON 产物和分散文件产物。
- 支持通过平台 adapter 描述 checker、interactor、mediator 和产物布局，便于迁移到其他 OJ。
- 提供阶段 checkpoint，帮助上下文较小的 Agent 在关键步骤重新读取规则。

## 产物模式

Skill 会先生成统一的过程文件，例如：

```text
description.json
tests/*.in
tests/*.out
provenance.json
reports/
```

然后在最后一步把它们转换到 `artifacts/` 下的目标产物格式。过程文件和最终产物是解耦的，因此可以复用同一套验证、对拍、样例追溯和归档逻辑。

当前内置的平台 adapter：

- `alkalibase-aoj`：默认 adapter，位于 `skills/generate-oj-problem/config/platforms/alkalibase-aoj.json`。
  它描述 AOJ 当前的 C++20 runner、custom checker 参数、interactive verdict 环境变量、protocol mediator 参数和平台产物路径。

无论目标平台如何，默认都会先生成平台无关包：

```text
artifacts/
  package.json
```

`package.json` 是迁移和二次 materialize 的稳定中间层，包含题面、限制、judge mode、checker/interactor/mediator source、平台 contract、测试数据和 artifact 路径。

当前内置两种产物模式：

- `aoj_json`：默认模式，生成一个适配 [AlkaliOJ / AOJ](https://alkalibase.com/oj) 的单文件 JSON。

```text
artifacts/
  package.json
  problem.json
  aoj/
    problem.json
```

其中 `artifacts/problem.json` 是兼容旧上传流程的 AOJ JSON，`artifacts/aoj/problem.json` 是 `alkalibase-aoj` adapter 下的平台产物。

- `split_files`：分散文件模式，适合需要单独管理题面、数据和源码的 OJ 或中间转换流程。

```text
artifacts/
  package.json
  statement.md
  metadata.json
  tests/
    01.in
    01.out
  sources/
    checker.cpp
    interactor.cpp
    mediator.cpp
    solution.cpp
```

通过修改 `config/defaults.json` 中的 `product_policy.mode` 可以切换默认产物模式。

## 对其他 OJ 的支持

如果你想适配其他 OJ，一般不需要改完整出题流程。推荐新增一个平台 adapter，并只在最终 materialize 阶段转换产物。

推荐步骤：

1. 在 `skills/generate-oj-problem/config/platforms/` 下新增平台配置，例如：

```text
skills/generate-oj-problem/config/platforms/example-oj.json
```

2. 在 adapter 中描述平台 contract，例如：

```json
{
  "platform": "example-oj",
  "runner": {
    "language": "cpp20",
    "compile": "g++ -std=c++20 -O2 -pipe",
    "sandbox": "example"
  },
  "contracts": {
    "custom_checker": {
      "argv": ["input_file", "user_output_file", "answer_file"]
    },
    "interactive": {
      "argv": ["input_file", "answer_file"],
      "communication": "stdin_stdout_bidirectional",
      "verdict_env": "EXAMPLE_VERDICT_FILE"
    },
    "protocol": {
      "mediator_argv": ["input_file", "first_user_output_file", "second_input_file_path"]
    }
  },
  "artifacts": {
    "universal_package": "package.json",
    "platform_json": "example/problem.json"
  }
}
```

3. 在 `config/defaults.json` 的 `product_policy.platform_adapter` 中切换默认 adapter，或调用 `scripts/materialize_product.py --platform-adapter <adapter.json>`。

4. 必要时在 `scripts/materialize_product.py` 中为该平台添加专门输出逻辑。不要改生成器、样例选择、provenance 或验证流程，除非通用 `package.json` schema 本身需要升级。

推荐保持内部流程不变：

```text
description.json + tests/*.in/out + provenance.json -> artifacts/package.json -> platform artifact
```

这样验证、对拍、归档和样例追溯逻辑都可以继续复用。

## 目录

```text
skills/generate-oj-problem/
  SKILL.md
  config/
    defaults.json
    platforms/
      alkalibase-aoj.json
  references/
  scripts/
```

根目录下的 `*.sample*.json` 和 `oj-problem-authoring.md` 是 AOJ 题型与字段参考。
