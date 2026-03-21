# Craft.md — vigil

> My operational brain for this project. I update this before and after every work session.
> If it's not here, it's not tracked. If it's tracked, I follow it.

---

## Project Identity

- **Name**: vigil
- **One-liner**: Predictive risk intelligence for open source dependencies
- **Thesis**: Security scanning tells you what's broken. Vigil tells you what's about to break.
- **Differentiation**: Not CVE scanning (Snyk, Socket, Endor Labs own that). Sustainability prediction — maintainer health, community trajectory, cascade risk, regulatory readiness.
- **Target user**: Any developer or team that depends on open source (everyone)
- **Delivery**: CLI-first, Python, runs locally or in CI

---

## Current Phase

**Phase 0: Foundation** (COMPLETE)
- [x] Project scaffolding (pyproject.toml, src layout, tests)
- [x] Core data model design (Signal, HealthProfile, ScanResult)
- [x] GitHub API client (rate-limit aware, cached, auth via GITHUB_TOKEN)
- [x] PyPI metadata client (package info, release history, repo URL extraction)
- [x] Signal extraction framework (Analyzer base class, AnalyzerContext)
- [x] Maintainer analyzer (push recency, commit trend, bus factor, release cadence)
- [x] CLI wired end-to-end (vigil scan, vigil check)
- [x] Rich terminal output (summary table + detailed signal breakdown)
- [x] JSON output mode
- [x] 25 tests passing

**Phase 1: More Analyzers** (COMPLETE)
- [x] Community health analyzer (issue responsiveness, close rate, contributor breadth, community size)
- [x] Security posture analyzer (security policy, license, dev status, yanked releases, fork detection)
- [x] Sustainability analyzer (org backing, project maturity, funding signals, maintenance load)
- [x] 46 tests passing
- [x] Repo live: https://github.com/SatishoBananamoto/vigil

**Phase 1.5: Hardening** (IN PROGRESS)
- [x] GitHub rate limit handling (config module, auth CLI, budget tracking)
- [ ] Commit trend with linear regression (not just quarter-over-quarter)
- [ ] Issue response time refinement (use comments API, not just updated_at proxy)
- [x] Graceful degradation when signals fail (partial results on rate limit, not crash)

**Phase 2: Dependency Graph** (COMPLETE)
- [x] Parse requirements.txt / pyproject.toml
- [x] Resolve transitive dependencies (DependencyResolver, recursive PyPI requires_dist)
- [x] Cascade risk mapping (3 signals: worst transitive, breadth, fragility)
- [x] Depth-weighted risk aggregation (decay: 1.0 / 0.7 / 0.4 by depth)

**Phase 3: Intelligence**
- [ ] Trend analysis (is this project growing, stable, or declining?)
- [ ] Burnout signal detection (response latency increase, sentiment shift)
- [ ] Regulatory readiness scoring (CRA compliance, SBOM, attestation)
- [ ] AI-specific risks (slopsquatting exposure, hallucination probability)
- [ ] Migration difficulty assessment

