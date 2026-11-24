"""MCP-сервер Dev Dashboard: stdio JSON-RPC (newline-delimited JSON).

Ходит только в локальный HTTP API (default :4850) — бизнес-логика не
дублируется. Подключение (Cursor/Codex/Cline): см. README_MCP.md.
"""
import json
import os
import sys
import urllib.request
import urllib.error
import urllib.parse

# порт API: DEVDASH_PORT (наследуют дочерние процессы дашборда) → маркер
# api.port (bound-порт, внешние агенты) → default 4850
_port = os.environ.get("DEVDASH_PORT")
if not _port:
    try:
        from backend import DATA_DIR
        _port = open(os.path.join(DATA_DIR, "api.port"),
                     encoding="ascii").read().strip()
    except (ImportError, OSError):
        _port = None
API = "http://127.0.0.1:" + (_port or "4850")


def _get(path):
    with urllib.request.urlopen(API + path, timeout=10) as r:
        return json.loads(r.read())


def _post(path, body=None):
    req = urllib.request.Request(
        API + path, data=json.dumps(body or {}).encode(),
        headers={"Content-Type": "application/json"}, method="POST")
    with urllib.request.urlopen(req, timeout=10) as r:
        return json.loads(r.read())


def list_services():
    st = _get("/api/state")
    rows = [{"name": s["name"], "state": s["state"], "chip": s.get("chip"),
             "sub": s.get("sub"), "metrics": s.get("metrics"),
             "remote": s.get("remote", False)}
            for s in st["services"] + st["remotes"]]
    rows += [{"name": p["name"], "state": p["state"], "chip": p.get("chip"),
              "sub": p.get("sub"), "metrics": p.get("metrics"),
              "remote": False, "project": True}
             for p in st["projects"]]
    return rows


def get_service_logs(name, lines=100):
    r = _get("/api/service-log?name=" + urllib.parse.quote(name)
             + f"&tail={int(lines)}")
    return [l["t"] if isinstance(l, dict) else l for l in r.get("lines", [])]


def get_issues():
    return _get("/api/issues")


def get_runs(name):
    return _get("/api/runs?name=" + urllib.parse.quote(name))


def _svc_action(act):
    def go(name):
        return _post(f"/api/services/{urllib.parse.quote(name)}/{act}")
    return go


TOOLS = [
    {"name": "list_services",
     "description": "List services and projects: state, port/IP, metrics",
     "inputSchema": {"type": "object", "properties": {}},
     "_fn": lambda: list_services()},
    {"name": "get_service_logs",
     "description": "Last N log lines of a service or project",
     "inputSchema": {"type": "object", "properties": {
         "name": {"type": "string"},
         "lines": {"type": "integer", "default": 100}},
         "required": ["name"]},
     "_fn": lambda name, lines=100: get_service_logs(name, lines)},
    {"name": "get_issues",
     "description": "Active events/errors (crash, port, deps_timeout, "
                    "crash_loop, log_error) with dedup",
     "inputSchema": {"type": "object", "properties": {}},
     "_fn": lambda: get_issues()},
    {"name": "get_runs",
     "description": "History of recent service/project launches",
     "inputSchema": {"type": "object", "properties": {
         "name": {"type": "string"}}, "required": ["name"]},
     "_fn": lambda name: get_runs(name)},
    {"name": "start_service",
     "description": "Start a service (respecting depends_on)",
     "inputSchema": {"type": "object", "properties": {
         "name": {"type": "string"}}, "required": ["name"]},
     "_fn": _svc_action("start")},
    {"name": "stop_service",
     "description": "Stop a service (kills the process tree)",
     "inputSchema": {"type": "object", "properties": {
         "name": {"type": "string"}}, "required": ["name"]},
     "_fn": _svc_action("stop")},
    {"name": "restart_service",
     "description": "Restart a service",
     "inputSchema": {"type": "object", "properties": {
         "name": {"type": "string"}}, "required": ["name"]},
     "_fn": _svc_action("restart")},
]


def _ok(rid, result):
    return {"jsonrpc": "2.0", "id": rid, "result": result}


def _err(rid, code, msg):
    return {"jsonrpc": "2.0", "id": rid, "error": {"code": code,
                                                  "message": msg}}


def _text(data):
    return {"content": [{"type": "text",
                         "text": json.dumps(data, ensure_ascii=False,
                                            indent=1)}]}


def handle(msg):
    if not isinstance(msg, dict):
        return None
    rid, method, params = msg.get("id"), msg.get("method"), \
        msg.get("params") or {}
    if not isinstance(params, dict):
        params = {}
    if method == "initialize":
        return _ok(rid, {
            "protocolVersion": "2024-11-05",
            "capabilities": {"tools": {}},
            "serverInfo": {"name": "dev-dashboard", "version": "1.0.0"}})
    if method == "ping":
        return _ok(rid, {})
    if method == "tools/list":
        return _ok(rid, {"tools": [
            {k: v for k, v in t.items() if k != "_fn"} for t in TOOLS]})
    if method == "tools/call":
        tool = next((t for t in TOOLS if t["name"] == params.get("name")),
                    None)
        if not tool:
            return _err(rid, -32602, "unknown tool")
        try:
            return _ok(rid, _text(tool["_fn"](**params.get("arguments")
                                                or {})))
        except urllib.error.HTTPError as e:
            return _ok(rid, {"content": [{"type": "text",
                                         "text": f"API {e.code}: "
                                                 f"{e.read()[:300]}"}],
                             "isError": True})
        except Exception as e:
            return _ok(rid, {"content": [{"type": "text", "text": str(e)}],
                             "isError": True})
    return _err(rid, -32601, "method not found") if rid is not None else None


def main():
    out = sys.stdout
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        try:
            msg = json.loads(line)
        except json.JSONDecodeError:
            continue
        if "id" not in msg:          # notification — отвечать не нужно
            continue
        resp = handle(msg)
        if resp is not None:
            out.write(json.dumps(resp, ensure_ascii=False) + "\n")
            out.flush()


if __name__ == "__main__":
    main()
