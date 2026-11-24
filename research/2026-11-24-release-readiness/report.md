# Dev Dashboard — готовность к open-source релизу на GitHub

> Mode: deep · Date: 2026-11-24 · Run: research/2026-11-24-release-readiness
> Workers: W1 (web-ресёрч) + W2 (код-аудит) + оркестратор (live-тесты) + cite-checker
> Reuse: research/2026-11-24-dev-dashboard-competitors (128 verified facts), audit/final_report.md

## Executive summary

**Не готово.** Функционально ядро зрелое и честно работает (live-проверено:
API, пробы, env-маскирование, backoff/depends_on, валидация входа), но
приложение сейчас собрано «под владельца»: fresh-инсталл показывает чужому
человеку 7 сервисов автора с `Z:\pet`-путями и его ZeroTier-IP, а собранный
`DevDashboard.exe` в чистой папке отдаёт `{"error": "frontend not built"}` —
окно пустое. Плюс нет git-репо, .gitignore, лицензии, README и версии.
До релиза — один рабочий заход на блокеры (оценка: 6 блокеров, все локальные,
без новой архитектуры) и один — на release-hygiene.

## Метод

- Песочница `Temp\dd_sandbox`: копия только шипящихся файлов, чистый конфиг,
  `core.Dashboard().start()`, прогон API как у новичка/соло-дева/фрилансера.
- Песочница `Temp\dd_exe`: голый `DevDashboard.exe` без репо — эмуляция
  «юзер скачал exe».
- W2 — статический аудит 11 файлов на хардкоды/ассумпции.
- W1 + cite-checker — нормы OSS-релиза ниши (5 репо-эталонов).
- Скриншот fresh-инсталла: `sources/shot_fresh_install.png`.

## Findings

### Q1. Заточенность под владельца — подтверждена, 6 блокеров

**B1. Дефолтный конфиг = личная инфраструктура автора.**
`backend.py:481-506` `DEFAULT_SERVICES` — OmniRoute (`E:\Program Files`),
shot2note ×3 (`Z:\pet\screenshot_to_notes`, autorestart), Syncthing
(`Z:\pet\syncthing`), ZeroTier (`C:\ProgramData\ZeroTier\authtoken.secret`).
`load_services()` (`backend.py:509-516`) **пишет это на диск при первом
запуске**. Live: песочница и exe получили все 7 сервисов; у автора они даже
«up» (пробы находят реальные процессы — и показывают его VPN-IP).
На машине чужого человека: 7 красных/серых строк, попытки автостарта
несуществующих путей → crash-loop → issues-шум. Дефолт должен быть `[]`.

**B2. Собранный exe не находит свой фронтенд.**
`DevDashboard.spec` — onefile, datas `frontend/dist`+`icon.ico` распаковываются
в `sys._MEIPASS`. Но `STATIC_DIR` (`core.py:38`) = `BASE_DIR/frontend/dist`,
а `BASE_DIR` (`backend.py:21-22`) при frozen = dir(exe). `_MEIPASS` нигде не
используется. Live: exe в чистой папке → `GET / → 404 {"error":"frontend
not built"}` — окно пустое. У автора работает только потому, что рядом лежит
репо. Минимальный фикс: `STATIC_DIR` искать сначала в `_MEIPASS`.

**B3. `state.db` пишется в `_MEIPASS` под onefile.**
`storage.py:6` — `dirname(__file__)` без frozen-ветки → БД в temp-распаковке,
стирается при каждом запуске → runs/issues не персистятся в exe-режиме.
Инконсистентно с `backend.BASE_DIR` (там frozen учтён).

**B4. Нет .gitignore / git-репо — `git add .` утечёт всё.**
`state.db*` (история), `services_config.json` (карта инфраструктуры автора,
включая мусорные env-ключи `"123"`, `"ч12"`), `projects_config.json`
(приватные имена проектов), `settings.json`, `logs/` (9 файлов), файл `nul`
(зарезервированное имя — ломает clone на Windows), 15 ресёрч-дампов `*.txt`
в корне, `audit/`, `research/`, `_t/`, `_legacy_qml/` (старый код с теми же
хардкодами), `build/`, `dist/`, `DevDashboard.exe` (40MB) в корне,
`node_modules`, `.omx/`, `.agents/`, `__pycache__`. Также не должны шипиться:
`AGENT_PROMPT.md` (карта инфраструктуры + промпт для агента), возможно
`DESIGN.md`/`AGENTS.md` — решение владельца.

