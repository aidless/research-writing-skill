#!/usr/bin/env python3
"""Deterministic manuscript checks. Mechanics only, not writing quality.

A numeric claim is the marker {{claim:ID=LITERAL}}. A citation marker is
{{cite:KEY}}. Unmarked prose numbers and narrative citations are ignored.
Figure rows must name a script, a data file, and the sha256 of that data
file. The script is not executed and is not checked for reading the file.
"""
from __future__ import annotations

import hashlib
import re
from pathlib import Path


CLAIM_RE = re.compile(r"\{\{claim:([A-Za-z][A-Za-z0-9_-]*)=([-+]?(?:\d+\.\d+|\d+))\}\}")
CITE_RE = re.compile(r"\{\{cite:([A-Za-z0-9_:-]+)\}\}")
BIB_RE = re.compile(r"(?m)^@\w+\{\s*([^,\s]+)")

CLAIM_COLUMNS = ("claim_id", "literal", "source")
FIGURE_COLUMNS = ("figure_id", "script", "data_file", "sha256")


def tree_sha256(root: Path) -> str:
    """Hash a fixture tree. Path order is sorted. Labels live outside the tree."""
    digest = hashlib.sha256()
    files = sorted(
        path
        for path in root.rglob("*")
        if path.is_file() and "__pycache__" not in path.parts and path.suffix != ".pyc"
    )
    for path in files:
        relative = path.relative_to(root).as_posix().encode("utf-8")
        data = path.read_bytes()
        digest.update(relative)
        digest.update(b"\n")
        digest.update(f"{len(data):016d}".encode("ascii"))
        digest.update(b"\n")
        digest.update(data)
        digest.update(b"\n")
    return digest.hexdigest()


def _parse_table(text: str, required: tuple[str, ...]) -> tuple[list[dict[str, str]] | None, str | None]:
    header: list[str] | None = None
    rows: list[dict[str, str]] = []
    for line in text.splitlines():
        stripped = line.strip()
        if not stripped.startswith("|"):
            continue
        cells = [cell.strip() for cell in stripped.strip("|").split("|")]
        if cells and all(cell and set(cell) <= set("-: ") for cell in cells):
            continue
        if header is None:
            header = cells
            continue
        if len(cells) < len(header):
            return None, "short table row"
        rows.append(dict(zip(header, cells)))
    if header is None:
        return None, "no table"
    missing = [name for name in required if name not in header]
    if missing:
        return None, "missing column " + ",".join(missing)
    return rows, None


def _inside(root: Path, relative: str) -> Path | None:
    if not relative or relative.startswith(("/", "\\")) or ".." in Path(relative).parts:
        return None
    candidate = (root / relative).resolve()
    try:
        candidate.relative_to(root.resolve())
    except ValueError:
        return None
    return candidate


def _chapter_text(root: Path) -> str:
    chapters = root / "chapters"
    if not chapters.is_dir():
        return ""
    parts = []
    for path in sorted(chapters.rglob("*.md")):
        parts.append(path.read_text(encoding="utf-8"))
    return "\n".join(parts)


def _bib_keys(root: Path) -> set[str]:
    keys: set[str] = set()
    refs = root / "refs"
    if not refs.is_dir():
        return keys
    for path in sorted(refs.glob("*.bib")):
        keys.update(BIB_RE.findall(path.read_text(encoding="utf-8")))
    return keys


def check_manuscript(root: Path) -> list[str]:
    """Return sorted violation type codes. Empty means no mechanical hit."""
    codes: set[str] = set()
    text = _chapter_text(root)
    claims = CLAIM_RE.findall(text)
    cites = CITE_RE.findall(text)
    bib_keys = _bib_keys(root)
    if cites and not bib_keys and not (root / "refs").is_dir():
        codes.add("missing_bibliography")

    evidence_path = root / "plan" / "evidence-map.md"
    evidence_rows: list[dict[str, str]] = []
    if claims and not evidence_path.is_file():
        codes.add("missing_evidence_map")
    elif evidence_path.is_file():
        parsed, error = _parse_table(evidence_path.read_text(encoding="utf-8"), CLAIM_COLUMNS)
        if error:
            codes.add("bad_evidence_map")
        else:
            evidence_rows = parsed or []

    by_id: dict[str, list[dict[str, str]]] = {}
    for row in evidence_rows:
        by_id.setdefault(row["claim_id"], []).append(row)
    for claim_id, group in by_id.items():
        if len(group) > 1:
            codes.add("duplicate_claim_id")

    for claim_id, literal in claims:
        group = by_id.get(claim_id)
        if not group:
            codes.add("unmapped_claim")
            continue
        if group[0]["literal"] != literal:
            codes.add("claim_literal_mismatch")
        source = group[0]["source"]
        if source.startswith("bib:"):
            if source[4:] not in bib_keys:
                codes.add("unresolved_citation")

    for key in cites:
        if key not in bib_keys:
            codes.add("unresolved_citation")

    manifest_path = root / "figures" / "data-manifest.md"
    if manifest_path.is_file():
        parsed, error = _parse_table(manifest_path.read_text(encoding="utf-8"), FIGURE_COLUMNS)
        if error:
            codes.add("bad_figure_manifest")
        else:
            for row in parsed or []:
                script = _inside(root, row["script"])
                data_file = _inside(root, row["data_file"])
                if script is None or data_file is None:
                    codes.add("path_escape")
                    continue
                if not script.is_file():
                    codes.add("missing_figure_script")
                if not data_file.is_file():
                    codes.add("missing_data_file")
                    continue
                actual = hashlib.sha256(data_file.read_bytes()).hexdigest()
                if actual != row["sha256"].strip().lower():
                    codes.add("data_hash_mismatch")
    return sorted(codes)


def evaluate(fixtures: Path, labels: dict, *, check_hash: bool = True) -> list[str]:
    """Compare checker output to frozen expected codes. Does not rewrite labels."""
    failures: list[str] = []
    declared = labels.get("fixtures")
    if not isinstance(declared, dict) or not declared:
        return ["labels.json has no fixtures"]
    for name, spec in declared.items():
        root = fixtures / name
        if not root.is_dir():
            failures.append(f"{name}: fixture directory missing")
            continue
        if check_hash:
            actual_hash = tree_sha256(root)
            if actual_hash != spec.get("sha256"):
                failures.append(
                    f"{name}: sha256 {actual_hash} != frozen {spec.get('sha256')}"
                )
        detected = check_manuscript(root)
        expected = list(spec.get("expected_codes") or [])
        if detected != expected:
            failures.append(f"{name}: detected {detected} != expected {expected}")
    return failures


def detection_report(fixtures: Path, labels: dict) -> list[str]:
    lines = []
    for name, spec in labels["fixtures"].items():
        detected = check_manuscript(fixtures / name)
        expected = list(spec.get("expected_codes") or [])
        lines.append(
            f"  {name}: expected={expected} detected={detected} match={detected == expected}"
        )
    return lines
