# Dev Dashboard — конкурентный анализ и чеклист к релизу

> Mode: deep · Date: 2026-11-24 · Run: research/2026-11-24-dev-dashboard-competitors
> Stopped by: coverage-complete · Workers: 6 + cite-checker · Sources: 81 · Claims: 128/131 verified

## Executive summary

Ниша «дэшборд локальных dev-серверов» в 2026 перегрета — за год вышло 10+ тулов
(бум вызван AI-агентами, плодящими серверы). Почти все — **macOS-only**; окно
Windows-capable продуктов узкое и незанятое платным лидером. Ближайший аналог
Dev Dashboard — **getlocalhost.app** (MIT, Win10/11 через Tauri/Rust): тот же
костяк (проект→сервисы→порты, env-профили, MCP, трей) и у него уже есть фичи,
которых у нас нет (SSH Machines, env-профили, signed self-update). Наше ядро
конкурентоспособно (Job Objects, backoff, circuit-breaker, depends_on, issues),
но до релиза не хватает четырёх блоков: **подпись+инсталлятор+апдейтер**,
**авто-детект env/проектов**, **Windows-распространение** (winget/scoop),
**v1.0-полировка** (версия, README, онбординг-финализация).

## Findings

### Q1: getlocalhost.app — ближайший аналог

MIT-лицензированный десктоп-менеджер процессов. macOS нативный SwiftUI,
Windows 10/11 x64 и Linux — через Tauri на общем Rust-ядре. Модель: Project=
папка, Service=команда в login-shell (на Windows — cmd.exe), Port=TCP-accept
readiness-проба с ~1.5s fallback.

- Авто-детект: скан папки → package.json scripts (с дефолтными портами
  известных фреймворков), compose-файлы, Python apps (venv-детект), Cargo
  binaries — всё предложениями, которые юзер ревьюит
- Порты: атрибуция всех TCP-слушателей; **порт-конфликт → авто-перенос на
  следующий свободный порт per-run**
- Env: слои переменных + **profiles**; секреты в OS-хранилищах (Credential
  Manager на Windows)
- MCP-сервер на 15 тулов на общем background-ядре
- **Machines**: полный контроль удалённой машины по SSH с форвардами портов
- Self-update через GitHub Releases (6-часовые проверки, подписанный)
- Сознательно **без авто-рестарта** (у нас наоборот — backoff+circuit breaker)
- Пока **не подписан**; репо окт 2026, v0.6.0, ~7 звёзд — ранняя стадия

### Q2: Прямые конкуренты

19 тулов; Windows-capable из них: **RunBay** (Windows-only — наш самый прямой
соперник: env profiles + .env editor, depends-order diagram, авто-рестарт,
ngrok + request inspector, .test-домены, port map), **PortDoc** (Rust+web UI,
signed builds), **Kiri** (CLI), **Portmaster** (Go+WebView2 — наша же схема
стека), **Everyport** (Tauri, WSL/SSH/K8s), **Port Detective** (платный, MS
Store), Portarium, Roulette, Port Pilot, localhostkiller (VS Code ext).

Конвергенция детекции: listener enum → **cwd→проект → framework labels →
git branch**; новые помечают *кто запустил* (Claude Code/Codex session).
Health = probe + CPU/mem тренды. Зависимости — `depends_on` (pier/Homeport/
Switchboard — у нас то же поле уже есть).

Уникальные механики: recycled-PID kill-гард, port-remap+undo (Switchboard),
live/error/dead классификация с probe-диагностикой (Portbook),
орфан-процессы (Kiri), **cmdline secret redaction** (Portbook), signed
auto-update (Roulette).

### Q3: Смежные категории

- **Laravel Herd Services panel** — ближайший шипнутый GUI-аналог: start/stop,
  порты, launch-at-login, логи/env — но PHP/Laravel-скоуп, свои рантаймы (€69/год)
- **PM2** — почти паритет по lifecycle, но CLI+SaaS-дашборд, node-центрично
- **ServBay** — MCP-оверлап: агенты стартуют/стопят сервисы, читают логи,
  чекают порты — но managed runtimes, не user-процессы
- **NSSM/WinSW** — Windows service lifecycle (backoff, env, log rotation) —
  per-service конфиги, без дашборда
- supervisord — Unix-only

**Дифференциация: никто из смежных не покрывает наш юнион** — Windows GUI +
произвольные процессы + инвентарь портов + HTTP/TCP health + автозапуск +
env + issues.

Гэпы у нас от них: watch/memory-cap/cron-рестарты (PM2), response-time
display + docker-label discovery (homepage/Dashy), CPU/mem колонки + AI
flagging (Docker Desktop).

