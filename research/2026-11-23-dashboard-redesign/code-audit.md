Subagent agent_id=a19e95ff completed successfully:

I cannot write the file — my toolset in this session is read-only (`read`, `grep`, `find_file_by_name`, `code_search`, `web_search`, `get_output`, `notebook_read`); there is no write/edit tool available to me. The parent agent should save the report below verbatim to `Z:\pet\dashboard\research\2026-11-23-dashboard-redesign\code-audit.md`.

---

# dashboard.py — Read-Only Audit (2379 lines)

Scope: `Z:\pet\dashboard\dashboard.py`, `services_config.json`, `projects_config.json`, `_verify.py`, spec `docs/superpowers/specs/2025-01-redesign-design.md`. All three row widgets implement the spec's `[pill] [name+sub] [chip] [metrics] [▶/■] [↻] [⋯]` pattern — but each builds it differently, which is the root of the alignment complaint.

## 1. UX PROBLEM MAP

**Row misalignment — root cause.** All three row types use freeform `QHBoxLayout` with different column contracts, so nothing lines up across sections and only partially within a section:

- `ServiceWidget` (L1228–1310): `pill(88px fixed) | info(stretch=3) | chip(variable width, natural size) | lbl_status(stretch=2) | [btn_toggle 24px] [btn_restart 24px] [btn_menu 24px]`. Monitor/remote rows omit the two action buttons entirely (L1296–1308) — so metrics and menu columns sit in different X positions between "control" rows and "monitor" rows.
- `ProjectWidget` (L968–1022): same stretches (`info=3`, `status=2`) but the chip (`lbl_url`) is hidden for URL-less projects (L993) → button columns shift left on those rows.
- `AutorunWidget` (L1389–1438): pill is 60px not 88 (L1394), info is `setFixedWidth(480)` (L1413), status is `setFixedWidth(120)` (L1417), and buttons differ again: text "Вкл/Выкл" 48px ghost (L1424–1431) + edit + trash — never play/restart/dots. The cmd is elided at a hardcoded 460px (L1403) unrelated to actual width.
- The "failed" 2px left border (STYLESHEET L58) shifts row content right 2px for dead rows vs. healthy rows — visible jitter when state flips (also unpolish/polish at L202–206).
- Sections have no shared grid: services, remote, projects, autorun are independent `QVBoxLayout`s, so even identical internal geometry can't align across section boundaries.

**Inconsistent patterns between row types:** pill vocabulary/width differs ("работает/остановлен/упал/выкл" 88px vs "вкл/выкл" 60px, L1341–1344 vs L1394,1441–1447); service names are non-interactive `QLabel` but project names become `ClickableLabel` only when a URL exists (L976–987) — same-looking text, different affordance; service "reason" appears under the name (`reason_w`, L1246–1262) while project "упал" state shows nothing under the name; autorun rows use a text toggle button instead of icon buttons.

