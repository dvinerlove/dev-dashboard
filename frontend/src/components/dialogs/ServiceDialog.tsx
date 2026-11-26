import { useState } from "react";
import type { ServiceSpec } from "../../lib/api";
import { api } from "../../lib/api";
import { useApp } from "../../lib/ctx";
import { useT } from "../../lib/i18n";
import { refresh } from "../../lib/store";
import { cn } from "../../lib/utils";
import { Button } from "../ui/button";
import {
  Dialog,
  DialogContent,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "../ui/dialog";
import { Input } from "../ui/input";
import { Switch } from "../ui/switch";
import { ChevronDown } from "lucide-react";
import { toast } from "sonner";

function Field({
  label,
  mono,
  placeholder,
  value,
  onChange,
  autoFocus,
  className,
  spell,
}: {
  label: string;
  mono?: boolean;
  placeholder?: string;
  value: string;
  onChange: (v: string) => void;
  autoFocus?: boolean;
  className?: string;
  spell?: boolean;
}) {
  return (
    <label className={cn("block text-[11.5px] text-(--text-muted)", className)}>
      {label}
      <Input
        className={cn("mt-1", mono && "font-mono")}
        placeholder={placeholder}
        value={value}
        spellCheck={spell ?? false}
        autoFocus={autoFocus}
        onChange={(e) => onChange(e.target.value)}
      />
    </label>
  );
}

const TYPES = [
  { id: "local", label: "LOCAL_TYPE" },
  { id: "http", label: "TYPE_HTTP" },
  { id: "tcp", label: "tcp" },
  { id: "docker", label: "docker" },
];

export function ServiceDialog({
  spec,
  isNew,
}: {
  spec: ServiceSpec | null;
  isNew?: boolean;
}) {
  const app = useApp();
  const t = useT();
  const s = spec ?? {};
  // a spec delivered by a candidate is new: name pre-fills the form, not the
  // rename key — oldName empty keeps the "New service" title and save-as-new
  const oldName = spec && !isNew ? (s.name ?? "") : "";
  // a spec with an unknown type is kept whole so its fields are not erased
  const origSpec =
    s.type && !["local", "http", "tcp", "docker"].includes(s.type) ? s : null;

  const init = () => ({
    name: s.name ?? "",
    sub: s.sub ?? "",
    type: s.type && TYPES.some((t) => t.id === s.type) ? s.type : "local",
    ports: (s.ports ?? []).join(", "),
    proc: s.proc ?? "",
    match: s.match ?? "",
    urlHttp: s.type === "http" ? (s.url ?? "") : "",
    link: !s.type ? (s.url ?? "") : "",
    host: s.host ?? "",
    portNum: s.port ? String(s.port) : "",
    keyword: s.keyword ?? "",
    container: s.container ?? "",
    interval: s.interval ? String(s.interval) : "",
    start: s.start ?? "",
    cwd: s.cwd ?? "",
    deps: (s.depends_on ?? []).join(", "),
    path: s.path ?? "",
    note: s.note ?? "",
    envKey: s.env_key ?? "",
    envFile: s.env_file ?? "",
    healthUrl: s.health_url ?? "",
    memLimit: s.mem_limit_mb ? String(s.mem_limit_mb) : "",
    restartEvery: s.restart_every_min ? String(s.restart_every_min) : "",
    watch: !!s.watch,
    autorestart: !!s.autorestart,
    monitorOnly: !!s.monitor_only,
  });
  const [f, setF] = useState(init);
  const set = (k: keyof typeof f) => (v: string | boolean) =>
    setF((p) => ({ ...p, [k]: v }));

  const collect = (): ServiceSpec => {
    const d: ServiceSpec = { name: f.name.trim(), sub: f.sub.trim() };
    const put = (k: keyof ServiceSpec, v: string) => {
      if (v.trim()) (d as Record<string, unknown>)[k] = v.trim();
    };
    if (f.type !== "local") d.type = f.type;
    put("ports", f.ports);
    put("proc", f.proc);
    put("match", f.match);
    if (f.type === "http") put("url", f.urlHttp);
    if (f.type === "local") {
      put("url", f.link);
      put("health_url", f.healthUrl);
      const mem = parseInt(f.memLimit.trim(), 10);
      if (mem > 0) d.mem_limit_mb = mem;
    }
    put("host", f.host);
    if (f.portNum.trim()) d.port = parseInt(f.portNum.trim(), 10) || 0;
    put("keyword", f.keyword);
    put("container", f.container);
    if (f.interval.trim()) d.interval = parseInt(f.interval.trim(), 10) || 0;
    put("start", f.start);
    put("cwd", f.cwd);
    const deps = f.deps.split(",").map((x) => x.trim()).filter(Boolean);
    if (deps.length) d.depends_on = deps;
    put("path", f.path);
    put("note", f.note);
    put("env_key", f.envKey);
    put("env_file", f.envFile);
    if (f.autorestart) d.autorestart = true;
    if (f.monitorOnly) d.monitor_only = true;
    // known keys absent from data get wiped server-side — always send these;
    // falsy values are dropped by the backend anyway
    d.watch = f.watch;
    d.restart_every_min = parseInt(f.restartEvery.trim(), 10) || 0;
    // env* keys are edited on the ENV tab, not here — pass through so the
    // known-key wipe does not erase them
    for (const k of ["env", "env_profiles", "env_profile"] as const)
      if (s[k] !== undefined) (d as Record<string, unknown>)[k] = s[k];
    if (origSpec)
      for (const k in origSpec) if (!(k in d)) d[k] = origSpec[k];
    return d;
  };

  const ty = f.type;
  // rare fields hide behind disclosure; it opens itself when the spec
  // already carries any of them (prefilled candidates included)
  const [advOpen, setAdvOpen] = useState(() =>
    [s.path, s.note, s.env_key, s.env_file, s.health_url, s.mem_limit_mb,
     s.restart_every_min, s.watch, s.type ? "" : s.url].some(
      (v) => v && String(v).trim(),
    ),
  );
  const advN = [f.path, f.note, f.envKey, f.envFile,
    ty === "local" ? f.link : "",
    ty === "local" ? f.healthUrl : "",
    ty === "local" ? f.memLimit : "",
    ty === "local" ? f.restartEvery : "",
    ty === "local" && f.watch ? "1" : "",
  ].filter((v) => (v ?? "").trim()).length;
  return (
    <Dialog open onOpenChange={(v) => !v && app.closeDlg()}>
      <DialogContent
        className="max-w-xl"
        aria-describedby={undefined}
        onKeyDown={(e) => {
          if (e.key === "Enter" && !e.nativeEvent.isComposing && (e.target as HTMLElement).tagName === "INPUT" && f.name.trim()) {
            e.preventDefault();
            api.saveService(oldName, collect()).then((r) => {
              if (!r.ok) return toast(r.msg || t("ERROR"));
              app.closeDlg();
              refresh();
            });
          }
        }}
      >
        <DialogHeader>
          <DialogTitle>
            {oldName ? t("EDIT_SERVICE") : t("NEW_SERVICE")}
          </DialogTitle>
        </DialogHeader>
        <div className="max-h-[75vh] space-y-2 overflow-y-auto overscroll-contain pr-1">
          <div className="grid grid-cols-2 gap-x-3">
            <Field label={t("NAME_REQUIRED")} autoFocus value={f.name} onChange={set("name")} />
            <Field
              label={t("CAPTION")}
              placeholder={t("CAPTION_PLACEHOLDER")}
              value={f.sub}
              onChange={set("sub")}
            />
          </div>
          <div
            className="flex items-center gap-2 pt-1"
            role="group"
            aria-label={t("TYPE")}
          >
            <span className="w-[60px] text-[11.5px] text-(--text-muted)" aria-hidden="true">
              {t("TYPE")}
            </span>
            <div className="flex gap-1">
              {TYPES.map((x) => (
                <button
                  key={x.id}
                  type="button"
                  aria-pressed={ty === x.id}
                  onClick={() => set("type")(x.id)}
                  className={cn(
                    "h-6 cursor-pointer rounded-md border px-2 text-[11.5px] transition-colors",
                    ty === x.id
                      ? "border-(--accent) bg-(--accent)/15 text-(--text-primary)"
                      : "border-(--border-strong) text-(--text-muted) hover:text-(--text-secondary)",
                  )}
                >
                  {t(x.label)}
                </button>
              ))}
            </div>
          </div>

          {ty === "local" && (
            <div className="grid grid-cols-2 gap-x-3 gap-y-2">
              <Field label={t("SECTION_PORTS")} mono placeholder="3000, 8080" value={f.ports} onChange={set("ports")} />
              <Field label={t("PROCESS_NAME")} mono placeholder="proc.exe" value={f.proc} onChange={set("proc")} />
              <Field label={t("CMDLINE_FRAGMENT")} mono placeholder="app.py serve" value={f.match} onChange={set("match")} />
              <Field label={t("DEPENDS_ON_CSV")} mono value={f.deps} onChange={set("deps")} />
              <Field label={t("START_FIELD")} mono className="col-span-2" placeholder={t("COMMAND_OR_PATH")} value={f.start} onChange={set("start")} />
              <Field label={t("WORK_DIR")} mono className="col-span-2" value={f.cwd} onChange={set("cwd")} />
            </div>
          )}
          {ty === "http" && (
            <div className="grid grid-cols-2 gap-x-3 gap-y-2">
              <Field label={t("URL_REQUIRED")} mono className="col-span-2" placeholder="https://host:port/path" value={f.urlHttp} onChange={set("urlHttp")} />
              <Field label={t("KEYWORD")} mono placeholder={t("KEYWORD_PLACEHOLDER")} value={f.keyword} onChange={set("keyword")} />
              <Field label={t("INTERVAL_SEC")} mono placeholder="30" value={f.interval} onChange={set("interval")} />
            </div>
          )}
          {ty === "tcp" && (
            <div className="grid grid-cols-2 gap-x-3 gap-y-2">
              <Field label={t("HOST")} mono value={f.host} onChange={set("host")} />
              <Field label={t("PORT_FIELD")} mono value={f.portNum} onChange={set("portNum")} />
              <Field label={t("INTERVAL_SEC")} mono placeholder="30" value={f.interval} onChange={set("interval")} />
            </div>
          )}
          {ty === "docker" && (
            <div className="grid grid-cols-2 gap-x-3 gap-y-2">
              <Field label={t("CONTAINER")} mono value={f.container} onChange={set("container")} />
              <Field label={t("INTERVAL_SEC")} mono placeholder="15" value={f.interval} onChange={set("interval")} />
            </div>
          )}

          <div className="pt-1">
            <button
              type="button"
              aria-expanded={advOpen}
              aria-controls="svc-adv"
              onClick={() => setAdvOpen(!advOpen)}
              className="flex cursor-pointer items-center gap-1 text-[11px] text-(--text-muted) hover:text-(--text-secondary)"
            >
              <ChevronDown
                className={cn("h-3 w-3 transition-transform", !advOpen && "-rotate-90")}
              />
              {t("ADVANCED")}
              {!advOpen && advN > 0 && (
                <span className="text-(--text-secondary)">· {advN}</span>
              )}
            </button>
            {advOpen && (
              <div id="svc-adv" className="mt-2 grid grid-cols-2 gap-x-3 gap-y-2">
                {ty === "local" && (
                  <Field label={t("URL_FIELD")} mono placeholder="http://127.0.0.1:3000" value={f.link} onChange={set("link")} />
                )}
                {ty === "local" && (
                  <Field label={t("HEALTH_URL")} mono placeholder="http://…/health" value={f.healthUrl} onChange={set("healthUrl")} />
                )}
                {ty === "local" && (
                  <Field label={t("RAM_LIMIT_MB")} mono placeholder="512" value={f.memLimit} onChange={(v) => set("memLimit")(v.replace(/\D/g, ""))} />
                )}
                {ty === "local" && (
                  <Field label={t("RESTART_EVERY_MIN")} mono placeholder="60" value={f.restartEvery} onChange={(v) => set("restartEvery")(v.replace(/\D/g, ""))} />
                )}
                {ty === "local" && (
                  <label className="flex cursor-pointer items-center gap-2 self-center pt-4 text-[11.5px] text-(--text-secondary)">
                    <Switch
                      aria-label={t("WATCH_FILES")}
                      checked={f.watch}
                      onCheckedChange={(v) => set("watch")(v)}
                    />
                    {t("WATCH_FILES")}
                  </label>
                )}
                <Field label={t("FOLDER")} mono value={f.path} onChange={set("path")} />
                <Field label={t("NOTE_WHEN_OFF")} spell placeholder={t("NOTE_PLACEHOLDER")} value={f.note} onChange={set("note")} />
                <Field label={t("ENV_KEY_FIELD")} mono placeholder="API_KEY" value={f.envKey} onChange={set("envKey")} />
                <Field label={t("ENV_FILE_FIELD")} mono placeholder={t("ENV_FILE_PLACEHOLDER")} value={f.envFile} onChange={set("envFile")} />
              </div>
            )}
          </div>

          <div className="flex flex-wrap gap-x-5 gap-y-2 pt-2">
            {(
              [
                ["AUTORESTART_SWITCH", "autorestart"],
                ["MONITOR_ONLY", "monitorOnly"],
              ] as const
            ).map(([label, k]) => (
              <label
                key={k}
                className="flex cursor-pointer items-center gap-2 text-[11.5px] text-(--text-secondary)"
              >
                <Switch
                  aria-label={t(label)}
                  checked={f[k] as boolean}
                  onCheckedChange={(v) => set(k)(v)}
                />
                {t(label)}
              </label>
            ))}
          </div>
        </div>
        <DialogFooter>
          <Button variant="ghost" size="sm" onClick={app.closeDlg}>
            {t("CANCEL")}
          </Button>
          <Button
            size="sm"
            disabled={!f.name.trim()}
            onClick={() => {
              api.saveService(oldName, collect()).then((r) => {
                if (!r.ok) return toast(r.msg || t("ERROR"));
                app.closeDlg();
                refresh();
              });
            }}
          >
            {t("SAVE")}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
