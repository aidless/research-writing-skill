#!/usr/bin/env python3
"""Tests for the offline mechanical check. Not a writing-quality eval."""
import importlib
import shutil
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "checks"))

gates = importlib.import_module("gates")
run_check = importlib.import_module("run_check")


def _manuscript(tmp_path: Path) -> Path:
    root = tmp_path / "paper"
    (root / "chapters").mkdir(parents=True)
    (root / "plan").mkdir()
    (root / "figures" / "data").mkdir(parents=True)
    (root / "refs").mkdir()
    (root / "chapters" / "01-introduction.md").write_text(
        "Held-out accuracy was {{claim:acc=0.91}}.\nBackground is {{cite:smith2020}}.\n",
        encoding="utf-8",
    )
    (root / "plan" / "evidence-map.md").write_text(
        "| claim_id | literal | source |\n| --- | --- | --- |\n| acc | 0.91 | bib:smith2020 |\n",
        encoding="utf-8",
    )
    (root / "refs" / "references.bib").write_text(
        "@article{smith2020,\n  title = {Example}\n}\n",
        encoding="utf-8",
    )
    (root / "figures" / "plot_fig1.py").write_text("# fixture\n", encoding="utf-8")
    data = root / "figures" / "data" / "fig1.csv"
    data.write_text("x,y\n1,2\n", encoding="utf-8")
    digest = __import__("hashlib").sha256(data.read_bytes()).hexdigest()
    (root / "figures" / "data-manifest.md").write_text(
        "| figure_id | script | data_file | sha256 |\n"
        "| --- | --- | --- | --- |\n"
        f"| fig1 | figures/plot_fig1.py | figures/data/fig1.csv | {digest} |\n",
        encoding="utf-8",
    )
    return root


def test_clean_manual_project_has_no_codes(tmp_path):
    assert gates.check_manuscript(_manuscript(tmp_path)) == []


def test_unmapped_claim_and_exact_literal(tmp_path):
    root = _manuscript(tmp_path)
    chapter = root / "chapters" / "01-introduction.md"
    chapter.write_text(
        chapter.read_text(encoding="utf-8") + "Extra {{claim:ghost=0.50}}.\n",
        encoding="utf-8",
    )
    assert gates.check_manuscript(root) == ["unmapped_claim"]
    chapter.write_text(
        "Held-out accuracy was {{claim:acc=0.50}}.\nBackground is {{cite:smith2020}}.\n",
        encoding="utf-8",
    )
    assert gates.check_manuscript(root) == ["claim_literal_mismatch"]


def test_fixture_bytes_are_locked():
    labels_path = ROOT / "checks" / "fixtures" / "labels.json"
    labels = __import__("json").loads(labels_path.read_text(encoding="utf-8"))
    fixtures = ROOT / "checks" / "fixtures" / "manuscripts"
    assert gates.evaluate(fixtures, labels) == []
    tampered = __import__("json").loads(__import__("json").dumps(labels))
    tampered["fixtures"]["clean"]["expected_codes"] = ["unmapped_claim"]
    failures = gates.evaluate(fixtures, tampered)
    assert any(item.startswith("clean:") for item in failures)


def test_tree_hash_changes_when_a_byte_changes(tmp_path):
    source = ROOT / "checks" / "fixtures" / "manuscripts" / "clean"
    copied = tmp_path / "clean"
    shutil.copytree(source, copied)
    before = gates.tree_sha256(copied)
    chapter = copied / "chapters" / "01-introduction.md"
    chapter.write_text(chapter.read_text(encoding="utf-8") + "\n", encoding="utf-8")
    assert gates.tree_sha256(copied) != before


def test_run_all_matches_readme():
    ok, report = run_check.run_all()
    assert ok, report
    assert "This tests mechanics, not writing quality or LLM behavior." in report
    assert "RESULT: pass" in report
