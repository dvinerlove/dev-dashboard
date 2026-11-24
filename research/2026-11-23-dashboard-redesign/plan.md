# Plan: атомные вопросы

- Q1 Конкуренты — визуальная анатомия: getlocalhost.app (marcellosso/localhost
  на GitHub), Docker Desktop, RunBay (tharana/runbay), PortDoc, Laragon/ServBay,
  Uptime Kuma. Что вытащить: информационная архитектура (как группируют
  сущности), как показывают состояние (слова/цвет/иконки), плотность списков,
  главное действие строки, что делает flow очевидным, типичные UX-решения
  (start/stop all, логи, алерты). Источники: README, docs, скриншоты в репо.
- Q2 Дизайн dark control-panel/deck 2024–2026: Linear, Vercel Dashboard,
  Raycast, Arc, современные sysadmin-инструменты. Палитры (конкретные
  значения/контрасты), типографика (шкала, mono для метрик), spacing rhythm,
  status pills/бейджи, motion principles (длительности, где анимация уместна),
  density для control panels.
- Q3 Реализуемость в PyQt6/QSS: что реально можно сделать (QSS-возможности и
  пределы, кастомная отрисовка, QPropertyAnimation, плавные ховеры, border
  radius, тени, скроллбары, frameless/acrylic на Windows), где грабли
  (QSS не поддерживает transitions/filters, ограничения QScrollArea styling),
  типовые приёмы современных PyQt6-дашбордов. Шрифты с кириллицей на Windows
  (Segoe UI, Cascadia, Inter?).
- Q4 (локальный, отдельный агент) Аудит текущего dashboard.py: карта
  UX-проблем и технических рисков, что болит, что уже хорошо.

Стоп: все Q covered; load-bearing claims — ≥2 кластера или single-source флаг.
Бюджет: deep — ≤2 волны, ≤40 источников.
