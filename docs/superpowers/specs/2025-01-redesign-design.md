# Dashboard Redesign — спека

## Каркас
Одна скролл-страница (QScrollArea на всё), без вкладок. Секции сверху вниз:
ИНФРА · локальные → ИНФРА · удалённые → ПРОЕКТЫ → АВТОЗАПУСК (свои / сторонние свёрнуты).
Снизу — выдвижная панель лога (свёрнута по умолчанию, QPropertyAnimation 150мс).
Статусбар: `● N ок · ⚠ <имя проблемного>` — считает только неожиданные проблемы.

## Строки (заменяют карточки)
Единый паттерн: [пилюля состояния] [имя + причина под ним] [порт-чип] [метрики mono] [▶/■] [↻] [⋯]
- Пилюля: цветной фон 12% + слово. Словарь: работает / остановлен / упал / выкл.
- Причина сбоя — строкой под именем красным: «порт занят pid N (procname) [убить]» — kill_process_by_port одним кликом.
- ⋯ QMenu: лог, токен, url, папка, редактировать, удалить, авто-рестарт.
- Автозапуск — свой статус вкл/выкл × запущен; свои — красное если «вкл·не запущен».
- monitor_only/remote — без кнопок действий, ⋯ остаётся.

## Remote-мониторы
spec `type: http|tcp|docker`; нет type = локальный (как сейчас).
- http: urlopen, status code, латентность, keyword, дни до cert-expiry.
- tcp: create_connection + latency.
- docker: docker ps --format json, состояния cli-нет/engine-выкл/статус контейнера.
- http + env_key: Bearer + apikey-дубль из env-токена (PAT → Z:\pet\dashboard\.env).
- Пробы — ThreadPoolExecutor(4) внутри _probe_worker, per-spec interval (remote 30с, docker 15с).
- Remote = monitor_only; «ожидаемо выкл» через note — не считается проблемой.

## Визуал
Tokens dict: bg#16181d surface#1f222b elevated#262a35 border#2a2f3a
text#e4e6eb/#8b92a3/#5a6072 accent#7aa2f7 ok#9ece6a warn#e0af68 bad#f7768e
Типографика: имя Segoe 13sb, sub 11 muted, порты/метрики Cascadia Mono 11.
Hover: surface→elevated. Упавшая строка — 2px красная кромка слева.

## Фиксы в том же проходе
- Origin-check на :4850 POST (CSRF): Origin отсутствует или localhost — иначе 403.
- Подтверждение kill/stop с именами процессов.
- cpu% сервисов: кеш {pid: psutil.Process}.
- QScrollArea на секциях.
- Start All / Stop All в шапке ИНФРА.
- Трей-уведомление при падении сервиса (notify_dead на сервисы тоже).

## Что НЕ меняем
Probe→signal архитектура, mini_btn/иконки, StartupApproved, env-токен механика,
watchdog, один файл, PyQt6 без новых зависимостей.

## Проверка
ast.parse, offscreen-рендер всех секций (включая remote-mock и worst-case данные),
smoke: watchdog/remote/probe, реестр-круг, затем перезапуск из исходника.
