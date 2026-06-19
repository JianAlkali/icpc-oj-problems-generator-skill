# Generate OJ Problem Skill

一个用于生成 OJ / ACM / OI 题目的 Codex Skill。它把一个题意灵感转成可验证、可归档、可产出的题目包，默认面向 AOJ JSON 格式，同时支持扩展到其他 OJ 产物格式。

## 使用方式

1. 给支持 Skill 的 Agent 添加本项目中的 `skills/generate-oj-problem`。
2. 直接告诉 AI 你的出题想法，例如：

```text
出一道线段树板子题，区间第 k 小、区间修改之类都给它整上。
```

3. 等待生成完成。默认 AOJ 产物模式下，最终产物位于：

```text
artifacts/problem.json
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
- 支持 AOJ 单 JSON 产物和分散文件产物。
- 提供阶段 checkpoint，帮助上下文较小的 Agent 在关键步骤重新读取规则。

## 对其他 OJ 的支持

如果你想适配其他 OJ，一般不需要改完整出题流程，只需要新增一种“产物模式”。

例如要支持 Codeforces / Polygon 风格产物：

1. 在配置中将 `product_policy.allowed_modes` 增加所需产物名，例如：

```json
"codeforces_polygon"
```

2. 在 `product_policy` 下新增格式配置，例如：

```json
"codeforces_polygon": {
  "statement_file": "statement.md",
  "tests_dir": "tests",
  "answers_dir": "answers",
  "checker_file": "checker.cpp",
  "validator_file": "validator.cpp",
  "solution_file": "solution.cpp",
  "generator_file": "generator.cpp",
  "metadata_file": "problem.json",
  "rule": "Produce a Codeforces/Polygon-like package with statement, tests, answers, checker, validator, generator, and solution files separated."
}
```

3. 在产物生成脚本中为该模式添加对应输出逻辑。

推荐保持内部流程不变：

```text
description.json + tests/*.in/out + provenance.json
```

最后只在产物阶段转换为目标 OJ 所需格式。这样验证、对拍、归档和样例追溯逻辑都可以继续复用。

## 目录

```text
skills/generate-oj-problem/
  SKILL.md
  config/defaults.json
  references/
  scripts/
```

根目录下的 `*.sample*.json` 和 `oj-problem-authoring.md` 是 AOJ 题型与字段参考。
