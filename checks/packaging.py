#!/usr/bin/env python3
"""Packaging conformance for files this repo actually ships.

Schema checks follow public docs fetched on 2026-11-16. They do not load
Claude Code, Cursor, Codex, OpenCode, or Gemini CLI.

Docs:
- Claude manifest: https://code.claude.com/docs/en/plugins/manifest-reference
- Claude hooks: https://code.claude.com/docs/en/hooks
- Cursor manifest schema: https://raw.githubusercontent.com/cursor/plugins/main/schemas/plugin.schema.json
- Cursor hooks: https://cursor.com/docs/hooks
- Codex skills: https://developers.openai.com/plugins/build/skills
- Gemini context: https://geminicli.com/docs/cli/gemini-md/
- OpenCode plugins: https://opencode.ai/docs/plugins/
- OpenCode skills: https://opencode.ai/docs/skills/
"""
from __future__ import annotations

import json
import re
import subprocess
from pathlib import Path


CLAUDE_KEYS = {
    "$schema",
    "name",
    "displayName",
    "version",
    "description",
    "author",
    "homepage",
    "repository",
    "license",
    "keywords",
    "skills",
    "commands",
    "agents",
    "hooks",
    "mcpServers",
    "lspServers",
}
CLAUDE_AUTHOR_KEYS = {"name", "email", "url"}
CURSOR_KEYS = {
    "name",
    "displayName",
    "description",
    "version",
    "minClientVersions",
    "author",
    "publisher",
    "homepage",
    "repository",
    "license",
    "logo",
    "keywords",
    "category",
    "tags",
    "commands",
    "agents",
    "skills",
    "rules",
    "hooks",
    "variables",
    "mcpServers",
}
CURSOR_AUTHOR_KEYS = {"name", "email"}
CURSOR_HOOKS = {
    "sessionStart",
    "sessionEnd",
    "preToolUse",
    "postToolUse",
    "postToolUseFailure",
    "subagentStart",
    "subagentStop",
    "beforeShellExecution",
    "afterShellExecution",
    "beforeMCPExecution",
    "afterMCPExecution",
    "beforeReadFile",
    "afterFileEdit",
    "beforeSubmitPrompt",
    "preCompact",
    "stop",
    "afterAgentResponse",
    "afterAgentThought",
    "beforeTabFileRead",
    "afterTabFileEdit",
    "workspaceOpen",
}
CLAUDE_HOOKS = {
    "SessionStart",
    "SessionEnd",
    "PreToolUse",
    "PostToolUse",
    "UserPromptSubmit",
    "Stop",
    "SubagentStart",
    "SubagentStop",
    "PreCompact",
    "PostCompact",
    "Notification",
}
SKILL_NAME_RE = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")
KEBAB_RE = re.compile(r"^[a-z0-9]([a-z0-9.-]*[a-z0-9])?$")
SHARED_FIELDS = (
    "name",
    "displayName",
    "description",
    "version",
    "license",
    "keywords",
    "skills",
    "homepage",
    "repository",
    "author",
)


def _load_json(path: Path, failures: list[str]) -> dict | None:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        failures.append(f"{path}: invalid JSON ({exc})")
        return None
    if not isinstance(data, dict):
        failures.append(f"{path}: JSON value is not an object")
        return None
    return data


def _frontmatter(text: str) -> dict[str, str] | None:
    if text.startswith("\ufeff"):
        text = text[1:]
    if not text.startswith("---"):
        return None
    end = text.find("\n---", 3)
    if end < 0:
        return None
    data: dict[str, str] = {}
    for line in text[3:end].splitlines():
        if not line.strip() or line.lstrip().startswith("#") or ":" not in line:
            continue
        key, value = line.split(":", 1)
        data[key.strip()] = value.strip().strip("\"'")
    return data


