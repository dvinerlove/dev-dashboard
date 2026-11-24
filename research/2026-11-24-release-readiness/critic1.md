# critic-1 (skeptic) — регрессии и баги в ee58a82

Scope: backend.py, storage.py, core.py, dashboard.py, mcp_server.py,
process_tree.py, platform_impl.py, App.tsx, spec, test_upgrades.py,
_t/i18n_check.py. `python test_upgrades.py` → **ALL PASS**;
`python _t/i18n_check.py` → clean (но см. F12 — чекер слеп к части ключей).

## P1

**F1. `stop_service` не убивает adopted-pid сервис — «остановил» процесс,
который продолжает жить.** `core.py:1171-1191`: `_stop_service` чистит
`spec["pid"]/pid_ctime` и `_svc_spawn`, затем убивает только `job` +
процессы по `proc/match`. После перезапуска дашборда `_jobs` пуст
(in-memory), `job=None`, а pid из spec в список жертв не входит → для
сервиса без proc/match (ровно сценарий B6) stop возвращает True, ничего не
убив; UI через 4с покажет «stopped» при живом процессе-сироте.
`restart_service` (`:1202`) поверх этого стартует вторую копию. Та же дыра
в-сессии, если `ptree.Job()` кинул OSError в `_do_start` (`:1076-1078` →
job=None). Фикс: kill по popped `_svc_spawn`/spec pid через
`be.kill_proc_tree`, когда job is None.

## P2

**F2. Мусорный `api_port` в settings.json роняет весь дашборд.**
`core.py:2021`: `except OSError` не ловит `OverflowError` (порт >65535,
verified: `socket.bind` бросает OverflowError, не OSError) и `TypeError`
(строка в `range()`). Валидация 1024-65535 есть только в `save_settings`
(`:1757`), `load_settings` грязь с диска пропускает → `dash.start()`
падает до UI. Clamp в `load_settings` или ловить Exception.

**F3. Single-instance сломан на POSIX.** `platform_impl.py:196-202`
возвращает открытый lock-файл; `dashboard.py:50` использует результат
только в `if not` → временный объект GC'ится сразу, flock отпускается →
каждый запуск считает себя первым → N дашбордов на fallback-портах.
Windows-мьютекс живёт в ядре — там всё ок. Фикс: держать ссылку
(`_SINGLETON = pi.acquire_single_instance(...)`).

**F4. `release.yml` `test_upgrades.py` вероятно падает на GitHub
Windows-раннере.** `test_upgrades.py:34` — `assert job is not None`, но
hosted-раннеры выполняют шаги внутри Job Object →
`AssignProcessToJobObject` даёт ACCESS_DENIED → `popen_in_job` возвращает
`job=None` (by design, `process_tree.py:147-151`). Шаг «Run core tests»
ломает релизный пайплайн. Плюс `test1` — `cmd.exe/ping` — тесты
Windows-only, POSIX-ветку релиза проверить нечем (`:32`).

## P3

**F5. Онбординг игнорирует remotes.** `App.tsx:173-185`: условие
`st.services.length===0 && st.projects.length===0` не учитывает
`st.remotes` — конфиг только из удалённых мониторов откроет мастер как
«пустой».

**F6. Порт spawned-сервиса — «чужой» в /api/ports.** `core.py:1778-1786`:
`own` строится по proc/match/pid проектов, `_svc_spawn` и `spec["pid"]`
не учитываются → порт сервиса, запущенного дашбордом без proc/match, не
получает owner и page_title (`:1840`), и `kill_port` его убьёт без
подсказки «это твой сервис».

**F7. `delete_service` сиротит запущенный сервис.** `core.py:1260-1268`:
spec удаляется, но `_jobs[name]`/`_svc_spawn[name]` и сам процесс
остаются; после рестарта процесс жив, а конфига и pid нет — добить его из
UI можно только через kill-port.

