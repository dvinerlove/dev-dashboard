# DESIGN.md — Dev Dashboard

Тёмный десктопный инструмент уровня Linear/OrbStack/Raycast. Плотный, плоский,
семантический: цвет — только для статуса и фокуса, группировка — пространством
и 1px hairline, не рамками.

## Tokens

```yaml
color:
  bg:
    base: "#0B0D11"      # фон окна, сайдбар
    canvas: "#101318"    # основная область
    surface: "#161A22"   # контейнеры строк, инспектор
    hover: "#1C212B"     # hover-состояния, скелетоны
    selected: "#1F2636"  # выбранная строка
  border:
    hairline: "#222733"  # разделители, контуры контейнеров
    strong: "#313848"    # бордеры инпутов, кнопок, диалогов
  text:
    primary: "#ECEFF4"   # ≥14:1 на всех фонах
    secondary: "#8E97A8" # ~6:1 — подписи, команды, метрики
    muted: "#78839A"     # ~4.6:1 — третичный текст, плейсхолдеры
  accent:
    default: "#5E81F4"   # ссылки, фокус, выбранное
    deep: "#4A6BE0"      # фон primary-кнопки (белый текст 4.7:1)
    text: "#8AADFF"      # акцентный текст на тёмных фонах (≥6.8:1)
  status:
    green: "#22C55E"     # up/ok
    amber: "#F59E0B"     # warn, внимание
    red: "#EF4444"       # error, деструктивные действия
    gray: "#6B7280"      # off/unknown-точки
```

## Типографика

```yaml
font:
  ui: '"Geist", "Segoe UI Variable", "Segoe UI", system-ui'
  mono: '"JetBrains Mono", "Cascadia Code", monospace'
size:
  section-title: 11px uppercase tracking-[0.08em] font-medium (muted)
  row-name: 13px medium
  row-sub: 11.5px
  body: 12–13px
numeric: tabular-nums на всех метриках, портах, счётчиках (.font-mono, .tnum)
```

## Принципы

- **Строки, не карточки**: списки — единый контейнер + hairline `border-b`,
  строка 46px (сервисы/проекты), 38px (порты), 34px (события). Вложенных
  рамок внутри списка нет; метрики инспектора — stat-strip через `divide-x`.
- **Статус = точка 8px**: `StatusDot`, цвет семантический. Пилюли запрещены,
  кроме предупреждений (`WarnBadge`, янтарь) и exit-кодов.
- **Motion**: 140ms `cubic-bezier(0.22,1,0.36,1)`, только color/transform/opacity.
  Ноль анимации на навигации/поиске/палитре. `prefers-reduced-motion` → всё off.
- **Глубина**: один слой — `.elev` (inset-блик сверху + мягкая тень) на
  overlay (палитра, диалоги); primary-кнопка — inset-блик, без drop-shadow.
- **Optimistic UI**: действия показывают `запуск…/остановка…` + спиннер
  мгновенно, не дожидаясь поллинга.
- **Скролл**: 6px полупрозрачный, `scrollbar-gutter: stable` — ноль сдвигов.
- **Empty states**: иконка `strokeWidth 1.5` + одна строка мягкого текста.
- **A11y**: строки — `role=button` + Enter/Space; icon-кнопки получают имя
  через `Tip` (aria-label); фильтры — `aria-pressed`; формы сабмитятся Enter.
