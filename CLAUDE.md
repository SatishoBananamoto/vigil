<!-- scroll:start -->
## Project Knowledge (scroll)

*Extracted from `vigil` git history.*

### Decisions

- **DEC-001**: Published package as 'vigil-risk' instead of 'vigil' due to name conflict (high)
  - The desired package name 'vigil' was already taken on PyPI, forcing the team to choose an alternative name that still clearly identifies the tool's purpose.

### Learnings

- **LRN-001**: Stale positive signals from old metadata inflate health scores on abandoned packages (high)
  - Positive signals from package metadata become misleading indicators of current health when they're significantly outdated. The age of the signal is as important as the signal itself for accurate risk assessment.
- **LRN-002**: HTTP redirects can cause analyzer crashes without proper handling
  - Package repository URLs can change over time, and services like GitHub frequently use redirects. Analyzers must handle HTTP redirects gracefully to maintain robustness when processing real-world package metadata.

### Observations

- **OBS-001**: Cascade validation reveals scoring asymmetry issue with transitive dependencies (high)
  - This identifies a fundamental challenge in transitive dependency scoring: cascade signals can mask direct abandonment indicators, leading to false confidence in risky dependencies. The issue suggests that category-weighted scoring is needed where cascade signals have lower influence when direct signals indicate abandonment.

### Goals

- **GOL-001**: Achieve 100% validation accuracy through systematic threshold tuning (high)
  - - 100% exact match: risk classifications exactly match expected values
  - - 100% tolerant match: risk classifications within one risk level of expected
  - - No false positives or negatives in critical risk detection

<!-- scroll:end -->
