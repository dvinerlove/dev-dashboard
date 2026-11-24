# Source 04 — localhost .github/workflows/ci.yml + release.yml + GitHub Releases assets

- URLs:
  - https://raw.githubusercontent.com/marcellosso/localhost/main/.github/workflows/ci.yml
  - https://raw.githubusercontent.com/marcellosso/localhost/main/.github/workflows/release.yml
  - https://api.github.com/repos/marcellosso/localhost/releases
- Publisher: marcellosso/localhost | Tier: L1 | source_class: vendor-authored
- Fetched: 2026-11-24

## ci.yml — verbatim

- Header comment: "Each job runs on a pull request only when files it depends on changed, and on every push to main. The gating is a job-level `if:` on the `changes` job's outputs, never workflow-level `paths:`: a skipped job reports as passing, so a required check never waits for a run that didn't start."
- `on: pull_request: [opened, synchronize, reopened, ready_for_review]` + `push: branches: [main]`; `concurrency: group: ci-${{ github.ref }} cancel-in-progress: true`.
- A `changes` job diffs `HEAD^1 HEAD` and emits per-area booleans (core/macos/desktop/cli) → downstream jobs `if: needs.changes.outputs.X == 'true'`.
- Matrix of jobs: Rust core (Linux), plus macOS/Windows/desktop/cli jobs (per CONTRIBUTING).

## release.yml — verbatim

- `on: push: tags: ["v*"]` AND `release: types: [published]` — tag builds a draft; publishing re-runs workflow for the Homebrew job.
- `permissions: contents: write`; `concurrency: group: release-${{ github.ref }}`.
- Version job: "A release without signed updates would leave every user of it on that version for good, so none is built without the keys." — fails before building if `TAURI_SIGNING_PRIVATE_KEY`, `TAURI_SIGNING_PRIVATE_KEY_PASSWORD`, `SPARKLE_PRIVATE_KEY`, `TAURI_UPDATER_PUBLIC_KEY`, `SPARKLE_PUBLIC_KEY` missing. Tag regex check: `if [[ ! $version =~ ^[0-9]+\.[0-9]+\.[0-9]+$ ]]`.
- macOS job (`runs-on: macos-26`) chooses signing mode by which secrets exist (developer-id / self-signed / ad-hoc), imports `.p12` into a throwaway keychain, builds+signs DMG, `notarytool submit --wait` + `stapler staple` only in developer-id mode, `shasum -a 256` sidecar, signs appcast with Sparkle tools pinned by `SPARKLE_VERSION`/`SPARKLE_SHA256`.

## GitHub Releases (v0.6.0, published 2026-11-14; cadence ~1-2/wk since v0.5.0 on 2026-11-05)

Assets verbatim: `appcast.xml`, `latest.json`, `localhost-0.6.0.dmg`(+`.sha256`), `localhost-app-0.6.0-1.x86_64.rpm`(+`.sha256`), `localhost-app_0.6.0_amd64.AppImage`(+`.sha256`), `localhost-app_0.6.0_amd64.deb`(+`.sha256`), `localhostd` (WSL helper binary), `localhost_0.6.0_x64-setup.exe`(+`.sha256`).

Signal: every release artifact has a `.sha256` sidecar; updater feeds (appcast/latest.json) ship on the release itself so `releases/latest/download/` URLs work.
