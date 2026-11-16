# OpenCode

OpenCode was not executed in this check.

This repository has no package.json. OpenCode's documented git and npm plugin install expects a package with an export entry. A `plugin` git spec will not register these skills by itself.

Sources consulted on 2026-11-16:

- https://opencode.ai/docs/plugins/
- https://opencode.ai/docs/build/plugins/
- https://opencode.ai/docs/skills/

OpenCode discovers skill directories at `.opencode/skills/<name>/SKILL.md`, and it also reads `.agents/skills` and `.claude/skills`. Copy or symlink each `skills/<name>` directory into one of those locations. That copy was not run here.

Repository: https://github.com/aidless/research-writing-skill
