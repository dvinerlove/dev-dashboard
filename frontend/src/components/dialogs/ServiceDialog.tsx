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
import { toast } from "sonner";

function Field({
  label,
  mono,
  placeholder,
  value,
  onChange,
  autoFocus,
}: {
  label: string;
  mono?: boolean;
  placeholder?: string;
  value: string;
  onChange: (v: string) => void;
  autoFocus?: boolean;
}) {
  return (
    <label className="block text-[11.5px] text-(--text-muted)">
      {label}
      <Input
        className={cn("mt-1", mono && "font-mono")}
        placeholder={placeholder}
        value={value}
        spellCheck={false}
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

export function ServiceDialog({ spec }: { spec: ServiceSpec | null }) {
  const app = useApp();
  const t = useT();
  const s = spec ?? {};
  const oldName = s.name ?? "";
  // spec с неизвестным type храним целиком, чтобы не стереть его поля
  const origSpec =
    s.type && !["local", "http", "tcp", "docker"].includes(s.type) ? s : null;

  const [f, setF] = useState({
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
    autorestart: !!s.autorestart,
    monitorOnly: !!s.monitor_only,
    zerotier: !!s.zerotier,
    supabase: !!s.supabase,
  });
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
    if (f.type === "local") put("url", f.link);
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
    if (f.zerotier) d.zerotier = true;
    if (f.supabase) d.supabase = true;
    if (origSpec)
      for (const k in origSpec) if (!(k in d)) d[k] = origSpec[k];
    return d;
  };

  const ty = f.type;
  return (
    <Dialog open onOpenChange={(v) => !v && app.closeDlg()}>
      <DialogContent
        className="max-w-lg"
        onKeyDown={(e) => {
          if (e.key === "Enter" && (e.target as HTMLElement).tagName === "INPUT" && f.name.trim()) {
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
        <div className="max-h-[60vh] space-y-2 overflow-y-auto overscroll-contain pr-1">
          <Field label={t("NAME_REQUIRED")} autoFocus value={f.name} onChange={set("name")} />
          <Field
            label={t("CAPTION")}
            placeholder={t("CAPTION_PLACEHOLDER")}
            value={f.sub}
            onChange={set("sub")}
          />
          <div className="flex items-center gap-2 pt-1">
            <span className="w-[60px] text-[11.5px] text-(--text-muted)">{t("TYPE")}</span>
            <div className="flex gap-1">
              {TYPES.map((x) => (
                <button
                  key={x.id}
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
            <>
              <div className="pt-1 text-[10px] uppercase tracking-wider text-(--text-muted)">
                {t("LOCAL_PROC_HEADER")}
              </div>
              <Field label={t("SECTION_PORTS")} mono placeholder="3000, 8080" value={f.ports} onChange={set("ports")} />
              <Field label={t("PROCESS_NAME")} mono placeholder="proc.exe" value={f.proc} onChange={set("proc")} />
              <Field label={t("CMDLINE_FRAGMENT")} mono placeholder="app.py serve" value={f.match} onChange={set("match")} />
              <Field label={t("START_FIELD")} mono placeholder={t("COMMAND_OR_PATH")} value={f.start} onChange={set("start")} />
              <Field label={t("WORK_DIR")} mono value={f.cwd} onChange={set("cwd")} />
              <Field label={t("DEPENDS_ON_CSV")} mono value={f.deps} onChange={set("deps")} />
            </>
          )}
          {ty !== "local" && (
            <div className="pt-1 text-[10px] uppercase tracking-wider text-(--text-muted)">
              {t("REMOTE_MONITOR_HEADER")}
            </div>
          )}
          {ty === "http" && (
            <>
              <Field label={t("URL_REQUIRED")} mono placeholder="https://host:port/path" value={f.urlHttp} onChange={set("urlHttp")} />
              <Field label={t("KEYWORD")} mono placeholder={t("KEYWORD_PLACEHOLDER")} value={f.keyword} onChange={set("keyword")} />
            </>
          )}
          {ty === "tcp" && (
            <>
              <Field label={t("HOST")} mono value={f.host} onChange={set("host")} />
              <Field label={t("PORT_FIELD")} mono value={f.portNum} onChange={set("portNum")} />
            </>
          )}
          {ty === "docker" && (
            <Field label={t("CONTAINER")} mono value={f.container} onChange={set("container")} />
          )}
          {ty !== "local" && (
            <Field label={t("INTERVAL_SEC")} mono placeholder="http/tcp 30 · docker 15 · supabase 60" value={f.interval} onChange={set("interval")} />
          )}

          {ty === "local" && (
            <Field label={t("URL_FIELD")} mono placeholder="http://127.0.0.1:3000" value={f.link} onChange={set("link")} />
          )}
          <Field label={t("FOLDER")} mono value={f.path} onChange={set("path")} />
          <Field label={t("NOTE_WHEN_OFF")} placeholder={t("NOTE_PLACEHOLDER")} value={f.note} onChange={set("note")} />
          <Field label={t("ENV_KEY_FIELD")} mono placeholder="API_KEY" value={f.envKey} onChange={set("envKey")} />
          <Field label={t("ENV_FILE_FIELD")} mono placeholder={t("ENV_FILE_PLACEHOLDER")} value={f.envFile} onChange={set("envFile")} />

          <div className="flex flex-wrap gap-x-5 gap-y-2 pt-2">
            {(
              [
                ["AUTORESTART_SWITCH", "autorestart"],
                ["MONITOR_ONLY", "monitorOnly"],
                ["zerotier", "zerotier"],
                ["supabase", "supabase"],
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
