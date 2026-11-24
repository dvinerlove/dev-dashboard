# Source 09 — Velopack docs: Code Signing / SmartScreen & Antivirus

- URL: https://docs.velopack.io/packaging/signing (fetched via r.jina.ai, full page)
- Publisher: Velopack (Caelan Sayler) | Tier: L2 (official product docs) | source_class: vendor-authored
- Fetched: 2026-11-24

## Key verbatim quotes

- "Code signing is an essential part of application distribution. On Windows, applications without code signatures are likely to be flagged as viruses. On OSX, codesigning and Notarization is required before your application can be run by users."
- "On Windows, unsigned applications are frequently flagged by SmartScreen and antivirus software… The most reliable way to avoid this is to **code-sign** your application, but signing alone is not always instant — SmartScreen warnings are driven by _reputation_, which builds up over time as more users run your signed binaries."
- Reputation model verbatim: unsigned → "People get smart screen warnings for a while until the reputation on that file increases" (per-file, resets every release); OV cert → reputation accumulates on the *certificate*, "You release MyApp-v2.exe. People don't get warnings because the certificate already has a good reputation" (resets on renewal); "You sign your code with an EV (Extended Validation) certificate. People never get warnings, because EV certificates are granted instant SmartScreen reputation."
- "In short: code-sign, prefer an EV (or Azure Artifact Signing) certificate for instant reputation, and expect a short reputation-building period for OV certificates."
- Azure Artifact Signing (formerly Trusted Signing): "Costs USD$10/mo (or USD$120/yr)… Full cloud solution… Signing can be automated (eg. in your CI pipeline)… Artifact Signing certificates get built-in instant reputation for smart-screen and defender."
- HSM warning verbatim: "since June 1, 2023 there has been a policy change… it is no longer possible to download your code signing certificate. It must be either stored in an authorised cloud HSM or a USB HSM will be shipped to you. Many of these solutions will require manual steps and not be compatible with automation / CI."
- signtool path: `vpk pack ... --signParams "/td sha256 /fd sha256 /f yourCert.pfx /tr http://timestamp.comodoca.com"`; default signs all PE files (exe+dll), `--signExclude`, `--signParallel 10`.

## Signals

- The niche's documented mitigation for SmartScreen on unsigned Python/desktop OSS: (a) document "More info → Run anyway", (b) sign — OV builds reputation over releases, EV/Azure Artifact Signing = instant.
