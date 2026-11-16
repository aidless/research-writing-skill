# Research Writing Assistant

STATUS: WORK-IN-PROGRESS — not A yet

> Directory-packaged workflow for research drafts. This repository offline-checks manifest files, one mechanical manuscript gate, and one regenerable figure. It does not measure writing quality, acceptance, or adoption, and it was not loaded in Claude Code, Cursor, Codex, OpenCode, or Gemini CLI.

[中文](README.md)

A chat draft is hard to resume, and its numbers, figures, and citations can drift from their sources.
This repository is a set of skill instructions and scripts that ask for plan files, an evidence table, and per-chapter drafts.
The table below says whether those mechanical checks pass. It does not say that the resulting papers are better.

Gaps that are still open are listed in [FAILURE_MODES.md](FAILURE_MODES.md).

## Numbers recomputed by make check

`make check` recomputes this table from the repository and fails on drift. It does not use the network.

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

Version: 3.1.0

The mechanical check is unreleased. The package version is the `package_version` row.

## What actually ran

This tests mechanics, not writing quality or LLM behavior.

The code is in `checks/`. It does not call a model and it does not score prose.

- Packaging: every skill directory has `SKILL.md` whose frontmatter `name` matches the directory; both `plugin.json` files use keys from the cited platform docs; referenced paths exist; name, version, description, license, keywords, skills path, and repository URL agree.
- Gate: in the fixture drafts, `{{claim:ID=LITERAL}}` must match an evidence-map row with that same literal; `{{cite:KEY}}` must resolve in a `.bib` file; each figure-manifest row must name a script and a data file, and the data file's content hash must match. Expected violation types were chosen when the fixtures were written. Fixture bytes are locked with a hash.
- Figure: `checks/figure/plot_series.py` turns a fixed CSV into an SVG with the standard library, then the hash is compared. This is not a matplotlib raster and not a layout check.

`scripts/research_quality_gate.ps1` is a separate Windows manuscript script. `make check` does not run it. PowerShell is not required here.

## Platform files

| Platform | Files in this repo | What was checked |
| --- | --- | --- |
| Claude Code | `.claude-plugin/plugin.json`, `hooks/hooks.json` | Fields and paths; Claude Code was not run |
| Cursor | `.cursor-plugin/plugin.json`, `hooks/hooks-cursor.json` | Fields and paths; Cursor was not run |
| Codex | `skills/*/SKILL.md`, `.codex/INSTALL.md` | Frontmatter and the install note; Codex was not run |
| OpenCode | `.opencode/INSTALL.md` | The note says this repository has no `package.json`, so it is not the documented git plugin package; OpenCode was not run |
| Gemini CLI | `GEMINI.md` | The context file exists and its `@./` imports exist; Gemini CLI was not run |

```bash
git clone https://github.com/aidless/research-writing-skill.git
cd research-writing-skill
make check
```

## Skills

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

Older notes are in `modules/`. Plan templates are in `plan-template/`.

## Claims withdrawn

The previous README said this skill is more reliable than ordinary conversational writing tools, and that the platforms above were already adapted. There is no comparison study and no record of a live load, so those sentences are gone. A pass over the author's own draft is not re-run here; that draft is not in the repository.