### Q4: Авто-конфигурация

**Env-валидация — один индустриальный паттерн** (все 5 тулов):
key-set diff `.env` vs `.env.example` → missing (error), undocumented (warn),
empty (warn). Второе поколение: git-exposure checks (committed-env, not-
gitignored, in-history), typed JSON schema (port/url/enum), `${VAR}` extraction.

**Framework-детект**: Vercel-модель `{every,some}×{path,matchContent,
matchPackage}`; pier: cwd→marker walk-up, argv rules (meta-frameworks first),
deps disambiguate Vite, name-beats-port for infra. **Portlivo folder table
(самая полная)**: Procfile > composer/artisan > package.json scripts
(lockfile-matched pm) > bin/dev|rails > manage.py > go.mod > compose.

**Маппинг на наш сканер**: marker-list, Procfile/compose, `.gitignore`-cover
на `.env`, missing/undocumented issues — всё дёшево.

### Q5: Запросы юзеров

Топ повторяющихся: tray/menubar-поверхность над портами; «какой проект держит
порт» (cwd+favicon/title); **next-free-port finder**; port-readiness wait;
lifecycle-нотификации (новый сервер, смена владельца, crash→relaunch);
**safe-kill с confirm + process-group kill + PID-reuse checks +
protect-листы (БД/OS)**; LAN-exposure warnings; **zombie-детект** (parent
gone, folder deleted, duplicate, >24h); worktree-aware grouping; port
claims/reservations под мульти-агентность; Docker-контейнеры; agent
attribution.

**Windows-спрос реален и выражен в коде**: sonar Windows support пришёл
комьюнити-PR; DevBar — явный Windows-ребилд mac-тулза; Sweepling существует
потому что cc-reaper mac/Linux-only; claude-code issues про орфан-процессы
на Windows (11 bash + 7 node блокируют Git installer). Новые входы (Porticle,
Roulette, portcheck) все шипят Windows.

### Q6: Release-readiness

**Подпись** (MS docs, high confidence): EV больше не обходит SmartScreen —
OV/EV предупреждают одинаково, пока репутация не наберётся («несколько недель
+ сотни чистых установок»). Реалистично для инди: Azure Artifact Signing
~$9.99/мес (организации US/CA/EU/UK; физлица — только US/CA), OV cert
$150–300/год + HSM-токен (с июня 2023 CA/B Forum требует), **SignPath —
бесплатно для OSS**, **MSIX через Store — бесплатная подпись от Microsoft**.

**Дистрибуция**: winget = YAML-PR в winget-pkgs (тихая установка обязательна);
chocolatey = human moderation; **scoop — самый простой** (свой bucket через
BucketTemplate).

**Апдейт**: PyInstaller не имеет встроенного. Варианты: **Velopack** (активный
наследник Squirrel, Python-либа, требует `--onedir`), tufup, DIY
(HTTPS+hash+sign). **Важно: наш текущий spec — onefile → несовместим с
Velopack без пересборки на --onedir.**

**MCP-важность**: упакованный MCP-сервер для Windows-агентов требует подписи
Microsoft Trusted Root — у нас MCP есть, учесть.

**Прайсинг**: норма ниши — **$9–15 одноразово + 7-дневный триал** (Portlivo
$8.99–19.99, Rungeist $14.99). Бесплатные OSS-альтернативы прижимают потолок.
«No telemetry» — хедлайн-фича у обоих платных тулов.

**v1.0-норма**: трей-меню как главная поверхность + опц. окно, global hotkey,
launch-at-login, CLI-компаньон.

## Contradictions & uncertainty

- getlocalhost.app сознательно без авто-рестарта — мы наоборот имеем
  backoff+circuit-breaker; это не баг, а расхождение философий (их аргумент:
  предсказуемость; наш: сервисы-вахтёры). Решение за продуктом.
- Portlivo Windows/Linux — waitlist, не шипнуто; считаю Windows-конкурентом
  «потенциально», не «существующим».
- F183 (EV-bypass removal) — single-source L1 MS Learn doc; принято, но помечено.

## Что нам нужно до релиза — полный чеклист

### Блок A — поставка (критично, без этого релиза нет)
1. **Версия**: `version=` в PyInstaller spec + `VERSION` константа + отображение
   в UI (About/Settings). Сейчас ни версии, ни ресурса версии в exe нет
2. **Инсталлятор**: Inno Setup/MSIX — per-user, silent-флаг для winget, иконка,
   uninstall корректный (сейчас только голый exe)