**F8. Fallback-порт не виден второму инстансу и MCP.**
`dashboard.py:52-55` пингует `load_settings()["api_port"]` (конфиг, не
bound) — при fallback 4851 окно первого инстанса не поднимется.
`mcp_server.py:14` знает реальный порт только через `DEVDASH_PORT`
(наследуют дети дашборда; внешний агент — нет) + docstring `:3` застрял на
«:4850». Связано: `core.py:2029` env ставится, но ни один consumer кроме
дочерних процессов его не увидит.

**F9. Гонка `_probe_worker` ↔ `_do_start` на `_svc_spawn`.**
`core.py:468-475` читает и `del`-ит dict без `self._lock`, записи под
локом (`:1100`, `:1174`). Check-then-del может снести свежую запись
(самолечится следующим тиком) или дать KeyError → transient «bad spec» +
traceback. Низкая цена, реальная гонка.

**F10. `is_pid_running` без ctime = снятая защита PID-reuse.**
`backend.py:435-439` `pid_ctime` → None если процесс умер до чтения
ctime; `(pid, None)` в `_svc_spawn`/spec сводит проверку к `pid_exists` →
переиспользованный pid примется за свой. Окно узкое, но именно тот край,
ради которого ctime вводили.

**F11. `save_settings`/`_probe_loop` без clamp на диск-грязи.**
`core.py:1765` `tuple(saved["backoff"])` — без `or RESTART_BACKOFF`,
который есть в `__init__:353`; `backoff:[]` с диска → IndexError в
`_svc_autorestart:821`. Там же `float(self._probe_interval)` в
`_probe_loop:413` на мусоре убьёт probe-поток навсегда. Только ручная
порча settings.json, но `_save_json` — не граница доверия.

**F12. i18n_check имеет слепые зоны.** `_t/i18n_check.py:28`: regex
`tr\(\s*"([A-Z_]+)"` берёт только первый литерал — `be.tr("ENABLED" if x
else "DISABLED")` теряет DISABLED; динамические `be.tr(word)` (PILL_*,
`core.py:581`), `be.tr(label)` (PROC_CATS/CATS значения, `core.py:1834`)
не проверяются вовсе. Сейчас ключи есть, но пропажа не поймается.

**F13. `_stop_service` early-return без `_force_probe`.** `core.py:1184-1186`
(`not matched`) выходит без probe — статус висит до следующего тика. Мелочь
в контексте F1.

**F14. `_static` prefix-check — обход через соседа `dist*`.**
`core.py:181-184`: `startswith(normpath(STATIC_DIR))` без os.sep →
`.../frontend/dist2/...` проходит проверку. Нужен существующий каталог
`dist*` рядом — маловероятно, но паттерн дырявый.

## Проверено — ок

- `_DATA_MARKERS` (backend.py:40-44) = реальные файлы; POSIX fresh-run
  пишет только в DATA_DIR (configs/logs/state.db/env), read-only —
  RESOURCE_DIR/_MEIPASS. `load_services` пишет `[]` — ок.
- `storage.py:6` `__import__("backend")` — backend не импортирует storage,
  цикла нет; `makedirs` в `_c()` — ок.
- `allow_reuse_address = not IS_WIN` (core.py:69) — верная логика:
  Windows SO_REUSEADDR разрешает двойной bind, отключение чинит fallback;
  POSIX семантика не меняется.
- `is_pid_running(pid, ctime)` консистентен во всех 8 точках; `_norm_service`
  pid/pid_ctime сохраняет; `save_service` `known`-set pid не стирает.
- `popen_kwargs`/`shell_argv` нетронуты; POSIX Job (pgid/killpg) корректно
  назначается в `start_service_process`.
- `dashboard.py`: `dash.api_port` биндится в `dash.start()` до
  `create_window` — порядок верный; `version.txt` парсится, upx=False.
- `pick_dir` try/except → `(False,msg)` → `{ok:false,msg}` — фронт
  гасит (`r.dir &&`). Onboarding once-only: ref + `uiSetting` + dlg-guard.
