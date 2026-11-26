# Dev Dashboard — что есть

Полный инвентарь функциональности по факту кода. Сухой список, без оценок.
Источники: `backend.py`, `core.py`, `dashboard.py`, `process_tree.py`,
`platform_impl.py`, `storage.py`, `mcp_server.py`, `frontend/src/`.

## Self-update

- POST `/api/self-update` — канал определяется по пути exe: `winget` (под
  `Microsoft\WinGet`) → `winget upgrade --id Dvinerlove.DevDashboard`,
  `scoop` → `scoop update dev-dashboard`, zip → прямое скачивание релиза
  и подмена exe; `dev` (из исходников) — отказ с объяснением.
- Механика: detached ps1-хелпер ждёт смерти pid, применяет обновление,
  перезапускает exe. Не `.bat` — `find`/`timeout` перехватываются
  Git/MSYS-бинарниками на dev-машинах; не `DETACHED_PROCESS` — powershell
  без консоли не стартует. Сервисы переживают обновление (disarm jobs).
- UI: в настройках при наличии новой версии — кнопка «Обновить» рядом
  со ссылкой на релиз; в dev-режиме скрыта.

## Платформа и архитектура

- Десктопное приложение Windows (primary), macOS/Linux частично
- UI: pywebview (Edge WebView2) + React 19 + TypeScript + Tailwind v4
- Бэкенд: Python 3.10+, зависимости только `pywebview`, `pystray`, `pillow`, `psutil`
- Локальный HTTP API `127.0.0.1:4850` (перебор `want..want+9` при занятости)
- Одно окно `1240×780` (min `920×600`), frameless DWM на Windows
- `--web` режим: то же UI+API без окна, в браузере
- Single-instance: mutex (Win) / flock (POSIX); второй запуск поднимает окно первого
- Закрытие окна = свернуть в трей (не выход); трей-меню: «Открыть», подменю «Сервисы»/«Проекты» с start/stop toggle по состоянию (monitor_only/remote — disabled), ребилд каждые 4с, «Выход»
- Global hotkey: Ctrl+Alt+D → показ окна (RegisterHotKey, Windows-only)
- CLI-компаньон: `dashboard.py status|services|projects|ports|start|stop|restart NAME|kill-port N|scan` — запросы к API живого инстанса без открытия окна, exit 0/1
- `DATA_DIR`: `%LOCALAPPDATA%\DevDashboard` / `~/Library/Application Support` / `~/.config/dev-dashboard` (или рядом с кодом при marker-файлах)

## Сервисы