3. **Подпись**: выбрать путь — Artifact Signing $9.99/мес (быстро, если US/CA)
   / OV $150–300+HSM / SignPath free (OSS) / MSIX-Store (бесплатно, но
   store-ревью). Без подписи — SmartScreen «unrecognized» каждому юзеру
4. **Апдейт**: Velopack (требует пересборки spec на `--onedir`) или
   минимум — check-update endpoint + баннер «новая версия» + ссылка
   (первый релиз может отложить апдейтер, но подпись — нет)
5. **UPX**: выключить — false-positive в антивирусах убивает репутацию
   SmartScreen быстрее, чем она накапливается

### Блок B — Windows-распространение (неделя релиза)
6. winget-манифест (PR в winget-pkgs) — главный канал для dev-инструментов
7. scoop bucket (BucketTemplate — пара часов, запасной канал)
8. GitHub Releases pipeline: build → sign → attach exe+installer →
   release notes

### Блок C — авто-детект (главный продуктовый гэп, отвечает на «нет TG_TOKEN»)
9. **`.env` vs `.env.example` diff при скане**: missing keys → issue
   «нет TG_TOKEN» динамически (заменяет хардкод-note). Паттерн — все 5 env-тулов
10. **Скан не-Node проектов**: `pyproject.toml`/`requirements.txt`/`manage.py`/
    `Procfile`/`docker-compose.yml`/`go.mod` — по таблице Portlivo
    (Procfile > composer > package.json > bin/dev > manage.py > go.mod > compose)
11. **Framework-лейбл** из package.json deps / pyproject (дёшево — карточки
    читаются как у pier/Portlivo)
12. **Page-title probe** на своих портах (`GET /` → `<title>` + favicon) —
    Portbook/pier-фишка, решает «какой из 5 node — мой»
13. **`.gitignore`-cover** на `.env` — если .env не заигнорен → issue
    (dotenv-sentinel-фича, дёшево)

### Блок D — укрепление ядра (конкурентные фичи)
14. **Next-free-port** при конфликте: порт занят → предложить следующий
    свободный (getlocalhost.app, Switchboard — у нас только portconflict-dialog
    без оффера)
15. **Safe-kill**: confirm + protect-листы (postgres/redis/OS-процессы) +
    kill process-group (watcher-респавнит) + PID-reuse check — топ-3 запрос
    юзеров (W5)
16. **Zombie-детект**: сервер чей cwd удалён / parent умер / >24h idle —
    маркировка «можно гасить»
17. **LAN-exposure badge**: laddr `0.0.0.0`/`::` → «видно в сети» (PortDoc/pier)
18. **depends_on-визуализация**: поле есть, граф/порядок старта — нет
    (RunBay имеет depends-order diagram)
19. **Env-профили** (getlocalhost): наборы env для dev/test — у нас env есть,
    профилей нет
20. **Git branch** у проектов (cwd→git rev-parse — у pier/Portlivo; дёшево)

### Блок E — v1.0-полировка
21. README.md юзерский (сейчас только AGENTS/DESIGN/README_MCP)
22. Трей-меню как главная поверхность: быстрый старт/стоп без открытия окна
    (норма ниши — W6); у нас трей есть, но минимальный
23. Global hotkey на показ окна
24. «No telemetry» — явная позиция в README (хедлайн у конкурентов)
25. CLI-компаньон (`devdash ports`/`start`) — норма ниши и корм для MCP-агентов
26. Onboarding: уже есть визард — довести до «пустой стейт → скан → первый
    сервис запущен» за <60с
27. **MCP-подпись**: если MCP регистрируется для Windows-агентов — нужен
    Trusted Root cert (блок A решает)

### Сознательно НЕ делаем для v1.0
- SSH Machines (getlocalhost-фича — крупный скоуп, v2)
- Multi-agent port claims/reservations (нишевый)
- Платная модель — решение за владельцем; норма ниши $9–15+trial, но OSS-
  альтернативы бесплатные
- AI-flagging аномалий (Docker Desktop-фича — шум)

## Sources
[81 источник в sources/ — см. ledger.csv для вердиктов по каждому факту]

## Appendix
- 6 workers wave 1, 0 retries, coverage-complete за 1 волну
- Cite-check: 128 verified / 3 misquoted (PortDoc port-release claim —
  убран; PM2 quote-строка — исправлена; Herd цена €69 не $69 — исправлена)
- Не верифицировано: 0 critical
- Гэпы: frameworks.dev таймаут; github API rate-limit поздно; reddit JSON
  API заблокирован — сентимент-блок из GitHub issues/HN