**Missing affordances / discoverability:**
- `ClickableLabel` has no `accessibleName`, no keyboard focus, no underline — chip and name links are pointer-only.
- Service "убить" button only materializes inside the reason row when a port is squatted (L1360) — the action is invisible until failure.
- `+ Сервис` dialog has 12 fields incl. raw config keys (`env_key`, `env_file`, `match`) — config editing UX, not task UX. No remote-monitor creation path exists in the UI (ServiceDialog never exposes `type`, `host`, `port`, `container`, `keyword`, `interval` — they're only `setdefault`-preserved, L875–877).
- Tray menu is only "Открыть/Выход" (L2337–2347) — no status summary, no quick stop.
- `Сканировать` (L2202) walks the entire parent of `BASE_DIR` (`Z:\pet`) — slow, and the found list dialog is a bare checkbox list with no search.
- Log panel: filter combo sits in a collapsed-by-default header (`ЛОГ ▸`, L1615–1632) — log is undiscoverable; clear button clears view but `entries` keep growing; no copy-all, no auto-scroll lock; `set_filter` re-renders ALL entries each change (L944–949).

**Narrow width / empty states:** min 740px (L1514). Autorun's fixed 480px info + 120px status + pill leaves <100px at minimum width → buttons may clip; `lbl_status` metrics text (`pid · cpu% · MB · uptime`, L418) is long and unbounded (no elision). Empty states exist only for services and projects (L1844–1848, 2141–2146); autorun shows plain `QLabel("Записей в автозагрузке нет")` unstyled (L1828); remote section label hidden until specs exist (L1568) — fine.

**Info hierarchy:** statusbar shows only first problem name + count (L2191–2194) — no way to see which others without scanning; "∞" autorestart glyph in sub text (L1239) is cryptic (tooltip-only); squatter reason text is red 11px under the name — good — but project crashes leave no equivalent reason.

## 2. TECHNICAL RISK MAP

**Threading:** `_probe_worker` (L1696–1735) runs on a raw daemon thread; it reads `self.services_data`, `self.projects_data`, `self._remote_*`, `self._svc_cpu` dicts — all mutated on the GUI thread concurrently (e.g. `services_data.remove` L2063, `.append` L2071, `spec.clear()` L2032 — a mid-iteration `spec.clear()` can produce a KeyError crash of the whole probe, which emits `None` and silently stops updating statuses). `list()` copies the list but not the specs. `psutil.Process.cwd()` is called inside `_autorun_running` per-process (L652–658) — expensive, can block the worker past the 4s tick; `_probing` flag guards overlap (L1691–1694) but a wedged remote probe (5s urlopen + 3s tcp + 3s cert ≈ 11s+) just skips ticks — acceptable but means stale UI silently.

**Probe correctness:**
- `_probe_service` only checks `ports[0]`-first-open (`next(...)`, L448) — Syncthing's second port 8384 ignored; a service listening on a different listed port reports "up" for the wrong port.
- Squatter detection (L450–453) requires `proc` or `match` — a port-only spec can't detect squatting.
- `_port_open` on 127.0.0.1 only — services bound to other interfaces false-negative.
- `proc` matching is exact `p["name"] == spec["proc"]` (L443) — config says `omniroute.exe` but actual name may differ in case already normalized — OK, but `match` substring (`"shot2note.py serve" in cl`) can false-positive on e.g. `pythonw shot2note.py server` or a different venv python.
- `_probe_zerotier` reads `C:\ProgramData\ZeroTier\One\authtoken.secret` (L426) — requires admin; failure → "dead" not "off", which flags a false problem in statusbar.
- `_autorun_is_mine` (L622–625): substring `"z:\pet\"` or `"omniroute"` — any third-party app under Z:\pet becomes "mine" and can be red-flagged; conversely anything outside is "other".
- `_autorun_target` regex (L632) truncates paths at `.exe`/`.cmd` etc. — misses targets whose command is a bare folder or unquoted path with spaces.
- `find_project_pid` picks lowest pid whose cmdline *contains* the cwd path (L291–305) — `code.exe`/terminals excluded via SHELLS but e.g. `node` from *another* project passing the path arg false-matches; also picks the *oldest-looking* pid, not the one spawned.
- `kill_process_by_port` (L269–278) matches ANY conn with `laddr.port == port`, not only LISTEN — can kill a process that merely has an outbound connection *from* that local port. (Also kills everything on the port — no LISTEN filter is a real risk.)

**Watchdog:** restart requires `prev == "up"` transition to down/dead + 30s cooldown (L1754–1764). Good against storms, but: service that never reached "up" (e.g. starts dead at app boot) is never autorestarted; a service flapping faster than probe interval may toggle; `notify_dead` fires only up→dead, not up→down (L1754) — clean stop vs crash indistinguishable if process dies between probes. `start_service` from watchdog is fire-and-forget; no backoff escalation or max-restarts.

**Registry:** `_read_autorun`/`_autorun_disabled` open keys without `KEY_WOW64_64KEY` while writes use it (L594, L2087) — on a 32-bit build this reads/writes different views. `_autorun_set_enabled` writes the 12-byte StartupApproved blob directly (L595–596) — correct format (`02`/`03` + 11 zero bytes) but overwrites any nonstandard blob rather than patching byte 0. Deletes are `DeleteValue` on HKCU Run — user-scope only, safe-ish; confirmation exists (L2077–2081). No backup/export.

**HTTP API (L1462–1505):** `HTTPServer` is single-threaded — a slow/blocking `_call` (BlockingQueuedConnection into GUI thread) serializes all API clients and can deadlock if invoked while the GUI thread is blocked in a modal `QMessageBox` (e.g. POST /stop → stop_process → no dialog for projects, OK; but `start_service` on services isn't reachable via API — projects only). Origin check exists (spec-required CSRF fix, L1493–1497) but only on POST, and `startswith("http://localhost")` also accepts `http://localhost.evil.com`. GET endpoints (`/api/projects`, `/api/logs`) expose cwd paths and full log contents — logs may contain secrets dumped by child processes; `tail` is `int()`-parsed without bounds (huge n is fine memory-wise, negative n slices weirdly). Project name in POST path is `unquote`d then `re.match(.+)` — `(.+)` matches `/` too, so `a/b/start` works — harmless but sloppy; no auth at all beyond origin, by design (localhost).

**Config load/save:** `load_projects`/`load_services` return defaults on ANY exception — a corrupt file silently nukes user config into defaults in memory, though it doesn't rewrite the file unless something calls save. `ProjectDialog.get_data` (L726–734) **drops unknown keys** (rebuilds dict from fields) — e.g. a `tag`/`group` key would be lost on edit; `ServiceDialog.get_data` preserves unknowns via `setdefault` (L875–877) — inconsistent, project side is the bug. No atomic write (`json.dump` direct, L253–255, L366–368) — crash mid-write corrupts config. `load_projects` doesn't validate structure (list of dicts). `pid` is persisted to config on every save — stale pids get probed on startup, mildly wasteful but guarded.

**QProcess lifecycle:** `start_process` (L1148–1164) spawns `cmd.exe /C` — `project["pid"]` is the **cmd.exe pid**, not the actual dev server; `kill_proc_tree` handles that (children recursive), but `is_pid_running(pid)` on the cmd pid is fine since cmd stays alive. If `waitForStarted` fails → `process_finished` marks "упал". `stop_process` sets `_stopping` then kills; if the QProcess already died, `finished` may have already fired — edge handled via flag. `restart_process` calls stop then start synchronously (L1109–1112) — process may not be fully dead; no wait. Old `QProcess` objects parented to self, overwritten each start — previous process objects leak until widget death (small). `handle_stdout` appends each read chunk; lines may be split mid-UTF-8 (decode errors='ignore' eats bytes).

**Memory:** `LogView.entries` grows unboundedly (L924, 940) — every stdout chunk of every project, forever; `QTextEdit` document also grows (no `setMaximumBlockCount`). `_svc_cpu` cache is pruned by pid-existence (L1707–1709) — good. `_remote_last`/`_remote_next` keyed by name — deleted services leave stale entries (harmless). `find_project_pid`/`_proc_snapshot` iterate all processes every 4s tick *per project refresh* (`refresh_state` → `find_project_pid` per widget, L1059) — O(projects × processes); `net_connections` per project in `find_project_ports` — heavy on busy machines, on the GUI thread (L1681–1685 runs in main thread! `refresh_states` calls `find_project_pid`, `find_project_ports`, `is_pid_running` all on UI thread — the periodic freeze source).

**Fragile spots:** `LogView` parses `[tag]` via regex on raw text (L929) — `[...] ` in program output becomes a fake tag; ERR detection is substring `" ERR]"` (L928) — a normal line containing it turns red. `set_state` re-parses squatter info out of the detail string (L1351) — presentation depends on probe's exact format. `scan_projects` os.walk can take minutes on big trees with no progress/cancel. `_env_get` splits on `=` without stripping comments/`export` — standard-ish. `open_folder` uses `os.startfile` on config-supplied path — fine on Windows, no validation.

**Verify coverage (`_verify.py`):** solid offscreen smoke — probes, squatter row, monitor-only buttons, API origin, log panel, statusbar. Gaps: no watchdog/autorestart test, no registry round-trip (spec asked), no narrow-width render, no project start/stop lifecycle test.

## 3. WHAT'S ALREADY GOOD — do not regress

- Probe-on-worker-thread → `probe_done` signal → `apply_probe` GUI boundary is clean (L1694–1735); `_probing` guard prevents overlap.
- Remote probes isolated: `ThreadPoolExecutor(4)`, per-spec intervals (`_remote_interval`), last-result caching for not-due specs (L1711–1726).
- `cpu_percent` cache by pid (L1521, 405–420) — the classic psutil gotcha, handled.
- Squatter detection + one-click "убить" with named-process confirmation (L1351–1364, 1987–2005) — spec's killer feature, done well.
- StartupApproved toggle without deleting Run entries (L588–596) — matches Task Manager semantics.
- Unknown-key preservation in `ServiceDialog.get_data` (L872–877).
- CSRF origin check, BlockingQueuedConnection into GUI for API calls, monitor_only/remote have no control buttons, staggered start/stop-all (L1874–1892), autorestart 30s cooldown, log `entries` kept separately for filter/API, atomic-ish pill/row-failed styling via dynamic property.
- `start_service` PATH fallback to `cmd /c` on FileNotFoundError (L1954–1958).

## 4. IMPROVEMENT OPPORTUNITIES — ranked (UI layer only; probe/worker/config/API intact)

1. **One shared row grid.** Extract a common `RowWidget` skeleton (QGridLayout or fixed columns: pill | info(flex) | chip | metrics(flex) | actions(fixed 3 slots)) used by all four row types; render placeholder 24px spacers where a button is absent so columns align everywhere incl. monitor rows; unify pill to one fixed width (or per-section consistent); reserve the 2px failed border via `border-left` on a fixed-width wrapper or `padding-left` compensation so dead rows don't shift. Fixes the #1 complaint with no backend change.
2. **Unified metrics/elision**: metrics label gets `ElideRight` + max width; autorun's hardcoded 480/120 replaced by the shared columns.
3. **Consistent affordances**: all names clickable-when-linked gets `AccessibleName`, focus, hover underline; reason row under the name for ALL row types (project crashes show "упал" reason too); same icon-button set + ⋯ overflow menu everywhere (autorun gets dots-menu with вкл/выкл/изменить/убрать, or keeps buttons but same geometry).
4. **Log panel**: `setMaximumBlockCount(~2000)`, cap `entries` deque, filter applies incrementally, "Все/Errors" toggle, keep-alive autoscroll; make the log header visible state clearer; error lines from tag `" ERR]"` → proper tag prefix.
5. **Statusbar → problem popover**: `⚠ N` clickable → menu listing all problem rows; jump-to-row on click.
6. **Remote monitor editing**: extend `ServiceDialog` (or a second small dialog) with `type` combobox + conditional fields — currently remote specs are write-only-JSON.
7. **Empty/skeleton states**: rows show "…" pill — add a subtle "probing…" shimmer/first-probe timestamp; consistent styled empty state for autorun.
8. **Backend fixes worth bundling (cheap)**: `net_connections` LISTEN-only in `kill_process_by_port`; atomic config writes (tmp+rename); `load_*` back up corrupt file instead of silent defaults; `ProjectDialog.get_data` preserve unknown keys like ServiceDialog does; WOW64 flag consistency on registry reads; move `find_project_pid`/`find_project_ports` off the UI-thread refresh path (fold into `_probe_worker` payload).
9. **Keyboard/discoverability**: Ctrl+L log toggle, tray menu with N-ok summary + "stop all", tooltips on ghost buttons exist — add shortcut hints.

**Risks to relay:** the biggest live bugs are (a) GUI-thread process scans every 4s (UI freezes — `refresh_states` L1681), (b) `kill_process_by_port` killing non-LISTEN connections, (c) non-atomic config writes + silent-default load path, (d) `spec.clear()` racing the probe worker.

**Could not do:** write the report file (no write tool in this session); run `_verify.py` or inspect the rendered window (read-only mode).