- Spec в `services_config.json`: name, sub, type, ports, proc, match, url, host, port, keyword, container, interval, start, cwd, path, note, env_key, env_file, autorestart, monitor_only, depends_on, env, env_profiles, env_profile, watch, restart_every_min, mem_limit_mb, health_url
- Проба каждые `probe_interval` сек (дефолт 4, диапазон 0.5–60)
- Детекция состояния: TCP-порт открыт / процесс по `proc` (exe) или `match` (cmdline) / fallback по spawn-pid
- Состояния: up, down, dead, off, failed, check
- `dead` при: порт занят чужим pid, процесс есть но порт закрыт, процесс умер снаружи
- Start/stop/restart по одному и `start_all`/`stop_all` (топосорт по depends_on, стаггер 0.8с/0.5с)
- `depends_on`: рекурсивный старт зависимостей, ожидание готовности — `health_url` HTTP 200–399, `ports[0]` TCP, или процесс жив 0.5с; таймаут `dep_timeout` (дефолт 15с) → issue `deps_timeout`; цикл → issue `dep_cycle`
- Авторестарт `autorestart`: backoff `2→5→10→20`с (настраивается), окно 60с, circuit breaker после 5 падений → state `failed` + issue `crash_loop`, сброс при uptime >60с и при ручном старте
- `_start_verify` через 8с: инста-краш (<4с) тоже считается падением
- Логи: stdout+stderr в `logs/<name>.log`, маркеры запусков, чтение хвоста 256КБ, классификация error/warn/info, fallback на event-log
- `monitor_only`: только наблюдение, без actions и без spawn-fallback
- `mem_limit_mb`: рестарт при превышении RSS-лимита дерева (через crash-бюджет — circuit breaker ловит вечный перезапуск)
- `watch`: рестарт при росте mtime файлов в cwd (скан каждый тик, пропуск .git/node_modules/bin/dist/…, bail на 8000 файлах; рестарт через тот же crash-бюджет, что mem_limit)
- `restart_every_min`: плановый рестарт по интервалу (PM2 `--cron-restart` аналог)
- Единый planned-restart блок: mem_limit/watch/cron делят один путь — issue `restart` + `_stop_service` + relaunch через backoff/circuit breaker
- Port auto-remap при старте: `ports[0]` занят чужим pid → скан +20 свободных, `PORT`/`DEVDASH_PORT` в env процесса, issue `PORT_REMAPPED`; spec не мутируется
- `health_url`: готовность зависимости по HTTP 200–399 (поле в диалоге)
- Логи сервисов: хвост `logs/<name>.log` по offset каждый тик → error-строки в issue `log_error` (дедуп 60с, без парсинга истории)
- Токен сервиса: `env_key`+`env_file` → чтение/запись `KEY=value` в .env; проверка наличия ключа каждые 30с → envWarn-бейдж
- `service_targets`: список процессов, которые умрут при stop (для confirm-диалога)
- `port_conflict`: перед стартом → `{port, pid, pname, suggest}`; suggest = первый свободный порт +1..+60
- `api_action` (compat): start/stop/restart с проверкой состояния

## Проекты

- Spec в `projects_config.json`: name, cmd, cwd (обязательны), url, autostart
- Start: `popen_in_job` в Job Object, stdout/stderr → event-log с тегом `[name]`/`[name ERR]`; error-строки → issue `log_error`
- Stop: pid обнуляется до kill (не считается крашем), terminate + Job.terminate + добивка дерева
- Autostart: проекты с `autostart` стартуют при запуске дашборда
- Ре-адопция: поиск процесса по cwd (минимальный pid, без шеллов), `pid_ctime` защита от pid-reuse
- Авто-url: первый LISTEN-порт дерева процесса → `http://localhost:<port>` если url не задан
- Env проекта: `.env` из cwd с маскированием секретов + `missing` из `env_diff`; сохранение перезаписывает `.env` с сохранением комментариев
- `delete_project` не убивает процесс — только память удаления + убрать из списка
- `NAME_TAKEN` на дубль имени при create; dedup по имени и cwd в `add_projects`
- Открыть папку (Explorer), открыть в IDE (cursor/code/codium/insiders/sublime через PATH)

## Скан проектов

