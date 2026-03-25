# Vigil — Review

---

## v3 — 2026-03-25

**Reviewer**: Claude (Opus 4.6, partner session)
**Version Reviewed**: v0.2.0, Phase 2.5 (validation) complete, ~3,876 LOC (source + tests + validation), 98 tests
**Previous Review**: v2 — 2026-03-21 (Grade: B+)
**Grade: A-** Validation done with honest reporting. Thresholds proven against real packages. Remaining mismatches identified with clear fix paths.

### Summary

Phase 2.5 (threshold validation) is complete. Vigil was tested against 20 real PyPI packages — 10 healthy controls, 5 known-abandoned, 5 gray-area. Results: **70% exact match, 95% within 1 level**. Two root causes identified for the 6 mismatches (boundary sensitivity at 0.25, stale positive signals diluting abandoned package scores). Conditional penalty signals added for packages with no GitHub repo. 24 real PyPI incidents researched and documented. The tool now has empirical evidence that its signals discriminate between healthy and dying projects.

### What Changed Since v2

- **Threshold validation completed** — 20 packages scanned with GitHub auth, compared against expected risk levels. 70% exact, 95% tolerant. Honest reporting (D-012).
- **Conditional penalty signals** — sustainability.py now detects missing GitHub repos. Soft penalty if recent releases exist, hard penalty if stale. Fixes false alarms on healthy packages (numpy, rich) that previously scored MODERATE due to missing repo signals (D-011).
- **GitHub redirect fix** — `follow_redirects=True` added to httpx client. Repo renames (deep-translator) no longer crash with 301.
- **Intel research** — 24 real PyPI incidents (2022-2025) documented in `intel/pypi-incidents-2022-2025.md`. Most compromised packages removed from PyPI, confirming validation must use known-abandoned + healthy controls.
- **Validation framework** — `validation/validate.py` (315 LOC) runs vigil against curated test set, compares actual vs expected, reports exact + tolerant match rates.
- **v0.2.0 committed and pushed** — version bumped, all Phase 2 work on GitHub.

### Strengths (new)

1. **Empirical validation with honest reporting.** 70% exact / 95% tolerant isn't perfect — and the project says so. D-012 explicitly requires both strict and tolerant reporting. This is more trustworthy than claiming 100%.

2. **Clear signal separation.** Healthy packages average 0.225 risk, risky average 0.621, moderate average 0.432. The signals genuinely discriminate — not just noise.

3. **Conditional penalties are principled.** Missing repo + recent releases = maybe they just don't use GitHub (soft penalty). Missing repo + stale releases = genuinely abandoned (hard penalty). This is smarter than a flat penalty.

4. **Intel research is a strategic asset.** 24 documented incidents with dates, methods, and outcomes. This becomes blog content, marketing material, and calibration data for future thresholds.

### Remaining Weaknesses

1. **6 threshold mismatches unresolved.** Three healthy packages (click, httpx, pillow) score MODERATE due to 0.25 boundary being too tight. Two abandoned packages (pycrypto, nose) can't reach CRITICAL because stale positive signals (dev_status="stable", 0 yanked) dilute the score. Decision pending between Option A (adjust boundary) and Option B (reduce stale signal confidence). **Fix**: Implement Option B — it addresses both problems from the root cause.

2. **Uncommitted validation work.** sustainability.py changes, github.py redirect fix, validation/ directory, intel/ directory are not committed. **Fix**: Commit now.

3. **No PyPI release.** v0.2.0 is on GitHub but not pip-installable by strangers. **Fix**: `python -m build && twine upload dist/*`.

4. **Issue responsiveness still proxy.** created_at → updated_at gap, not actual first-response time. Unchanged from v1.

5. **No integration tests.** Unit tests are strong (98 passing) but no end-to-end pipeline test with mocked APIs.

6. **Cascade not included in validation run.** The 20-package validation didn't use `--cascade` flag. Cascade signals untested against real packages.

### Recommendations (Priority Order)

1. **Fix threshold mismatches (Option B).** Reduce confidence on stale positive signals (dev_status, yanked_releases) when package has no recent activity. Re-run validation. Target: 85%+ exact match.

2. **Commit validation work.** sustainability.py, github.py, validation/, intel/ — all uncommitted. Ship it.

3. **Release to PyPI.** v0.2.0 is ready. Get it in front of users. `pip install vigil-security` or similar.

