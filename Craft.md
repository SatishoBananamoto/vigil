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

**Phase 1: More Analyzers** (next)
- [ ] Community health metrics (contributor diversity, issue velocity, PR merge time)
- [ ] Security posture analyzer (CI/CD presence, branch protection signals)
- [ ] Sustainability indicators (funding, org backing, license stability)
- [ ] Commit trend with linear regression (not just quarter-over-quarter)
- [ ] Issue response time analyzer

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
- [ ] CLI interface (vigil scan requirements.txt)
- [ ] Risk scorecard output (terminal, JSON, markdown)
- [ ] CI integration mode (exit codes, thresholds)
- [ ] Caching layer (don't re-fetch unchanged data)

---

## Decision Log

| ID | Date | Decision | Reasoning |
|----|------|----------|-----------|
| D-001 | 2026-03-20 | Python, CLI-first, no web UI | Chromebook constraints. Fastest to ship. Can add UI later. |
| D-002 | 2026-03-20 | Start with PyPI ecosystem only | Satish's primary language. Simpler to model one ecosystem deeply first. |
| D-003 | 2026-03-20 | Focus on sustainability prediction, not CVE scanning | Crowded at CVE layer (Snyk $300M+ ARR, Socket $65M, Endor $188M). Empty at sustainability prediction layer. |

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

### 2026-03-20 — Session 1: Inception + Phase 0
- Proposed vigil concept to Satish — accepted
- Completed web research: supply chain landscape 2025-2026
- Key findings: space crowded at CVE layer, empty at sustainability prediction
- Created operational docs (Craft.md, Skills.md, Intel.md)
- Built entire Phase 0: models, parsers, GitHub client, PyPI client, analyzer framework
- Built first analyzer (MaintainerAnalyzer): push recency, commit trend, bus factor, release cadence
- Wired CLI end-to-end: `vigil scan` and `vigil check` commands
- Rich terminal output with summary table + detailed signal view + JSON mode
- Fixed timezone bug (PyPI returns naive datetimes, GitHub returns aware)
- 25 tests passing, 4 real packages scanned successfully
- **Next**: More analyzers (community health, security posture), GitHub repo creation
