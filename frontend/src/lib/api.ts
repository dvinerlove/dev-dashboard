// Типы и клиент локального API :4850 (core.py)

export type SvcState = "up" | "down" | "dead" | "off" | "check" | "failed";

export interface LogLine {
  t: string;
  l: "error" | "warn" | "info";
}

export interface EnvVar {
  key: string;
  value: string;
  secret: boolean;
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
  lan?: string | boolean;  // ip бинда или true; truthy = открыт в сеть
  title?: string;
  age?: number;
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
  squatterPort: number;
  autorestart: boolean;
  hasToken: boolean;
  hasUrl: boolean;
  hasPath: boolean;
  remote: boolean;
  inAutorun?: boolean;
  arName?: string;
  envWarn?: string;
  m?: Metrics;
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
  problems: string[];
  issues: number;
  infraUp: number;
  infraTotal: number;
  platform?: string;
  lang?: "ru" | "en";
  version?: string;
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
  zerotier?: boolean;
  supabase?: boolean;
  depends_on?: string[];
  [k: string]: unknown;
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
}

async function get<T>(path: string): Promise<T> {
  const r = await fetch(path);
  if (!r.ok) throw new Error(`${r.status}`);
  return r.json() as Promise<T>;
}

async function post<T = { ok: boolean; msg?: string }>(
  path: string,
  body: unknown = {},
): Promise<T> {
  const r = await fetch(path, {
    method: "POST",
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
    post<{ restart_required?: boolean }>(
      `/api/services/${encodeURIComponent(name)}/env`,
      env,
    ),
  projectEnv: (name: string, reveal = false) =>
    get<{ env: EnvVar[]; missing: { key: string; secret: boolean }[] }>(
      `/api/projects/${encodeURIComponent(name)}/env${reveal ? "?reveal=1" : ""}`,
    ),
  saveProjectEnv: (name: string, env: Record<string, string>) =>
    post<{ ok?: boolean }>(
      `/api/projects/${encodeURIComponent(name)}/env`,
      env,
    ),

  svcAction: (name: string, act: "start" | "stop" | "restart") =>
    post(`/api/services/${encodeURIComponent(name)}/${act}`),
  prjAction: (name: string, act: "start" | "stop" | "restart") =>
    post(`/api/projects/${encodeURIComponent(name)}/${act}`),
  openProjectFolder: (name: string) =>
    post(`/api/projects/${encodeURIComponent(name)}/open-folder`),
  openProjectIde: (name: string) =>
    post(`/api/projects/${encodeURIComponent(name)}/open-ide`),
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
  port_mine: string[];
  port_hidden: string[];
  probe_interval: number;
  dep_timeout: number;
  backoff: number[];
  api_port: number;
  config_dir: string;
  lang?: "auto" | "ru" | "en";
  lang_resolved?: "ru" | "en";
}

export function copyText(text: string, msg?: string) {
  navigator.clipboard.writeText(text).catch(() => {});
  return msg;
}