**Phase 4: Output & Integration**
- [x] CLI interface (vigil scan, vigil check)
- [x] Risk scorecard output (terminal table + detailed signal view)
- [x] JSON output mode (--json flag)
- [ ] CI integration mode (exit codes, thresholds)
- [ ] Caching layer (don't re-fetch unchanged data)
- [ ] Markdown output mode

---

## Decision Log

| ID | Date | Decision | Reasoning |
|----|------|----------|-----------|
| D-001 | 2026-03-20 | Python, CLI-first, no web UI | Chromebook constraints. Fastest to ship. Can add UI later. |
| D-002 | 2026-03-20 | Start with PyPI ecosystem only | Satish's primary language. Simpler to model one ecosystem deeply first. |
| D-003 | 2026-03-20 | Focus on sustainability prediction, not CVE scanning | Crowded at CVE layer (Snyk $300M+ ARR, Socket $65M, Endor $188M). Empty at sustainability prediction layer. |
| D-004 | 2026-03-20 | Graceful degradation on API failures | Hit rate limit during scan — security/sustainability analyzers failed for httpx but rest of scan completed. This is correct behavior. |
| D-005 | 2026-03-21 | Token resolution: explicit → env → config file | Three-layer priority. Env var for CI, config.toml for dev workstations. No breaking change — GITHUB_TOKEN env still works. |
| D-006 | 2026-03-21 | No disk cache, no async, no retry/backoff | Rate limits are hard walls, not transient. Async is Phase 3. Disk cache adds complexity for marginal single-session gain. Keep it simple. |
| D-007 | 2026-03-21 | Cascade uses PyPI-only for transitive deps | GitHub API calls only for direct deps. Transitive deps scored via quick_risk (release recency, yank rate, maturity). Conserves API budget. |
| D-008 | 2026-03-21 | Cascade as --cascade flag, not default | Adds PyPI latency (~200ms × transitive count). Opt-in keeps default scan fast. |
| D-009 | 2026-03-21 | CASCADE as separate SignalCategory | Distinct analytical dimension — transitive dep health vs package's own health. Deserves its own category in output. |
| D-010 | 2026-03-21 | Safety limits: max_depth=3, max_nodes=200 | Prevents runaway resolution on huge trees (boto3, django). Diminishing returns past depth 3. |

---

## Open Questions

- What's the right granularity for risk scores? Single number vs multi-dimensional?
- How to handle packages with no GitHub repo (PyPI-only)?
- ~~Rate limiting strategy for GitHub API (5000 req/hr authenticated)?~~ → RESOLVED (D-005, D-006)
- Should we use git clone for deep analysis or API-only for speed?
- How to validate predictions? (need ground truth for abandoned projects)

---

## Risks

| Risk | Severity | Mitigation |
|------|----------|------------|
| GitHub API rate limits | ~~High~~ Low | MITIGATED: `vigil auth` CLI, config.toml, pre-flight budget check, partial results on limit hit |
| False positives (vacation vs abandonment) | High | Multi-signal fusion, minimum observation window, confidence intervals |
| Scope creep (trying to do everything) | Medium | Phase gates. Ship each phase before starting next. |
| Data freshness | Medium | TTL-based cache, staleness indicators in output |

---

## Session Log

### 2026-03-20 — Session 1: Inception through Phase 1
- Proposed vigil concept to Satish — accepted
- Completed web research: supply chain landscape 2025-2026
- Created operational docs (Craft.md, Skills.md, Intel.md)
- Built Phase 0: models, parsers, GitHub client, PyPI client, analyzer framework
- Built Phase 1: all 4 analyzers (maintainer, community, security, sustainability)
  - 15+ signals per package across 4 risk dimensions
- Wired CLI end-to-end: `vigil scan` and `vigil check` commands
- Rich terminal output with summary table + detailed signal view + JSON mode
- Fixed timezone bug (PyPI returns naive datetimes, GitHub returns aware)
- 46 tests passing, 4 real packages scanned successfully
- Repo created and pushed: https://github.com/SatishoBananamoto/vigil
- Hit GitHub rate limit (unauthenticated = 60 req/hr) — degraded gracefully
- Satish caught me not updating Craft.md before committing. Lesson learned.
- **Next**: Rate limit handling, signal refinement, hardening

### 2026-03-21 — Session 2: Rate Limiting Fix
- Reviewed REVIEW.md priorities. Checked engram for relevant learnings (LRN-012 — advisory vs containment, not directly applicable here).
- Built rate limiting solution in 3 layers:
  1. `config.py` — `~/.config/vigil/config.toml`, XDG-aware, 600 permissions, token resolution (explicit → env → config)
  2. `vigil auth login/status/logout` — guided token setup with validation, budget display
  3. Budget tracking in `GitHubClient` — `remaining`, `limit`, `requests_made` from response headers
- Pre-flight budget check before scanning: warns if insufficient, shows package capacity
- Mid-scan `RateLimitError` caught cleanly: partial results displayed, auth guidance shown
- Post-scan summary: shows API calls consumed and remaining budget
- 20 new tests (10 config, 10 github client). Total: 66/66 passing.
- Logged DEC-007 to engram.
- **Next**: Cascade risk (transitive dependency analysis — the differentiator)
- Starting cascade risk implementation (same session)
- Built cascade risk in 4 new files:
  - `resolver.py` — DependencyResolver: recursive PyPI requires_dist tree resolution, cycle detection, depth/node limits, fetch deduplication
  - `analyzers/cascade.py` — 3 signals: cascade_worst (depth-weighted), cascade_breadth (surface area), cascade_fragile (count of risky transitive deps). PyPI-only quick_risk scoring.
  - `output.py` — tree visualization with box-drawing chars and risk color coding
  - `models.py` — DependencyNode, SignalCategory.CASCADE, HealthProfile.dependency_tree
- 32 new tests (19 resolver, 13 cascade). Total: 98/98 passing.
- CLI: `vigil scan requirements.txt --cascade` and `vigil check requests --cascade`
- JSON output includes dependency_tree when cascade is enabled
- Logged DEC-008 through DEC-010 to Craft.md, DEC-009 to engram

**Recommended next priority:**
1. **Threshold validation** (retroactive testing against real abandoned packages) — credibility piece. Proves signals actually predict failure.
2. **Integration tests** (end-to-end with mocked APIs) — safety net for shipping.
3. **Phase 1.5 remaining**: commit trend regression, issue response via comments API — signal polish.
4. **Re-review**: REVIEW.md needs re-grading — rate limiting and cascade risk (the two blockers) are now addressed.
