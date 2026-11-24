# Brief — release-readiness Dev Dashboard (GitHub OSS)

## Вопрос
Готов ли Dev Dashboard к открытому релизу на GitHub? Три стороны:
(a) универсальность — не заточен ли код под машину/конфиги владельца,
(b) профили пользователей — работает ли у новичка / соло-дева / фрилансера,
(c) рыночный контекст — что в нише является нормой релиза (re-use отчёта
research/2026-11-24-dev-dashboard-competitors, 128/131 verified).

## Скоуп релиза (от юзера)
- Формат: open source на GitHub
- Платформы: Windows (окно+трей) + `--web` режим; macOS — «не проверено» пометка
- Аудитория: соло-дев с петами + фрилансер/агентство + новичок

## Контекст продукта
pywebview (WebView2) + React 19/TS/Tailwind фронт, Python core, API :4850,
PyInstaller onefile exe (upx=True, без version resource), MCP-сервер,
SQLite state.db, конфиги JSON в cwd.

## Уже сделано ранее (НЕ повторять)
- Конкурентный анализ + чеклист релиза: research/2026-11-24-dev-dashboard-competitors/report.md
- Аудит фич + skeptic-проход с фиксами: audit/final_report.md
- Автотесты: test_upgrades.py (ALL PASS), i18n_check.py, tsc чистый

## Гэпы этого рана
- Q1 Универсальность: хардкоды Z:\pet/C:\Users, zerotier-специфика, RU в коде,
  персональные файлы, которые уедут в репо/bundle
- Q2 Профили: живой прогон в песочнице — пустой конфиг (новичок),
  типовой соло-дев, фрилансер с 8+ сервисами
- Q3 Release-hygiene: .gitignore/license/README/version/CI, что шипить, что нет
- Q4 OSS-нормы ниши: как оформлены репо конкурентов (getlocalhost.app и др.),
  README-конвенции, CI/CD для PyInstaller (web-ресёрч)
- Q5 Синтез: готов/не готов + блокирующий список

## Тип: decision + survey · Временная чувствительность: 🟠 medium
