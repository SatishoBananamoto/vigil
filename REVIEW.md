# Vigil — Review

**Reviewer**: Claude (Opus 4.6, partner session)
**Date**: 2026-03-21 (updated from 2026-03-20)
**Version Reviewed**: v0.1.0 → Phase 2 complete, 5 analyzers + cascade, ~2,509 LOC, 98 tests
**Previous Review**: 2026-03-20 (Grade: B — rate limiting + cascade missing)

---

## Summary

Vigil is a predictive risk intelligence tool for open source dependencies. Not CVE scanning (Snyk, Socket, Endor Labs own that market with $1.3B+ invested). Instead: sustainability prediction — maintainer burnout signals, community health trajectory, bus factor analysis, cascade risk through dependency trees. It produces confidence-weighted risk scores from 18+ signals across 5 analyzers (maintainer, community, security, sustainability, cascade). The two critical blockers from the initial review — rate limiting and missing cascade risk — have both been fixed. The tool is now functional for real-world use.

---

## Dimension Assessments

### Thesis & Positioning

This is the strongest thesis in the portfolio.

**The gap**: $1.3B+ invested in CVE scanning. $0 in sustainability prediction. 60% of maintainers are unpaid. 44% experienced burnout. 42% of projects show lifecycle decline without formal EOL. The supply chain threat landscape (Shai-Hulud, S1ngularity/Nx, GlassWorm, slopsquatting) proves the attack surface is real and growing.

**The timing**: EU Cyber Resilience Act compliance deadline is September 11, 2026 — 6 months away. Companies need to answer "is this dependency going to be maintained long enough for us to comply?" Nobody else answers that question.

**The differentiation**: Socket does reachability analysis. Snyk does CVE scanning. Endor Labs does AI-suggested dep analysis. None of them predict maintainer burnout, model community health trajectory, or assess cascade risk through dependency trees. Vigil occupies genuinely empty space.

**Risk**: If Socket or Endor Labs decides to add a "maintainer health" score, they can ship it in two weeks with their existing data pipelines. The moat isn't the technology — it's the thesis and the speed of execution.

### Architecture

Clean modular design:

```
parsers → clients (GitHub, PyPI) → analyzers → models → output/CLI
```

| Module | Role | Assessment |
|--------|------|-----------|
| models.py | Signal, Dependency, HealthProfile, ScanResult | Clean. Confidence-weighted aggregation. |
| parsers.py | requirements.txt and pyproject.toml parsing | Solid. Handles edge cases. |
| clients/github.py | GitHub REST API with rate-limit awareness, caching | Good. 1-hour TTL cache. |
| clients/pypi.py | PyPI JSON API client | Clean. Timezone normalization. |
| analyzers/base.py | Analyzer abstract base + AnalyzerContext | Minimal, correct. |
| analyzers/maintainer.py | Push recency, commit trend, bus factor, release cadence | Strongest analyzer. |
| analyzers/community.py | Issue responsiveness, close rate, contributor breadth, stars | Good but proxy metrics. |
| analyzers/security.py | Security policy, license, dev status, yank rate, fork detection | Useful signals. |
| analyzers/sustainability.py | Org backing, project maturity, funding, maintenance load | Novel signals. |
| output.py | Rich terminal rendering | Good. Color-coded health bars. |
| cli.py | `vigil scan` and `vigil check` | Functional but minimal. |

The analyzer framework is well-designed for extensibility: add a new analyzer, register it in the list, done. Each analyzer returns a list of Signals, and the HealthProfile aggregates them with confidence weighting. This is the right abstraction.

**Concern**: No dependency graph yet. The analyzers assess individual packages in isolation. The real risk often lives in transitive dependencies — your direct dep is healthy but its dependency has a bus factor of 1.

### Code Quality

| Metric | Value | Assessment |
|--------|-------|-----------|
| Tests | 46 | Adequate for Phase 1 |
| LOC | ~1,646 | Lean |
| Dependencies | httpx, click, rich | Appropriate choices |
| Dev deps | pytest, respx | Standard |
| Build system | hatchling | Modern |

Test approach: synthetic data fixtures with known parameters to test signal thresholds. This is the right approach — you can't depend on real GitHub/PyPI responses in tests (they change, they rate-limit, they're slow).

Missing: integration tests. The synthetic fixture tests verify individual analyzers, but nothing tests the full pipeline (parse file → fetch metadata → analyze → render). Also no tests for the CLI commands.

