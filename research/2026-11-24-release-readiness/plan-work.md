# План закрытия блокеров — разбивка по воркерам

## Фундамент (сделано оркестратором, backend.py + storage.py + core.py)
- `RESOURCE_DIR` = _MEIPASS при frozen иначе BASE_DIR → STATIC_DIR/ICON_FILE
- `DATA_DIR` = BASE_DIR если там есть конфиг (portable/dev), иначе
  LOCALAPPDATA/DevDashboard | ~/.config/dev-dashboard | ~/Library;
  override `DEVDASH_DATA_DIR`
- `VERSION = "0.9.0"`, в /api/state; `DEFAULT_SERVICES=[]`, `DEFAULT_PROJECTS=[]`
- `scan_roots`: frozen→~, source→parent(BASE_DIR); `zt_token` spec-override
- `.env` default → DATA_DIR; `config_dir` в настройках → DATA_DIR

## Воркеры (параллельно, файлы не пересекаются)
- **B** core.py + dashboard.py + mcp_server.py (+1 ключ в backend.py):
  B6 spawned-pid проба; api_port из settings + bind-fallback; AUMID;
  pick_dir guard; mcp порт
- **C** frontend/**: onboarding auto-open; html lang; плейсхолдеры;
  version в UI; i18n; `npm run build` + tsc clean
- **D** release-файлы: .gitignore, LICENSE(MIT), README.md(EN),
  CONTRIBUTING, SECURITY, CHANGELOG, .github/workflows/release.yml,
  spec(upx off, version resource), nul-файлы, README_MCP пути
- **E** тесты: test_upgrades.py (без Z:\pet, DATA_DIR-изоляция),
  i18n_check.py (покрытие backend/mcp/storage/process_tree)

## Интеграция → критики
1. Оркестратор: импорты/сборка/test_upgrades/i18n_check/песочница+exe-прогон
2. Critic-1 (skeptic): ревью полного diff — регрессии, frozen-пути, B6
3. Critic-2 (release): повторный прогон чеклиста — exe в чистой папке,
   git status без личных файлов, README-полнота
4. Финал: git init + commit, отчёт готово/не готово