def _repo_file(root: Path, value: str) -> Path | None:
    raw = value.strip()
    if raw.startswith(("http://", "https://")):
        return None
    if raw.startswith("./"):
        raw = raw[2:]
    raw = raw.rstrip("/")
    if not raw or ".." in Path(raw).parts:
        return None
    candidate = (root / raw).resolve()
    try:
        candidate.relative_to(root.resolve())
    except ValueError:
        return None
    return candidate


def _check_author(label: str, author: object, allowed: set[str], failures: list[str]) -> None:
    if not isinstance(author, dict) or "name" not in author or not str(author.get("name", "")).strip():
        failures.append(f"{label}: author.name is required")
        return
    unknown = set(author) - allowed
    if unknown:
        failures.append(f"{label}: author has undocumented keys {sorted(unknown)}")


def _check_skills(root: Path, failures: list[str]) -> list[str]:
    names: list[str] = []
    skills = root / "skills"
    if not skills.is_dir():
        failures.append("skills/ directory missing")
        return names
    for directory in sorted(path for path in skills.iterdir() if path.is_dir()):
        skill_md = directory / "SKILL.md"
        names.append(directory.name)
        if not skill_md.is_file():
            failures.append(f"{directory.name}: missing SKILL.md")
            continue
        meta = _frontmatter(skill_md.read_text(encoding="utf-8"))
        if not meta:
            failures.append(f"{skill_md}: missing YAML frontmatter")
            continue
        name = meta.get("name", "")
        description = meta.get("description", "")
        if not SKILL_NAME_RE.fullmatch(name):
            failures.append(f"{skill_md}: name {name!r} is not kebab-case")
        if name != directory.name:
            failures.append(f"{skill_md}: name {name!r} != directory {directory.name}")
        if not description:
            failures.append(f"{skill_md}: description is empty")
    root_skill = root / "SKILL.md"
    if not root_skill.is_file():
        failures.append("SKILL.md missing at repository root")
    else:
        meta = _frontmatter(root_skill.read_text(encoding="utf-8"))
        if not meta or not meta.get("name") or not meta.get("description"):
            failures.append("SKILL.md: root frontmatter needs name and description")
    return names


def _check_claude_hooks(root: Path, path: Path, failures: list[str], notes: list[str]) -> None:
    data = _load_json(path, failures)
    if data is None:
        return
    hooks = data.get("hooks")
    if not isinstance(hooks, dict) or not hooks:
        failures.append(f"{path}: hooks object missing")
        return
    for event, groups in hooks.items():
        if event not in CLAUDE_HOOKS:
            failures.append(f"{path}: {event} is not in the cited Claude hook event list")
        if not isinstance(groups, list):
            failures.append(f"{path}: {event} is not a list")
            continue
        for group in groups:
            if not isinstance(group, dict) or not isinstance(group.get("hooks"), list):
                failures.append(f"{path}: {event} entry needs a hooks list")
                continue
            matcher = group.get("matcher")
            if event == "SessionStart" and isinstance(matcher, str):
                if "resume" not in matcher or "fork" not in matcher:
                    notes.append(
                        "Claude SessionStart matcher does not list resume and fork "
                        "(https://code.claude.com/docs/en/hooks). Not a schema failure."
                    )
            for hook in group["hooks"]:
                if not isinstance(hook, dict) or hook.get("type") != "command":
                    failures.append(f"{path}: hook type must be command")
                    continue
                command = str(hook.get("command", ""))
                if not command.strip():
                    failures.append(f"{path}: empty hook command")
                for relative in re.findall(r"hooks/[\w./-]+", command):
                    if not (root / relative).is_file():
                        failures.append(f"{path}: command references missing {relative}")