**B5. Нет юзер-записываемой директории конфигов.**
Все конфиги/логи/state.db = рядом с exe/скриптом (`backend.py:23-27`).
Установка в `C:\Program Files` → записи падают (services — молча,
`save_services` глотает OSError; settings — 500). Норма ниши —
`%APPDATA%`/`~/.config` или per-user install dir. Минимум: документировать
«portable app — не ставьте в Program Files» + понятная ошибка при
невозможности записи.

**B6. Сервис с `start` без proc/match/ports показывается «stopped», будучи
живым.** `_probe_service` (`backend.py:679-700`) смотрит только
proc/match/ports/zerotier; spawned-дескриптор (`_jobs`/`_procs`) в пробу не
входит. Live: `dep-worker` (`python -m http.server 8898`) запущен дашбордом,
слушает :8898 — UI показывает «остановлен». Новичок добавляет «просто
команду» и видит ложный статус. У автора не проявлялось — все его сервисы
с proc/match/ports. Фикс: проба должна учитывать живой spawned-дескриптор.

### Q2. Профили пользователей — живой прогон

| Профиль | Что получил | Вердикт |
|---|---|---|
| Новичок (fresh install) | UI работает и красив, но показывает 7 чужих сервисов + битый стаб «Electron App» + ZeroTier-IP чужой сети; onboarding-сценарий существует, но **никогда не открывается сам** (только кнопка в Settings) | Ломается на первом экране |
| Соло-дев | `save`→`start`→`up`→логи→порты — весь цикл работает; валидация имени/json/origin на месте; env PUT + маскирование `••••••••` + `?reveal=1` — ок | Работает, кроме B6 |
| Фрилансер | `autorestart` на крашущемся сервисе → backoff-рестарты + issue «авторестарт через 2с» (live); `depends_on` дождался готовности и поднял dep-worker | Механики работают; B6 портит статус |

Прочие live-находки:
- `api_port` в настройках — поле подсказывает «needs restart», но
  `save_settings` молча игнорирует его; порт 4850 захардкожен в
  core/mcp/dashboard. Занятый порт → мёртвое окно (`api=None`).
- `POST /api/scan` в песочнице → `{"found":[]}` корректно.
- `GET /api/ports` — атрибуция/категории/LAN-флаги работают.
- CSRF-фильтр Origin и allowlist Host — на месте (403 на чужой Origin).
- Плохой JSON/пустое имя/мусорные порты — отвергаются/нормализуются.

### Q3. Release-hygiene

| Пункт | Статус |
|---|---|
| git-репозиторий | **нет** (`fatal: not a git repository`) |
| .gitignore | **нет** — см. B4 |
| LICENSE | нет (нишевый выбор: MIT — у localhost/dekit/lazygit; процесс-менеджеры — Apache-2.0 у process-compose) |
| README для юзера | нет (только README_MCP/AGENTS/DESIGN — внутренние) |
| Версия | нет — ни константы, ни version-resource в exe, ни тегов |
| `DevDashboard.spec` | onefile (несовместим с Velopack-апдейтером), `upx=True` (AV false-positive), datas чистые |
| CI | нет |
| Скриншоты/demo в репо | нет |
| Комментарии/доки | весь код-комментарий и документация — на русском; для OSS-ниши (англоязычной) — барьер контрибьюторов; `index.html` lang="ru" захардкожен |
| Тесты | `test_upgrades.py` хардкодит `Z:\pet\dashboard` и трогает реальную `state.db`; `i18n_check` не покрывает backend/mcp/storage |

### Q4. OSS-норма ниши (W1, верифицировано cite-checker'ом — см. ledger.csv)

Эталон — `marcellosso/localhost` (getlocalhost.app, MIT, окт 2026):
полный набор community-файлов (LICENSE, README, CONTRIBUTING, CODE_OF_CONDUCT,
SECURITY, RELEASING.md, issue/PR-шаблоны, CODEOWNERS, dependabot); README =
wordmark+badges+demo-gif→install-таблица по ОС→first-launch (с явным разделом
про SmartScreen/notarization со скриншотами)→FAQ→compares; релиз = `v*` тег →
CI-матрица → **draft**-релиз с `.sha256` на каждый артефакт →
ручная публикация; тег — единственный источник версии; подпись тирно
(Developer ID > self-signed > ad hoc; Windows PFX опционально).
⚠ Cluster-note: 13 фактов об этом эталоне = один источник (сам репо);
норма «signed update-feeds» (F005/F030) показана только на localhost —
single-source, помечено в ledger.

Сопоставимые: process-compose/lazygit = GoReleaser+checksums+brew;
dekit/mprocs = install.sh/ps1 + npm/PyPI зеркала; dupeguru = Python/Qt
exe-инсталлеры + GPG-подписи; portmaster = релизы без ассетов (свой апдейтер).

