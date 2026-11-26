"""Dev Dashboard MCP server: stdio JSON-RPC (newline-delimited JSON).

Talks only to the local HTTP API (default :4850) — no business-logic
duplication. Connection (Cursor/Codex/Cline): see README_MCP.md.
"""
import json
import os
import re
import sys
import urllib.request
import urllib.error
import urllib.parse

# API port: DEVDASH_PORT (inherited by dashboard child processes) →
# api.port marker (bound port, external agents) → default 4850
_port = os.environ.get("DEVDASH_PORT")
if not _port:
    try:
        from backend import DATA_DIR, DEFAULT_SETTINGS
        _port = open(os.path.join(DATA_DIR, "api.port"),
                     encoding="ascii").read().strip()
    except (ImportError, OSError):
        _port = None
API = "http://127.0.0.1:" + (_port or str(
    DEFAULT_SETTINGS.get("api_port", 4850)))


def _get(path):
    with urllib.request.urlopen(API + path, timeout=10) as r:
        return json.loads(r.read())


def _post(path, body=None, method="POST"):
    req = urllib.request.Request(
        API + path, data=json.dumps(body or {}).encode(),
        headers={"Content-Type": "application/json"}, method=method)
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


def _proj_action(act):
    def go(name):
        return _post(f"/api/projects/{urllib.parse.quote(name)}/{act}")
    return go


def _spec_data(name, fields):
    """Spec payload for save: 'cmd' aliases 'start'; every supplied key
    is forwarded — unknown spec keys are preserved server-side, but
    known keys absent from the payload get deleted on update."""
    if "cmd" in fields and "start" not in fields:
        fields["start"] = fields.pop("cmd")
    return {"name": name, **fields}


def add_service(name, **fields):
    return _post("/api/services/save",
                 {"old_name": "", "data": _spec_data(name, fields)})


def update_service(name, **fields):
    """Read-modify-write: the save endpoint deletes known keys missing
    from data, so merge the patch into the current spec first."""
    spec = _get("/api/service?name=" + urllib.parse.quote(name))
    if not spec:
        return {"ok": False, "error": "service not found"}
    spec.update(_spec_data(name, fields))
    return _post("/api/services/save", {"old_name": name, "data": spec})


def delete_service(name):
    return _post("/api/services/delete", {"name": name})


def set_settings(settings=None, **flat):
    """Read-modify-write patch of dashboard settings."""
    cur = _get("/api/settings")
    cur.update(settings or {})
    cur.update(flat)
    return _post("/api/settings", cur)


def set_env_profile(name, profile=""):
    return _post("/api/services/" + urllib.parse.quote(name)
                 + "/env-profile", {"profile": profile})


def set_env_profiles(name, profiles):
    return _post("/api/services/" + urllib.parse.quote(name)
                 + "/env-profiles", {"profiles": profiles or {}},
                 method="PUT")