def _check_cursor_hooks(root: Path, path: Path, failures: list[str]) -> None:
    data = _load_json(path, failures)
    if data is None:
        return
    version = data.get("version")
    if not isinstance(version, int) or version < 1:
        failures.append(f"{path}: version must be a positive integer (Cursor hooks docs)")
    hooks = data.get("hooks")
    if not isinstance(hooks, dict) or not hooks:
        failures.append(f"{path}: hooks object missing")
        return
    for event, entries in hooks.items():
        if event not in CURSOR_HOOKS:
            failures.append(f"{path}: {event} is not in the cited Cursor hook event list")
        if not isinstance(entries, list):
            failures.append(f"{path}: {event} is not a list")
            continue
        for entry in entries:
            if not isinstance(entry, dict) or not str(entry.get("command", "")).strip():
                failures.append(f"{path}: {event} entry needs a command")
                continue
            command = str(entry["command"])
            if command.startswith("./"):
                target = _repo_file(root, command.split()[0])
                if target is None or not target.is_file():
                    failures.append(f"{path}: command file missing: {command}")


def _origin_url(root: Path) -> str | None:
    try:
        completed = subprocess.run(
            ["git", "remote", "get-url", "origin"],
            cwd=root,
            check=False,
            capture_output=True,
            text=True,
        )
    except OSError:
        return None
    if completed.returncode != 0:
        return None
    url = completed.stdout.strip()
    url = re.sub(r"https://[^@/]+@", "https://", url)
    url = re.sub(r"\.git$", "", url)
    return url.rstrip("/")


def _bash_syntax(root: Path, relative: str, failures: list[str]) -> None:
    path = root / relative
    if not path.is_file():
        failures.append(f"missing {relative}")
        return
    completed = subprocess.run(
        ["bash", "-n", str(path)],
        check=False,
        capture_output=True,
        text=True,
    )
    if completed.returncode != 0:
        failures.append(f"{relative}: bash -n failed: {completed.stderr.strip()}")


