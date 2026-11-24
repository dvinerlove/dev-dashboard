# Coverage matrix

| Q | status | clusters | key sources | gap |
|---|--------|----------|-------------|-----|
| Q1 конкуренты | covered | ~10 | github.com/marcellosso/localhost, Docker docs, RunBay, PortDoc, Laragon/ServBay, Uptime Kuma | live screenshots not reviewed (text-level only) |
| Q2 dark control-panel дизайн | covered | ~8 | primer primitives CSS, Grafana, Linear (secondary), Vercel, M2/M3, Radix | proprietary tokens (Datadog/PagerDuty) непубличны |
| Q3 PyQt6/QSS реализуемость | covered | ~6 | doc.qt.io (L1), KDAB, QFluentWidgets src, PyQt-Frameless-Window, MS DWM docs | StyleKit (Qt 6.12 Labs) — future, не применимо сейчас |
| Q4 аудит кода | covered | — | dashboard.py + спека + конфиги (локальный агент) | — |

Stop criteria: все Q covered, новых измерений в волне не всплыло.
Load-bearing для дизайн-решений: палитра/пилюли/плотность (Q2 — ≥2 кластера),
IA-паттерны (Q1 — несколько независимых приложений), QSS-лимиты (Q3 — L1 Qt docs).
