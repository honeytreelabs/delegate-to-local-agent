# Changelog

Each entry names the version and the change.

## 1.0.0, 2026-11-11

- Initial release. The skill packages the delegate → review → integrate
  workflow for local coding-agent harnesses (Pi, oh-my-pi, OpenCode, custom):
  task-spec template, harness profiles, isolated-worktree procedure,
  review and security checklist, round limits, and integration/cleanup steps.
- Distribution: Agent Skills standard (`npx skills add`), Claude Code plugin
  manifest, Codex plugin manifest, generic `.agents` manifest, and a
  standalone system prompt in `prompts/` for harnesses without skill support.
- No hooks: the skill is an on-demand procedure, so it loads only when the
  task calls for delegation.