def check_packaging(root: Path) -> tuple[list[str], list[str], str, list[str]]:
    failures: list[str] = []
    notes: list[str] = [
        "Platform products were not launched. File and schema checks only.",
        "claude plugin validate was not run.",
    ]
    skill_names = _check_skills(root, failures)
    claude_path = root / ".claude-plugin" / "plugin.json"
    cursor_path = root / ".cursor-plugin" / "plugin.json"
    claude = _load_json(claude_path, failures)
    cursor = _load_json(cursor_path, failures)
    repository = ""
    if claude is not None:
        unknown = set(claude) - CLAUDE_KEYS
        if unknown:
            failures.append(f"Claude manifest has keys outside the cited field list: {sorted(unknown)}")
        name = str(claude.get("name", ""))
        if not KEBAB_RE.fullmatch(name):
            failures.append(f"Claude manifest name {name!r} is not kebab-case")
        _check_author("Claude manifest", claude.get("author"), CLAUDE_AUTHOR_KEYS, failures)
        for field in ("skills", "hooks"):
            value = claude.get(field)
            if not isinstance(value, str):
                failures.append(f"Claude manifest {field} must be a path string in this repo")
                continue
            target = _repo_file(root, value)
            if target is None or not target.exists():
                failures.append(f"Claude manifest {field} path missing: {value}")
            elif field == "hooks":
                _check_claude_hooks(root, target, failures, notes)
        repository = str(claude.get("repository", "")).rstrip("/")
    if cursor is not None:
        unknown = set(cursor) - CURSOR_KEYS
        if unknown:
            failures.append(f"Cursor manifest has keys outside the cited schema: {sorted(unknown)}")
        name = str(cursor.get("name", ""))
        if not KEBAB_RE.fullmatch(name):
            failures.append(f"Cursor manifest name {name!r} fails the cited name pattern")
        _check_author("Cursor manifest", cursor.get("author"), CURSOR_AUTHOR_KEYS, failures)
        for field in ("skills", "hooks"):
            value = cursor.get(field)
            if not isinstance(value, str):
                failures.append(f"Cursor manifest {field} must be a path string in this repo")
                continue
            target = _repo_file(root, value)
            if target is None or not target.exists():
                failures.append(f"Cursor manifest {field} path missing: {value}")
            elif field == "hooks":
                _check_cursor_hooks(root, target, failures)
    if claude is not None and cursor is not None:
        for field in SHARED_FIELDS:
            if claude.get(field) != cursor.get(field):
                failures.append(f"Claude and Cursor manifests disagree on {field}")
        if "hooks" in claude and claude.get("hooks") == cursor.get("hooks"):
            failures.append("Claude and Cursor hook files are the same path; their schemas differ")
    version = str((claude or {}).get("version", ""))
    changelog = (root / "CHANGELOG.md").read_text(encoding="utf-8")
    released = re.search(r"(?m)^## \[(\d+\.\d+\.\d+)\]", changelog)
    if released is None or released.group(1) != version:
        failures.append(f"CHANGELOG released version != manifest version {version}")
    origin = _origin_url(root)
    if origin and repository and origin != repository:
        failures.append(f"git origin {origin} != manifest repository {repository}")
    banned = "github.com/Norman-bury/research-writing-skill"
    checked_docs = [
        root / "README.md",
        root / "README_EN.md",
        root / ".codex" / "INSTALL.md",
        root / ".opencode" / "INSTALL.md",
        claude_path,
        cursor_path,
    ]
    for path in checked_docs:
        if path.is_file() and banned in path.read_text(encoding="utf-8"):
            failures.append(f"{path.relative_to(root)} still points at {banned}")
        if path.is_file() and repository and path.suffix == ".md" and repository not in path.read_text(encoding="utf-8"):
            failures.append(f"{path.relative_to(root)} does not contain manifest repository URL")
    codex = root / ".codex" / "INSTALL.md"
    if not codex.is_file():
        failures.append(".codex/INSTALL.md missing")
    else:
        text = codex.read_text(encoding="utf-8")
        if "was not executed" not in text:
            failures.append(".codex/INSTALL.md must say Codex was not executed")
        if ".agents/skills/<name>" not in text:
            failures.append(".codex/INSTALL.md must describe .agents/skills/<name>")
        if "ln -s ~/.codex/research-writing-skill/skills ~/.agents/skills/research-writing" in text:
            failures.append(".codex/INSTALL.md still symlinks the parent skills directory as one skill")
    opencode = root / ".opencode" / "INSTALL.md"
    package_json = root / "package.json"
    if not opencode.is_file():
        failures.append(".opencode/INSTALL.md missing")
    else:
        text = opencode.read_text(encoding="utf-8")
        if "was not executed" not in text:
            failures.append(".opencode/INSTALL.md must say OpenCode was not executed")
        if package_json.exists() and "no package.json" in text:
            failures.append("package.json exists but OpenCode install doc says it does not")
        if not package_json.exists() and "no package.json" not in text:
            failures.append(".opencode/INSTALL.md must say this repository has no package.json")
        if "自动安装并注册" in text or "research-writing-assistant@git+" in text:
            failures.append(".opencode/INSTALL.md still claims automatic git-plugin registration")
        if not package_json.exists():
            notes.append(
                "OpenCode git plugin install is not validated: this repository has no package.json "
                "(https://opencode.ai/docs/plugins/)."
            )
    gemini = root / "GEMINI.md"
    if not gemini.is_file() or not gemini.read_text(encoding="utf-8").strip():
        failures.append("GEMINI.md missing or empty")
    else:
        for relative in re.findall(r"@(\./[^\s)]+)", gemini.read_text(encoding="utf-8")):
            target = _repo_file(root, relative)
            if target is None or not target.is_file():
                failures.append(f"GEMINI.md import missing: {relative}")
        notes.append(
            "GEMINI.md is a context file (https://geminicli.com/docs/cli/gemini-md/). Gemini CLI was not run."
        )
    if not (root / "AGENTS.md").is_file():
        failures.append("AGENTS.md missing")
    else:
        notes.append("AGENTS.md has no platform manifest schema. Existence only.")
    _bash_syntax(root, "hooks/session-start", failures)
    if not (root / "hooks" / "run-hook.cmd").is_file():
        failures.append("hooks/run-hook.cmd missing")
    return failures, notes, version, skill_names
