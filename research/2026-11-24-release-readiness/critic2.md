# Critic-2 — эмпирическая проверка готовности к релизу

> Date: 2026-11-24 · Verifier: critic-2 · Method: clean-dir exe run, sandboxed
> source run, live API, git/gitignore audit, README↔code spot-checks, CI review.
> Все проверки воспроизводимы; live-эксперименты ниже.

## Вердикт: **НЕ ГОТОВО** — один жёсткий блокер + мелкие хвосты

`requirements.txt` и `version.txt` заигнорены правилом `/*.txt` и **не
закоммичены** → CI (`pip install -r requirements.txt`, spec `version='version.txt'`)
и source-install из README падают на чистом клоне. Фикс — 3 строки
(`!requirements.txt`, `!version.txt` в .gitignore + `git add`).

---

## 1. Clean-dir exe test — **PASS**

| Проверка | Результат |
|---|---|
| `dist/DevDashboard.exe` существует, свежий | 40 110 378 B, built 24 Nov 15:43 |
| exe скопирован в `%TEMP%\dd_c2` один, запущен | ок |
| `GET /` | **200**, полноценный React HTML (`<html lang="en">`, hashed assets) — НЕ «frontend not built» |
| `GET /api/state` | `services:[]`, `projects:[]`, `version:0.9.0`, `platform:windows` |
| Файлы рядом с exe | **нет** (только сам exe до и после) |
| `%LOCALAPPDATA%\DevDashboard` | создан: `state.db`(+shm/wal), `services_config.json` (`[]`) |
| Онбординг при пустом конфиге | **авто-открывается** («Первоначальная настройка» 1/3) — скриншот `critic2_exe_shot.png` (playwright, 1240×780) |
| Version resource в exe | `ProductVersion/FileVersion 0.9.0.0`, `LegalCopyright: MIT License` |
| UI пустого состояния | «Всё спокойно», 0 сервисов — чужой инфраструктуры нет |

Фиксы B1/B2/B3/B5 подтверждены и в коде (`backend.py:24` RESOURCE_DIR→_MEIPASS;
`:42-44` DATA_DIR→%LOCALAPPDATA% при отсутствии маркеров; `storage.py:5` DB→
DATA_DIR; `backend.py:501` `DEFAULT_SERVICES=[]`, `:53` `DEFAULT_PROJECTS=[]`),
и live.

## 2. Repo hygiene — **PASS с одним исключением-блокером**

- `git ls-files` (243 файла): **нет** `*_config.json`, `state.db*`, `*.log`,
  `*.txt` в корне, `*.exe`, `nul`, `AGENT_PROMPT.md`, `node_modules`, `audit/`,
  `_t/`, `_legacy_qml/`, `build/`, `dist/`, `skills-lock.json`. `git status` clean.
- `git check-ignore` подтверждён на 16 паттернах (все игнорятся).
- LICENSE — канонический MIT, «Dev Dashboard contributors», 2026.
- Ни один tracked-файл не содержит `Z:\pet`, `C:\Users\adrew`, ZeroTier-IP
  (`git ls-files | grep` → 0 хитов, включая research/).
- ⚠ `research/` (~150 файлов) и `docs/superpowers/specs/` **закоммичены** —
  личных данных нет, но отчёт рекомендовал не шипить; решение владельца.
- ❌ **БЛОКЕР**: `requirements.txt` и `version.txt` попадают под `/*.txt` →
  untracked. Локально есть, в клоне — нет (см. п.5).
- ⚠ мелочь: `node_modules/` игнорится только в `frontend/`; корневой — нет.

## 3. README.md — **PASS с оговорками**

Есть всё требуемое: install (exe+source), SmartScreen-note («More info → Run
anyway»), таблицы схем `services_config`/`projects_config`/`settings`,
data-location таблица (4 случая + `DEVDASH_DATA_DIR`), platform-table
(macOS/Linux = experimental, `--web`), ссылка на README_MCP, «No telemetry…
binds 127.0.0.1 only», MIT.

Spot-checks vs код: ✅ backoff 2→5→10→20 + circuit 5/60с (`core.py:31-34`);
✅ dep_timeout 15 (`:35`); ✅ секреты маскируются (`:45-46`, regex шире — честно);
✅ bind 127.0.0.1 (`:2023`).

Огрехи (не блокеры): `OWNER/dev-dashboard` — плейсхолдер в бейдже/ссылках
Releases (3 места); dev-секция зовёт `python _t/i18n_check.py`, но `_t/` в
.gitignore — у клонирующего файла не будет; в таблице settings нет `api_port`;
скриншота в репо нет (только html-комментарий-плейсхолдер).

## 4. Version consistency — **PASS**

