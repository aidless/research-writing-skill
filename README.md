# 科研写作助手

STATUS: WORK-IN-PROGRESS — not A yet

> 目录化的论文写作流程技能。本仓库离线检查了清单文件、一套机械稿件门禁，和一张可复算的图。没有写作质量、录用或采用方面的测量，也没有在 Claude Code、Cursor、Codex、OpenCode 或 Gemini CLI 里实机加载。

[English](README_EN.md)

论文草稿如果只留在一轮对话里，数字、图和引用容易和出处脱节，过程也难恢复。
这个仓库是一组技能说明和脚本，要求计划文件、证据表和分章草稿。
下表只说明机械检查是否通过，不说明写出来的论文更好。

未测完的差距写在 [FAILURE_MODES.md](FAILURE_MODES.md)。

## 结果数字（真实可复算）

`make check` 用仓库文件重算下表。不一致就失败。不访问网络。

| key | value |
| --- | --- |
| skill_directories | 19 |
| skills_with_skill_md | 19 |
| tool_scripts | 8 |
| legacy_module_files | 14 |
| plan_template_files | 5 |
| package_version | 3.1.0 |
| packaging_failures | 0 |
| planted_violation_types | 6 |
| violation_types_detected | 6 |
| clean_fixture_false_positives | 0 |
| figure_svg_sha256 | b637d3d54a4667c483a078814c3cd9e96313a834a6cde04e17eec141a98482ed |
| latex_compile | not_tested |

机械检查尚未单独发版，包版本以上表为准。

## 这次实际跑了什么

这次检查的是机制，不是写作质量，也不是模型行为。

代码在 `checks/`。它不调用模型，也不给文章打分。

- 清单：每个技能目录都有 `SKILL.md`，且前置信息里的 `name` 与目录名一致；两个 `plugin.json` 的字段落在各自文档列出的键里，引用的路径在仓库中存在；两边的名称、版本、描述、许可、关键词、技能路径和仓库地址一致。
- 门禁：夹具稿里的 `{{claim:ID=字面量}}` 必须在证据表里有同一字面量；`{{cite:KEY}}` 必须能在 `.bib` 里找到；图清单里的脚本和数据文件必须存在，且数据文件的哈希与清单一致。期望的违反类型在写夹具时就定了，夹具字节用哈希锁住。
- 图：`checks/figure/plot_series.py` 只用标准库把固定 CSV 画成 SVG，再比对哈希。这不是 matplotlib 位图，也不是版面检查。

Windows 上另有稿件脚本 `scripts/research_quality_gate.ps1`。`make check` 不运行它，因为这里没有 PowerShell。

## 平台文件

| 平台 | 仓库里的文件 | 检查范围 |
| --- | --- | --- |
| Claude Code | `.claude-plugin/plugin.json`、`hooks/hooks.json` | 字段与路径；未运行 Claude Code |
| Cursor | `.cursor-plugin/plugin.json`、`hooks/hooks-cursor.json` | 字段与路径；未运行 Cursor |
| Codex | `skills/*/SKILL.md`、`.codex/INSTALL.md` | 前置信息与安装说明；未运行 Codex |
| OpenCode | `.opencode/INSTALL.md` | 写明本仓库没有 `package.json`，所以不是文档里的 git 插件包；未运行 OpenCode |
| Gemini CLI | `GEMINI.md` | 上下文文件存在，且 `@./` 引用的文件存在；未运行 Gemini CLI |

```bash
git clone https://github.com/aidless/research-writing-skill.git
cd research-writing-skill
make check
```

## 技能

- `skills/using-research-writing/`
- `skills/paper-orchestration/`
- `skills/brainstorming-research/`
- `skills/evidence-driven-writing/`
- `skills/writing-chapters/`
- `skills/experiment-results-planning/`
- `skills/latex-output/`
- `skills/literature-review/`
- `skills/figures-python/`
- `skills/figures-diagram/`
- `skills/peer-review/`
- `skills/statistical-analysis/`
- `skills/verification/`
- `skills/environment-setup/`
- `skills/prompts-collection/`
- `skills/writing-core/`
- `skills/writing-humanities/`
- `skills/writing-medical/`
- `skills/writing-law/`

旧说明在 `modules/`。计划模板在 `plan-template/`。

## 已撤回的说法

旧 README 写过比普通对话式写作工具更稳定，也写过各平台已经适配。这里没有对照实验，也没有实机加载记录，所以这两句删掉了。作者草稿跑通过一遍的说法，草稿不在本仓库，本次没有复跑。
