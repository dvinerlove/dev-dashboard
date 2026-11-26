# Dev Dashboard — чего нет и хотелось бы

Гэпы по сравнению с конкурентами (`research/2026-11-24-dev-dashboard-competitors`)
и техдолг, замеченный в коде. Пункты, реализованные после ресёрча, вычеркнуты.

## Поставка и релиз (критично для v1.0)

- **Подпись кода**: exe без подписи → SmartScreen «unrecognized» каждому юзеру. Пути: Azure Artifact Signing ~$10/мес, OV cert $150–300/год + HSM, SignPath (бесплатно для OSS), MSIX через Store (бесплатная подпись от Microsoft)
- ~~**Инсталлятор**~~ — **не нужен**: zip содержит один portable-exe; winget `NestedInstallerType: portable` сам даёт uninstall-запись, shim в PATH (`devdash`) и корректное удаление. Inno/MSIX не добавляют ничего
- ~~**Авто-апдейт**~~ — **сделано** без Velopack: POST `/api/self-update` — канал по пути exe: winget → `winget upgrade`, scoop → `scoop update`, zip → скачать+подмена exe. Detached ps1-хелпер ждёт смерти pid, применяет, перезапускает; сервисы переживают (disarm). Velopack не нужен: onedir-пересборка дороже выигрыша
- ~~**winget/scoop**~~ — **сделано**: scoop жив (`scoop bucket add dvinerlove`), winget — PR microsoft/winget-pkgs#488869
- ~~**Версия в UI**~~ — **сделано**: «Dev Dashboard v0.9.0» в настройках

## Трей и десктоп-поверхность

- ~~**Трей-меню как главная поверхность**~~ — **сделано**: подменю «Сервисы»/«Проекты» со start/stop toggle, ребилд каждые 4с, monitor_only/remote disabled
- ~~**Global hotkey**~~ — **сделано**: Ctrl+Alt+D → показ окна (RegisterHotKey, Windows)
- ~~**CLI-компаньон**~~ — **сделано**: `status|services|projects|ports|start|stop|restart NAME|kill-port N|scan` в dashboard.py до запуска окна

## MCP (сейчас 22 tools + 3 resources, у getlocalhost — 15)

- ~~Нет tools для проектов~~ — **сделано**: `start_project`/`stop_project`/`restart_project`, `list_projects`
- ~~Нет `list_ports`/`kill_port`~~ — **сделано**
- ~~Нет `scan_projects`~~ — **сделано**
- ~~Нет `get_env`~~ — **сделано** `get_service_env` (секреты маскированы, `?reveal` не отдаётся)
- ~~Нет `get_settings`~~ — **сделано**
- ~~Нет `add_service`/`update_service`/`set_settings`~~ — **сделано**: RMW-семантика внутри (фетч→мердж→save), `delete_service` тоже; всего **22 tools**
- ~~MCP resources~~ — **сделано**: `dashboard://state`, `dashboard://issues`, `dashboard://services/{name}/log` (template); попутно фикс краша stdio на не-ASCII (UTF-8 reconfigure)
- ~~MCP prompts~~ — **сделано**: `debug_service` (spec+log+runs+issues), `health_summary`, `free_port_restart`; capabilities.prompts
- Подпись MCP-сервера для Windows-агентов требует Trusted Root cert

## Процессы и жизненный цикл

- ~~**Zombie-детект**~~ — **сделано**: `cwd_missing`/`parent_dead` (умер на глазах, не исторически)/`aged` флаги на портах, кандидатах и bg-процессах + чип в UI
- ~~**Agent attribution**~~ — **сделано**: цепочка предков ≤8 → `claude`/`codex`/`cursor`/`windsurf`/`aider` чип на портах и кандидатах
- ~~**Port remap per-run**~~ — **сделано**: порт занят чужим процессом при старте → скан +20 свободных, `PORT`/`DEVDASH_PORT` env процессу, issue `PORT_REMAPPED`; spec не мутируется. Undo нет
- ~~**Orphan-процессы**~~ — **сделано** как часть zombie-флагов (`parent_dead`)
- ~~**Watch mode**~~ — **сделано**: `watch` в spec + чекбокс в диалоге; `latest_mtime` walk (пропуск .git/node_modules/bin/dist, bail 8000 файлов) каждый тик, рост mtime → плановый рестарт через crash-бюджет
- ~~**Memory cap restart**~~ — **сделано**: `mem_limit_mb` в spec + поле в диалоге, рестарт через crash-бюджет (circuit breaker ловит перезапуск-спам)
- ~~**Cron/scheduled restarts**~~ — **сделано**: `restart_every_min` в spec + поле в диалоге; единый planned-restart блок с mem_limit/watch
- ~~**`log_error` для сервисов**~~ — **сделано**: хвост `logs/<name>.log` по offset, error-строки → issue с дедупом 60с
- **POSIX-сироты**: крах дашборда на macOS/Linux не убивает дерево процессов (нет аналога KILL_ON_JOB_CLOSE)

## Env

