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
- Auth via `GITHUB_TOKEN` env var → 5000 req/hr. Without: 60 req/hr.
- `/repos/{owner}/{name}/stats/commit_activity` returns 202 if GitHub is computing — treat as "not ready"
- Contributors endpoint returns top 30 by default, sorted by commit count — sufficient for bus factor
- Cache responses with TTL — repo metadata doesn't change fast

## Data Modeling

- Normalize all signal values to 0-1 (1 = healthiest). Makes aggregation uniform.
- Confidence weighting in risk score: `1 - (sum(value * confidence) / sum(confidence))`
- No signals = risk score 1.0 (unknown is dangerous, not safe)

## Signal Processing

- Bus factor: count contributors needed to reach 80% of total commits. Bus factor 1 = critical.
- Commit trend: compare last-quarter vs previous-quarter totals. Ratio < 0.4 = fast decline.
- Release cadence: combine "time since last release" + "gap between last two releases" for fuller picture.

## Testing Strategies

- Test models in isolation — signal clamping, risk score math, category filtering
- Parser tests use tempfiles with known content
- API client tests will need respx mocks (not yet implemented)

## Performance & Caching

- In-memory dict cache with TTL in GitHub client — simple and effective for single scan runs
- PyPI is fast enough to not need caching for typical dependency counts (< 100)

## Gotchas

### Timezone Hell (hit: 2026-03-20)
PyPI returns naive datetimes. GitHub returns ISO with `Z` suffix. `datetime.now(timezone.utc)` is aware.
Comparing naive vs aware raises TypeError. Fix: always normalize to UTC-aware at parse time.
Affects: PyPI client `upload_time` parsing AND the sort fallback (`datetime.min` is naive).
