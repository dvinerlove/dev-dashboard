# Contributing

## Setup

```bash
pip install -r requirements.txt
cd frontend && npm ci && npm run build && cd ..
python dashboard.py          # windowed
python dashboard.py --web    # headless, UI at http://127.0.0.1:4850
```

## Tests

```bash
python test_upgrades.py        # core: Job objects, backoff, deps, log parser, env
python _t/i18n_check.py        # i18n coverage
cd frontend && npx tsc --noEmit
```

## Rules of the house

- **i18n is mandatory.** Every user-facing string goes through the dictionaries — `t()`/`useT()` + `locales.ts` (RU/EN) on the frontend, `be.tr()` on the backend. Never hardcode a UI string.
- `backend.py` must not import Qt or webview — keep it pure logic.
- Internal docs (`AGENTS.md`, `DESIGN.md`) and code comments are currently in Russian. PRs translating them to English are welcome; new comments may be written in English.
- `save_service`/`save_project` delete keys that were not submitted — always send the full form, never a patch.

## Pull requests

Small, focused diffs. Describe what you tested.