The confidence-weighted risk aggregation in HealthProfile.risk_score is elegant:
```
total_weighted = sum(signal.value * signal.confidence for signal in signals)
total_confidence = sum(signal.confidence for signal in signals)
raw_score = total_weighted / total_confidence
risk_score = 1.0 - raw_score  # invert: high value = low risk
```
This means a high-confidence bad signal outweighs multiple low-confidence good signals. Correct behavior.

### Completeness

**Complete:**
- Dependency file parsing (requirements.txt, pyproject.toml)
- GitHub REST API client with auth, caching, rate-limit detection
- PyPI JSON API client with timezone normalization
- 4 analyzers producing 15+ signals:
  - Maintainer: push recency, commit trend, bus factor, release cadence
  - Community: issue responsiveness, close rate, contributor breadth, stars
  - Security: security policy, license, dev status, yank rate, fork detection
  - Sustainability: org backing, project maturity, funding, maintenance load
- Confidence-weighted risk aggregation
- Risk level classification (LOW/MODERATE/HIGH/CRITICAL/UNKNOWN)
- Rich terminal output (color-coded tables, health bars)
- JSON output mode
- CLI with scan (batch) and check (single package) commands

**Missing (by phase):**

Phase 1.5 (hardening):
- GitHub auth handling in CLI (users must manually set GITHUB_TOKEN)
- Commit trend with regression (currently quarter-over-quarter only)
- Issue response time via comments API (currently proxy: created→updated gap)
- Better graceful degradation messaging

Phase 2 (differentiator):
- Transitive dependency resolution
- Cascade risk mapping ("if X dies, what breaks?")
- Depth-weighted risk aggregation

Phase 3 (intelligence):
- Trend analysis over time
- Burnout signal detection
- Regulatory readiness scoring (CRA compliance)
- AI-specific risks (slopsquatting exposure)
- Migration difficulty assessment

### Usability

**Setup**: `pip install -e .` (in development). Requires `GITHUB_TOKEN` for meaningful results — unauthenticated gets 60 req/hr which runs out after 3-4 packages. The CLI doesn't prompt for or help set up the token.

**CLI**: Clean and intuitive.
- `vigil scan requirements.txt` — scan all dependencies
- `vigil scan requirements.txt --detail` — show signal breakdown
- `vigil scan requirements.txt --json` — machine-readable output
- `vigil check requests` — check single package

**Output**: Rich terminal tables are well-designed. Risk icons (OK, WARN, HIGH, CRIT) are clear. Detail mode shows per-signal health bars with color coding.

**Pain point**: Rate limiting. A real requirements.txt has 20-50 packages. With 4 analyzers making multiple API calls each, you hit GitHub's 60 req/hr limit scanning 3-4 packages. The tool becomes unusable without auth, and auth setup isn't guided.

### Sustainability

No LLM dependency — all signals from public APIs. Cost is zero (GitHub and PyPI APIs are free). The main sustainability risk is API rate limiting, not cost.

httpx, click, and rich are all well-maintained, widely-used libraries. Low risk of dependency rot.

The analyzer framework is modular — new analyzers can be added without touching existing code. This is good for maintainability.

**Growth ceiling**: The current architecture scans packages sequentially. At 100+ packages, this will be slow even with auth. Needs async/concurrent fetching for scale.

### Portfolio Fit

Vigil is the most market-facing tool in the portfolio. It solves a problem strangers have, not just Satish. It's the strongest candidate for external adoption.

Connection to engram: vigil could produce engram observations ("OBS: requests has bus factor 1, declining commit trend"). Connection to scroll: scroll could extract dependency-related decisions from git history, feeding vigil context about why a dependency was chosen.

Vigil should receive the most investment of any project in the portfolio. It has the clearest path to external value.

---

## Strengths

1. **Sharp thesis in empty market space.** $1.3B+ invested in CVE scanning, $0 in sustainability prediction. The Intel.md research is exceptional — Shai-Hulud, S1ngularity/Nx, GlassWorm, CRA deadlines. This isn't hand-waving about supply chain risk; it's specific, dated, quantified competitive analysis.

2. **Confidence-weighted signal aggregation.** Each signal carries both a value (0-1) and a confidence (0-1). The aggregation weights signals by confidence, so a high-confidence bad signal outweighs multiple low-confidence good signals. This is mathematically sound and produces better risk scores than simple averaging.

3. **Bus factor calculation.** Contributors needed to reach 80% of commits — not just "number of contributors" which tells you nothing about concentration. This is the right metric for predicting key-person risk.

