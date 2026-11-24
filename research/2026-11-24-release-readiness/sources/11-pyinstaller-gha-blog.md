# Source 11 — alexjcoleman.me: "Building your PyInstaller App for multiple OSs with GitHub Actions" (blog, 2023-03-28)

- URL: https://www.alexjcoleman.me/blog/2023-03-28-building-your-pyinstaller-app-for-multiple-oss-with-github-actions.html (fetched via r.jina.ai, full page)
- Publisher: Alex Coleman (personal blog) | Tier: L4 | source_class: independent-secondary
- Fetched: 2026-11-24

## Key verbatim quotes / workflow shape

- Trigger: `on: push: tags: ["v*"]` — "I want to setup an action that will build my executable on a new git tag, zip up all the bits from the build and deposit that in a GitHub release for the associated tag."
- Matrix: `runs-on: ${{ matrix.os }}` over `[ubuntu-latest, macos-latest, windows-latest]`; `actions/setup-python` + `pip3 install pyinstaller`.
- Build: `pyinstaller -n redwrench --onefile --windowed app.py` on macOS/Linux, `pyinstaller -n redwrench --onefile app.py` on Windows ("--windowed isn't a thing on Windows" per the post — author drops it there).
- Publish: zip `dist/` → `softprops/action-gh-release` `with: files: ${{ matrix.os }}-${{github.ref_name}}.zip`.

## Signals

- This is the canonical community recipe for PyInstaller OSS releases: tag → per-OS matrix → onefile → zip per OS → `softprops/action-gh-release`. Confirmed in the wild by several repo workflows surfaced in the same search (e.g. sukritphiboon/fc-inventory uses `softprops/action-gh-release` + SHA-256 checksums + optional `azure/trusted-signing-action` gated behind a repo var).
