# AGENTS.md

## Repository Overview

- Purpose: an agent skill (`delegate-to-local-agent`) that lets an
  orchestrating agent delegate well-scoped implementation tasks to a local
  coding-agent harness (Pi, oh-my-pi, OpenCode, custom) on a local LLM in an
  isolated git worktree, then review, verify and integrate the diff.
- Core tech: Markdown (the skill itself), Python (a dependency-free eval
  checker), uv, GitHub Actions.

The skill is documentation, not a library. Most changes are edits to
Markdown files. The minimum Python version is in `pyproject.toml`.

## Layout

- `skills/delegate-to-local-agent/SKILL.md`: the skill. Its frontmatter
  carries `metadata.version`.
- `skills/delegate-to-local-agent/references/`: the harness profiles and
  the task-spec template that `SKILL.md` links to.
- `prompts/system-prompt.md`: a one-paragraph mirror of the skill for
  harnesses without skill support. Keep it in sync with `SKILL.md`.
- `evals/check_skill.py`: static checks (frontmatter, links, safety
  invariants, version consistency). Uses only the Python standard library.
- `evals/scenarios.json`, `evals/pressure-tests.md`: manual eval scenarios.
- `examples/task-specs.md`: good and bad task specs.
- `.claude-plugin/`, `.codex-plugin/`, `.agents/plugins/`: plugin and
  marketplace manifests.
- `README.md`: user-facing overview. Its config table and procedure
  summary mirror `SKILL.md`.
- `CHANGELOG.md`: one entry per version, plus an `## Unreleased` section.
- `pyproject.toml`, `uv.lock`: a virtual uv project (no dependencies, no
  build system).

## Common Commands

Always prefix any python-related command with `uv run`, e.g.:

- Self-test the checker: `uv run evals/check_skill.py --self-test`
- Check the skill and packaging: `uv run evals/check_skill.py`
- Validate all JSON files (as CI does):
  `uv run python -c "import json,glob; [json.load(open(f)) for f in glob.glob('**/*.json', recursive=True) if '.git' not in f]"`

## Keeping Files Consistent

- The version lives in five places: `SKILL.md` (`metadata.version`),
  `.claude-plugin/plugin.json`, `.claude-plugin/marketplace.json`,
  `.codex-plugin/plugin.json` and `pyproject.toml`. A release bumps all
  of them and adds a `## <version>` entry to `CHANGELOG.md`.
- Add user-visible changes to `## Unreleased` in `CHANGELOG.md`.
- When you change the procedure or the configuration variables in
  `SKILL.md`, update `prompts/system-prompt.md` and the `README.md`
  config table and procedure summary as well.
- When you add a safety rule that must not get lost, add its anchor text
  to `REQUIRED_INVARIANTS` in `evals/check_skill.py`. If it is critical,
  also add a seed to `self_test()`.

## Commit Messages

Read this section before running `git commit`.

### General rules

- Group changes by feature. One commit carries one feature or one fix.
- Never mix unrelated changes in one commit. Stage only the files that
  belong to the change; leave unrelated files unstaged.
- Never commit generated files, editor state, or local configuration.
  Check `.gitignore` first. If a local artifact is not ignored, ask
  before adding a new ignore pattern.
- Write the subject line in the imperative mood. Say what the commit
  does: "Add a debug panel", not "Added" or "Adds".
- Keep the subject line under 60 characters (excluding the Conventional
  Commit prefix, see below). Do not end it with a period.
- Add exactly one paragraph of description below the subject, separated
  by one blank line. Keep it short; three sentences are enough for most
  changes.
- Write the message in simple English. Use short sentences, active
  voice, and simple tenses. Name the actor. Do not use contractions.
- Say why the change is needed, then what it does. Do not list every
  file. Do not describe the code line by line.
- Do not add AI credits, tool names, or "Generated with" footers.

This repository uses Conventional Commit prefixes on the subject line
(`feat:`, `fix:`, `ci:`, `chore:`, ...). Changes to the skill's content
(`skills/`, `prompts/`) use the `skill:` prefix. Follow the established
style of recent commits.

Message shape (adapt the words, keep the shape):

- New feature:

  ```text
  feat: add <feature>

  <User needs this because ...>. Add <what you built>. <One sentence
  about how it behaves or how it is enabled.>
  ```

- Bug fix:

  ```text
  fix: <what was broken>

  <What happened before, in one sentence.>. <What the cause was.>.
  <What the code does now.>.
  ```

- Dependency or tooling change:

  ```text
  chore: <what was updated>

  <What failed or was outdated.>. <What you changed.>. <One sentence
  that says the checks still pass.>
  ```

### Before you commit

- Run the checks and catch failures early:

  ```bash
  uv run evals/check_skill.py --self-test
  uv run evals/check_skill.py
  ```

- If a hook fails, fix the problem and commit again. Do not use
  `--no-verify` unless the user asks for it.
- Do not sign commits. Run `git commit` with `--no-gpg-sign`, and do not
  use `-S`.
- Show the user the commit hash and subject after a successful commit.

## Testing Patterns

- `evals/check_skill.py` is the only automated test. Keep it
  dependency-free (standard library only), so it runs anywhere.
- The self-test must fail on a seeded broken copy of the repo and pass
  on the real one. Run both modes after every change to the checker.
- The scenarios in `evals/` are manual. Do not claim that a scenario
  passed unless you ran it against a real harness.
- The local harnesses (`pi`, `omp`, `opencode`) and a local model are
  usually not available in this environment. Say so instead of claiming
  a live delegation run.

## Writing Style for the Skill

- Write `SKILL.md` and its references in simple English: short sentences,
  active voice, imperative mood for instructions.
- The reader is an agent. Give exact commands and file paths instead of
  general advice, and say what not to do when there is an obvious wrong
  path.
- Keep `SKILL.md` focused on the procedure. Move details that are needed
  only sometimes (per-harness flags, templates) into `references/`.

## Implementation Details

- Add concise/precise docstrings to utility functions.
  - Docstrings use Python Sphinx format (e.g. `:param foo:`, `:returns:`, `:raises ValueError:`).
- Add Python typing hints where possible.
- Prefer pragmatic solutions; if a shortcut is taken, call out the shortcomings explicitly.
