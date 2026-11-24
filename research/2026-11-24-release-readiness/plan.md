# Plan — atomic questions

| Q | Вопрос | Метод | Исполнитель |
|---|--------|-------|-------------|
| Q1 | Универсальность кода: personal hardcodes, machine-specific assumptions, i18n gaps, zerotier/monitor_only специфика, что попадёт в git/exe | grep + read core.py, backend.py, dashboard.py, platform_impl.py, process_tree.py, storage.py, mcp_server.py, frontend/src | W2 explore subagent |
| Q2 | Профили пользователей: работает ли на пустом конфиге, что видит новичок, валидна ли типовая соло/фрилансер-нагрузка | sandbox-копия, clean configs, `core.Dashboard().start()`, curl API, playwright shots | оркестратор (hands-on) |
| Q3 | Release-hygiene репо: что в дереве vs что шипить, license, README, version, .gitignore, spec-правки (UPX off, onedir?, version resource) | file inventory + spec review | оркестратор |
| Q4 | OSS-нормы ниши на GitHub: README-структура, license выбор, CI (GitHub Actions PyInstaller), releases, скриншоты/demo, issue templates — как у getlocalhost.app и аналогов | web research, L1 = реальные репо | W1 researcher |
| Q5 | Рыночная норма релиза (re-use): чеклист блоков A–E из competitors-отчёта | цитирование verified-фактов прошлого рана | оркестратор |

## Workers
- W1 (researcher, background): Q4 — sources 01-19, facts/W1.jsonl
- W2 (subagent_explore, background): Q1 — write facts/W2.md (report-style, no jsonl needed for code findings) + list file:line evidence
- W3 (оркестратор): Q2+Q3 hands-on

## Budget: deep — waves ≤2, sources ≤40 (минус уже собранные 81 из прошлого рана — цитируем, не перечитываем)