`backend.py:25` VERSION="0.9.0" = `version.txt` filevers/prodvers 0.9.0.0 =
CHANGELOG `## [0.9.0] — 2026-11-24` = exe version-resource 0.9.0.0 (live).
Тега `v0.9.0` пока нет — ожидаемо, создаётся при пуше.

## 5. CI release.yml — **FAIL (сломается на чистом runner)**

Сам workflow корректен: checkout@v4, setup-python@v5 (3.12), setup-node@v4 (22),
`pip install -r requirements.txt pyinstaller`, `npm ci` (package-lock.json
закоммичен ✓), `npm run build`, `python test_upgrades.py` (локально **ALL PASS**,
изолирован через `DEVDASH_DATA_DIR`, chdir-агностик — item 10 закрыт),
`pyinstaller DevDashboard.spec --clean` (`upx=False` ✓ — item 6 закрыт),
pwsh sha256-синтаксис верен, `Compress-Archive` позиционно биндится корректно,
`softprops/action-gh-release@v2` draft+files — ок.

**Но**: на fresh clone `requirements.txt` отсутствует → шаг 4 падает;
даже пропустив его, `version='version.txt'` в spec упадёт в PyInstaller.
Артефакт-пути (`dist/DevDashboard.exe` → zip) верны.

## 6. Fresh-source-run — **PASS**

Чистый `%TEMP%\dd_src` (только 7 шипящихся .py + `frontend/dist`),
`DEVDASH_DATA_DIR` → `core.Dashboard().start()`:
`GET /` 200 HTML; `/api/state` → `services:[]`, `projects:[]`, `version:0.9.0`,
`platform:windows`, `api_port:4850`, `lang:ru` (OS=ru). В DATA_DIR пишутся
только `services_config.json`+`state.db*`; в src — лишь `__pycache__`.
`npm run build` в frontend — проходит (vite 3.66s).

## 7. Residual hardcodes — **PASS**

По шипящимся источникам (`backend/core/dashboard/mcp_server/storage/
process_tree/platform_impl` + `frontend/src`): `Z:\`, `C:\Users`, `adrew`,
`omniroute`, `shot2note`, `pet\.` — **0 функциональных хитов**. Единственное —
`core.py:689-690` комментарий использует «shot2note» как пример name-mangling
(косметика). `index.html` теперь `lang="en"`. Вендор-пробы zerotier/supabase
задокументированы в README (`:77-79`) — item 8 решён документацией.
`ZT_AUTHTOKEN` читает `C:\ProgramData\ZeroTier\...` — легитимный vendor-путь.

## 8. Leftovers / api_port — **PASS (end-to-end, live)**

- `POST /api/settings {api_port:49991}` → `api_port:49991`,
  `restart_required:true`; после рестарта exe **биндится на 49991**, старый
  4850 мёртв. Конфигурируемо честно — item 7 закрыт.
- Плюс fallback: при занятом 4850 дашборд сел на **4851** (live, `core.py:2021`
  `range(want, want+10)`); `DEVDASH_PORT` прокидывается детям, `mcp_server.py:14`
  его читает.
- B6 live: сервис `{name,start}` без proc/match/ports после start →
  `state:"up"`, `metrics:"pid 33976"` (spawned-descriptor fallback,
  `core.py:465-475`) — блокер 5 закрыт.
- `scan_roots` default frozen→`~`, source→parent(BASE_DIR) (`backend.py:949-951`,
  в settings ответе `C:\Users\adrew`) — item 11 закрыт.
- Онбординг авто-открыт — хвост блокера 1 закрыт.
- Открыто по списку «release, не blocker»: item 9 частично (README/CONTRIBUTING
  EN ✓, код-комментарии RU остаются — задокументированная позиция, README
  не дисклеймит «RU codebase»); item 12 (winget/instаллятор/подпись) — нет,
  допустимо для 0.9.0; SmartScreen-нота в README компенсирует.

## Сводка

| # | Пункт | Статус |
|---|---|---|
| 1 | Clean-dir exe | **PASS** |
| 2 | Repo hygiene | **FAIL** — `requirements.txt`+`version.txt` ignored/untracked |
| 3 | README | PASS (мелкие огрехи) |
| 4 | Versions | **PASS** |
| 5 | CI | **FAIL** — следствие п.2, сам yml корректен |
| 6 | Fresh source | **PASS** |
| 7 | Hardcodes | **PASS** |
| 8 | api_port/leftovers | **PASS** |

**Готовность:** все 6 must-fix-блокеров отчёта реально исправлены и
доказаны live; релизу мешает один новый баг гигиены репо (`.gitignore /*.txt`
съел два нужных файла) — чинится тремя строками. После `git add` + push-tag
CI зелёный с высокой вероятностью (все шаги проверены по отдельности).

*Cleanup выполнен: exe убит, %LOCALAPPDATA%\DevDashboard и temp-песочницы удалены,
порты 4850/4851/49991/8899 свободны.*
