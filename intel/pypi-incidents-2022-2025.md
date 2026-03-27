# PyPI Supply Chain Incidents (2022-2025)

> Curated dataset of real, documented Python package incidents for vigil signal calibration.
> Each entry verified against published security reports. No fabricated packages.

**Last updated**: 2026-03-21
**Total incidents**: 24

---

## Category Legend

| Code | Meaning |
|------|---------|
| **HIJACK** | Legitimate package taken over (account compromise, domain expiry) |
| **DORMANT** | Inactive package weaponized after period of abandonment |
| **TYPOSQUAT** | Malicious package mimicking a popular name |
| **DEP-CONFUSION** | Dependency confusion / namespace collision attack |
| **MAINTAINER-ATTACK** | Package author themselves injected malicious code |
| **ABANDONED** | Package unmaintained, creating downstream risk (no malicious injection) |
| **CAMPAIGN** | Coordinated multi-package malware campaign |

---

## 1. ctx

| Field | Value |
|-------|-------|
| **PyPI name** | `ctx` |
| **Category** | HIJACK |
| **Date** | May 14, 2022 |
| **What happened** | Attacker purchased the expired email domain (figlief.com) of the maintainer for $5, performed a password reset, took over the PyPI account, and replaced the package with code that exfiltrated environment variables (including AWS keys) to a Heroku endpoint. |
| **Pre-incident state** | Small utility (dict dot-notation access). Unchanged for 8 years. Single maintainer with an expired domain. |
| **Downloads during attack** | ~27,000 malicious copies downloaded between May 14-24 |
| **GitHub repo** | Unknown / not linked |
| **Still on PyPI** | Removed |
| **Source** | [The Register](https://www.theregister.com/2022/05/24/pypi_ctx_package_compromised/), [Hacker News](https://thehackernews.com/2022/05/pypi-package-ctx-and-php-library-phpass.html) |
| **Vigil relevance** | Textbook case: expired maintainer domain = account takeover. Vigil should flag domain expiry as critical signal. |

---

## 2. torchtriton (PyTorch dependency confusion)

| Field | Value |
|-------|-------|
| **PyPI name** | `torchtriton` |
| **Category** | DEP-CONFUSION |
| **Date** | December 25-30, 2022 |
| **What happened** | Attacker registered `torchtriton` on public PyPI with the same name as PyTorch's internal dependency. Because pip prioritizes public PyPI over private indexes, anyone installing `pytorch-nightly` on Linux got the malicious version instead. Payload stole SSH keys, up to 1000 files from $HOME, and system metadata. |
| **Pre-incident state** | `torchtriton` was an internal PyTorch dependency, not meant to be on public PyPI. PyTorch nightly has massive download volume. |
| **GitHub repo** | https://github.com/pytorch/pytorch |
| **Still on PyPI** | Removed. PyTorch renamed to `pytorch-triton` and registered it on public PyPI to prevent recurrence. |
| **Source** | [PyTorch Blog](https://pytorch.org/blog/compromised-nightly-dependency/), [SentinelOne](https://www.sentinelone.com/blog/pytorch-dependency-torchtriton-supply-chain-attack/) |
| **Vigil relevance** | Private/public namespace collision. Vigil should flag packages that depend on private indexes without public namespace reservation. |

---

## 3. exotel

| Field | Value |
|-------|-------|
| **PyPI name** | `exotel` |
| **Category** | HIJACK |
| **Date** | August 2022 |
| **What happened** | JuiceLedger threat actor phished PyPI maintainers with fake login pages mimicking PyPI. Compromised the maintainer's credentials, published malicious versions. Part of first-ever known phishing campaign targeting PyPI users. |
| **Pre-incident state** | Legitimate package, 480,000+ total downloads. |
| **GitHub repo** | Unknown |
| **Still on PyPI** | Malicious versions removed |
| **Source** | [SentinelOne](https://www.sentinelone.com/labs/pypi-phishing-campaign-juiceledger-threat-actor-pivots-from-fake-apps-to-supply-chain-attacks/), [Checkmarx](https://checkmarx.com/blog/first-known-phishing-attack-against-pypi-users/) |
| **Vigil relevance** | Phishing-based account takeover. Pre-2FA era. Vigil signal: does maintainer have 2FA enabled? |

---

## 4. spam

| Field | Value |
|-------|-------|
| **PyPI name** | `spam` |
| **Category** | HIJACK |
| **Date** | August 2022 |
| **What happened** | Same JuiceLedger phishing campaign as exotel. Versions 2.0.2 and 4.0.2 were poisoned after maintainer credentials were stolen via phishing. |
| **Pre-incident state** | 200,000+ total downloads. |
| **GitHub repo** | Unknown |
| **Still on PyPI** | Malicious versions removed |
| **Source** | [SentinelOne](https://www.sentinelone.com/labs/pypi-phishing-campaign-juiceledger-threat-actor-pivots-from-fake-apps-to-supply-chain-attacks/) |
| **Vigil relevance** | Same campaign as exotel. Pattern: phishing targets maintainers of moderately popular packages. |

---

## 5. deep-translator

| Field | Value |
|-------|-------|
| **PyPI name** | `deep-translator` |
| **Category** | HIJACK |
| **Date** | August 2022 |
| **What happened** | Third confirmed victim of the JuiceLedger phishing campaign. Compromised account released a version that exploited environment variables and downloaded malware during installation. |
| **Pre-incident state** | Part of a trio with exotel and spam totaling ~700K combined downloads. |
| **GitHub repo** | https://github.com/nidhaloff/deep-translator |
| **Still on PyPI** | Yes (malicious version removed) |
| **Source** | [Vulert](https://vulert.com/vuln-db/pypi-deep-translator-30671) |
| **Vigil relevance** | Legitimate package with active users. Attack came via credential theft, not code vulnerability. |

---

## 6. ssh-decorator

| Field | Value |
|-------|-------|
| **PyPI name** | `ssh-decorator` |
| **Category** | HIJACK |
| **Date** | ~2022 (exact date unclear, reported mid-2022) |
| **What happened** | Package was hijacked and backdoored to collect SSH credentials, sending them to a remote server. Versions 0.28-0.31 were malicious; version 0.27 was the last safe release. |
| **Pre-incident state** | Small utility for SSH connections in Python. Single maintainer. |
| **GitHub repo** | Unknown |
| **Still on PyPI** | Removed / malicious versions pulled |
| **Source** | [BleepingComputer](https://www.bleepingcomputer.com/news/security/backdoored-python-library-caught-stealing-ssh-credentials/) |
| **Vigil relevance** | Dormant small package with security-sensitive functionality (SSH). Perfect target for hijacking. |

---

## 7. W4SP Stealer Campaign (29 packages)

| Field | Value |
|-------|-------|
| **PyPI names** | `typesutil`, `typestring`, `sutiltype`, `duonet`, `fatnoob`, `strinfer`, `pydprotect`, `incrivelsim`, `twyne`, `pyptext`, `installpy`, `faq`, `colorwin`, `requests-httpx`, `colorsama`, `shaasigma`, `stringe`, `felpesviadinho`, `cypress`, `pystyte`, `pyslyte`, `pystyle`, `pyurllib`, `algorithmic`, `oiu`, `iao`, `curlapi`, `type-color`, `pyhints` |
| **Category** | CAMPAIGN / TYPOSQUAT |
| **Date** | October-November 2022 |
| **What happened** | 29 packages delivering W4SP Stealer, a Python trojan that steals passwords, browser cookies, Discord tokens, crypto wallet data, and system metadata. Campaign peaked around October 22, 2022. |
| **Pre-incident state** | All newly created malicious packages. Some typosquatting popular names (requests-httpx, colorsama, pyurllib). |
| **GitHub repo** | N/A (malicious) |
| **Still on PyPI** | All removed |
| **Source** | [Hacker News](https://thehackernews.com/2022/11/researchers-uncover-29-malicious-pypi.html), [BleepingComputer](https://www.bleepingcomputer.com/news/security/devs-targeted-by-w4sp-stealer-malware-in-malicious-pypi-packages/) |
| **Vigil relevance** | Campaign-scale attack. Names like `requests-httpx` and `colorsama` target popular package misspellings. Vigil needs typosquat distance analysis. |

---

## 8. colorslib / httpslib / libhttps (Lolip0p)

| Field | Value |
|-------|-------|
| **PyPI names** | `colorslib`, `httpslib`, `libhttps` |
| **Category** | TYPOSQUAT / CAMPAIGN |
| **Date** | January 7-12, 2023 |
| **What happened** | Uploaded by threat actor "Lolip0p". All three contained identical setup.py that ran PowerShell to download and execute an info-stealer ("Oxzy.exe" from Dropbox), which then deployed the Wacatac trojan. |
| **Pre-incident state** | New packages, no prior history. 550+ total downloads before removal. |
| **GitHub repo** | N/A (malicious) |
| **Still on PyPI** | Removed January 17, 2023 |
| **Source** | [Fortinet](https://www.fortinet.com/blog/threat-research/supply-chain-attack-using-identical-pypi-packages-colorslib-httpslib-libhttps), [BleepingComputer](https://www.bleepingcomputer.com/news/security/malicious-lolip0p-pypi-packages-install-info-stealing-malware/) |
| **Vigil relevance** | Cross-reference: automated uploads by single actor. Package age < 7 days should be a signal. |

---

## 9. easytimestamp / pyrologin / discorder / discord-dev / style.py / pythonstyles

| Field | Value |
|-------|-------|
| **PyPI names** | `easytimestamp`, `pyrologin`, `discorder`, `discord-dev`, `style.py`, `pythonstyles` |
| **Category** | CAMPAIGN |
| **Date** | December 2022 - January 2023 |
| **What happened** | Six packages combining RAT + info-stealer capabilities ("RAT mutants"). Launched PowerShell to download ZIP, installed remote control (mouse/keyboard/screenshot) plus credential/crypto/cookie theft. |
| **Pre-incident state** | New malicious packages. |
| **GitHub repo** | N/A (malicious) |
| **Still on PyPI** | Removed |
| **Source** | [Unit42/Palo Alto](https://unit42.paloaltonetworks.com/malicious-packages-in-pypi/) |
| **Vigil relevance** | Hybrid malware (RAT + stealer) is escalating sophistication in PyPI attacks. |

---

## 10. 116-package malware campaign (May-December 2023)

| Field | Value |
|-------|-------|
| **PyPI names** | 116 packages (bulk campaign, individual names vary) |
| **Category** | CAMPAIGN |
| **Date** | May - December 2023 |
| **What happened** | 116 malware packages discovered, estimated 10,000+ downloads total. Various payloads targeting Windows and Linux systems. |
| **Pre-incident state** | Bulk-created malicious packages. |
| **GitHub repo** | N/A |
| **Still on PyPI** | Removed |
| **Source** | [Hacker News](https://thehackernews.com/2023/12/116-malware-packages-found-on-pypi.html) |
| **Vigil relevance** | Scale indicator: 116 packages in a single campaign shows automation. |

---

## 11. django-log-tracker (NovaSentinel)

| Field | Value |
|-------|-------|
| **PyPI name** | `django-log-tracker` |
| **Category** | DORMANT / HIJACK |
| **Date** | February 21, 2024 |
| **What happened** | Dormant since April 2022, suddenly received a malicious update deploying NovaSentinel info-stealer. Attacker stripped original code, replaced with steal-everything malware (browser secrets, crypto wallets, Discord tokens, wifi passwords). Likely PyPI account compromise. |
| **Pre-incident state** | 3,866 total downloads. GitHub repo inactive since April 2022. Small Django logging utility. |
| **GitHub repo** | Exists but dormant since April 2022 |
| **Still on PyPI** | Removed |
| **Source** | [Hacker News](https://thehackernews.com/2024/02/dormant-pypi-package-compromised-to.html), [Phylum](https://blog.phylum.io/dormant-pypi-package-updated-to-deploy-novasentinel-stealer/) |
| **Vigil relevance** | Core vigil signal: dormant package + account compromise = weaponized abandonware. 2-year gap between last legitimate release and malicious update. |

---

## 12. Lazarus Group packages (pycryptoenv, pycryptoconf, quasarlib, swapmempool)

| Field | Value |
|-------|-------|
| **PyPI names** | `pycryptoenv`, `pycryptoconf`, `quasarlib`, `swapmempool` |
| **Category** | TYPOSQUAT / STATE-ACTOR |
| **Date** | February 2024 |
| **What happened** | North Korean state-backed Lazarus Group uploaded 4 packages typosquatting `pycrypto`. Contained Comebacker malware (XOR-encoded DLL). Same malware family used in Lazarus attacks on security researchers (2021). |
| **Pre-incident state** | New malicious packages, 3,269 combined downloads. `pycryptoenv` and `pycryptoconf` exploit the naming confusion around the abandoned `pycrypto` package. |
| **GitHub repo** | N/A (malicious) |
| **Still on PyPI** | Removed |
| **Source** | [JPCERT/CC](https://blogs.jpcert.or.jp/en/2024/02/lazarus_pypi.html), [BleepingComputer](https://www.bleepingcomputer.com/news/security/japan-warns-of-malicious-pypi-packages-created-by-north-korean-hackers/) |
| **Vigil relevance** | Nation-state attackers exploiting the naming confusion caused by abandoned `pycrypto`. Vigil should flag when typosquat targets of abandoned packages appear. |

---

## 13. March 2024 Mass Typosquatting (500+ packages)

| Field | Value |
|-------|-------|
| **PyPI names** | 500+ packages mimicking `tensorflow`, `beautifulsoup4`, `requests`, `colorama`, and others |
| **Category** | CAMPAIGN / TYPOSQUAT |
| **Date** | March 26-28, 2024 |
| **What happened** | Automated campaign uploaded 500+ typosquatted packages with zgRAT malware in setup.py. PyPI had to halt all new user registrations and package uploads for 10 hours. |
| **Pre-incident state** | Automated attack at unprecedented scale. |
| **GitHub repo** | N/A |
| **Still on PyPI** | Removed |
| **Source** | [Check Point](https://blog.checkpoint.com/securing-the-cloud/pypi-inundated-by-malicious-typosquatting-campaign/), [Hacker News](https://thehackernews.com/2024/03/pypi-halts-sign-ups-amid-surge-of.html) |
| **Vigil relevance** | First time PyPI itself had to shut down registrations. Scale of automation is a threat multiplier. |

---

## 14. Colorama poisoning (Top.gg attack)

| Field | Value |
|-------|-------|
| **PyPI name** | Fake `colorama` via fake mirror (`files.pypihosted.org`) |
| **Category** | TYPOSQUAT + INFRASTRUCTURE |
| **Date** | February - March 2024 |
| **What happened** | Attackers registered `pypihosted.org` (typosquat of `pythonhosted.org`), hosted a poisoned copy of the legitimate `colorama` package with malware appended after hundreds of spaces (invisible without horizontal scrolling). Compromised a Top.gg GitHub contributor's account to inject the fake mirror URL into requirements. Affected community of 170,000+ members. |
| **Pre-incident state** | `colorama` is one of the most popular PyPI packages (~150M+ monthly downloads). Attack targeted its distribution infrastructure, not the package itself. |
| **GitHub repo** | https://github.com/tartley/colorama (legitimate, not compromised) |
| **Still on PyPI** | Legitimate colorama unaffected. Fake mirror taken down. |
| **Source** | [Checkmarx](https://checkmarx.com/blog/over-170k-users-affected-by-attack-using-fake-python-infrastructure/), [The Register](https://www.theregister.com/2024/03/25/python_package_malware/) |
| **Vigil relevance** | Attack on infrastructure, not the package itself. Vigil signal: are there domain typosquats of the project's hosting? |

---

## 15. Revival Hijack (22,000 packages at risk)

| Field | Value |
|-------|-------|
| **PyPI names** | 22,000+ removed packages at risk; `pingdomv3` confirmed exploited in-the-wild |
| **Category** | HIJACK |
| **Date** | March 30, 2024 (pingdomv3 exploit); September 2024 (JFrog disclosure) |
| **What happened** | PyPI allows anyone to re-register a package name after the original owner deletes it. Attacker "Jinnis" grabbed `pingdomv3` the same day the original owner removed it, uploaded first a benign version, then a version with obfuscated malicious payload. JFrog identified 22,000 packages vulnerable to this technique and preemptively registered them under a `security_holding` account with version 0.0.0.1 placeholders. |
| **Pre-incident state** | `pingdomv3` was a legitimate package by user "cheneyyan". |
| **GitHub repo** | N/A |
| **Still on PyPI** | 22,000 names held by JFrog's security_holding account |
| **Source** | [JFrog](https://jfrog.com/blog/revival-hijack-pypi-hijack-technique-exploited-22k-packages-at-risk/), [Hacker News](https://thehackernews.com/2024/09/hackers-hijack-22000-removed-pypi.html) |
| **Vigil relevance** | Systemic PyPI vulnerability. Vigil should flag packages whose dependencies were recently deleted from PyPI. |

---

## 16. ultralytics

| Field | Value |
|-------|-------|
| **PyPI name** | `ultralytics` |
| **Category** | HIJACK (CI/CD compromise) |
| **Date** | December 4-7, 2024 |
| **What happened** | Attacker exploited a known GitHub Actions script injection vulnerability to steal the project's PyPI API token. Published versions 8.3.41, 8.3.42, 8.3.45, 8.3.46 containing XMRig crypto-miner (Monero). Two waves of attack. Notably, the compromised versions had valid signed provenance attestations because the build environment itself was compromised. |
| **Pre-incident state** | ultralytics (YOLO) is one of the most popular computer vision libraries. 60M+ total downloads. Active project with multiple maintainers. |
| **GitHub repo** | https://github.com/ultralytics/ultralytics |
| **Still on PyPI** | Yes (malicious versions removed, clean versions available) |
| **Source** | [PyPI Blog](https://blog.pypi.org/posts/2024-12-11-ultralytics-attack-analysis/), [Snyk](https://snyk.io/blog/ultralytics-ai-pwn-request-supply-chain-attack/) |
| **Vigil relevance** | High-profile case showing that signed provenance alone doesn't prevent CI/CD compromises. Vigil signal: GitHub Actions workflow security as risk factor. |

---

## 17. aiocpa

| Field | Value |
|-------|-------|
| **PyPI name** | `aiocpa` |
| **Category** | MAINTAINER-ATTACK |
| **Date** | November 2024 |
| **What happened** | Original maintainer published a legitimate crypto payment client (September 2024), built a user base of 12,100 downloads, then injected malicious code in a later update. The payload (in `utils/sync.py`) exfiltrated cryptocurrency private keys to a Telegram bot using Base64 + zlib obfuscation. PyPI quarantined the package. |
| **Pre-incident state** | Legitimate-seeming new package. 12,100 downloads. Single maintainer. |
| **GitHub repo** | The Git repo was kept clean -- malicious code was only in the PyPI-published version, not in the source repository |
| **Still on PyPI** | Quarantined |
| **Source** | [PyPI Blog](https://blog.pypi.org/posts/2024-11-25-aiocpa-attack-analysis/), [ReversingLabs](https://www.reversinglabs.com/blog/malicious-pypi-crypto-pay-package-aiocpa-implants-infostealer-code) |
| **Vigil relevance** | Novel attack: maintainer is the attacker. Code in PyPI differs from code in Git. Vigil signal: diff between published artifact and source repo. |

---

## 18. gptplus / claudeai-eng (JarkaStealer)

| Field | Value |
|-------|-------|
| **PyPI names** | `gptplus`, `claudeai-eng` |
| **Category** | TYPOSQUAT |
| **Date** | November 2023 (uploaded), November 2024 (discovered by Kaspersky) |
| **What happened** | Packages by user "Xeroline" pretended to be wrappers for GPT-4 Turbo and Claude AI APIs. Deployed JarkaStealer via a hidden JAR file download from GitHub. Stole browser data, screenshots, system info, Telegram/Discord/Steam session data. Active for ~1 year before detection. |
| **Pre-incident state** | New packages, 1,748 and 1,826 downloads respectively. Exploited developer interest in AI API access. |
| **GitHub repo** | N/A (malicious) |
| **Still on PyPI** | Removed |
| **Source** | [Hacker News](https://thehackernews.com/2024/11/pypi-attack-chatgpt-claude.html), [Kaspersky](https://www.kaspersky.com/about/press-releases/kaspersky-uncovers-year-long-pypi-supply-chain-attack-using-ai-chatbot-tools-as-lure) |
| **Vigil relevance** | Year-long dwell time. Exploits trending topics (AI). Vigil signal: new packages claiming to wrap popular APIs by unknown authors. |

---

## 19. dydx-v4-client

| Field | Value |
|-------|-------|
| **PyPI name** | `dydx-v4-client` |
| **Category** | HIJACK |
| **Date** | January 27, 2026 |
| **What happened** | Attacker compromised legitimate dYdX developer credentials and published malicious version 1.1.5post1 containing both a wallet stealer and a Python-based RAT. The RAT beaconed to C2 every 10 seconds. |
| **Pre-incident state** | Official dYdX decentralized exchange client library. Widely used in crypto trading. |
| **GitHub repo** | https://github.com/dydxprotocol |
| **Still on PyPI** | Malicious version removed |
| **Source** | [Hacker News](https://thehackernews.com/2026/02/compromised-dydx-npm-and-pypi-packages.html), [Socket](https://socket.dev/blog/malicious-dydx-packages-published-to-npm-and-pypi) |
| **Vigil relevance** | High-value target (crypto exchange SDK). Credential compromise of official developer. |

---

## 20. bitcoinlibdbfix / bitcoinlib-dev

| Field | Value |
|-------|-------|
| **PyPI names** | `bitcoinlibdbfix`, `bitcoinlib-dev` |
| **Category** | TYPOSQUAT |
| **Date** | April 2025 |
| **What happened** | Targeted users of the legitimate `bitcoinlib` package by masquerading as bug fixes for a recently reported error during Bitcoin transfers. Overwrote the legitimate `clw` CLI command with wallet-draining malware that stole private keys and wallet addresses. Second package uploaded right after first was removed. |
| **Pre-incident state** | `bitcoinlib` is a popular Bitcoin library. Attackers exploited a real open issue to create social engineering credibility. |
| **GitHub repo** | N/A (malicious), targeting https://github.com/1200wd/bitcoinlib |
| **Still on PyPI** | Removed |
| **Source** | [ReversingLabs](https://www.reversinglabs.com/blog/malicious-python-packages-target-popular-bitcoin-library), [Hacker News](https://thehackernews.com/2025/04/malicious-python-packages-on-pypi.html) |
| **Vigil relevance** | Attackers weaponized real bug reports as social engineering. Vigil signal: new packages referencing known issues in popular packages. |

---

## 21. PyCrypto (abandoned, still downloaded)

| Field | Value |
|-------|-------|
| **PyPI name** | `pycrypto` |
| **Category** | ABANDONED |
| **Date** | Last release: June 2014. Effectively dead since then. |
| **What happened** | Maintainer stopped development. Package contains known vulnerabilities (CVE-2013-7459: heap-based buffer overflow). No security patches since 2014. Still pulled ~1.5M downloads/month as of 2024-2025 because it remains in dependency trees of other packages. PyCryptodome exists as a maintained drop-in replacement but many packages haven't migrated. |
| **Pre-incident state** | Was the standard Python cryptography library. Single maintainer (Dwayne Litzenberger). |
| **GitHub repo** | https://github.com/pycrypto/pycrypto (dormant since 2014) |
| **Still on PyPI** | Yes |
| **Vigil relevance** | Canonical example of dangerous abandonment. Still getting millions of downloads 10+ years after last release. Known CVEs unfixed. Lazarus Group typosquatted it (see #12). |

---

## 22. nose

| Field | Value |
|-------|-------|
| **PyPI name** | `nose` |
| **Category** | ABANDONED |
| **Date** | Last release: 2015. Broken on Python 3.10+ (2021). Fully incompatible with Python 3.12 (2023). |
| **What happened** | Testing framework abandoned by maintainer. No releases since 2015. Broke on Python 3.10 due to removed `collections.Callable`. Completely non-functional on Python 3.12. Still listed as dependency in legacy packages. `nose2` exists as spiritual successor but never achieved comparable adoption. |
| **Pre-incident state** | One of the two major Python test frameworks (alongside pytest). Widely depended upon. |
| **GitHub repo** | https://github.com/nose-devs/nose (dormant) |
| **Still on PyPI** | Yes |
| **Vigil relevance** | Widely-depended package that broke silently across Python versions. Vigil signal: last release vs. Python version compatibility matrix. |

---

## 23. Domain Resurrection Risk (1,800 accounts)

| Field | Value |
|-------|-------|
| **PyPI names** | 1,800+ accounts with expired email domains (systemic risk, not single package) |
| **Category** | ABANDONED (systemic) |
| **Date** | Mitigated August 2025 by PyPI |
| **What happened** | PyPI discovered that 1,800+ maintainer email addresses were tied to expired domains. Any attacker could purchase the expired domain, reset the password, and take over the account (exactly as happened with `ctx` in 2022). PyPI began checking domain expiry every 30 days and unverifying affected emails. Accounts with post-2024 activity also require 2FA. |
| **Pre-incident state** | Systemic vulnerability affecting thousands of packages maintained by accounts with expired email domains. |
| **GitHub repo** | N/A (systemic) |
| **Still on PyPI** | Ongoing mitigation |
| **Source** | [PyPI Blog](https://blog.pypi.org/posts/2025-08-18-preventing-domain-resurrections/), [Hacker News](https://thehackernews.com/2025/08/pypi-blocks-1800-expired-domain-emails.html) |
| **Vigil relevance** | 1,800 accounts. This is exactly the kind of leading indicator vigil should detect: maintainer email domain health. |

---

## 24. setuptools (maintenance concerns)

| Field | Value |
|-------|-------|
| **PyPI name** | `setuptools` |
| **Category** | ABANDONED (contested / partially recovered) |
| **Date** | Mid-2025 (concern period) |
| **What happened** | In October 2025, the Python community raised alarms about setuptools maintenance -- only 2 commits in July, then nothing. All bug reports had "Needs Triage" with no maintainer response. Discussion thread: "Are setuptools abandoned?" A v78.0.1 release in early 2026 then broke installations of many older packages. The project appears to have recovered somewhat, but the episode revealed fragility in one of Python's most critical packages. |
| **Pre-incident state** | setuptools is arguably the most critical Python packaging tool. Downloaded billions of times. Maintained primarily by Jason R. Coombs. |
| **GitHub repo** | https://github.com/pypa/setuptools |
| **Still on PyPI** | Yes, actively releasing (82.0.1 as of March 2026) |
| **Source** | [Python Discussion](https://discuss.python.org/t/are-setuptools-abandoned/104390) |
| **Vigil relevance** | Even the most foundational Python package can show maintenance decline signals. Commit frequency drop + issue triage backlog = vigil early warning territory. |

---

## Summary by Category

| Category | Count | Examples |
|----------|-------|----------|
| HIJACK (account/credential compromise) | 7 | ctx, exotel, spam, deep-translator, ssh-decorator, ultralytics, dydx-v4-client |
| DORMANT (abandoned then weaponized) | 1 | django-log-tracker |
| TYPOSQUAT | 5 | W4SP campaign, Lolip0p, Lazarus, bitcoinlib*, gptplus/claudeai-eng |
| DEP-CONFUSION | 1 | torchtriton |
| MAINTAINER-ATTACK | 1 | aiocpa |
| CAMPAIGN (multi-package) | 4 | W4SP (29), RAT mutants (6), 116-package campaign, March 2024 (500+) |
| ABANDONED | 3 | pycrypto, nose, setuptools (partial) |
| SYSTEMIC | 2 | Revival Hijack (22K), Domain Resurrection (1,800) |

## Patterns Relevant to Vigil Signals

1. **Domain expiry -> account takeover** (ctx, 1800 at-risk accounts): Check maintainer email domain health
2. **Dormant package -> malicious update** (django-log-tracker): Flag packages with long gaps between releases
3. **CI/CD compromise -> signed malicious builds** (ultralytics): Provenance attestation alone is insufficient
4. **Maintainer IS the attacker** (aiocpa): Compare published artifact to source repo
5. **Abandoned package -> typosquatting magnet** (pycrypto -> Lazarus): Abandoned popular packages attract targeted typosquats
6. **Private namespace not reserved on public registry** (torchtriton): Flag dependencies from private indexes without public placeholders
7. **Revival Hijack** (pingdomv3): Flag when your dependencies were recently deleted from PyPI
8. **Phishing waves** (JuiceLedger): Maintainers without 2FA are targets
9. **AI-themed social engineering** (gptplus, claudeai-eng): New packages exploiting trending topics
10. **Real bug reports weaponized** (bitcoinlibdbfix): Attackers monitor issue trackers for social engineering opportunities
