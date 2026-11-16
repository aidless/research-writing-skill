# Codex

This file is an install note. Codex was not executed in this check.

A Codex skill is a directory whose root contains `SKILL.md` with `name` and `description` frontmatter. Documented locations include `.agents/skills/<name>/SKILL.md` and `~/.agents/skills/<name>/SKILL.md`.

Sources consulted on 2026-11-16:

- https://developers.openai.com/plugins/build/skills
- https://learn.chatgpt.com/docs/build-skills

This repository stores those directories at `skills/<name>/`. Symlinking the parent `skills/` directory onto one skill name does not put `SKILL.md` at that skill root, so that layout is not the documented one.

Clone the repository that contains these files:

```bash
git clone https://github.com/aidless/research-writing-skill.git
```

Then link or copy each skill directory into `.agents/skills/<name>`:

```bash
mkdir -p .agents/skills
for d in skills/*; do
  ln -s "$(pwd)/$d" ".agents/skills/$(basename "$d")"
done
```

The loop was not run here. It only mirrors the documented one-directory-per-skill layout.
