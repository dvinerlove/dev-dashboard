// Types and client for the local API :4850 (core.py)

export type SvcState = "up" | "down" | "dead" | "off" | "check" | "failed";

export interface LogLine {
  t: string;
  l: "error" | "warn" | "info";
}

export interface ServiceCandidate {
  name: string;
  pid: number;
  proc: string;
  match: string;
  ports: number[];
  start: string;
  cwd: string;
  cat: string;
  label: string;
  hint?: Partial<ServiceSpec> | null;
  alive?: boolean;
  why?: string[];
  zombie?: string | null;   // "cwd_missing" | "parent_dead" | "aged"
  agent?: string | null;    // "claude" | "codex" | "cursor" | "windsurf" | "aider"
  score: number;
}

export interface EnvVar {
  key: string;
  value: string;
  secret: boolean;
}

export interface EnvWarn {
  key: string;
  code: string;
  msg: string;
}

export interface PortRow {
  port: number;
  pid: number;
  proc: string;
  cmd: string;
  owner: string | null;
  self: boolean;
  cat: "db" | "dev" | "net" | "sys" | "other";
  label: string;
  mine: boolean;
  hidden: boolean;
  lan?: string | boolean;  // bind ip or true; truthy = LAN-exposed
  title?: string;
  favicon?: string;
  age?: number;
  score?: number;
  zombie?: string | null;
  agent?: string | null;
}

export interface BgProc {
  name: string;
  pid: number;
  mb: number;
  owner: string | null;
}

export interface Metrics {
  pid: number;
  cpu: number;
  mb: number;
  up: string;
}

export interface ServiceRow {
  name: string;
  sub: string;
  state: SvcState;
  pillText: string;
  tone: string;
  failed: boolean;
  metrics: string;
  warn: boolean;
  chip: string;
  chipUrl: string;
  monitor: boolean;
  reason: string;
  reasonKey?: string;  // untranslated kind ("circuit_open") — reason itself is localized
  squatterPort: number;
  autorestart: boolean;
  hasToken: boolean;
  hasUrl: boolean;
  hasPath: boolean;
  remote: boolean;
  deps?: string[];  // depends_on names, for the inspector dep graph
  inAutorun?: boolean;
  arName?: string;
  envWarn?: string;
  m?: Metrics;
  ms_hist?: number[];  // last probe ms (http/tcp remotes), oldest → newest
  uptime?: number | null;  // remotes: probe uptime % (0–100), null = n/a
}

export interface ProjectRow {
  name: string;
  sub: string;
  state: SvcState;
  failed: boolean;
  metrics: string;
  chip: string;
  chipUrl: string;
  running: boolean;
  pid: number;
  cwd: string;
  framework?: string;
  branch?: string;
  envMissing?: string[];
  envExtra?: string[];
  envEmpty?: string[];
  envOpen?: boolean;
  m?: Metrics;
}

export interface AutorunRow {
  name: string;
  sub: string;
  pillText: string;
  tone: string;
  failed: boolean;
  metrics: string;
  arEnabled: boolean;
  mine: boolean;
  self?: boolean;
  state: SvcState;
}

export interface Issue {
  t: number;
  kind: "crash" | "port" | "restart" | "deps" | string;
  name: string;
  text: string;
  count: number;
}

export interface Run {
  t0: number;
  t1: number | null;
  exit: string | null;
}

export interface DashState {
  services: ServiceRow[];
  remotes: ServiceRow[];
  projects: ProjectRow[];
  autorunMine: AutorunRow[];
  autorunOther: AutorunRow[];
  status: string;
  problems: { name: string; why: string }[];
  issues: number;
  infraUp: number;
  infraTotal: number;
  platform?: string;
  lang?: string;
  version?: string;
  updChannel?: "dev" | "git" | "winget" | "scoop";
  memMb: number;
  ts: number;
}

export interface ServiceSpec {
  name?: string;
  sub?: string;
  type?: string;
  ports?: number[];
  proc?: string;
  match?: string;
  url?: string;
  host?: string;
  port?: number;
  keyword?: string;
  container?: string;
  interval?: number;
  start?: string;
  cwd?: string;
  path?: string;
  note?: string;
  env_key?: string;
  env_file?: string;
  autorestart?: boolean;
  monitor_only?: boolean;
  depends_on?: string[];
  health_url?: string;
  mem_limit_mb?: number;
  watch?: boolean;
  restart_every_min?: number;
  env?: Record<string, string>;
  env_profiles?: Record<string, Record<string, string>>;
  env_profile?: string;
  [k: string]: unknown;
}

