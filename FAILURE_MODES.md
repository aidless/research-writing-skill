# Failure modes

This file lists what the mechanical check does not catch, and the claims that are still false if read from outside the README.

STATUS: WORK-IN-PROGRESS — not A yet. The README tables agree with `make check`. The GitHub About text does not, and this pull request cannot change it.

## What `make check` measures

- Packaging files parse, cited manifest keys are the ones used, referenced paths exist, and the Claude and Cursor manifests agree on shared metadata.
- Six planted manuscript defects, one per fixture, are detected by type. The clean fixture reports no defect. Codes:
  - `unmapped_claim`
  - `claim_literal_mismatch` (the literal text must match, so `0.50` and `0.5` differ)
  - `unresolved_citation`
  - `missing_figure_script`
  - `missing_data_file`
  - `data_hash_mismatch`
- `checks/figure/plot_series.py` regenerates one SVG. The committed sha256 is `b637d3d54a4667c483a078814c3cd9e96313a834a6cde04e17eec141a98482ed`.
- LaTeX in the environment where this was written: no `pdflatex`, `xelatex`, `lualatex`, or `tectonic` on `PATH`. README value `not_tested`. If a later machine has an engine, `make check` compiles `checks/latex/tiny.tex` and then requires the README value `passed`, or fails if the compile fails.

`planted_violation_types` is the number of non-empty expectation lists in `checks/fixtures/labels.json`. It is not a count of bugs in anyone's paper. `violation_types_detected` is how many of those fixtures the checker matched exactly on this run.

The expected codes were written with the fixtures. The sha256 values lock the bytes. `checks/run_check.py` does not rewrite the label file. A tampered clean expectation must make the run fail. This is a same-change specification, not a preregistration filed before the checker existed.

## What it does not measure

- Writing quality, user studies, acceptance, adoption, or model obedience. Skill markdown is instructions. Nothing here shows a model follows them.
- Unmarked numbers in prose. Only `{{claim:ID=LITERAL}}` is a numeric claim. A sentence such as "accuracy was 91%" with no marker is invisible to the checker.
- Narrative citations. Only `{{cite:KEY}}` is resolved. `(Smith, 2020)` is not.
- Whether a figure script reads the data file it names. The gate checks that the path exists and that the data bytes match the manifest hash. It does not execute the script.
- Matplotlib, PNG, or PDF figure bytes. Fonts and library versions change those bytes. The hashed artifact is the stdlib SVG only.
- The PowerShell manuscript gate `scripts/research_quality_gate.ps1`. It was not run. Linux CI does not install PowerShell for `make check`.
- Live loads of Claude Code, Cursor, Codex, OpenCode, or Gemini CLI. `claude plugin validate` was not run.
- OpenCode as a git plugin. Current docs require a package with an export entry. This repository has no `package.json`. Copying `SKILL.md` directories was not executed either.
- Codex discovery. The install note matches the documented one-directory-per-skill layout. Codex was not started.
- The author's end-to-end draft mentioned in the old README. That draft is not in this repository and was not repeated.
- Network tools: `scripts/scholar_search.py` calls `sys.exit` on import when `requests` is missing, and the search itself needs an API. `make check` does not import it. `eval/run_cases.py` does, so that older case file is not an offline check.
- `scripts/style_check.sh` needs `rg`. Without `rg` the script says so and does not silently prove a style pass. `make check` does not run it.

## Known disagreements and stale surfaces

- GitHub About (unchanged by this PR), read on 2026-11-16:

  科研写作助手（多平台 Skill）：头脑风暴定题、逐章写作与 LaTeX 产出，带证据映射与质量门控，适配 Claude Code/Cursor/Codex 等。

  Replacement text:

  科研写作流程的目录技能。离线检查了清单、机械门禁和一张可复算的图；未测写作质量，也未在各平台实机加载。

  English, if the About field is switched:

  Directory-packaged research-writing workflow. Offline checks cover manifests, a mechanical manuscript gate, and one deterministic figure. No writing-quality measurement and no live load on Claude Code, Cursor, Codex, OpenCode, or Gemini CLI.

  Topics were left as they are. `prompts` is a topic, not a measured result.

- `.github/workflows/pr-checks.yml` still runs `python -m compileall -q . || true` and `pip install ... || true`. A syntax error in that job can be swallowed. `make check` is a separate step and is not under `|| true`. The `ci.yml` verify job also runs `make check` without `|| true`.
- `.github/workflows/publish.yml` is named Publish to PyPI. There is no `pyproject.toml`, `setup.py`, or `setup.cfg`, so the build step skips and the publish step does not run. This repository is not a published Python package.
- The old Chinese and English READMEs named different QQ groups (`827924233` and `649198361`). Neither was re-checked. Both are removed.
- The old English README linked `img/*.png` and `img/qq-research-writing-group.jpg`. Those files are not in the tree. The links are removed. The Chinese README had already said the images were not shipped.
- The old Chinese README embedded one live arXiv reply inside a "five minute" example. That reply is not an offline result and is not repeated.
- Claude `SessionStart` matcher is `startup|clear|compact`. The cited hooks doc also lists `resume` and `fork`. Those sources may not inject context. `make check` records this as a note, not a failure.
- Dependabot pull requests #1, #2, #5, #6, and #7 were not merged and not installed here. See the PR description for the triage. Raising the PyMuPDF floor to 2.x is the one most likely to break `scripts/pdf_parser.py`, and that was not tested.

## Fresh clone

`make check` uses Python 3 and GNU make. It does not install `requirements.txt` and it does not use the network. On the machine that added the check (2026-11-16) the command finished in under one second, inside a 15 minute offline budget. Cloning the repository still needs a network; the check after that does not.

Digits inside inline code, such as the PowerShell filename, are not treated as results. A digit in ordinary prose outside the number table fails `make check`.