4. **Graceful degradation.** When an analyzer fails or hits rate limits, it returns no signals rather than crashing. Partial results are better than no results. The scan completes with whatever data it could get.

5. **Operational documentation.** Craft.md (phase gates, session log), Skills.md (API patterns, gotchas), Intel.md (competitive landscape). This level of operational discipline is rare in solo projects.

---

## Weaknesses

1. ~~**Rate limiting is a showstopper.**~~ **FIXED (2026-03-21).** `vigil auth login/status/logout` with token validation, XDG-aware config persistence (`~/.config/vigil/config.toml`, mode 600), 3-layer token resolution (explicit → env → config), pre-flight budget checks, and post-scan consumption summary. 10 config tests passing.

2. ~~**No transitive dependency analysis.**~~ **FIXED (2026-03-21).** `DependencyResolver` recursively fetches `requires_dist` from PyPI to build dependency trees. `CascadeAnalyzer` produces 3 signals: `cascade_worst` (depth-weighted worst transitive dep), `cascade_breadth` (surface area), `cascade_fragile` (count of risky transitive deps). Depth decay: 1.0 / 0.7 / 0.4. PyPI-only for transitive (no GitHub budget cost). CLI: `--cascade` flag on scan/check. 29 new tests (16 resolver + 13 cascade).

3. **Issue responsiveness is a weak proxy.** `created_at → updated_at` gap isn't first-response time. It could be a bot label, an auto-close, or the author editing. **Fix**: Use the comments API for actual first human response time.

4. **No signal validation against ground truth.** Thresholds are reasonable heuristics but unvalidated against real project failures. **Fix**: Retroactive testing against 20-30 abandoned/compromised packages. This becomes both validation AND marketing content.

5. **Python-only ecosystem support.** npm is where supply chain attacks are worst. **Fix**: Abstract client layer for npm/cargo support. Phase 3+.

6. **Version not bumped.** Still v0.1.0 despite Phase 2 completion. Rate limiting + cascade risk + auth commands = a v0.2.0 release. **Fix**: Bump version, tag release, push to PyPI.

---

## Recommendations (Priority Order)

1. ~~**Fix rate limiting now.**~~ DONE.

2. ~~**Build cascade risk.**~~ DONE.

3. **Validate thresholds retroactively.** Pick 20-30 abandoned/compromised packages. Run vigil signals against pre-incident state. Publish the results — validation AND marketing content. This is now the #1 priority.

4. **Bump version to v0.2.0 and release to PyPI.** Rate limiting + cascade risk + auth = a real release. Get it in front of users.

5. **Add integration tests.** End-to-end: parse file → mock API responses → analyze → verify risk levels. Unit tests are strong (98 passing) but no full pipeline test.

6. **Commit and push the Phase 2 work.** The cascade risk, resolver, and auth code appears uncommitted. Ship it.

---

## Risks

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|-----------|
| ~~Rate limiting makes tool unusable~~ | ~~High~~ | ~~Critical~~ | FIXED — auth + config + budget checks |
| ~~Cascade risk not built~~ | ~~High~~ | ~~Critical~~ | FIXED — resolver + cascade analyzer + CLI |
| Thresholds don't predict real failures | Medium | High | Retroactive validation study |
| Competitors add sustainability signals | Medium | High | Cascade risk is shipped — maintain speed |
| CRA deadline passes without vigil being ready | Medium | Medium | Focus on CRA compliance scoring next |
| Phase 2 work uncommitted | High | Medium | Commit and push immediately |
| npm ecosystem left unserved | Medium | Medium | Abstract client layer |

---

## Verdict

Vigil has the best thesis and strongest market positioning of any project in the portfolio. The two critical blockers from the initial review — rate limiting and cascade risk — have both been fixed. The tool now has 5 analyzers producing 18+ signals, transitive dependency analysis with depth-weighted cascade risk, and proper GitHub auth with budget management. 98 tests passing. Ready for v0.2.0 release and real-world testing.

The next leap is validation: prove the thresholds predict real project failures. That's the difference between "this tool has signals" and "this tool predicts risk." Ship v0.2.0, validate retroactively, then put it in front of strangers.

**Grade: B+** (upgraded from B — both critical blockers fixed)
Excellent thesis, solid architecture, thoughtful signal design, cascade risk shipped, rate limiting solved. Loses the A- because thresholds are unvalidated and the work appears uncommitted. Moves to A- when v0.2.0 ships to PyPI with retroactive validation.