/** Candidate → spec for the "new service" dialog: the remembered spec
 * (hint) is the base, live candidate data fills the gaps. */
export function candidateToSpec(c: ServiceCandidate): ServiceSpec {
  const h = (c.hint ?? {}) as ServiceSpec;
  return {
    ...h,
    name: h.name || c.name,
    ports: h.ports ?? c.ports,
    proc: h.proc || c.proc,
    match: h.match || c.match,
    start: c.start || h.start,
    cwd: c.cwd || h.cwd,
    path: h.path || c.cwd,
  };
}

export interface ProjectSpec {
  name?: string;
  cmd?: string;
  cwd?: string;
  url?: string;
  autostart?: boolean;
  pid?: number | null;
}

export interface ProcTarget {
  name: string;
  pid: number;
}

export interface PortConflict {
  port?: number;
  pid?: number;
  pname?: string;
  suggest?: number;
}

export interface ServiceLog {
  kind: "file" | "events";
  lines: LogLine[];
  path: string;
}

export interface ScannedProject {
  name: string;
  cmd: string;
  cwd: string;
  framework?: string;
  branch?: string;
  env_missing?: string[];
  env_open?: boolean;
  env_committed?: boolean;  // .env is tracked by git
  score?: number;
  root?: string;
  running?: boolean;
  url?: string;
  autostart?: boolean;
  restored?: boolean;
  worktree?: boolean;  // this dir is a git worktree checkout
  worktrees?: { cwd: string; branch?: string }[];  // all checkouts of the repo
  compose_services?: string[];
}

/** Scanned folder → spec for the "new project" dialog. */
export function projectToSpec(p: ScannedProject): ProjectSpec {
  const s: ProjectSpec = { name: p.name, cmd: p.cmd, cwd: p.cwd };
  if (p.url) s.url = p.url;
  if (p.autostart) s.autostart = true;
  return s;
}

async function get<T>(path: string): Promise<T> {
  const r = await fetch(path);
  if (!r.ok) throw new Error(`${r.status}`);
  return r.json() as Promise<T>;
}

