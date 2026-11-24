# Source 03 — localhost RELEASING.md + CONTRIBUTING.md + SECURITY.md + issue templates (raw)

- URLs:
  - https://raw.githubusercontent.com/marcellosso/localhost/main/RELEASING.md
  - https://raw.githubusercontent.com/marcellosso/localhost/main/CONTRIBUTING.md
  - https://raw.githubusercontent.com/marcellosso/localhost/main/SECURITY.md
  - https://raw.githubusercontent.com/marcellosso/localhost/main/.github/ISSUE_TEMPLATE/{bug_report.yml,config.yml}
- Publisher: marcellosso/localhost | Tier: L1 | source_class: vendor-authored
- Fetched: 2026-11-24

## RELEASING.md — key verbatim quotes

- "Releases are on GitHub Releases: a DMG for macOS; for Linux, a `.deb`, an `.rpm` and an AppImage; and an installer for Windows. Pushing a `v*` tag runs the [Release workflow]… Then it drafts one GitHub Release with all of them, a SHA-256 for each, and notes generated from the merged PRs. Nothing is public until a maintainer publishes the draft."
- "The tag is the only place the version lives: `v0.3.1` builds version `0.3.1`… Tags are `vMAJOR.MINOR.PATCH`, nothing else; the workflow rejects any other `v*` tag." (SemVer, `0.x` for now)
- "Publishing the release runs the workflow once more, to write the Homebrew cask for its DMG into the tap." (brew install --cask marcellosso/tap/localhost)
- Signing table: Developer ID (5 secrets → notarized) > Self-signed (`SIGNING_CERTIFICATE_P12` today → "First launch needs **Open Anyway**") > ad hoc.
- Windows: "The Windows installer… are signed when the `WINDOWS_CERTIFICATE_PFX`… and `WINDOWS_CERTIFICATE_PASSWORD` secrets exist… Without the secrets, the installer is unsigned: SmartScreen asks first, and the README's Windows section has the steps. … Use a code signing certificate from a certificate authority: SmartScreen gives a self-signed one no trust… An OV certificate still builds reputation with each download; EV certificates usually live on hardware tokens, which this workflow can't use."
- Update feeds: "the release carries `latest.json` for the Linux and Windows app and `appcast.xml` for the macOS app… each signed with the updater keys"; release fails early without them — "Failing is deliberate: a release built without them would install fine but could never update itself".
- "Cutting a release" runbook: green CI → hand-run packages.yml → tag → draft → manual smoke-test checklist → Publish → verify Homebrew cask job.

## CONTRIBUTING.md — key verbatim quotes

- "For anything larger than a small fix, open an issue first so we can agree on the approach before you write it."
- "CI runs the core's tests on Linux, macOS and Windows, the Swift layer's tests, an unsigned app build, and the desktop app's checks… all must pass." Path-gated jobs; "The macOS job also skips draft PRs (macOS minutes cost the most)".
- "By contributing, you agree your contributions are licensed under the MIT license in LICENSE."

## SECURITY.md (13 lines, verbatim)

- "Please don't open a public issue. Report it privately through [GitHub's security advisories](https://github.com/marcellosso/localhost/security/advisories/new)…" / "You'll get an answer within a week." / "Supported versions: Only the latest release gets security fixes."

## Issue templates

- `bug_report.yml` (GitHub form schema): required "What happened", "Steps to reproduce" (placeholder shows Project+Service setup), required Platform dropdown (macOS/Linux/Windows/Windows-Project-in-WSL/CLI), required version input, OS version, logs textarea.
- `config.yml`: `blank_issues_enabled: false` + contact_links → security advisories ("Please report security issues privately, not as a public issue.").
- `feature_request.yml` (21 lines) separate template.
