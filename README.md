# vigil

Predictive risk intelligence for open source dependencies. Know before they break.

## The Problem

Your project depends on 47 packages. Three of them haven't had a release in two years. One has a single maintainer who stopped responding to issues. Another was compromised last quarter. You find out when your build breaks or your users get pwned.

## What Vigil Does

Vigil scans your dependencies and produces a health assessment for each one, using signals from PyPI and GitHub:

- **Maintainer health**: push recency, commit trends, bus factor, release cadence
- **Community health**: issue responsiveness, close rate, contributor breadth
- **Security posture**: security policy, license clarity, yank rate, dev status
- **Sustainability**: org backing, funding, project maturity, maintenance load
- **Cascade risk**: transitive dependency analysis, depth-weighted risk scoring

## Quick Start

```bash
pip install vigil-risk
```

```bash
# Check a single package
vigil check requests

# Scan your whole project
vigil scan pyproject.toml
vigil scan requirements.txt

# Include transitive dependencies
vigil scan pyproject.toml --cascade

# JSON output for CI integration
vigil check numpy --json
```

## Example Output

```
vigil check click
  click MODERATE (score: 0.295)

  maintainer
    commit_trend: Dropping fast — commits at 3% of previous quarter.
    release_cadence: Moderate release pace — latest 131d ago.
    bus_factor: Bus factor 5 — healthy contributor base.
    push_recency: Recent activity — last push 11d ago.

  community
    issue_responsiveness: Very slow — median first activity within 6269h.
    contributor_breadth: Broad contributor base — 30+ contributors.

  security
    license: Permissive license: BSD-3-Clause.
    dev_status: Declared stable.

  sustainability
    org_backing: Backed by small organization 'pallets'.
    project_maturity: Mature and active — 11.9 years old.
```

## GitHub Authentication

Vigil uses GitHub's API for detailed analysis. Authenticate for higher rate limits:

```bash
vigil auth login    # Uses gh CLI token
vigil auth status   # Check your budget
```

## Validation

Vigil has been validated against 20 real PyPI packages:
- 10 healthy controls (requests, django, pytest, numpy, etc.)
- 5 known-abandoned (pycrypto, nose, distribute, etc.)
- 5 gray-area (setuptools, colorama, deep-translator)

Result: **100% exact match** on risk level classification.

## Stale Signal Decay

Vigil doesn't trust frozen metadata. A "Production/Stable" classifier from 2014 on an abandoned package gets its confidence reduced from 0.5 to 0.15. Static signals decay when the package shows no recent activity.

## License

MIT