async function post<T = { ok: boolean; msg?: string }>(
  path: string,
  body: unknown = {},
  method = "POST",
): Promise<T> {
  const r = await fetch(path, {
    method,
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  if (!r.ok) throw new Error(`${r.status}`);
  return r.json() as Promise<T>;
}

export const api = {
  state: () => get<DashState>("/api/state"),
  issues: () => get<Issue[]>("/api/issues"),
  runs: (name: string) => get<Run[]>(`/api/runs?name=${encodeURIComponent(name)}`),
  serviceLog: (name: string, tail = 300) =>
    get<ServiceLog>(`/api/service-log?name=${encodeURIComponent(name)}&tail=${tail}`),
  serviceSpec: (name: string) =>
    get<ServiceSpec>(`/api/service?name=${encodeURIComponent(name)}`),
  projectSpec: (name: string) =>
    get<ProjectSpec>(`/api/project?name=${encodeURIComponent(name)}`),
  serviceTargets: (name: string) =>
    get<ProcTarget[]>(`/api/service-targets?name=${encodeURIComponent(name)}`),
  stopAllTargets: () => get<string[]>("/api/stop-all-targets"),
  portTargets: (port: number) => get<ProcTarget[]>(`/api/port-targets?port=${port}`),
  freePort: (from = 8000) =>
    get<{ port: number | null; from: number }>(`/api/free-port?from=${from}`),
  ports: () =>
    get<{ ports: PortRow[]; bg: BgProc[] }>("/api/ports"),
  portConflict: (name: string) =>
    get<PortConflict>(`/api/port-conflict?name=${encodeURIComponent(name)}`),
  serviceToken: (name: string) =>
    get<{ value: string }>(`/api/service-token?name=${encodeURIComponent(name)}`),
  serviceEnv: (name: string, reveal = false) =>
    get<EnvVar[]>(
      `/api/services/${encodeURIComponent(name)}/env${reveal ? "?reveal=1" : ""}`,
    ),
  saveEnv: (name: string, env: Record<string, string>) =>
    post<{ restart_required?: boolean; warnings?: EnvWarn[] }>(
      `/api/services/${encodeURIComponent(name)}/env`,
      env,
    ),
  saveEnvProfiles: (
    name: string,
    profiles: Record<string, Record<string, string>>,
  ) =>
    post<{
      ok: boolean;
      restart_required?: boolean;
      msg?: string;
      warnings?: EnvWarn[];
    }>(
      `/api/services/${encodeURIComponent(name)}/env-profiles`,
      { profiles },
      "PUT",
    ),
  setEnvProfile: (name: string, profile: string) =>
    post<{ ok: boolean; restart_required?: boolean; msg?: string }>(
      `/api/services/${encodeURIComponent(name)}/env-profile`,
      { profile },
    ),
  setEnvSecret: (name: string, key: string, value: string) =>
    post<{ ok: boolean; restart_required?: boolean; msg?: string }>(
      `/api/services/${encodeURIComponent(name)}/env-secret`,
      { key, value },
    ),
  projectEnv: (name: string, reveal = false) =>
    get<{ env: EnvVar[]; missing: { key: string; secret: boolean }[] }>(
      `/api/projects/${encodeURIComponent(name)}/env${reveal ? "?reveal=1" : ""}`,
    ),
  saveProjectEnv: (name: string, env: Record<string, string>) =>
    post<{ ok?: boolean; warnings?: EnvWarn[] }>(
      `/api/projects/${encodeURIComponent(name)}/env`,
      env,
    ),

  selfUpdate: () =>
    post<{ ok: boolean; msg?: string; channel?: string; version?: string }>(
      "/api/self-update",
      {},
    ),
  svcAction: (name: string, act: "start" | "stop" | "restart") =>
    post(`/api/services/${encodeURIComponent(name)}/${act}`),
  prjAction: (name: string, act: "start" | "stop" | "restart") =>
    post(`/api/projects/${encodeURIComponent(name)}/${act}`),
  openProjectFolder: (name: string) =>
    post(`/api/projects/${encodeURIComponent(name)}/open-folder`),
  openProjectIde: (name: string) =>
    post(`/api/projects/${encodeURIComponent(name)}/open-ide`),
  serviceCandidates: () =>
    get<ServiceCandidate[]>("/api/service-candidates"),
  saveService: (old_name: string, data: ServiceSpec) =>
    post("/api/services/save", { old_name, data }),
  deleteService: (name: string) => post("/api/services/delete", { name }),
  setAutorestart: (name: string, enabled: boolean) =>
    post("/api/services/autorestart", { name, enabled }),
  setServiceToken: (name: string, value: string) =>
    post("/api/services/token", { name, value }),
  openServiceLog: (name: string) => post("/api/services/open-log", { name }),
  clearServiceLog: (name: string) => post("/api/services/clear-log", { name }),
  saveProject: (old_name: string, data: ProjectSpec) =>
    post("/api/projects/save", { old_name, data }),
  deleteProject: (name: string) => post("/api/projects/delete", { name }),
  addProjects: (items: ScannedProject[]) => post("/api/projects/add", { items }),
  startAll: () => post("/api/actions/start-all"),
  stopAll: () => post("/api/actions/stop-all"),
  autorunToggle: (name: string, enabled: boolean) =>
    post("/api/autorun/toggle", { name, enabled }),
  autorunSave: (name: string, cmd: string, old_name: string) =>
    post("/api/autorun/save", { name, cmd, old_name }),
  autorunDelete: (name: string) => post("/api/autorun/delete", { name }),
  killPort: (port: number) => post("/api/kill-port", { port }),
  killPid: (pid: number) => post("/api/kill-pid", { pid }),
  scan: () => post<{ found: ScannedProject[] }>("/api/scan"),
  clearIssues: () => post("/api/issues/clear"),
  openUrl: (url: string) => post("/api/open", { url }),
  openPath: (path: string) => post("/api/open", { path }),
  openEditor: (path: string) => post("/api/open", { path, editor: true }),
  pickDir: (start: string) => post<{ dir: string }>("/api/pick-dir", { start }),
  settings: () => get<AppSettings>("/api/settings"),
  saveSettings: (s: Partial<AppSettings>) =>
    post<AppSettings & { ok: boolean; msg?: string }>("/api/settings", s),
};

export interface AppSettings {
  scan_roots: string[];
  scan_roots_auto?: string[];
  port_mine: string[];
  port_hidden: string[];
  probe_interval: number;
  dep_timeout: number;
  backoff: number[];
  api_port: number;
  config_dir: string;
  lang?: string;
  lang_resolved?: string;
  autostart?: boolean;
}

export function copyText(text: string, msg?: string) {
  navigator.clipboard.writeText(text).catch(() => {});
  return msg;
}