- Корни: `scan_roots` из settings (пусто → домашняя папка); кэш 30с
- Обход: skip node_modules/dist/build/__pycache__/venv/target/vendor/obj/bin/out/coverage/DerivedData/Pods/AppData и все dot-директории, глубина ≤4, найденный проект = стоп спуска
- Манифесты по приоритету: Procfile > composer.json > package.json > bin/dev > manage.py > artisan > go.mod > Cargo.toml > pyproject/requirements+entry > .csproj > pubspec.yaml > mix.exs > pom.xml > build.gradle > Gemfile > justfile > Taskfile.yml > Makefile > compose
- Команды запуска: `<pm> run dev|start`, `uv run`, `poetry run`, `pipenv run`, `python`, `dotnet run`, `flutter run`, `mix run|phx.server`, `mvn(w) spring-boot:run`, `gradle(w) run|bootRun`, `bin/rails s`, `bundle exec rackup`, `just`, `task`, `make dev|run|serve|up|start`, `docker compose up`, `php artisan serve`, `go run .`, `cargo run`, `python manage.py runserver`
- PM-детекция: `packageManager` field > pnpm-lock/bun.lock(b)/yarn.lock > npm
- .csproj: только executable (`Sdk.Web|Worker|OutputType=Exe/WinExe`), тесты пропускаются (xunit/nunit/mstest/*.Tests)
- gradle: пропуск `com.android`; `bootRun` при spring (проверяет и settings.gradle)
- pom.xml: `spring-boot:run` только при "spring-boot" в файле
- Score: git +3, branch +1, framework +1, env-template +1, процесс внутри +3, mtime <30д +2 / <180д +1
- URL-префилл: живой LISTEN-порт процесса > `--port`/`PORT=` в команде > `PORT=` в `.env`/`.env.local` > дефолт фреймворка (Vite 5173, Next/CRA/Nuxt/Remix/Nest/Express/Fastify 3000, Angular 4200, Astro 4321, Gatsby/Expo/Django/FastAPI/Starlette 8000, Flask 5000) > `vite.config` `server.port` > `launchSettings.json` `applicationUrl`
- Framework-детекция: JS по deps (next>nuxt>angular>sveltekit>astro>remix>nest>expo>cra>gatsby>vite>express>fastify>vue>svelte>react), Python по pyproject/requirements (Django/FastAPI/Flask/Starlette)
- `env_diff`: `.env` vs `.env.example/.sample/.template/.dist/.defaults` → missing/extra/empty
- `env_gitignore_open`: `.env` есть, `.git` есть, `.gitignore` не покрывает → чип «env в гите»
- `env_committed`: `.env` отслеживается git'ом (`git ls-files --error-unmatch`) → тот же чип
- Worktree-grouping: `.git`-файл → gitdir-pointer → repo_key; N checkout'ов одного репо = одна строка + чипы веток всех worktree'ов
- `compose_services`: сервисы из compose.yml (2-space парсер) → чипы на строке проекта, клик → prefilled `docker compose up <svc>`
- `git_branch`: чтение `.git/HEAD` без subprocess, worktree и detached-sha
- Восстановление: `prj_deleted` memory (10 записей) → чип «удалён ранее», воскрешение полей
- Дубли имён: квалификатор `NAME · PARENT` до 4 уровней
- Кандидаты фильтруются по cwd уже добавленных проектов

## Порты (`/api/ports` каждые 4с)

- Все TCP LISTEN-слушатели машины с атрибуцией: spec proc/match → spawn/adopted pid → pid проекта → цепочка предков до 8 уровней → cmdline содержит cwd проекта
- Категории по имени процесса (~40 имён: db/dev/net/sys/other) и по номеру порта (well-known)
- LAN-экспозиция: bind не на localhost → флаг + ip
- Page-title + favicon: `GET /` → `<title>` и `GET /favicon.ico` → URL (timeout ~0.5с, кэши 60с) — все локальные слушатели (кроме SYSTEM-pid и LAN-only binds), ThreadPoolExecutor(6); favicon → `<img>` в строке
- Score-сортировка: owner/self +100, вес категории, mine +3, lan +2, title +1, age ≥5м/1ч +1
- `bg`: dev-процессы без портов (предки слушателей исключены), сортировка по памяти
- `port_mine`/`port_hidden`: пользовательские метки имён процессов
- `kill_port`/`kill_pid`: валидация, отказ на свой api_port и `_protected_pid` (sys/db-процессы не принадлежащие сервисам — postgres/svchost не убьёшь случайно), добивка только LISTEN-владельцев
- `port_targets`/`pids_on_port`: владельцы порта для диалога
- `GET /api/free-port?from=N`: ближайший свободный порт (from сам считается) → подсказка в KillPortDialog + копия, команда «Найти свободный порт» в палитре
- Zombie-флаги: `cwd_missing` (cwd удалён), `parent_dead` (родитель умер на глазах — был в прошлом снапшоте), `aged` (>24ч); чипы на портах/кандидатах/bg
- Agent-attribution: цепочка предков ≤8 → `claude`/`codex`/`cursor`/`windsurf`/`aider` чип
- Port-watch: новый unattributed LISTEN-порт и смена owner → трей-нотификация (первый снапшот тихий)
- Promote порта → ServiceDialog с prefilled spec (service-candidates по pid)

## Ремоуты (удалённые мониторы)

- Типы: `http`, `tcp`, `docker`; параллельные пробы по своему интервалу (docker 15с, прочие 30с)
- HTTP: GET с timeout 5с, `keyword` — подстрока в 64КБ тела, `env_key`+`env_file` → Bearer+apikey из .env, HTTPS → `cert {d}d` предупреждение при <14 днях
- Availability: каждый прогон → `remote_probes` в state.db; `uptime` (% за 24ч, ≥3 сэмплов) в строке ремоута рядом со спарклайном
- TCP: `create_connection` timeout 3с → `"{ms}ms"`
- Docker: `docker ps` → контейнер по подстроке в Names, State==running → up
- `ms_hist`: последние 30 измерений response-time (http/tcp) → спарклайн в строке
- Состояния: up/dead/off с detail (`unreachable`, `timeout`, `no cli`, `engine down`, `container not found`)

## Автозапуск

- Windows: чтение `HKCU\...\Run` + `StartupApproved\Run` (disabled-байт); macOS: `~/Library/LaunchAgents/*.plist`
- Разделение mine/other: запись «своя» если cmd содержит cwd проекта/сервиса или токены имени/стемы файлов из `start`
- Running-детекция: по exe/name, по пути в cmdline, по cwd процесса внутри папки лаунчера
- Toggle без удаления (StartupApproved `02`/`03` как Task Manager)
- Save (rename = delete+write), delete, confirm для чужих записей
- Свои-незапущенные → problems (`AR_PROBLEM`)

## События / issues

- Deque 120, дедуп подряд same kind+name (count++), персист в SQLite
- Kinds: `crash`, `crash_loop`, `restart`, `port`, `dep_cycle`, `deps_timeout`, `deps`, `log_error`
- `log_error` — только для проектов (pump stdout), дедуп по тексту 60с
- UI: фильтры все/сбои/порты/рестарты/зависимости/логи, время HH:MM или дата, ×count-бейдж
- Секция «Сейчас»: живые problems (мёртвые сервисы/автозапуск) над логом — то, что входит в бейдж
- «Очистить» → `DELETE FROM issues` (персистентно, не воскресает)
- Runs-история: deque 10 на имя `{t0,t1,exit}`, `_run_start` на up, `_run_end` на exit/down/dead
- `problems`: сервисы down/dead без `note` + свои-незапущенные autorun → бейдж `max(issues, problems)`

## ENV и секреты

- Редактор env на сервис/проект в Inspector: таблица key/value, добавление, удаление
- Маскирование: `TOKEN|SECRET|KEY|PASSWORD|PASS|AUTH|CREDENTIAL|JWT|SESSION` → `••••••••`; `?reveal=1` раскрывает
- Авто-secret по regex при добавлении ключа
- Сохранение сервиса: полная замена `spec["env"]`, `restart_required` если up
- Env-профили: `env_profiles` (имя → набор K=V) в spec; чипы в env-редакторе — клик активирует, × удаляет, «Save as profile» снимает текущие overrides (reveal-фетч, masked ••• не сохраняется); активный профиль перекрывает `env` при запуске
- `${VAR}`/`$VAR`/`%VAR%`-экспансия env-оверрайдов из os.environ при запуске
- `cred:<target>` ссылки в env — секрет в Windows Credential Manager (ctypes advapi32), config держит только ссылку; `POST /api/services/<n>/env-secret` пишет в хранилище и подставляет ссылку; reveal резолвит
- Typed env-валидация (warn-only): `*_PORT` → 1-65535, `*_URL/URI/ENDPOINT` → http(s):// → `warnings` в ответах сохранения + янтарные чипы в env-редакторе; никогда не блокирует
- Сохранение проекта: перезапись `.env` с сохранением комментариев и порядка
- Секреты не пишутся в state.db, не логируются

## Inspector (правая/нижняя панель)

- Телеметрия: PID, CPU%, RAM MB, RAM-спарклайн 30 тиков
- Таб Логи: поллинг 1.5с tail=400, поиск, фильтры all/error/warn, перенос, автоскролл с отключением при скролле вверх, копирование, очистка файла
- Таб История: runs с длительностью и exit-бейджем
- Таб ENV: env-редактор с reveal, missing-строки для проектов, баннер «нужен рестарт»
- Таб Конфиг: свитчи autorun/autorestart/autostart + все KV-поля spec, depends_on SVG-граф — BFS-колонки (зависимости слева, зависимые справа), bezier-рёбра, клик по узлу → выбор сервиса, циклы красным, >24 узлов → список; «открыть в редакторе»
- Таб ENV: env-профили чипами над списком (клик=активировать, ×=удалить, «+ Save as profile» из текущих)
- «Скопировать AI-диагностику»: markdown-дамп статуса/pid/port/cmd/cwd/deps/env-ключи/3 runs/120 строк лога в буфер

## UI/UX

- Секции: Обзор, Сервисы, Проекты, Порты, Автозапуск, События, Настройки
- Сайдбар: rail 48px / wide 196px, авто-rail <1150px, драг-ручка 48–320px со snap, бейджи-счётчики, кнопки «Сканировать»/«Освободить порт»
- Топбар: breadcrumb, центрированный поиск (Ctrl+K), live-статус `up/total · RAM`, Start/Stop all, «+ Добавить», toggle Inspector, window-controls
- Обзор: статы, «требует внимания» (failed/crash/circuit_open/squatterPort/warn), живые проекты, запущенные сервисы
- Сервисы: строки 46px с dot-статусом, бейджи autorun/monitor/envWarn, chip-порт (клик открыть/копировать), CPU%+MB+uptime, меню ⋯ (лог/токен/ссылка/папка/история/autorestart/редактировать/удалить)
- CandidatesStrip: бар «Обнаружено · N», разворот grid-rows, список с точкой alive/именем/label/why/портами, поиск >4, клик → prefilled ServiceDialog
- ProjectsStrip: бар «Найдено · N», чекбоксы bulk-add, фильтр по корням, поиск, чипы framework/branch/restored/env-open/env-missing, клик → prefilled ProjectDialog
- Проекты: карточки 46px, dot+edge-статус, framework/branch/env-чипы, chip-порт, MB, действия (папка/IDE/ссылка/start/stop), меню ⋯
- Порты: фильтры все/наши/db/dev/net/sys/other, поиск, hover-действия (promote/mine/hide/copy/kill), секция bg-процессов с kill
- Автозапуск: Switch, dot-статус, метрики, меню редактировать/удалить
- События: фильтры групп, строки с kind-цветом и ×count
- Палитра Ctrl+K: команды, 6 тем, переходы к сервисам/проектам/секциям, старт/стоп/рестарт по имени, русские алиасы
- Диалоги: Service (табы типа, «Дополнительно», isNew), Project (isNew, pick-dir), Onboarding (4 шага: тема/scan_roots/запуск первого сервиса/готово), Confirm, PortConflict (с suggest-портом), KillPort (живой список процессов по порту + подсказка ближайшего свободного), Autorun, Token
- Optimistic UI: `markPending` → спиннер + «Запуск/Остановка» 10с
- Skeleton-строки при первом полле, shimmer в стрипах
- Горячие клавиши: Ctrl+K, Ctrl+I, ArrowUp/Down по списку
- Настройки: версия приложения + «Проверить обновления» (semver-сравнение с GitHub Releases, ссылка на релиз)
- 6 тем: graphite, console, paper, paperdark1 (Midnight), paperdark2 (Espresso), retro (Win95); console = всегда rail + нижний Inspector
- i18n: RU/EN, auto по языку ОС, ~417 ключей, плюрали one/few/many, auto-discovery локалей
- Reduced-motion и reduced-transparency: все анимации глушатся
- Адаптив: метрики <1100px, действия <680px, breadcrumb <1150px, статус <1400px
- A11y: aria-expanded/pressed/busy/current/describedby, Tip-тултипы, фокус-менеджмент, selectable-логи, tabular-nums

## MCP-сервер

- stdio JSON-RPC 2.0, newline-delimited, чистый stdlib (zero deps)
- Прокси к HTTP API; порт: `DEVDASH_PORT` → `api.port` файл → дефолт 4850
- Protocol version `2024-11-05`, capabilities `tools` + `resources`
- 22 tools: `list_services`, `list_projects`, `list_ports`, `get_service_logs`, `get_service_env`, `get_issues`, `get_runs`, `get_settings`, `set_settings`, `scan_projects`, `start_service`, `stop_service`, `restart_service`, `start_project`, `stop_project`, `restart_project`, `kill_port`, `add_service`, `update_service`, `delete_service`, `set_env_profile`, `set_env_profiles`
- Resources: `dashboard://state`, `dashboard://issues`, `dashboard://services/{name}/log`
- Prompts: `debug_service` (spec+log+runs+issues), `health_summary`, `free_port_restart`
- `update_service`/`set_settings` — read-modify-write внутри (фетч→мердж→save, save-эндпоинт стирает непереданные ключи)
- Подключение: mcp.json для Cursor/Cline, TOML для Codex; дашборд должен быть запущен

## Процессы и изоляция

- Windows Job Objects: `KILL_ON_JOB_CLOSE`, CREATE_SUSPENDED → assign → resume, `TerminateJobObject` на стопе — всё дерево мгновенно
- `disarm()` при штатном выходе → сервисы переживают закрытие окна
- Отказ assign (чужой Job) → процесс живёт без изоляции
- POSIX: `start_new_session` + `killpg`; крах дашборда НЕ убивает дерево (сироты подбираются на следующем старте)
- `pid_ctime` защита от pid-reuse на всех проверках живости
- `_find_launcher`: подъём по предкам через run-tools (npm/cargo/go/dotnet/uv и др.) и shell-обёртки (.cmd/.bat/.ps1/.sh)
- `_smart_name`: generic stem/dir → имя от ближайшей осмысленной папки
- `exe_label`: FileDescription/ProductName из version.dll для неизвестных процессов

## Персистентность

- SQLite `state.db` (WAL, busy_timeout 2с): `runs` (50/имя), `issues` (200), ротация при insert, update по `_rid`
- `settings.json`: probe_interval, dep_timeout, backoff, scan_roots, port_mine, port_hidden, svc_deleted, prj_deleted, lang, api_port — валидация на загрузке
- Атомарная запись: tmp + `os.replace`; битый JSON → `.corrupt-<ts>` + дефолт
- Кэши: `_scan_cache` 30с, `_TITLE_CACHE` 60с, `_fw_cache`, `_envinfo`, `_envval` 30с
- localStorage фронт: тема, inspector open/width, railAuto, onboarded, lang

## Безопасность

- Host allowlist: только `127.0.0.1|localhost|::1` — anti-DNS-rebinding
- CSRF: Origin обязан localhost при наличии; тело ≤1MB, обязан JSON-объект
- Path traversal: нормализация + prefix-check на статике
- `_protected_pid`: sys/db-процессы не принадлежащие сервисам нельзя убить
- `allow_reuse_address` off на Windows — второй инстанс не перехватит порт
- Секреты env: маскирование в API, не в БД, не в логах

## Сборка и тесты

- PyInstaller `DevDashboard.spec`: onefile, windowed, datas=`frontend/dist`+`icon.ico`+`locales`, hiddenimports для webview/pystray, `version='version.txt'`
- Packaging: winget manifests (schema 1.9.0, portable zip, алиас `devdash`), scoop manifest (checkver+autoupdate) — подготовлены, не отправлены
- `test_upgrades.py`: 7 тестов (Job kill, backoff+circuit, depends_on, log classify, ENV-API, ротация БД, worktree+compose скан), изоляция `DEVDASH_DATA_DIR`
- `_t/ui_tests/run_ui_tests.py`: playwright-сьют, 10 тестов (mount/console-errors, onboarding, навигация, палитра, start/stop сервиса, диалоги, порты, i18n ru/en, killport), изолированный инстанс на свободном порту
- i18n-чек: `_t/i18n_check.py` — покрытие ключей обеих локалей
