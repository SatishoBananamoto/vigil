# Skills.md — vigil

> Patterns, techniques, and hard-won knowledge I accumulate while building this project.
> Not documentation — operational intelligence. If I learned it the hard way, it goes here.

---

## API Patterns

### PyPI JSON API
- Endpoint: `https://pypi.org/pypi/{package}/json`
- No auth needed. Returns full metadata + all releases.
- `project_urls` dict has repo links under keys like "Source", "Source Code", "Repository", "GitHub"
- Fall back to `home_page` if project_urls missing
- Release upload times are **naive datetimes** (UTC but no tzinfo) — must add timezone before comparing

### GitHub REST API
- Auth resolution (D-005): explicit param → `GITHUB_TOKEN` env var → `~/.config/vigil/config.toml`
- Unauthenticated: 60 req/hr. Authenticated: 5000 req/hr.
- `/repos/{owner}/{name}/stats/commit_activity` returns 202 if GitHub is computing — treat as "not ready"
- Contributors endpoint returns top 30 by default, sorted by commit count — sufficient for bus factor
- Cache responses with TTL — repo metadata doesn't change fast
- Budget: ~7 API calls per package (repo, commit_activity, contributors, issues, community/profile, users/owner, contents/FUNDING.yml). Contributors call is cached across MaintainerAnalyzer and CommunityAnalyzer.
- Response headers `x-ratelimit-remaining` / `x-ratelimit-limit` / `x-ratelimit-reset` are tracked on every request for live budget monitoring.

## Data Modeling

- Normalize all signal values to 0-1 (1 = healthiest). Makes aggregation uniform.
- Confidence weighting in risk score: `1 - (sum(value * confidence) / sum(confidence))`
- No signals = risk score 1.0 (unknown is dangerous, not safe)

## Signal Processing

- Bus factor: count contributors needed to reach 80% of total commits. Bus factor 1 = critical.
- Commit trend: compare last-quarter vs previous-quarter totals. Ratio < 0.4 = fast decline.
- Release cadence: combine "time since last release" + "gap between last two releases" for fuller picture.

### Cascade Risk (added: 2026-03-21)
- Transitive deps resolved from PyPI `requires_dist` — no GitHub calls, no rate limit concern.
- `parse_requires_dist()` filters `extra ==` markers (optional deps) but keeps environment markers (runtime deps).
- PEP 503 name normalization: `re.sub(r'[-_.]+', '-', name).lower()`.
- DependencyResolver uses two dedup layers: `ancestors frozenset` (cycle detection per branch), `_pkg_cache` (PyPI fetch dedup across trees).
- Safety: `max_depth=3`, `MAX_TOTAL_NODES=200` prevents runaway on huge trees.
- `quick_risk()` scores transitive deps using PyPI-only data (release recency, yank rate, release count). Returns 0-1 where 1 = riskiest.
- Depth decay weights: depth 1 = 1.0, depth 2 = 0.7, depth 3 = 0.4. Risk at greater depth matters less.

## Testing Strategies

- Test models in isolation — signal clamping, risk score math, category filtering
- Parser tests use tempfiles with known content
- API client tests use respx mocks — see `tests/test_github_client.py` for patterns
- Config tests use `monkeypatch` to override `CONFIG_DIR`/`CONFIG_FILE` paths with `tmp_path`
- Resolver tests use `MagicMock` PyPI client with controllable `requires_dist` — no network calls
- Cascade tests use synthetic `DependencyNode` trees + `_pypi_info()` factory with controllable staleness/yank params
- Quick_risk threshold tests: be careful with compound scoring — 3 signals averaged can produce unexpected values. Test with extreme params (500+ days stale, 0-1 releases) to get reliably high risk.

## Performance & Caching

- In-memory dict cache with TTL in GitHub client — simple and effective for single scan runs
- PyPI is fast enough to not need caching for typical dependency counts (< 100)

## Gotchas

### Timezone Hell (hit: 2026-03-20)
PyPI returns naive datetimes. GitHub returns ISO with `Z` suffix. `datetime.now(timezone.utc)` is aware.
Comparing naive vs aware raises TypeError. Fix: always normalize to UTC-aware at parse time.
Affects: PyPI client `upload_time` parsing AND the sort fallback (`datetime.min` is naive).

### GitHub Rate Limits (hit: 2026-03-20, fixed: 2026-03-21)
Unauthenticated: 60 req/hr (~8 packages). Authenticated: 5000 req/hr (~714 packages).
Fixed with: `vigil auth login/status/logout` CLI, config.toml persistence, pre-flight budget check, mid-scan RateLimitError handling with partial results, post-scan consumption summary.
Key files: `config.py`, `clients/github.py` (budget tracking), `cli.py` (auth commands + budget display).

### Process Discipline (hit: 2026-03-20, again: 2026-03-21)
Satish caught me pushing to GitHub without updating Craft.md first.
Then in Session 2, I built the entire rate limiting feature before touching Craft.md — caught again.
My own contract says "update before and after every work block."
Rule: Always update Craft.md BEFORE committing/pushing. No exceptions.
Rule: At session start, read Craft.md, REVIEW.md, check engram. At session end, update all three.
