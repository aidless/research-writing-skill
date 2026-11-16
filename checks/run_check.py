#!/usr/bin/env python3
"""Offline mechanical check. Recomputes the README number table.

This tests mechanics, not writing quality or LLM behavior.
"""
from __future__ import annotations

import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import figures  # noqa: E402
import gates  # noqa: E402
import packaging  # noqa: E402
import readme_sync  # noqa: E402


ROOT = Path(__file__).resolve().parents[1]
LABELS = ROOT / "checks" / "fixtures" / "labels.json"
FIXTURES = ROOT / "checks" / "fixtures" / "manuscripts"
LATEX = ROOT / "checks" / "latex" / "tiny.tex"


def _latex_status() -> tuple[str, str | None]:
    for engine in ("pdflatex", "xelatex", "lualatex", "tectonic"):
        if shutil.which(engine):
            break
    else:
        return "not_tested", "no pdflatex, xelatex, lualatex, or tectonic on PATH"
    with tempfile.TemporaryDirectory() as tmp:
        destination = Path(tmp)
        source = destination / "tiny.tex"
        source.write_text(LATEX.read_text(encoding="utf-8"), encoding="utf-8")
        if engine == "tectonic":
            command = ["tectonic", "--outdir", str(destination), str(source)]
        else:
            command = [
                engine,
                "-interaction=nonstopmode",
                "-halt-on-error",
                f"-output-directory={destination}",
                source.name,
            ]
        completed = subprocess.run(
            command,
            cwd=destination,
            check=False,
            capture_output=True,
            text=True,
        )
        pdf = destination / "tiny.pdf"
        if completed.returncode != 0 or not pdf.is_file():
            tail = (completed.stdout or completed.stderr or "").strip().splitlines()
            detail = tail[-1] if tail else "no output"
            return "failed", f"{engine} failed: {detail}"
    return "passed", f"compiled with {engine}"


def _gate_numbers(labels: dict) -> tuple[dict[str, str], list[str]]:
    failures = gates.evaluate(FIXTURES, labels)
    planted = 0
    detected = 0
    clean_false = 0
    for name, spec in labels["fixtures"].items():
        expected = list(spec.get("expected_codes") or [])
        actual = gates.check_manuscript(FIXTURES / name)
        if name == "clean":
            clean_false = len(actual)
        if expected:
            planted += 1
            if actual == expected and not any(item.startswith(f"{name}:") for item in failures):
                detected += 1
    numbers = {
        "planted_violation_types": str(planted),
        "violation_types_detected": str(detected),
        "clean_fixture_false_positives": str(clean_false),
    }
    return numbers, failures


def run_all() -> tuple[bool, str]:
    lines: list[str] = [
        "This tests mechanics, not writing quality or LLM behavior.",
    ]
    packaging_failures, notes, version, skill_names = packaging.check_packaging(ROOT)
    lines.append(f"packaging_failures: {len(packaging_failures)}")
    for item in packaging_failures:
        lines.append(f"  FAIL {item}")
    for item in notes:
        lines.append(f"  note: {item}")

    labels = json.loads(LABELS.read_text(encoding="utf-8"))
    gate_numbers, gate_failures = _gate_numbers(labels)
    lines.append("gate fixtures:")
    lines.extend(gates.detection_report(FIXTURES, labels))
    tampered = json.loads(json.dumps(labels))
    tampered["fixtures"]["clean"]["expected_codes"] = ["unmapped_claim"]
    tamper_failures = gates.evaluate(FIXTURES, tampered)
    selftest_ok = any(item.startswith("clean:") and "expected" in item for item in tamper_failures)
    lines.append(f"label selftest rejects a wrong clean expectation: {selftest_ok}")
    if not selftest_ok:
        gate_failures.append("selftest accepted a tampered clean label")
    for item in gate_failures:
        lines.append(f"  FAIL {item}")

    try:
        figure_hash = figures.regenerated_sha256()
        locked = figures.locked_sha256()
    except (OSError, RuntimeError) as exc:
        figure_hash = ""
        locked = ""
        gate_failures.append(f"figure regeneration failed: {exc}")
    figure_ok = bool(figure_hash) and figure_hash == locked
    lines.append(f"figure_svg_sha256: {figure_hash}")
    lines.append(f"figure lock match: {figure_ok}")
    if not figure_ok:
        gate_failures.append(f"figure hash {figure_hash} != {figures.EXPECTED} ({locked})")

    latex_value, latex_detail = _latex_status()
    lines.append(f"latex_compile: {latex_value}")
    if latex_detail:
        lines.append(f"  note: {latex_detail}")
    if latex_value == "failed":
        gate_failures.append("LaTeX engine was present and the tiny document failed")

    computed = readme_sync.counts(ROOT)
    computed["package_version"] = version
    computed["packaging_failures"] = str(len(packaging_failures))
    computed.update(gate_numbers)
    computed["figure_svg_sha256"] = figure_hash
    computed["latex_compile"] = latex_value
    ordered = {key: computed[key] for key in readme_sync.KEYS}
    readme_failures = readme_sync.check_readmes(ROOT, ordered, skill_names)
    for item in readme_failures:
        lines.append(f"  FAIL {item}")

    ok = not packaging_failures and not gate_failures and not readme_failures and selftest_ok and figure_ok
    lines.append("RESULT: pass" if ok else "RESULT: fail")
    return ok, "\n".join(lines) + "\n"


def main() -> int:
    ok, report = run_all()
    sys.stdout.write(report)
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
