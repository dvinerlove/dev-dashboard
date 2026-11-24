# Verification notes — 2026-11-24-release-readiness (facts.jsonl, 30 facts, all Q4)

Every cited URL re-fetched live on 2026-11-24 (all 200s; raw copies in `verify/`).
Verdicts: **30 verified, 0 misquoted, 0 unsupported, 0 contradicted, 0 outdated, 0 source-blocked.**

## Patterns found

### 1. Cluster labels understated single-origin concentration (independence)
The per-file clusters `localhost-repo`, `localhost-readme`, `localhost-releases`,
`localhost-release-pipeline`, `localhost-ci`, and `smartscreen-mitigation` (F004)
are ALL the same origin: the marcellosso/localhost repo. That is **one cluster
(13 facts: F001–F012, F029, F030)**, not six. Ledger `cluster` column normalized
to `localhost`. This is inherent (the facts describe the reference repo) but the
report must not count "5 sources agree" when they're one repo's docs.

Consequences for load-bearing normative claims:
- The "signed update feeds on GitHub Releases" pattern (F005, F030) is
  evidenced ONLY by localhost — dekit uses `dekit update`, Portmaster uses its
  own channel, lazygit/process-compose don't self-update. Treat as
  single-source if the report presents it as a niche norm.
- F021/F022 both trace to ONE Velopack docs page (`signing-smartscreen`
  cluster = 1 origin). The $10/mo price and "instant reputation" claims are
  single-source in the dataset.

### 2. Quote splice across sibling files (F010)
F010's `quote` concatenates a sentence from `release.yml`'s header comment with
a sentence that is verbatim in `RELEASING.md:124` — not in the cited file. Both
documents are real and the workflow implements the described check; the fact is
verified, but citations should list both files.

### 3. Minor numeric slips (non-fatal)
- F014: claim says "7 archives"; v1.124.0 ships **8** archives + checksums.txt
  (the fact's own quote lists 8).
- F005: "roughly weekly" understates actual cadence — 7 releases in 9 days
  (v0.5.0→v0.6.0). Direction is safe for the claim.
- F022: Azure Artifact Signing real price is **$9.99/mo for a 5,000-signature
  quota** (+$0.005/extra) per azure.microsoft.com — Velopack's "USD$10/mo" rounds
  and drops the quota. Also, Microsoft's own Learn doc says SmartScreen
  reputation "builds over time; initial warnings expected" even for Artifact
  Signing — Velopack's "built-in instant reputation" is rosier than Microsoft's
  wording. Keep the claim attributed to Velopack, not stated as fact.

### 4. Tier corrections
- F023/F024: PyInstaller's own `antivirus.md` issue template is the project's
  official position → **L1**, not L2.
- F025: firsthand blog example, n=1 → **L3**, not L4 (it's primary for what the
  author built; weak for "community standard").
- F026: correctly L1 independent-primary; repo live, workflow verbatim.

### 5. Second-source spot-checks (iron rule)
- localhost-0.6.0.dmg size 29,396,649 → confirmed via asset download endpoint
  Content-Length.
- lazygit v0.66.3 latest → confirmed via Homebrew formula (0.66.3).
- Azure Artifact Signing ~$10/mo → confirmed via azure.microsoft.com /
  Microsoft Learn ($9.99/mo, quota caveat above).

### 6. Honest classifications kept
source_class assignments were otherwise accurate: all repo files vendor-authored
(correct — they are self-published artifacts, which is the point for "norms"
claims), blog = independent-secondary, fc-inventory = independent-primary.
No reposts, PR-derived text, or vendor-curated content found.