PyInstaller-специфика: AV false-positives официально не устранимы (L1,
официальный faq PyInstaller; документировать SmartScreen click-through в
README — нишевой стандарт); `--windowed` детектится *чаще* console;
Azure Trusted Signing $9.99/мес (квота ~5k подписей) — современный
CI-friendly путь подписи; «мгновенная репутация» — формулировка Velopack,
доки Microsoft осторожнее (F022, single-source).

### Q5. Рыночный контекст (reuse verified)

Из `research/2026-11-24-dev-dashboard-competitors/report.md` (128/131
verified): ниша перегрета, но **Windows-capable окно свободно**; наш юнион
(Windows GUI + произвольные процессы + порты + health + автозапуск + env +
issues) никем не покрыт целиком; ближайший аналог getlocalhost.app уже имеет
env-профили, SSH Machines и signed self-update — наши диффы: backoff+
circuit-breaker, depends_on, issues-лента. Чеклист блоков A–E того отчёта
остаётся в силе: подпись/инсталлятор/апдейтер, winget/scoop, авто-детект
env/фреймворков, next-free-port, safe-kill, v1.0-полировка.

## Что блокирует релиз прямо сейчас (must-fix)

1. `DEFAULT_SERVICES = []` (и `DEFAULT_PROJECTS` = [] или реальный tutorial-проект) + авто-открытие онбординга при пустом конфиге
2. `STATIC_DIR`/icon/state.db — резолв через `_MEIPASS` для frozen + `%APPDATA%\DevDashboard` (или `~/.config`) для данных
3. `.gitignore` + вынос личных файлов из будущего репо
4. LICENSE + README.md (EN, wordmark/скриншот/install/SmartScreen-note/config-format) + версия (константа + version-resource + тег)
5. B6: проба учитывает spawned-дескриптор (или форма требует хотя бы одно probe-поле)
6. `upx=False` в spec; решить onefile vs onedir (Velopack)

## Должно быть решено до/при релизе (release, не blocker)

7. Порт 4850: либо конфигурируемый (settings+честный restart), либо fallback на свободный + баннер
8. `zerotier`/`supabase` — документировать как vendor-пробы или вынести в generic-механизм
9. Русские комментарии/доки — позиционирование: RU-first OSS существует, но ниша англоязычная; минимум README/CONTRIBUTING на EN
10. `test_upgrades.py` — chdir-агностик + изоляция от реальных конфигов
11. `scan_roots` default — не parent-installdir при frozen
12. winget/scoop/instаллятор + CI build→sign→release (Azure Trusted Signing ~$10/мес или SignPath free для OSS)

## Contradictions & uncertainty

- Onefile vs onedir: onefile проще раздавать, но ломает `_MEIPASS`-данные
  и Velopack; onedir — норма для инсталлеров. Решение влияет на B2/B3/апдейтер.
- Русскоязычная кодовая база: само по себе не баг, но для OSS-ниши —
  фрикция контрибьюции; пометка «RU codebase» в README — честный минимум.
- macOS «не проверено» — POSIX-ветка есть и skeptic-проход её чинил, но
  реального прогона не было: заявлять можно только как experimental.
- `zerotier` probe читает чужой authtoken.secret — на машине юзера без
  ZeroTier graceful-фейлится, но это недокументированная привилегия.

## Confidence

| Вывод | Уверенность | Основание |
|---|---|---|
| Не готово к OSS-релизу | **high** | 2 live-воспроизведённых блокера (exe=пустое окно; чужой конфиг) + отсутствие базовых файлов репо |
| Ядро функционально зрелое | high | live-прогон API + вчерашний верифицированный аудит фич |
| Windows-ниша свободна | high | 19 тулов, verified ledger прошлого рана |
| Норма релиза = тег→CI→artifacts+sha256+health-файлы | high | 5 репо-эталонов L1 + cite-check |
| POSIX-ветка работоспособна | low | не тестировалась live |

## Sources
- Локальные: `facts/W2.md`, live-логи песочниц, `sources/shot_fresh_install.png`
- W1: `sources/01–12` + `facts.jsonl` + `ledger.csv` (cite-check)
- Reuse: `research/2026-11-24-dev-dashboard-competitors/{report,facts,ledger}`

## Appendix
- Покрытие: `coverage.md` — все Q covered
- Не проверено: реальный прогон на macOS/Linux; `npm run build` из чистого клона; поведение при readonly-FS
- Стоп-критерий: coverage-complete (Q4 волна 1, локальные Q — live-доказаны)