4. **Run validation with --cascade.** Cascade is the differentiator but wasn't validated.

5. **Integration tests.** End-to-end with mocked APIs.

### Risks

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|-----------|
| ~~Rate limiting~~ | ~~Fixed~~ | | |
| ~~Cascade risk not built~~ | ~~Fixed~~ | | |
| ~~Thresholds unvalidated~~ | ~~Fixed~~ | | Validated: 70% exact, 95% tolerant |
| 6 mismatches degrade user trust | Medium | Medium | Fix boundary + stale signal confidence |
| Uncommitted work lost | Medium | High | Commit immediately |
| PyPI release delayed | High | Medium | Release this week |
| Competitors move into sustainability | Medium | High | Ship to users, build community |

---

## v2 — 2026-03-21 (Previous)

**Reviewer**: Claude (Opus 4.6, partner session)
**Version Reviewed**: v0.1.0 → Phase 2 complete, 5 analyzers + cascade, ~2,509 LOC, 98 tests
**Previous Review**: v1 — 2026-03-20 (Grade: B)
**Grade: B+** Both critical blockers fixed. Thresholds unvalidated.

### Summary

Vigil is a predictive risk intelligence tool for open source dependencies. Not CVE scanning (Snyk, Socket, Endor Labs own that market with $1.3B+ invested). Instead: sustainability prediction — maintainer burnout signals, community health trajectory, bus factor analysis, cascade risk through dependency trees. It produces confidence-weighted risk scores from 18+ signals across 5 analyzers (maintainer, community, security, sustainability, cascade). The two critical blockers from the initial review — rate limiting and missing cascade risk — have both been fixed. The tool is now functional for real-world use.

### What Changed Since v1

- Rate limiting fixed: `vigil auth login/status/logout`, config persistence, budget tracking
- Cascade risk shipped: resolver.py, cascade.py, 3 signals, depth-weighted scoring, `--cascade` CLI flag
- 98 tests passing (up from 46)
- v0.2.0 committed and pushed

### Weaknesses (at time of v2)

1. ~~Rate limiting~~ FIXED
2. ~~Cascade risk~~ FIXED
3. Issue responsiveness still proxy
4. Thresholds unvalidated — #1 priority
5. Python-only ecosystem
6. No PyPI release

---

## v1 — 2026-03-20 (Original)

**Reviewer**: Claude (Opus 4.6, partner session)
**Version Reviewed**: v0.1.0, Phase 1 complete, 4 analyzers, ~1,646 LOC, 46 tests
**Grade: B** Excellent thesis, rate limiting + cascade missing.

### Summary

Vigil is a predictive risk intelligence tool for open source dependencies. Sharp thesis in empty market space ($1.3B+ in CVE scanning, $0 in sustainability prediction). 4 analyzers producing 15+ signals with confidence-weighted aggregation. Two critical blockers: GitHub rate limiting makes the tool unusable after 3-4 packages, and the core differentiator (cascade risk through dependency trees) isn't built yet.

### Dimension Assessments

**Thesis & Positioning**: Strongest in portfolio. Real market gap. CRA deadline (Sept 2026) creates urgency.

**Architecture**: Clean modular design. Analyzer framework well-designed for extensibility. Each module earns its place.

**Code Quality**: 46 tests, functional approach with synthetic fixtures. Confidence-weighted aggregation is elegant. Missing integration tests.

**Completeness**: 4 analyzers, CLI, terminal + JSON output. Missing: rate limiting, cascade risk, threshold validation.

**Usability**: Clean CLI. Rate limiting made it unusable for real projects unauthenticated.

**Sustainability**: Zero LLM dependency. Free APIs. Modular analyzer framework.

**Portfolio Fit**: Most market-facing tool. Strongest candidate for external adoption.

### Strengths

1. Sharp thesis in empty market space
2. Confidence-weighted signal aggregation
3. Bus factor calculation (80% commit concentration)
4. Graceful degradation on API failures
5. Exceptional operational documentation (Craft.md, Skills.md, Intel.md)

### Original Recommendations

1. ~~Fix rate limiting~~ DONE (v2)
2. ~~Build cascade risk~~ DONE (v2)
3. ~~Validate thresholds retroactively~~ DONE (v3)
4. ~~Bump version, release~~ Bumped to v0.2.0 (v2), PyPI pending
5. Add integration tests — still pending
