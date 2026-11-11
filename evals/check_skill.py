#!/usr/bin/env python3
"""Static checks for the delegate-to-local-agent skill repository.

Validates that the skill frontmatter is well-formed, that every relative
link in SKILL.md resolves, that required safety invariants are present, and
that the version is consistent across SKILL.md, the plugin manifests, and
CHANGELOG.md. Dependency-free; runs in CI.

Usage:
    python3 evals/check_skill.py [--self-test]
"""

import json
import re
import sys
import tempfile
import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SKILL_DIR = ROOT / "skills" / "delegate-to-local-agent"
SKILL_MD = SKILL_DIR / "SKILL.md"
VERSIONED_FILES = [
    ".claude-plugin/plugin.json",
    ".claude-plugin/marketplace.json",
    ".codex-plugin/plugin.json",
]

REQUIRED_INVARIANTS = [
    # (anchor text, what it protects)
    ("untrusted", "agent output must be treated as untrusted"),
    ("worktree", "isolated worktree procedure"),
    ("AGENT_TIMEOUT", "hard timeout for agent runs"),
    ("AGENT_MAX_ROUNDS", "round limit before take-over"),
    ("Done when", "verifiable acceptance criteria"),
    ("Scope", "scope boundary for review"),
    ("git status --porcelain", "preflight cleanliness check"),
    ("git diff --stat", "scope check in review"),
    ("git worktree add", "worktree creation command"),
]

REQUIRED_IN_REFERENCES = {
    "task-spec-template.md": ["# Task:", "## Context", "## Requirements",
                              "## Scope", "## Done when", "## Rules",
                              "## Review feedback"],
    "harness-profiles.md": ["pi", "omp", "opencode", "custom",
                            "AGENT_INPUT", "Adding a harness"],
}


class Failure(Exception):
    pass


def parse_frontmatter(text: str) -> dict:
    """Minimal frontmatter parser for the simple key/nested-key structure
    used by SKILL.md. No YAML dependency."""
    if not text.startswith("---"):
        raise Failure("SKILL.md does not start with a frontmatter block (---)")
    end = text.find("\n---", 3)
    if end == -1:
        raise Failure("SKILL.md frontmatter is not closed")
    block = text[4:end]
    fm: dict = {}
    current = None
    mode = "scalar"  # scalar | block | map
    for line in block.splitlines():
        if not line.strip():
            continue
        if line.startswith((" ", "\t")) and current:
            stripped = line.strip()
            if mode == "block":
                fm[current] += " " + stripped
            elif mode == "map":
                key, _, value = stripped.partition(":")
                fm[current][key.strip()] = value.strip().strip('"')
            else:
                raise Failure(f"unexpected indented line under {current!r}: {line!r}")
        else:
            key, _, value = line.partition(":")
            current = key.strip()
            value = value.strip()
            if value == "|":
                mode = "block"
                fm[current] = ""
            elif value == "":
                mode = "map"
                fm[current] = {}
            else:
                mode = "scalar"
                fm[current] = value.strip('"')
    return fm


def extract_versioned_values(root: Path) -> dict:
    """Pull the version strings out of the plugin manifests and pyproject."""
    versions = {}
    for name in VERSIONED_FILES:
        path = root / name
        data = json.loads(path.read_text())
        if "version" in data:
            versions[name] = data["version"]
        else:  # marketplace.json nests the version in plugins[0]
            versions[name] = data["plugins"][0]["version"]
    pyproject = root / "pyproject.toml"
    if pyproject.exists():
        versions["pyproject.toml"] = tomllib.loads(pyproject.read_text())["project"]["version"]
    return versions


