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

**Phase 1.5: Hardening** (next)
- [ ] GitHub rate limit handling (authenticate, backoff, warn user)
- [ ] Commit trend with linear regression (not just quarter-over-quarter)
- [ ] Issue response time refinement (use comments API, not just updated_at proxy)
- [ ] Graceful degradation when signals fail (partial results, not crash)

**Phase 2: Dependency Graph**
- [x] Parse requirements.txt / pyproject.toml
- [ ] Resolve transitive dependencies
- [ ] Cascade risk mapping (if A dies, what breaks?)
- [ ] Depth-weighted risk aggregation

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

---

## Open Questions

- What's the right granularity for risk scores? Single number vs multi-dimensional?
- How to handle packages with no GitHub repo (PyPI-only)?
- Rate limiting strategy for GitHub API (5000 req/hr authenticated)?
- Should we use git clone for deep analysis or API-only for speed?
- How to validate predictions? (need ground truth for abandoned projects)

---

## Risks

| Risk | Severity | Mitigation |
|------|----------|------------|
| GitHub API rate limits | High | Aggressive caching, conditional requests (ETags), incremental updates |
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
