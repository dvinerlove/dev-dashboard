# MCP-сервер Dev Dashboard

Лёгкий stdio MCP-сервер поверх локального HTTP API (`127.0.0.1:4850`).
Никаких внешних зависимостей — только stdlib Python.

Дашборд должен быть запущен (`python dashboard.py`).

## Подключение

**Cursor** (`~/.cursor/mcp.json` или `.cursor/mcp.json` в проекте):

```json
{
  "mcpServers": {
    "dev-dashboard": {
      "command": "python",
      "args": ["C:\\path\\to\\dev-dashboard\\mcp_server.py"]
    }
  }
}
```

**Cline / Codex** — то же: `command=python`, `args=["C:\\path\\to\\dev-dashboard\\mcp_server.py"]`,
транспорт stdio.

> Порт API по умолчанию — `4850`. Если дашборд слушает другой порт,
> задайте `DEVDASH_PORT` в `env` подключения:
> `"env": {"DEVDASH_PORT": "4851"}`.

## Инструменты

| Tool | Что делает |
|---|---|
| `list_services` | Сервисы и проекты: состояние, порт/IP, метрики |
| `get_service_logs(name, lines=100)` | Последние N строк лога |
| `get_issues` | Активные события (crash, port, deps_timeout, crash_loop, log_error) |
| `get_runs(name)` | История запусков |
| `start_service(name)` / `stop_service(name)` / `restart_service(name)` | Управление сервисами |

## Smoke-тест

```bash
echo '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{}}' | python mcp_server.py
```
