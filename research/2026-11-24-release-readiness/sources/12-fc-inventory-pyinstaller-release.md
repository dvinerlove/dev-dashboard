# Source 12 — sukritphiboon/fc-inventory .github/workflows/build-release.yml (PyInstaller OSS release pipeline, in the wild)

- URL: https://raw.githubusercontent.com/sukritphiboon/fc-inventory/main/.github/workflows/build-release.yml
- Publisher: sukritphiboon/fc-inventory | Tier: L1 (repo file) | source_class: independent-primary
- Fetched: 2026-11-24

## Key verbatim quotes / structure

- Header comment: "Build the standalone .exe automatically when a version tag is pushed, attach it to the GitHub Release, and publish SHA-256 checksums. This proves the .exe is reproducibly built from the tagged source."
- `on: push: tags: - "v*.*.*"` + `workflow_dispatch`; `permissions: contents: write`; tests job (pytest) gates the build.
- Build: `pip install -r requirements.txt; pip install pyinstaller` → `pyinstaller --noconfirm --onedir --name FCInventoryTool --add-data ... app.py` on `windows-latest`.
- Signing block verbatim: "# Optional Authenticode signing via Azure Trusted Signing. No-ops until the repo variable AZURE_SIGNING_ENABLED is set to \"true\" and the corresponding secrets/variables are configured. Signing here (before zipping/hashing) ensures the published checksums cover the signed binary, and removes the Windows SmartScreen warning on first run." → `azure/trusted-signing-action@v0.5.9` with endpoint/account/profile vars.
- Ends: `Compute SHA-256 checksums` step, then `softprops/action-gh-release@v2` `if: startsWith(github.ref, 'refs/tags/v')`.

## Signals

- Independent confirmation of the canonical PyInstaller release recipe (tag → tests → onedir build → checksums → action-gh-release) plus the modern optional-signing pattern (Azure Trusted Signing behind a feature-flag variable, unsigned by default).