- ~~**Env-профили**~~ — **сделано**: `env_profiles` в spec, чипы в env-редакторе (клик=активировать, ×=удалить, «Save as profile» из текущих overrides), профильные значения перекрывают `env` при запуске
- ~~**Секреты в OS-хранилище**~~ — **сделано** (phase 1): `cred:<target>` ссылки в env → Credential Manager через ctypes (cred_read/write/delete), POST `/api/services/<n>/env-secret`, маскирование+reveal. Phase 2: UI-кнопка в env-редакторе + cred_delete при удалении строки
- ~~**`${VAR}`-экспансия**~~ — **сделано**: `${VAR}`/`$VAR`/`%VAR%` из os.environ в env-оверрайдах при запуске
- ~~**Typed env-валидация**~~ — **сделано** (warn-only): `be.validate_env` — `*_PORT` → 1-65535, `*_URL/URI/ENDPOINT` → http(s)://; `warnings` в ответах save_env/env_profiles/project_env + янтарные чипы в EnvTab. Никогда не блокирует
- ~~**Env в истории git**~~ — **сделано** (базовый уровень): `env_committed` флаг — `.env` отслеживается git'ом → чип ENV_IN_GIT
- ~~**`health_url` в форме**~~ — **сделано**: поле в «Дополнительно» ServiceDialog + фикс вайпа ключа при save_service

## Мониторинг

- ~~**CPU%-колонка**~~ — **сделано**: `{cpu}% · {mb} MB · {uptime}` в строках сервисов
- ~~**Response-time история**~~ — **сделано**: `ms_hist` (30 измерений) на http/tcp ремоутах + `MsSpark` спарклайн в строке
- ~~**Уведомления о событиях**~~ — **сделано**: новый unattributed LISTEN-порт и смена owner → трей-нотификации (`_watch_ports` каждый тик)
- **Docker-управление**: контейнеры только мониторятся (docker monitor) — нет start/stop/logs/exec; нет docker-label discovery
- ~~**Availability-статистика**~~ — **сделано**: `remote_probes` таблица (каждый прогон), `uptime_pct` за 24ч (None при <3 сэмплов) + чип «99.2%» рядом со спарклайном

## Зависимости

- ~~**depends_on визуализация**~~ — **сделано**: SVG мини-граф в Inspector — BFS-колонки (зависимости слева, зависимые справа), клик по узлу → выбор, циклы красным, >24 узлов → fallback-список

## Порты

- ~~**Page-title для чужих портов**~~ — **сделано**: title+favicon для всех слушателей на 127.0.0.1/0.0.0.0 (кроме SYSTEM-pid), ThreadPoolExecutor, кэши 60с
- ~~**Favicon-подбор**~~ — **сделано**: `port_favicon` GET /favicon.ico → `<img>` в PortsView (onError→fallback)
- ~~**Next-free-port finder**~~ — **сделано**: `GET /api/free-port?from=N`, подсказка «ближайший свободный» в KillPortDialog + копирование, команда в палитре (bilingual alias)
- **Порт-claims/reservations**: мульти-агентная резервация портов (нишево, но тренд)

## Скан и проекты

- **WSL-окружения**: проекты/процессы внутри WSL2 невидимы (Everyport умеет)
- ~~**Worktree-aware grouping**~~ — **сделано**: `.git`-файл → repo_key через gitdir-pointer; worktree'ы одного репо = одна строка + чипы веток; primary = основной checkout
- ~~**compose-сервисы по отдельности**~~ — **сделано**: `compose_services` из compose.yml (наивный 2-space парсер, ponytail-потолок) → чип на сервис → prefilled `docker compose up <svc>`
- ~~**url-префилл hardcoded `127.0.0.1`**~~ — частично: auto-url проектов нормализован на `127.0.0.1`; LAN-only слушатель всё ещё даст недостижимый url (edge case)

## UI

- ~~**Onboarding до «первый сервис запущен»**~~ — **сделано**: 4-й шаг LAUNCH — top-3 найденных проектов (fallback: service candidates) с «Add & run», live-статус через poll, шаг DONE показывает запущенное
- ~~**Отображение версии**~~ — **сделано** (см. выше)
- ~~**UI-тесты**~~ — **сделано**: `_t/ui_tests/run_ui_tests.py` — playwright, 10 тестов (mount/nav/palette/start-stop/i18n/killport), изолированный инстанс :4870+
- ~~**`localhost` vs `127.0.0.1`**~~ — **сделано**: везде `127.0.0.1`

## Техдолг

- ~~**`test_upgrades.py` пишет в боевую `state.db`**~~ — изоляция `DEVDASH_DATA_DIR` была в коде изначально; загрязнение было от старого запуска, вычищено `clear_issues`
- ~~**Settings RMW**~~ — проверено: `save_settings` уже полностью под `_lock`, гонки нет
- ~~**`aria-controls` стрипов**~~ — **сделано**: id перенесён на всегда смонтированный grid-wrapper
- ~~**Контраст env-чипов**~~ — **сделано**: `/12` → `/20` + `font-medium`
- ~~**`_env_port` без bound**~~ — **сделано**: `<= 65535`
- ~~**Бейдж событий смешивает issues+problems**~~ — **сделано**: секция «Сейчас» в EventsView показывает problems над логом — визуальное противоречие устранено

## Сознательно отложено (не для v1.0)

- **SSH Machines**: полный контроль удалённой машины по SSH с форвардами (getlocalhost-фича, крупный скоуп)
- **Request inspector / туннели**: ngrok-подобный прокси + `.test`-домены (RunBay)
- **AI-flagging аномалий**: эвристика «подозрительный процесс» (Docker Desktop — шум)
- **Платная модель**: норма ниши $9–15 + trial; решение за владельцем, OSS-альтернативы бесплатны
- **Multi-agent port claims**: резервации портов между агентами (нишевый кейс)
