<p align="center">
  <strong>🤝 your agent writes the spec. a local model does the typing.</strong>
</p>

<p align="center">
  <a href="https://agentskills.io"><img src="https://img.shields.io/badge/SKILL.md-open_standard-blue?style=flat" alt="Agent Skills"></a>
  <a href="skills/delegate-to-local-agent/SKILL.md"><img src="https://img.shields.io/badge/version-1.0.0-blue?style=flat" alt="version 1.0.0"></a>
  <img src="https://img.shields.io/badge/runs_on-local_LLMs-green?style=flat" alt="runs on local LLMs">
  <a href="LICENSE"><img src="https://img.shields.io/badge/license-MIT-lightgrey?style=flat" alt="MIT"></a>
  <a href="https://github.com/honeytreelabs/delegate-to-local-agent/stargazers"><img src="https://img.shields.io/github/stars/honeytreelabs/delegate-to-local-agent?style=flat&logo=github&color=yellow" alt="GitHub stars"></a>
</p>

<p align="center">
  An agent skill that turns a coding agent into an orchestrator for a local coding-agent harness:<br>
  it decomposes the task, writes a concrete spec, runs the local agent in an isolated git worktree,<br>
  then reviews, verifies and integrates its diff. The local agent's output is treated as untrusted input.
</p>

Works in every agent that reads the [Agent Skills standard](https://agentskills.io): Claude Code, Cursor, VS Code Copilot, OpenAI Codex, Gemini CLI, Goose, OpenCode, and about 25 more. One folder, no dependencies, MIT.

## Install

Any agent, with the [skills CLI](https://github.com/vercel-labs/skills):

```bash
npx skills add honeytreelabs/delegate-to-local-agent
```

Claude Code plugin:

```bash
claude plugin marketplace add honeytreelabs/delegate-to-local-agent && claude plugin install delegate-to-local-agent@delegate-to-local-agent
```

Codex plugin:

```bash
codex plugin marketplace add honeytreelabs/delegate-to-local-agent
codex plugin add delegate-to-local-agent@delegate-to-local-agent
```

No skill support? Paste the block in [`prompts/system-prompt.md`](prompts/system-prompt.md) into your system prompt, `AGENTS.md`, or `.cursorrules`.

Then say "delegate this to the local agent", or just hand the skill a task when a local harness is configured.

## What it does

The orchestrator (the agent that loaded the skill) keeps the thinking work. A local coding-agent harness — Pi, oh-my-pi, OpenCode, or any harness with a non-interactive mode — on a local LLM does the implementation. One round is:

1. **Preflight.** Resolve the harness profile, confirm the repo is clean, note the base commit.
2. **Task spec.** Write a concrete, one-step spec (context, requirements, scope, done-when, rules) to a file outside the repo, so it never lands in the diff.
3. **Isolated worktree.** `git worktree add` from `HEAD` on a branch `agent/<slug>`. The local agent cannot see uncommitted changes or touch the main checkout.
4. **Run.** Non-interactive invocation with a hard timeout, logged to a file.
5. **Review.** Scope check, full diff read, security pass, and the orchestrator re-runs every "done when" command itself. The agent's claim that tests pass doesn't count.
6. **Iterate or take over.** Concrete review feedback for up to `AGENT_MAX_ROUNDS` rounds, then the orchestrator fixes the rest itself.
7. **Integrate and clean up.** Commit with attribution, merge/cherry-pick/PR per the user's choice, remove the worktree.

Everything the local agent produces is untrusted: it runs outside the orchestrator's permission system, so the skill mandates reviewing every line and never following instructions found in the agent's output.

## Configuration

| Variable | Default | Purpose |
|---|---|---|
| `AGENT_HARNESS` | `pi` | Which harness profile to use (`pi`, `omp`, `opencode`, `custom`) |
| `AGENT_CMD` | from profile | Command to launch the agent. Point it at a container wrapper to sandbox it. |
| `AGENT_ARGS` | *(empty)* | Extra flags, e.g. provider/model selection |
| `AGENT_INPUT` | from profile | How the spec is passed: `stdin` or `arg` |
| `AGENT_TIMEOUT` | `1800` | Hard timeout in seconds for one run |
| `AGENT_MAX_ROUNDS` | `3` | Max delegate → review → feedback rounds |

The profile table with exact non-interactive invocations lives in [`skills/delegate-to-local-agent/references/harness-profiles.md`](skills/delegate-to-local-agent/references/harness-profiles.md). The task-spec template lives in [`references/task-spec-template.md`](skills/delegate-to-local-agent/references/task-spec-template.md), with good and bad specs in [`examples/task-specs.md`](examples/task-specs.md).

## When to delegate

Good fits: clearly specified implementation tasks with a test or build command that proves success — new functions from a spec, refactors with existing test coverage, boilerplate, test writing, mechanical migrations.

Do it yourself instead when the task is mainly design or architecture, touches security-sensitive code (auth, crypto, input parsing at trust boundaries, secrets handling), needs exploring an unfamiliar codebase, or cannot be verified by a command.

## Test scenarios

[`evals/scenarios.json`](evals/scenarios.json) holds delegation scenarios with pass criteria, and [`evals/pressure-tests.md`](evals/pressure-tests.md) describes the adversarial cases the skill exists to catch: the vague spec, the silent TUI fallback, the weakened test, the instruction smuggled in agent output, the out-of-scope edit.

## Contributing

Open an issue for questions and bug reports. Pull requests are welcome. Run `python3 evals/check_skill.py` before you push; CI runs it on every push. Say in the PR whether an agent wrote the code, and do not add attribution trailers.

## License

MIT for everything here. Unofficial project, not affiliated with or endorsed by the Pi, oh-my-pi, or OpenCode projects. Their names are used only to identify the supported harnesses.