_SERVICE_PROPS = {
    "name": {"type": "string"},
    "start": {"type": "string",
              "description": "launch command ('cmd' also accepted)"},
    "cmd": {"type": "string", "description": "alias of start"},
    "cwd": {"type": "string"},
    "ports": {"type": ["array", "string"],
              "description": "port list or CSV string"},
    "sub": {"type": "string"},
    "autorestart": {"type": "boolean"},
    "monitor_only": {"type": "boolean"},
    "depends_on": {"type": "array", "items": {"type": "string"}},
    "health_url": {"type": "string"},
    "mem_limit_mb": {"type": "integer"},
    "watch": {"type": "boolean"},
    "restart_every_min": {"type": "integer"},
    "env": {"type": "object"},
    "env_profiles": {"type": "object"},
}


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
    {"name": "list_projects",
     "description": "Registered projects: cmd, cwd, url, running/pid",
     "inputSchema": {"type": "object", "properties": {}},
     "_fn": lambda: _get("/api/projects")},
    {"name": "list_ports",
     "description": "TCP listeners with service/project attribution",
     "inputSchema": {"type": "object", "properties": {}},
     "_fn": lambda: _get("/api/ports")},
    {"name": "start_project",
     "description": "Start a project (really launches its process)",
     "inputSchema": {"type": "object", "properties": {
         "name": {"type": "string"}}, "required": ["name"]},
     "_fn": _proj_action("start")},
    {"name": "stop_project",
     "description": "Stop a project (kills its process tree)",
     "inputSchema": {"type": "object", "properties": {
         "name": {"type": "string"}}, "required": ["name"]},
     "_fn": _proj_action("stop")},
    {"name": "restart_project",
     "description": "Restart a project (kills then relaunches its process)",
     "inputSchema": {"type": "object", "properties": {
         "name": {"type": "string"}}, "required": ["name"]},
     "_fn": _proj_action("restart")},
    {"name": "kill_port",
     "description": "Free a TCP port by killing the process(es) "
                    "listening on it",
     "inputSchema": {"type": "object", "properties": {
         "port": {"type": "integer"}}, "required": ["port"]},
     "_fn": lambda port: _post("/api/kill-port", {"port": int(port)})},
    {"name": "scan_projects",
     "description": "Scan configured roots for new project dirs; "
                    "returns candidates in 'found'",
     "inputSchema": {"type": "object", "properties": {}},
     "_fn": lambda: _post("/api/scan")},
    {"name": "get_service_env",
     "description": "Env overrides of a service (secrets masked)",
     "inputSchema": {"type": "object", "properties": {
         "name": {"type": "string"}}, "required": ["name"]},
     "_fn": lambda name: _get("/api/services/"
                              + urllib.parse.quote(name) + "/env")},
    {"name": "get_settings",
     "description": "Dashboard settings (ports, scan roots, autorun, lang)",
     "inputSchema": {"type": "object", "properties": {}},
     "_fn": lambda: _get("/api/settings")},
    {"name": "add_service",
     "description": "Register a new service (full spec save)",
     "inputSchema": {"type": "object", "properties": _SERVICE_PROPS,
                     "required": ["name"]},
     "_fn": add_service},
    {"name": "update_service",
     "description": "Patch a service spec: current spec is fetched, "
                    "fields merged, full spec saved (missing known keys "
                    "would be wiped by the save endpoint)",
     "inputSchema": {"type": "object", "properties": _SERVICE_PROPS,
                     "required": ["name"]},
     "_fn": update_service},
    {"name": "delete_service",
     "description": "Delete a service (stops it first if running)",
     "inputSchema": {"type": "object", "properties": {
         "name": {"type": "string"}}, "required": ["name"]},
     "_fn": delete_service},
    {"name": "set_settings",
     "description": "Update dashboard settings (merged with current, "
                    "saved under lock server-side)",
     "inputSchema": {"type": "object", "properties": {
         "settings": {"type": "object",
                      "description": "settings keys to update"}}},
     "_fn": set_settings},
    {"name": "set_env_profile",
     "description": "Set active env profile of a service "
                    "(empty string clears)",
     "inputSchema": {"type": "object", "properties": {
         "name": {"type": "string"},
         "profile": {"type": "string", "default": ""}},
         "required": ["name"]},
     "_fn": set_env_profile},
    {"name": "set_env_profiles",
     "description": "Replace the env profiles map of a service",
     "inputSchema": {"type": "object", "properties": {
         "name": {"type": "string"},
         "profiles": {"type": "object"}},
         "required": ["name", "profiles"]},
     "_fn": set_env_profiles},
]


RESOURCES = [
    {"uri": "dashboard://state", "name": "Dashboard state",
     "description": "Full /api/state snapshot",
     "mimeType": "application/json"},
    {"uri": "dashboard://issues", "name": "Active issues",
     "description": "/api/issues snapshot",
     "mimeType": "application/json"},
]
RESOURCE_TEMPLATES = [
    {"uriTemplate": "dashboard://services/{name}/log",
     "name": "Service log", "description": "Last log lines of a service",
     "mimeType": "text/plain"},
]

PROMPTS = [
    {"name": "debug_service",
     "description": "Diagnose why a service or project is down or crashing",
     "arguments": [{"name": "name", "required": True,
                    "description": "service or project name"}]},
    {"name": "health_summary",
     "description": "Whole-dashboard health digest — up/down, problems, "
                    "recent issues",
     "arguments": []},
    {"name": "free_port_restart",
     "description": "Plan freeing a busy port and restarting its owner",
     "arguments": [{"name": "port", "required": True,
                    "description": "TCP port to free"}]},
]


def _read_resource(uri):
    def _json(data):
        return {"contents": [{"uri": uri, "mimeType": "application/json",
                              "text": json.dumps(data, ensure_ascii=False,
                                                 indent=1)}]}
    if uri == "dashboard://state":
        return _json(_get("/api/state"))
    if uri == "dashboard://issues":
        return _json(_get("/api/issues"))
    m = re.match(r"^dashboard://services/(.+)/log$", uri)
    if m:
        lines = get_service_logs(urllib.parse.unquote(m.group(1)))
        return {"contents": [{"uri": uri, "mimeType": "text/plain",
                              "text": "\n".join(lines)}]}
    return None


def _prompt_msg(text):
    return {"messages": [{"role": "user",
                          "content": {"type": "text", "text": text}}]}


def _issues_digest(name=""):
    rows = _get("/api/issues")
    if name:
        rows = [i for i in rows if i.get("name") == name]
    if not rows:
        return "none"
    return "\n".join(
        f"- {i.get('kind')}: {i.get('name')} — {i.get('text')}"
        + (f" (x{i['count']})" if (i.get("count") or 1) > 1 else "")
        for i in rows[-15:])


