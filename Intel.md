# Intel.md — vigil

> External research and data points that won't survive context windows.
> Timestamped, sourced, and structured so future-me can act on them.

---

## Last Updated: 2026-03-20

---

## Supply Chain Threat Landscape (2025-2026)

### Key Incidents
- **Shai-Hulud** (Sept 2025): First self-replicating npm worm. 500+ packages, 25K repos compromised. Registry-native propagation — a new class of attack. [ReversingLabs]
- **S1ngularity / Nx Build System** (Aug-Nov 2025): AI-powered malware injected into Nx packages. 2,349 credentials harvested from 1,079 dev systems. [Silobreaker]
- **GitHub Actions tj-actions/changed-files** (March 2025): CVE-2025-30066. CI/CD secrets leaked in public build logs. [Silobreaker]
- **npm Package Hijacking** (Sept 2025): 18 packages, 2B+ weekly downloads hijacked. [TechDemocracy]
- **GlassWorm** (Jan-Mar 2026): 72+ malicious Open VSX extensions mimicking dev tools. [The Hacker News]
- **XZ lingering** (Aug 2025): Docker Hub images on Debian base still carrying 2024 XZ backdoor 1+ year later. [The Hacker News]

### Slopsquatting (New Attack Class)
- AI code generators hallucinate package names ~20% of the time (756K-sample study)
- 43% of hallucinated names recur predictably across prompts
- Attackers register phantom packages with malicious payloads
- Named threat class as of 2025 [Bleeping Computer, Trend Micro]

### By the Numbers (2025)
| Metric | Value |
|--------|-------|
| New malicious packages discovered | 454,648 |
| Malicious package growth | +73% YoY |
| Total open source downloads | 9.8 trillion (+67% YoY) |
| Avoidable vulnerable downloads (Java alone) | 1.8 billion |
| CVEs lacking NVD CVSS score | ~65% |
| NVD median time-to-score | 41 days |

---

## Maintainer Crisis Data

| Metric | Value |
|--------|-------|
| Maintainers unpaid | 60% |
| Experienced burnout | 44% |
| Quit or considered quitting | 60% |
| Projects showing lifecycle decline (no formal EOL) | 42% |
| Primary OSS EOL events in 2025 | 150+ |

### Notable Casualties
- **Kubernetes Ingress NGINX** (Nov 2025): ~50% of cloud-native depends on it. 1-2 devs on personal time. Best-effort until March 2026, then dead. Migrate to Gateway API.
- **External Secrets Operator**: 4 maintainers burned out, 1 left. All updates frozen. Used in critical enterprise systems globally.
- **EOL'd in 2025**: Laravel v10, OpenSSL v3.1, Ruby v3.1

---

## Competitive Landscape

### Well-Funded Players (CVE/Security Layer)
| Company | Funding | Focus |
|---------|---------|-------|
| Endor Labs | $188M total | Dependency risk, AI-suggested dep analysis |
| Socket.dev | $65M + Coana acquisition | Reachability analysis, malware detection |
| Snyk | $1B+ raised, $300M+ ARR | SCA, container security, possible 2026 IPO |
| Black Duck | Divested $2.1B from Synopsys | SCA, license compliance |

### What They Do That We Don't
- CVE scanning and alerting
- Reachability analysis (Socket/Coana: 80% false positive reduction)
- Malware detection in packages
- SBOM generation

### What We Do That They Don't (Our Gap)
- Maintainer burnout prediction
- Community health trajectory modeling
- Sustainability collapse early warning
- Cascade risk through dependency graphs
- Regulatory readiness scoring (CRA timeline)
- AI-specific dependency risks (slopsquatting probability)

---

## Regulatory Landscape

### EU Cyber Resilience Act (CRA)
- Entered into force: Dec 10, 2024
- **Vulnerability/incident reporting**: Sept 11, 2026 (6 months from now)
- Conformity assessment framework: June 11, 2026
- Full product requirements: Dec 11, 2027
- SBOM requirements evolving toward unified frameworks
- OpenSSF has 3 free CRA courses

### US Executive Orders
- EO 14144 (Biden, Jan 2025): SBOMs, software attestation, secure dev practices for federal vendors
- Trump EO (June 2025): Kept EO 14144, directed NIST to update SSDF and SP 800-53. Rescinded CISA attestation mandate.
- CISA updated minimum SBOM elements in 2025

### Implications for Vigil
- CRA compliance scoring is a differentiator — Sept 2026 deadline creates urgency
- SBOM availability as a signal (does this project produce one?)
- Attestation support as a health indicator

---

## AI + Code Quality Data

- AI-co-authored PRs: 1.7x more issues than human PRs
- Correctness 1.75x worse, maintainability 1.64x worse, security 1.57x worse
- 80% of AI-suggested dependencies contain risks (Endor Labs)
- 34% of AI-suggested deps are hallucinations
- Engineers spend only 16% of their week writing code
- 20% increase in PRs per author from AI tools

---

## Standards & Tools Maturity

### Mature and Usable
- SLSA 1.0, SPDX 3, Sigstore — stable open standards
- Trusted publishing live across npm, PyPI, crates.io, NuGet
- 17% of PyPI uploads include attestations
- GUAC 1.0 — graph for understanding artifact composition
- OpenSSF OSPS Baseline — 6 control families, 3 maturity levels

### Immature / Gaps
- Only 12.6% of top-200 npm packages have provenance enabled
- Cross-format SBOM conversion still nascent (Protobom, BomCTL)
- NVD is broken (65% unscored, 41-day lag)
- No standard for sustainability metrics

---

## Funding & Sustainability Initiatives
- **Open Source Pledge**: ~$3M/year collective, $2K/dev minimum
- **Tidelift**: $100-150/dev/year subscription
- **Sovereign Tech Fund** (Germany): 23M EUR across 60 projects, budget increasing
- **GitHub Sponsors**: 99.999% freeloading rate among companies using OSS