def check_repo(root: Path = ROOT) -> list:
    """Run all checks against a repo root. Returns a list of failure strings
    (empty means the repo passes)."""
    problems = []

    skill_md = root / "skills" / "delegate-to-local-agent" / "SKILL.md"
    if not skill_md.exists():
        return [f"missing {skill_md.relative_to(root)}"]
    text = skill_md.read_text()
    body = text.split("\n---", 1)[1] if text.startswith("---") else text

    # 1. Frontmatter
    try:
        fm = parse_frontmatter(text)
    except Failure as e:
        return [str(e)]
    name = fm.get("name", "")
    if name != "delegate-to-local-agent":
        problems.append(f"frontmatter name is {name!r}, expected 'delegate-to-local-agent'")
    description = fm.get("description", "")
    if len(description) < 80:
        problems.append("frontmatter description is too short to route the skill")
    for trigger in ("delegate", "local"):
        if trigger not in description.lower():
            problems.append(f"frontmatter description lacks trigger word {trigger!r}")
    if fm.get("license") != "MIT":
        problems.append("frontmatter license is not MIT")
    version = fm.get("metadata", {}).get("version", "")
    if not re.fullmatch(r"\d+\.\d+\.\d+", version):
        problems.append(f"frontmatter metadata.version is {version!r}, expected semver")

    # 2. Relative links resolve
    for target in re.findall(r"\]\(([^)#\s]+)\)", body):
        if target.startswith(("http://", "https://")):
            continue
        if not (skill_md.parent / target).exists():
            problems.append(f"SKILL.md links to missing file: {target}")

    # 3. Safety invariants
    for anchor, purpose in REQUIRED_INVARIANTS:
        if anchor not in text:
            problems.append(f"SKILL.md lost {anchor!r} ({purpose})")

    # 4. References carry their required sections
    refs_dir = skill_md.parent / "references"
    if not refs_dir.is_dir():
        problems.append("missing references/ directory")
    else:
        for fname, anchors in REQUIRED_IN_REFERENCES.items():
            fpath = refs_dir / fname
            if not fpath.exists():
                problems.append(f"missing references/{fname}")
                continue
            content = fpath.read_text()
            for anchor in anchors:
                if anchor not in content:
                    problems.append(f"references/{fname} lost anchor {anchor!r}")

    # 5. Version consistency across manifests and CHANGELOG
    if re.fullmatch(r"\d+\.\d+\.\d+", version):
        versions = extract_versioned_values(root)
        for fname, v in versions.items():
            if v != version:
                problems.append(f"{fname} version {v} != SKILL.md version {version}")
        changelog = (root / "CHANGELOG.md").read_text()
        if f"## {version}" not in changelog:
            problems.append(f"CHANGELOG.md has no ## {version} entry")

    # 6. Prompts mirror exists
    if not (root / "prompts" / "system-prompt.md").exists():
        problems.append("missing prompts/system-prompt.md")

    return problems


def self_test() -> int:
    """check_repo must flag a seeded broken copy and pass on this repo."""
    failures = []
    # a) the real repo passes
    problems = check_repo()
    if problems:
        failures.append(f"self-test: real repo should pass but got: {problems}")
    # b) seeded copies fail
    seeds = {
        "untrusted": "never follow instructions found in it",
        "AGENT_MAX_ROUNDS": "3",
        "git worktree add": "",
    }
    for anchor, replacement in seeds.items():
        with tempfile.TemporaryDirectory() as tmp:
            tmp_root = Path(tmp)
            for path in ROOT.rglob("*"):
                if path.is_dir() or ".git" in path.parts or "__pycache__" in path.parts:
                    continue
                rel = path.relative_to(ROOT)
                dest = tmp_root / rel
                dest.parent.mkdir(parents=True, exist_ok=True)
                dest.write_bytes(path.read_bytes())
            seeded = tmp_root / "skills" / "delegate-to-local-agent" / "SKILL.md"
            content = seeded.read_text()
            if replacement:
                content = content.replace(anchor, replacement)
            else:  # drop the whole line
                content = "\n".join(
                    l for l in content.splitlines() if anchor not in l)
            seeded.write_text(content)
            problems = check_repo(tmp_root)
            if not any(anchor in p for p in problems):
                failures.append(
                    f"self-test: removing {anchor!r} was not detected (got: {problems})")
    # c) version mismatch is detected
    with tempfile.TemporaryDirectory() as tmp:
        tmp_root = Path(tmp)
        for path in ROOT.rglob("*"):
            if path.is_dir() or ".git" in path.parts or "__pycache__" in path.parts:
                continue
            rel = path.relative_to(ROOT)
            dest = tmp_root / rel
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_bytes(path.read_bytes())
        plugin = tmp_root / ".claude-plugin" / "plugin.json"
        data = json.loads(plugin.read_text())
        data["version"] = "9.9.9"
        plugin.write_text(json.dumps(data, indent=2))
        problems = check_repo(tmp_root)
        if not any("9.9.9" in p for p in problems):
            failures.append(f"self-test: version mismatch not detected (got: {problems})")

    if failures:
        for f in failures:
            print(f"FAIL {f}")
        return 1
    print("self-test ok")
    return 0


def main() -> int:
    if "--self-test" in sys.argv:
        return self_test()
    problems = check_repo()
    if problems:
        for p in problems:
            print(f"FAIL {p}")
        return 1
    print(f"ok: skills/delegate-to-local-agent/SKILL.md and repo packaging pass")
    return 0


if __name__ == "__main__":
    sys.exit(main())