def _render_prompt(name, args):
    """Prompt message text assembled from live dashboard data."""
    args = args if isinstance(args, dict) else {}
    if name == "debug_service":
        svc = str(args.get("name") or "").strip()
        rows = list_services()
        row = next((r for r in rows if r["name"] == svc), None)
        if not row:
            names = ", ".join(
                r["name"] + (" (project)" if r.get("project") else "")
                for r in rows)
            return _prompt_msg(
                f"Unknown name '{svc or '(empty)'}'. Available services "
                f"and projects: {names}. Pick one to diagnose.")
        kind = "project" if row.get("project") else "service"
        spec = _get(f"/api/{kind}?name=" + urllib.parse.quote(svc))
        log = "\n".join(get_service_logs(svc, 80)) or "(no log lines)"
        runs = json.dumps(get_runs(svc)[-5:], ensure_ascii=False)
        return _prompt_msg(
            f"{kind.capitalize()} '{svc}' — state: {row['state']}"
            + (f" ({row['sub']})" if row.get("sub") else "")
            + f", port chip: {row.get('chip') or 'n/a'}.\n"
            f"Spec: {json.dumps(spec, ensure_ascii=False)}\n"
            f"Last log lines:\n```\n{log}\n```\n"
            f"Recent runs: {runs}\n"
            f"Related issues:\n{_issues_digest(svc)}\n"
            "Diagnose the failure and suggest the fix (tools: "
            "get_service_logs, restart_service/restart_project, "
            "update_service, kill_port).")
    if name == "health_summary":
        st = _get("/api/status")
        probs = "\n".join(f"- {p['name']}: {p['why']}"
                          for p in st.get("problems", [])) or "- none"
        return _prompt_msg(
            f"Dashboard status: {st.get('status')}\n"
            f"Services up: {st.get('services_up')}/"
            f"{st.get('services_total')}, projects running: "
            f"{st.get('projects_running')}.\n"
            f"Problems:\n{probs}\n"
            f"Recent issues:\n{_issues_digest()}\n"
            "Summarize the overall health: what is down or crashing "
            "and what to check first.")
    if name == "free_port_restart":
        try:
            port = int(args.get("port"))
        except (TypeError, ValueError):
            return _prompt_msg(
                "No valid 'port' argument given. Tell me which TCP port "
                "to free and I'll plan the kill/restart.")
        targets = _get(f"/api/port-targets?port={port}")
        if not targets:
            return _prompt_msg(
                f"Nothing is listening on TCP port {port} — it is "
                "already free.")
        rows = _get("/api/ports").get("ports", [])
        row = next((r for r in rows if r.get("port") == port), {})
        try:
            free = _get(f"/api/free-port?from={port}").get("port")
        except urllib.error.HTTPError:
            free = None  # endpoint not landed yet — check via list_ports
        holders = ", ".join(f"{t['name']} (pid {t['pid']})"
                            for t in targets)
        hint = (f"Suggested free port: {free}.\n" if free else
                "No free-port suggestion available — pick a candidate "
                "absent from the list_ports tool output.\n")
        action = (f"Owned by dashboard service '{row['owner']}' — "
                  "restart/stop it to free the port "
                  f"(restart_service('{row['owner']}')).\n"
                  if row.get("owner") else
                  "Foreign process — free it with the kill_port tool "
                  f"(category '{row.get('cat', '?')}'); confirm before "
                  "killing a system/db process.\n")
        return _prompt_msg(
            f"TCP port {port} is held by {holders}"
            + (f" — cmd: {row['cmd']}" if row.get("cmd") else "")
            + f".\n{hint}{action}"
            "Plan the steps: free the port, then restart the owner or "
            "relaunch whatever should bind it.")
    raise ValueError(f"unknown prompt {name}")


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
            "capabilities": {"tools": {}, "resources": {},
                             "prompts": {}},
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
    if method == "resources/list":
        return _ok(rid, {"resources": RESOURCES})
    if method == "resources/templates/list":
        return _ok(rid, {"resourceTemplates": RESOURCE_TEMPLATES})
    if method == "resources/read":
        try:
            res = _read_resource(params.get("uri", ""))
        except urllib.error.HTTPError as e:
            return _err(rid, -32603, f"API {e.code}")
        except Exception as e:
            return _err(rid, -32603, str(e))
        return (_ok(rid, res) if res is not None
                else _err(rid, -32602, "unknown resource"))
    if method == "prompts/list":
        return _ok(rid, {"prompts": PROMPTS})
    if method == "prompts/get":
        p = next((x for x in PROMPTS if x["name"] == params.get("name")),
                 None)
        if not p:
            return _err(rid, -32602, "unknown prompt")
        try:
            res = _render_prompt(p["name"],
                                 params.get("arguments") or {})
        except Exception as e:
            return _err(rid, -32603, str(e))
        res["description"] = p["description"]
        return _ok(rid, res)
    return _err(rid, -32601, "method not found") if rid is not None else None


def main():
    for stream in (sys.stdin, sys.stdout):  # JSON-RPC frames are UTF-8
        try:
            stream.reconfigure(encoding="utf-8")
        except AttributeError:
            pass
    out = sys.stdout
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        try:
            msg = json.loads(line)
        except json.JSONDecodeError:
            continue
        if "id" not in msg:          # notification — no reply needed
            continue
        resp = handle(msg)
        if resp is not None:
            out.write(json.dumps(resp, ensure_ascii=False) + "\n")
            out.flush()


if __name__ == "__main__":
    main()
