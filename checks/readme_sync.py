#!/usr/bin/env python3
"""Recompute the README number table. Fail if either language file drifts."""
from __future__ import annotations

import re
from pathlib import Path


KEYS = (
    "skill_directories",
    "skills_with_skill_md",
    "tool_scripts",
    "legacy_module_files",
    "plan_template_files",
    "package_version",
    "packaging_failures",
    "planted_violation_types",
    "violation_types_detected",
    "clean_fixture_false_positives",
    "figure_svg_sha256",
    "latex_compile",
)

SECTIONS = {
    "README.md": "## 结果数字（真实可复算）",
    "README_EN.md": "## Numbers recomputed by make check",
}


def counts(root: Path) -> dict[str, str]:
    skills = [path for path in (root / "skills").iterdir() if path.is_dir()]
    with_skill = [path for path in skills if (path / "SKILL.md").is_file()]
    scripts = [
        path
        for path in (root / "scripts").iterdir()
        if path.is_file() and path.suffix in {".py", ".ps1", ".sh"}
    ]
    modules = [
        path
        for path in (root / "modules").iterdir()
        if path.is_file() and path.suffix == ".md"
    ]
    plans = [path for path in (root / "plan-template").iterdir() if path.is_file()]
    return {
        "skill_directories": str(len(skills)),
        "skills_with_skill_md": str(len(with_skill)),
        "tool_scripts": str(len(scripts)),
        "legacy_module_files": str(len(modules)),
        "plan_template_files": str(len(plans)),
    }


def extract_section(text: str, heading: str) -> str:
    index = text.find(heading)
    if index < 0:
        raise ValueError(f"missing heading {heading}")
    rest = text[index + len(heading) :]
    match = re.search(r"\n## ", rest)
    return rest if match is None else rest[: match.start()]


def parse_table(section: str) -> dict[str, str]:
    found: dict[str, str] = {}
    for line in section.splitlines():
        stripped = line.strip()
        if not stripped.startswith("|"):
            continue
        cells = [cell.strip() for cell in stripped.strip("|").split("|")]
        if len(cells) != 2:
            continue
        key, value = cells
        if key in {"key", "---"} or set(key) <= set("-: "):
            continue
        found[key] = value
    return found


def strip_unchecked(text: str, heading: str) -> str:
    section = extract_section(text, heading)
    text = text.replace(heading + section, "\n", 1)
    text = re.sub(r"<!--.*?-->", "", text, flags=re.S)
    text = re.sub(r"```.*?```", "", text, flags=re.S)
    # Filenames and commands (`research_quality_gate.ps1`) are not measured results.
    text = re.sub(r"`[^`\n]+`", "", text)
    return text


def check_readmes(root: Path, computed: dict[str, str], skill_names: list[str]) -> list[str]:
    failures: list[str] = []
    if list(computed) != list(KEYS):
        failures.append("computed keys differ from the required key order")
    parsed: dict[str, dict[str, str]] = {}
    for filename, heading in SECTIONS.items():
        text = (root / filename).read_text(encoding="utf-8")
        try:
            section = extract_section(text, heading)
        except ValueError as exc:
            failures.append(f"{filename}: {exc}")
            continue
        table = parse_table(section)
        parsed[filename] = table
        if tuple(table) != KEYS:
            failures.append(f"{filename}: table keys {tuple(table)} != {KEYS}")
        for key in KEYS:
            if key in table and table[key] != computed[key]:
                failures.append(
                    f"{filename}: {key} is {table[key]!r}, recomputed {computed[key]!r}"
                )
        outside = strip_unchecked(text, heading)
        digit = re.search(r"\d", outside)
        if digit:
            start = max(0, digit.start() - 24)
            failures.append(
                f"{filename}: digit outside the number table: {outside[start:digit.end() + 24]!r}"
            )
        for name in skill_names:
            if name not in text:
                failures.append(f"{filename}: skill directory {name} is not listed")
        if "research_quality_gate.ps1" not in text:
            failures.append(f"{filename}: missing research_quality_gate.ps1")
        if "FAILURE_MODES.md" not in text:
            failures.append(f"{filename}: missing FAILURE_MODES.md link")
    english = (root / "README_EN.md").read_text(encoding="utf-8")
    version_line = f"Version: {computed['package_version']}"
    if version_line not in english:
        failures.append(f"README_EN.md missing {version_line!r}")
    if len(parsed) == 2:
        left, right = parsed.values()
        if left != right:
            failures.append("README.md and README_EN.md number tables differ")
    return failures
