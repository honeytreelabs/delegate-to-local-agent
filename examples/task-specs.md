# Task specs: good and bad

Every "bad" spec below is the kind of instruction that fails with a local LLM. Every "good" spec is the same task written the way [`references/task-spec-template.md`](../skills/delegate-to-local-agent/references/task-spec-template.md) asks for. The orchestrator writes the good kind.

## 1. Vague feature request

**Bad — the orchestrator's own context, pasted as a task:**

> Add caching to the API client so repeated requests are faster. Use whatever approach fits best with the codebase.

A small model will pick a caching strategy nobody asked for, edit files across the whole client, and invent an invalidation policy. Nothing in the spec is checkable.

**Good:**

> # Task: Add response caching to APIClient.get
>
> ## Context
> `src/client.py` has `class APIClient` with `def get(self, url: str) -> dict`. It calls `self._request(url)` and returns the parsed JSON dict. `tests/test_client.py` has the fixtures `mock_response` and `frozen_time`.
>
> ## Requirements
> - Add an in-memory cache to `APIClient`: identical GET requests within `cache_ttl` seconds return the cached dict without calling `_request`.
> - Cache key is `(url,)`. TTL comes from the existing `self.timeout`-style constructor arg: add `cache_ttl: float = 60.0`.
> - Cache is per-instance and cleared by a new public method `clear_cache()`.
>
> ## Scope
> - Files you may change: `src/client.py`, `tests/test_client.py`
> - Do NOT change: `pyproject.toml`, any lockfile; do not add dependencies
>
> ## Done when
> - `python -m pytest tests/test_client.py` passes
> - New tests cover: cache hit skips `_request`, TTL expiry calls again, `clear_cache()` empties it
>
> ## Rules
> - Work only in the current directory. Do not commit, push, or touch git config.
> - No network access beyond what the build needs. Never print or write secrets.
> - Finish with a short summary: what you changed, what you're unsure about, anything left undone.

## 2. Mechanical migration

**Good:**

> # Task: Replace `requests` with `httpx` in the sync client
>
> ## Context
> The project is moving to `httpx` (already in `requirements.txt`). `src/fetch.py` uses `requests.get(...)` in three functions: `fetch_json`, `fetch_text`, `download`. Signatures must not change.
>
> ## Requirements
> - Each `requests.get(...)` call becomes `httpx.get(...)` with the same arguments.
> - `response.json()` and `response.text` work the same in `httpx`; no logic changes.
> - Remove `import requests` if no other use remains.
>
> ## Scope
> - Files you may change: `src/fetch.py`
> - Do NOT change: tests, `requirements.txt`, docs; no new dependencies
>
> ## Done when
> - `python -m pytest tests/test_fetch.py` passes
> - `grep -rn "requests" src/` returns nothing
>
> ## Rules
> - (verbatim from the template)

## 3. Review feedback round

**Bad — vague, will not land:**

> Round 2: the caching needs some edge cases handled better. Also make the tests more thorough.

**Good:**

> ## Review feedback (round 2)
> - `src/client.py:41`: the cache stores the dict by reference, so callers can mutate the cached entry. Return `copy.deepcopy(cached)`.
> - `src/client.py:48`: TTL check uses `time.time() >= expiry`; expired by exactly one microsecond must re-fetch, `>=` is correct — keep it, but add the test below.
> - `tests/test_client.py`: no test mutates a returned response. Add one: call `get`, mutate the returned dict, call `get` again, assert the second result equals the original fixture.
> - `tests/test_client.py:57`: you changed `assert ttl == 60.0` to `assert True`. Restore the original assertion; do not weaken tests.

## 4. Take-over decision

The spec stays the same across rounds; the orchestrator takes over when:

- the same defect survives two feedback rounds with concrete instructions (the step is too big or too ambiguous — split it or do it yourself);
- the agent edited outside Scope twice;
- the worktree diff grows between rounds without any requirement being satisfied (going in circles).

Say in the report which parts the agent wrote and which parts you fixed.
