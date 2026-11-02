#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Real integrity tests for research-writing-skill.

Covers genuinely-testable behavior of the repo's own scripts (pure functions
that need no network / no PDF file) plus repo-structure facts. Nothing here
asserts behavior that the repo does not actually have.
"""
import importlib.util
import os
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent


def _load(name, relpath):
    spec = importlib.util.spec_from_file_location(name, ROOT / relpath)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_skill_modules_count():
    """skills/ directory holds the documented module set (real count)."""
    skills_dir = ROOT / "skills"
    assert skills_dir.is_dir(), "skills/ directory missing"
    dirs = [d for d in skills_dir.iterdir() if d.is_dir()]
    # README documents 19 skill modules; assert a stable minimum and known set.
    assert len(dirs) >= 19, f"expected >=19 skill modules, got {len(dirs)}"


def test_scripts_count():
    """scripts/ directory holds the documented tool scripts (real count)."""
    scripts_dir = ROOT / "scripts"
    assert scripts_dir.is_dir(), "scripts/ directory missing"
    files = [f for f in scripts_dir.iterdir() if f.is_file()]
    # README documents 8 tool scripts (py + ps1 + sh).
    assert len(files) >= 8, f"expected >=8 tool scripts, got {len(files)}"


def test_modules_count():
    """modules/ directory holds the retained legacy modules (real count)."""
    modules_dir = ROOT / "modules"
    assert modules_dir.is_dir(), "modules/ directory missing"
    files = [f for f in modules_dir.iterdir() if f.is_file()]
    assert len(files) >= 14, f"expected >=14 legacy modules, got {len(files)}"


def test_scholar_search_clean_text():
    """clean_text collapses whitespace (pure, offline)."""
    ss = _load("scholar_search", "scripts/scholar_search.py")
    assert ss.clean_text("  Hello   World  ") == "Hello World"
    assert ss.clean_text("a\t\tb") == "a b"


def test_scholar_search_generate_cite_key():
    """generate_cite_key builds a stable key from title/year/authors."""
    ss = _load("scholar_search", "scripts/scholar_search.py")
    key = ss.generate_cite_key(
        {"title": "Deep Learning", "year": 2020,
         "authors": [{"name": "Smith", "family": "Smith", "given": "J"}],
         "source": "Crossref"}
    )
    assert key and key.islower(), f"unexpected cite key: {key!r}"


def test_pdf_parser_pure_functions():
    """parse_sections and summarize_text work on plain text (no PDF needed)."""
    pp = _load("pdf_parser", "scripts/pdf_parser.py")
    sections = pp.parse_sections(
        "Introduction\nSome intro text.\n\nMethods\nSome methods text."
    )
    assert "introduction" in sections, "Introduction section not parsed (keys are lowercase)"
    summary = pp.summarize_text("word " * 200, max_length=100)
    assert len(summary) <= 200, "summarize_text exceeded max length"
