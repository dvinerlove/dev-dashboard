# Dev Dashboard — архитектура и сборка

## Язык

- **English — язык проекта**: код, комментарии, docstrings, коммит-сообщения
  и пользовательские доки (README и т.п.) — только на английском.
- **Русский живёт только в `locales/ru.json`** (UI/server/detail/tpl).
  UI-строки — через `t()`/`be.tr()`, никакого хардкода.
- **Разрешённые исключения** — русский как данные, не текст:
  `CommandPalette.tsx` (поисковые алиасы `сервис`, `запустить`… в `value=`)
  и `OverviewView.tsx` (regex `ключ` матчит локализованный runtime-текст бэка).
- Внутренние доки могут быть на русском: `AGENTS.md`, `DESIGN.md`,
  `research/`, `docs/superpowers/` — рабочие заметки, не код.

## Стек

- **UI**: pywebview (Edge WebView2) + React 19 + TS + Tailwind v4, исходники в
  `frontend/`, собранный `frontend/dist/` отдаётся локальным HTTP-сервером.
- **Ядро**: `core.py` — Qt-free порт `bridge.py` (probe-loop 4с, действия,
  события, runs, HTTP API). `backend.py` — чистая логика (конфиги, пробы,
  реестр, env) — Qt/web не импортирует.
- **Изоляция процессов**: `process_tree.py` — Win32 Job Objects (ctypes,
  KILL_ON_JOB_CLOSE, CREATE_SUSPENDED→assign→resume); `disarm()` при штатном
  выходе, чтобы сервисы переживали закрытие окна в трей. POSIX-ветка —
  `start_new_session`+`killpg` с тем же API (Job/popen_in_job).
- **Платформы**: `platform_impl.py` — единственное место ОС-ветвлений
  (`pi.IS_WIN/IS_MAC/PLATFORM`): shell_argv, popen_kwargs, open_path,
  autorun (Run vs LaunchAgents), single-instance (mutex vs flock).
  `python dashboard.py --web` — режим без окна (API+фронт в браузере).
  `/api/state.platform` → UI скрывает window-controls не на Windows.
- **Персистентность**: `storage.py` — SQLite `state.db` (WAL): история runs
  и issues переживает перезапуск. Секреты ENV туда не пишутся.
- **i18n**: `locales/<lang>.json` в корне — один файл на язык
  (auto-discovery: добавить язык = положить файл, код не трогаем).
  Семантические `SCREAMING_SNAKE_CASE`-ключи, русского текста в коде нет.
  Плоские ключи — UI-строки фронта (`t()`/`useT()` в i18n.ts грузит все
  файлы через `import.meta.glob`); секция `server` — строки API
  (`be.tr`); `detail`/`tpl` — перевод runtime-текста проб (`be.tr_detail`,
  канонический формат — английский). Промах → en → сам ключ. `lang` в
  settings.json: `auto`→язык ОС (system_lang знает только ru/en). Чек
  покрытия: `python _t/i18n_check.py`.
- **MCP**: `mcp_server.py` — stdio JSON-RPC прокси к API (7 tools), см.
  `README_MCP.md`.
- **Процессы**: `process_tree.py` — Windows Job Objects (ctypes): запуск
  CREATE_SUSPENDED → assign → resume, `TerminateJobObject` на стопе,
  `disarm()` при штатном выходе (сервисы переживают выход дашборда).
- **Авторестарт**: backoff 2→5→10→20с (сброс при uptime>60с), circuit
  breaker — 5 падений/60с → state `failed`/`circuit_open` + issue
  `crash_loop`. Ручной старт сбрасывает.
- **depends_on**: `_wait_ready` — `health_url`→HTTP 200-399, `ports[0]`→TCP,
  иначе «процесс жив 0.5с»; таймаут 15с → issue `deps_timeout`, старт отменяется.
- **Логи**: `classify_log_line` → error/warn/info; ошибки → issue
  `log_error` (дедуп 60с). `api_service_log` отдаёт `{t,l}`.
- **ENV**: `spec["env"]` — оверрайды; `GET/PUT /api/services/<name>/env`,
  секреты (`TOKEN|SECRET|KEY|PASSWORD|PASS|AUTH`) маскируются без `?reveal=1`.
- **Точка входа**: `dashboard.py` — Dashboard + окно pywebview + трей
  (pystray). Закрытие окна = свернуть в трей, не выход.
- Легаси Qt Quick — `_legacy_qml/` (bridge.py, ui/, dashboard_old.py),
  локально, в репо нет.

## API :4850

GET `/api/state` — весь UI одним запросом (services/remotes/projects/autorun/
status/issues count/metrics). Остальные GET/POST — см. `core.py::_ApiHandler`.
POST защищён CSRF-фильтром по Origin + Host-allowlist (127.0.0.1/localhost).
GET `/api/ports` — TCP-слушатели с привязкой к сервисам; POST
`/api/show-window` — поднять окно (single-instance mutex в dashboard.py).
Фронт и API на одном origin — CORS не нужен.

## Сборка и проверка

```bash
cd frontend && npm install && npm run build   # tsc -b + vite build → dist/
cd .. && python dashboard.py                  # окно 1240×780, min 920×600
```

- Проверка без окна: `python -c "import core; core.Dashboard().start()"`,
  затем `curl http://127.0.0.1:4850/api/state`.
- Скриншот окна: `python _t/grab.py 1240 780 shots/x.png` (PrintWindow;
  скрипт локальный, в репо нет).
- Скриншот страницы: python-playwright на `http://127.0.0.1:4850`.
- exe: `pyinstaller DevDashboard.spec` (datas уже включает `frontend/dist`).
- Автотесты ядра: `python test_upgrades.py` (Job/backoff/deps/parser/env).

## Осторожно

- `services_data`/`projects_data` — общее состояние, мутировать под `_lock`.
- `save_service`/`save_project`: не переданные *известные* ключи УДАЛЯЮТСЯ
  из spec — слать полный набор полей формы, не патчи.
- Порт :4850 может быть занят старым экземпляром — bind молча падает,
  API тогда отвечает чужой процесс (проверять `/api/state`).
