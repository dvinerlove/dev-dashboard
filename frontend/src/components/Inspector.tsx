import { useEffect, useRef, useState } from "react";
import {
  ArrowDownToLine,
  Copy,
  Eraser,
  ExternalLink,
  Eye,
  Pencil,
  Play,
  Plus,
  RotateCw,
  Search,
  Sparkles,
  Square,
  Trash2,
  WrapText,
  X,
} from "lucide-react";
import { motion } from "motion/react";
import {
  api,
  type EnvVar,
  type LogLine,
  type ProjectRow,
  type ProjectSpec,
  type Run,
  type ServiceRow,
  type ServiceSpec,
} from "../lib/api";
import { useApp } from "../lib/ctx";
import { useT, t, localeTag } from "../lib/i18n";
import { markPending, ramHistory, refresh, useDash } from "../lib/store";
import { cn } from "../lib/utils";
import { StatusDot } from "./bits";
import { Button } from "./ui/button";
import { Switch } from "./ui/switch";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "./ui/tabs";
import { Tip } from "./ui/tooltip";
import { toast } from "sonner";

type Row = ServiceRow | ProjectRow;

function fmtRun(r: Run) {
  const d = new Date(r.t0 * 1000);
  const loc = localeTag();
  const date = d.toLocaleDateString(loc, { day: "2-digit", month: "2-digit" });
  const hm = d.toLocaleTimeString(loc, { hour: "2-digit", minute: "2-digit" });
  const dur = r.t1
    ? (() => {
        const m = Math.round((r.t1 - r.t0) / 60);
        return m >= 60 ? `${(m / 60) | 0}${t("UNIT_HOUR")} ${m % 60}${t("UNIT_MIN")}` : `${m}${t("UNIT_MIN")}`;
      })()
    : t("STATE_RUNNING");
  return { date, hm, dur };
}

// ---------- вкладка «Логи» ----------

function LogTab({ name }: { name: string }) {
  const t = useT();
  const [lines, setLines] = useState<LogLine[]>([]);
  const [kind, setKind] = useState<"file" | "events">("events");
  const [q, setQ] = useState("");
  const [lvl, setLvl] = useState<"all" | "error" | "warn">("all");
  const [wrap, setWrap] = useState(true);
  const [follow, setFollow] = useState(true);
  const box = useRef<HTMLDivElement>(null);

  useEffect(() => {
    let dead = false;
    const load = () =>
      api
        .serviceLog(name, 400)
        .then((r) => {
          if (dead) return;
          setLines(r.lines);
          setKind(r.kind);
        })
        .catch(() => {});
    load();
    const t = window.setInterval(load, 1500);
    return () => {
      dead = true;
      window.clearInterval(t);
    };
  }, [name]);

  useEffect(() => {
    if (follow && box.current) box.current.scrollTop = box.current.scrollHeight;
  }, [lines, follow]);

  const view = lines.filter(
    (l) =>
      (lvl === "all" || l.l === lvl) &&
      (!q || l.t.toLowerCase().includes(q.toLowerCase())),
  );

  return (
    <div className="flex min-h-0 flex-1 flex-col">
      <div className="flex h-8 shrink-0 items-center gap-1 border-b border-(--border-hairline) px-2">
        <Search size={13} strokeWidth={1.75} className="shrink-0 text-(--text-muted)" />
        <input
          aria-label={t("LOG_FILTER")}
          value={q}
          onChange={(e) => setQ(e.target.value)}
          placeholder={t("FILTER_PLACEHOLDER")}
          className="h-full min-w-[64px] flex-1 bg-transparent text-[11.5px] text-(--text-primary) outline-none placeholder:text-(--text-muted) selectable"
        />
        {(
          [
            ["all", "ALL"],
            ["error", "ERRORS"],
            ["warn", "WARN"],
          ] as const
        ).map(([v, label]) => (
          <button
            key={v}
            onClick={() => setLvl(v)}

            className={cn(
              "h-5 cursor-pointer rounded px-1.5 text-[10.5px] transition-colors",
              lvl === v
                ? "bg-(--bg-hover) text-(--text-primary)"
                : "text-(--text-muted) hover:text-(--text-secondary)",
            )}
          >
            {t(label)}
          </button>
        ))}
        <Tip label={t("WRAP_LINES")}>
          <button
            onClick={() => setWrap(!wrap)}
            className={cn(
              "cursor-pointer rounded-md p-1 hover:bg-(--bg-hover)",
              wrap ? "text-(--accent)" : "text-(--text-muted) hover:text-(--text-secondary)",
            )}
          >
            <WrapText size={13} strokeWidth={1.75} />
          </button>
        </Tip>
        <Tip label={t("AUTO_SCROLL")}>
          <button
            onClick={() => setFollow(!follow)}
            className={cn(
              "cursor-pointer rounded-md p-1 hover:bg-(--bg-hover)",
              follow ? "text-(--accent)" : "text-(--text-muted) hover:text-(--text-secondary)",
            )}
          >
            <ArrowDownToLine size={13} strokeWidth={1.75} />
          </button>
        </Tip>
        <Tip label={t("COPY")}>
          <button
            onClick={() => {
              navigator.clipboard
                .writeText(view.map((l) => l.t).join("\n"))
                .catch(() => {});
              toast(t("LOG_COPIED"));
            }}
            className="cursor-pointer rounded-md p-1 text-(--text-muted) hover:bg-(--bg-hover) hover:text-(--text-secondary)"
          >
            <Copy size={13} strokeWidth={1.75} />
          </button>
        </Tip>
        <Tip label={kind === "file" ? t("CLEAR_LOG_FILE") : t("EVENT_LOG_NO_CLEAR")}>
          <button
            aria-disabled={kind !== "file"}
            onClick={() => {
              if (kind === "file")
                api.clearServiceLog(name).then(() => setLines([]));
            }}
            className="cursor-pointer rounded-md p-1 text-(--text-muted) hover:bg-(--bg-hover) hover:text-(--status-red) aria-disabled:cursor-default aria-disabled:opacity-40"
          >
            <Eraser size={13} strokeWidth={1.75} />
          </button>
        </Tip>
      </div>
      <div
        ref={box}
        onScroll={(e) => {
          const el = e.currentTarget;
          // юзер отмотал вверх — выключаем автоскролл, вниз — включаем
          setFollow(el.scrollHeight - el.scrollTop - el.clientHeight < 30);
        }}
        className="selectable min-h-0 flex-1 overflow-auto bg-(--bg-base) p-3 font-mono text-[11.5px] leading-relaxed text-(--text-secondary)"
      >
        {view.length === 0 && (
          <span className="text-(--text-muted)">
            {kind === "file" ? t("LOG_EMPTY") : t("LOG_EMPTY_BOTH")}
          </span>
        )}
        {view.map((l, i) => (
          <div
            key={i}
            className={cn(
              "cv-auto",
              wrap ? "whitespace-pre-wrap break-all" : "whitespace-pre",
              l.l === "error" &&
                "-mx-1 rounded bg-(--status-red)/10 px-1 text-(--status-red)",
              l.l === "warn" && "text-(--status-amber)",
            )}
          >
            {l.t}
          </div>
        ))}
      </div>
    </div>
  );
}

// ---------- вкладка «История» ----------

function RunsTab({ name }: { name: string }) {
  const t = useT();
  const st = useDash();
  const [runs, setRuns] = useState<Run[]>([]);
  useEffect(() => {
    let dead = false;
    api.runs(name)
      .then((r) => !dead && setRuns([...r].reverse()))
      .catch(() => {});
    return () => {
      dead = true;
    };
  }, [name, st?.ts]);

  return (
    <div className="min-h-0 flex-1 overflow-y-auto p-2">
      {runs.length === 0 && (
        <div className="p-4 text-[12px] text-(--text-muted)">
          {t("NO_RUNS_YET")}
        </div>
      )}
      {runs.map((r, i) => {
        const f = fmtRun(r);
        const bad = r.exit && !/exit 0|up/.test(r.exit);
        return (
          <div
            key={i}
            className="flex items-center gap-2.5 rounded-md px-2 py-1.5 text-[11.5px] hover:bg-(--bg-hover)"
          >
            <span className="font-mono text-(--text-muted)">
              {f.date} {f.hm}
            </span>
            <span className="font-mono flex-1 text-(--text-secondary)">{f.dur}</span>
            {r.exit && (
              <span
                className={cn(
                  "font-mono rounded px-1.5 py-0.5 text-[10.5px]",
                  bad
                    ? "bg-(--status-red)/10 text-(--status-red)"
                    : "bg-(--status-green)/10 text-(--status-green)",
                )}
              >
                {r.exit}
              </span>
            )}
          </div>
        );
      })}
    </div>
  );
}

// ---------- вкладка «ENV» ----------

interface EnvRow {
  key: string;
  value: string;
  secret: boolean;
  touched?: boolean;
  revealed?: boolean;
}

function EnvTab({
  name,
  running,
  project,
}: {
  name: string;
  running: boolean;
  project?: boolean;
}) {
  const t = useT();
  const [rows, setRows] = useState<EnvRow[]>([]);
  const [newKey, setNewKey] = useState("");
  const [dirty, setDirty] = useState(false);
  const [needRestart, setNeedRestart] = useState(false);

  useEffect(() => {
    setDirty(false);
    setNeedRestart(false);
    if (project) {
      api
        .projectEnv(name)
        .then((r) =>
          setRows([
            ...r.env.map((e) => ({ ...e })),
            // ключи из .env.example — пустыми строками для заполнения
            ...r.missing.map((m) => ({
              key: m.key,
              value: "",
              secret: m.secret,
            })),
          ]),
        )
        .catch(() => {});
    } else {
      api
        .serviceEnv(name)
        .then((r) => setRows(r.map((e) => ({ ...e }))))
        .catch(() => {});
    }
  }, [name, project]);

  const set = (i: number, patch: Partial<EnvRow>) => {
    setRows((rs) => rs.map((r, j) => (j === i ? { ...r, ...patch } : r)));
    setDirty(true);
  };

  const reveal = async (i: number) => {
    const rv = await (project
      ? api.projectEnv(name, true).then((r) => r.env)
      : api.serviceEnv(name, true)
    ).catch(() => null);
    if (rv) {
      const real = Object.fromEntries(rv.map((e) => [e.key, e.value]));
      setRows((rs) =>
        rs.map((r, j) =>
          j === i && real[r.key] !== undefined
            ? { ...r, value: real[r.key], revealed: true }
            : r,
        ),
      );
    }
  };

  const save = async () => {
    // не тронутые секреты замаскированы — подставляем реальные значения,
    // чтобы не записать «••••••••» в конфиг; без reveal сохранять нельзя
    let real: Record<string, string> = {};
    if (rows.some((r) => r.secret && !r.touched)) {
      const rv = await (project
        ? api.projectEnv(name, true).then((r) => r.env)
        : api.serviceEnv(name, true)
      ).catch(() => null);
      if (!rv) {
        toast.error(t("ENV_SECRETS_FAIL"));
        return;
      }
      real = Object.fromEntries(rv.map((e) => [e.key, e.value]));
    }
    const env = Object.fromEntries(
      rows.map((r) => [
        r.key,
        r.secret && !r.touched ? (real[r.key] ?? r.value) : r.value,
      ]),
    );
    const res = await (project
      ? api.saveProjectEnv(name, env)
      : api.saveEnv(name, env)
    ).catch(() => null);
    if (!res) {
      toast.error(t("ENV_SAVE_FAILED"));
      return;
    }
    const restart = !project && "restart_required" in res &&
      res.restart_required;
    setNeedRestart(!!restart);
    setDirty(false);
    toast(restart ? t("ENV_SAVED_RESTART") : t("ENV_SAVED"));
  };

  return (
    <div className="flex min-h-0 flex-1 flex-col">
      {running && (dirty || needRestart) && (
        <div className="mx-3 mt-3 shrink-0 rounded-md border border-(--status-amber)/25 bg-(--status-amber)/10 px-2.5 py-1.5 text-[11.5px] text-(--status-amber)">
          {t("ENV_RESTART_NOTICE")}
        </div>
      )}
      <div className="min-h-0 flex-1 overflow-y-auto p-3">
        {rows.length === 0 && (
          <p className="text-[11.5px] text-(--text-muted)">
            {t("NO_CUSTOM_VARS")}
          </p>
        )}
        {rows.map((r, i) => (
          <div key={i} className="mb-1.5 flex items-center gap-1.5">
            <input
              aria-label={t("VAR_NAME")}
              value={r.key}
              onChange={(e) =>
                set(i, { key: e.target.value, touched: true })
              }
              spellCheck={false}
              className="h-7 w-2/5 rounded-md border border-(--border-strong) bg-(--bg-surface) px-2 font-mono text-[11.5px] text-(--text-primary) outline-none focus:border-(--accent)"
            />
            <input
              aria-label={t("VAR_VALUE")}
              value={r.value}
              type={
                r.secret && !r.touched && !r.revealed ? "password" : "text"
              }
              onChange={(e) =>
                set(i, { value: e.target.value, touched: true })
              }
              spellCheck={false}
              className="h-7 min-w-0 flex-1 rounded-md border border-(--border-strong) bg-(--bg-surface) px-2 font-mono text-[11.5px] text-(--text-primary) outline-none focus:border-(--accent)"
            />
            {r.secret && !r.touched && (
              <button
                aria-label={t("REVEAL_VALUE")}
                onClick={() => reveal(i)}
                className="cursor-pointer rounded-md p-1 text-(--text-muted) hover:bg-(--bg-hover) hover:text-(--text-secondary)"
                title={t("SHOW_VALUE")}
              >
                <Eye size={13} strokeWidth={1.75} />
              </button>
            )}
            <button
              aria-label={t("DELETE_VAR")}
              onClick={() => {
                setRows((rs) => rs.filter((_, j) => j !== i));
                setDirty(true);
              }}
              className="cursor-pointer rounded-md p-1 text-(--text-muted) hover:bg-(--bg-hover) hover:text-(--status-red)"
              title={t("DELETE")}
            >
              <Trash2 size={13} strokeWidth={1.75} />
            </button>
          </div>
        ))}
      </div>
      <div className="flex shrink-0 items-center gap-1.5 border-t border-(--border-hairline) p-3">
        <input
          aria-label={t("NEW_VAR_NAME")}
          value={newKey}
          onChange={(e) => setNewKey(e.target.value)}
          placeholder="NEW_KEY"
          spellCheck={false}
          className="h-7 min-w-0 flex-1 rounded-md border border-(--border-strong) bg-(--bg-surface) px-2 font-mono text-[11.5px] text-(--text-primary) outline-none placeholder:text-(--text-muted) focus:border-(--accent)"
        />
        <Button
          variant="ghost"
          size="sm"
          disabled={!newKey.trim()}
          onClick={() => {
            setRows((rs) => [
              ...rs,
              { key: newKey.trim(), value: "", secret: /TOKEN|SECRET|KEY|PASSWORD|PASS|AUTH/i.test(newKey), touched: true },
            ]);
            setNewKey("");
            setDirty(true);
          }}
        >
          <Plus size={13} strokeWidth={1.75} /> {t("ADD")}
        </Button>
        <Button size="sm" disabled={!dirty} onClick={save}>
          {t("SAVE")}
        </Button>
      </div>
    </div>
  );
}

// ---------- вкладка «Конфиг» ----------

function Kv({ k, v, mono }: { k: string; v?: React.ReactNode; mono?: boolean }) {
  if (v === undefined || v === null || v === "") return null;
  return (
    <div className="flex gap-2 px-2 py-1">
      <span className="w-[110px] shrink-0 text-[11.5px] text-(--text-muted)">{k}</span>
      <span
        className={cn(
          "selectable min-w-0 flex-1 break-all text-[11.5px] text-(--text-secondary)",
          mono && "font-mono",
        )}
      >
        {v}
      </span>
    </div>
  );
}

function ConfigTab({
  kind,
  name,
  row,
  onSelectDep,
}: {
  kind: "svc" | "prj";
  name: string;
  row: Row;
  onSelectDep: (dep: string) => void;
}) {
  const t = useT();
  const st = useDash();
  const [spec, setSpec] = useState<ServiceSpec | ProjectSpec | null>(null);
  useEffect(() => {
    (kind === "svc" ? api.serviceSpec(name) : api.projectSpec(name))
      .then(setSpec)
      .catch(() => {});
  }, [kind, name]);
  if (!spec) return <div className="p-4 text-[12px] text-(--text-muted)">…</div>;

  const s = spec as ServiceSpec;
  const dir = s.path || s.cwd || (spec as ProjectSpec).cwd;
  const svc = kind === "svc" ? (row as ServiceRow) : null;
  const prjSpec = spec as ProjectSpec;

  // запись автозагрузки, относящаяся к сервису (матчит бэкенд: arName)
  const arEntry = svc
    ? [...(st?.autorunMine ?? []), ...(st?.autorunOther ?? [])].find(
        (a) => a.name === svc.arName,
      )
    : undefined;
  const toggleWindowsAutorun = (v: boolean) => {
    if (arEntry) api.autorunToggle(arEntry.name, v).then(() => refresh());
    else if (v && s.start)
      api.autorunSave(name, s.start, "").then(() => refresh());
  };

  return (
    <div className="min-h-0 flex-1 overflow-y-auto p-2">
      {/* автоматика — бывшие тумблеры из шапки инспектора */}
      {((svc && !svc.remote && !svc.monitor) || kind === "prj") && (
        <div className="m-1 mb-3 space-y-2.5 rounded-md border border-(--border-hairline) bg-(--bg-canvas) p-2.5">
          {svc && !svc.remote && !svc.monitor && (
            <>
              <label className="flex cursor-pointer items-center justify-between text-[12px] text-(--text-secondary)">
                {t("START_WITH_WINDOWS")}
                <Switch
                  aria-label={t("START_WITH_WINDOWS")}
                  checked={!!arEntry?.arEnabled}
                  onCheckedChange={toggleWindowsAutorun}
                />
              </label>
              <label className="flex cursor-pointer items-center justify-between text-[12px] text-(--text-secondary)">
                {t("RESTART_ON_CRASH")}
                <Switch
                  aria-label={t("RESTART_ON_CRASH")}
                  checked={!!svc.autorestart}
                  onCheckedChange={(v) =>
                    api.setAutorestart(name, v).then(() => refresh())
                  }
                />
              </label>
            </>
          )}
          {kind === "prj" && (
            <label className="flex cursor-pointer items-center justify-between text-[12px] text-(--text-secondary)">
              {t("LAUNCH_WITH_DASHBOARD")}
              <Switch
                aria-label={t("LAUNCH_WITH_DASHBOARD")}
                checked={!!prjSpec.autostart}
                onCheckedChange={(v) =>
                  api
                    .saveProject(name, {
                      name: prjSpec.name,
                      cmd: prjSpec.cmd,
                      cwd: prjSpec.cwd,
                      ...(prjSpec.url ? { url: prjSpec.url } : {}),
                      autostart: v,
                    })
                    .then(() => refresh())
                }
              />
            </label>
          )}
        </div>
      )}
      <Kv k={t("NAME")} v={spec.name} />
      {kind === "svc" ? (
        <>
          <Kv k={t("CAPTION")} v={s.sub} />
          <Kv k={t("TYPE")} v={s.type || t("LOCAL_TYPE")} />
          <Kv k={t("SECTION_PORTS")} v={s.ports?.join(", ")} mono />
          <Kv k={t("PROCESS")} v={s.proc} mono />
          <Kv k={t("CMDLINE_FRAGMENT")} v={s.match} mono />
          <Kv k={t("URL_FIELD")} v={s.url} mono />
          <Kv k={t("START_FIELD")} v={s.start} mono />
          <Kv k={t("WORK_DIR")} v={s.cwd} mono />
          <Kv k={t("FOLDER")} v={s.path} mono />
          <Kv k={t("NOTE")} v={s.note} />
          <Kv k="ENV" v={s.env_key && `${s.env_key} → ${s.env_file}`} mono />
          {!!s.depends_on?.length && (
            <div className="flex gap-2 px-2 py-1">
              <span className="w-[110px] shrink-0 text-[11.5px] text-(--text-muted)">
                {t("DEPENDS_ON")}
              </span>
              <span className="flex flex-wrap gap-1">
                {s.depends_on.map((d) => (
                  <button
                    key={d}
                    onClick={() => onSelectDep(d)}
                    className="cursor-pointer rounded border border-(--border-hairline) bg-(--bg-canvas) px-1.5 py-0.5 font-mono text-[11px] text-(--text-secondary) hover:border-(--accent) hover:text-(--text-primary)"
                  >
                    {d}
                  </button>
                ))}
              </span>
            </div>
          )}
        </>
      ) : (
        <>
          <Kv k={t("COMMAND")} v={(spec as ProjectSpec).cmd} mono />
          <Kv k={t("FOLDER")} v={(spec as ProjectSpec).cwd} mono />
          <Kv k={t("URL_FIELD")} v={(spec as ProjectSpec).url} mono />
          <Kv
            k={t("AUTOSTART")}
            v={(spec as ProjectSpec).autostart ? t("YES") : undefined}
          />
        </>
      )}
      {dir && (
        <div className="mt-3 px-2">
          <Button variant="outline" size="sm" onClick={() => api.openEditor(dir)}>
            <ExternalLink size={13} strokeWidth={1.75} /> {t("OPEN_IN_EDITOR")}
          </Button>
        </div>
      )}
    </div>
  );
}

// ---------- сам инспектор ----------

export function Inspector() {
  const app = useApp();
  const t = useT();
  const st = useDash();
  const sel = app.sel;

  const row: Row | undefined = !sel
    ? undefined
    : sel.kind === "svc"
      ? [...(st?.services ?? []), ...(st?.remotes ?? [])].find(
          (r) => r.name === sel.name && (!sel.remote || r.remote),
        ) ??
        st?.remotes.find((r) => r.name === sel.name)
      : st?.projects.find((r) => r.name === sel.name);

  // svc-спек для свитчей (autorun запись нужна для «Автозапуск вместе с Windows»)
  const [spec, setSpec] = useState<ServiceSpec | null>(null);
  useEffect(() => {
    setSpec(null);
    if (sel?.kind === "svc") api.serviceSpec(sel.name).then(setSpec).catch(() => {});
  }, [sel?.kind, sel?.name]);

  if (!sel || !row || !st) {
    return (
      <div className="flex h-full items-center justify-center bg-(--bg-surface) text-[12px] text-(--text-muted)">
        {t("SELECT_ITEM")}
      </div>
    );
  }

  const isSvc = sel.kind === "svc";
  const svc = isSvc ? (row as ServiceRow) : null;
  const running = row.state === "up";
  const url =
    row.chipUrl && row.chipUrl !== "copy" && /^https?:/.test(row.chipUrl)
      ? row.chipUrl
      : "";
  const activeTab =
    app.inspectorTab === "env" && isSvc && svc?.remote
      ? "logs"
      : app.inspectorTab;

  const copyAiContext = async () => {
    try {
      const specD: ServiceSpec | ProjectSpec | null =
        spec ??
        (await (isSvc ? api.serviceSpec(row.name) : api.projectSpec(row.name))
          .catch(() => null));
      const [runs, log, env] = await Promise.all([
        api.runs(row.name).catch(() => [] as Run[]),
        api.serviceLog(row.name, 120).catch(() => null),
        isSvc
          ? api.serviceEnv(row.name).catch(() => [] as EnvVar[])
          : api.projectEnv(row.name).then((r) => r.env)
              .catch(() => [] as EnvVar[]),
      ]);
      const cmd =
        (specD as ServiceSpec)?.start ?? (specD as ProjectSpec)?.cmd ?? "";
      const lastRuns = runs.slice(-3);
      const md = [
        `### ${row.name} — ${t("DIAGNOSTICS")}`,
        `- ${t("STATUS_FIELD")}: ${row.state}${(row as ServiceRow).reason ? ` (${(row as ServiceRow).reason})` : ""}`,
        `- PID: ${row.m?.pid ?? "—"} · ${t("PORT_IP")}: ${row.chip || "—"}`,
        cmd ? `- ${t("START_FIELD")}: \`${cmd}\`` : "",
        specD?.cwd ? `- CWD: \`${specD.cwd}\`` : "",
        (specD as ServiceSpec)?.depends_on?.length
          ? `- depends_on: ${(specD as ServiceSpec).depends_on!.join(", ")}`
          : "",
        env.length ? `- ENV (${t("NAMES")}): ${env.map((e) => e.key).join(", ")}` : "",
        lastRuns.length
          ? `- ${t("RUNS")}: ${lastRuns
              .map(
                (r) =>
                  `${new Date(r.t0 * 1000).toLocaleTimeString()} → ${r.exit ?? "running"}`,
              )
              .join("; ")}`
          : "",
        "",
        "```",
        ...(log?.lines.map((l) => l.t) ?? []),
        "```",
      ]
        .filter((l) => l !== "")
        .join("\n");
      await navigator.clipboard.writeText(md);
      toast(t("DIAG_CONTEXT_COPIED"));
    } catch {
      toast.error(t("CONTEXT_FAIL"));
    }
  };

  return (
    <div className="flex h-full flex-col bg-(--bg-surface)">
      {/* шапка */}
      <div className="shrink-0 border-b border-(--border-hairline) p-4">
        <div className="flex items-start justify-between gap-2">
          <h2
            title={row.name}
            className="min-w-0 flex-1 truncate text-[13px] font-semibold text-(--text-primary)"
          >
            {row.name}
          </h2>
          <button
            aria-label={t("CLOSE_INSPECTOR")}
            onClick={() => app.setInspector(false)}
            className="cursor-pointer rounded-md p-1 text-(--text-muted) hover:bg-(--bg-hover) hover:text-(--text-primary)"
          >
            <X size={14} strokeWidth={1.75} />
          </button>
        </div>
        <div className="mt-1.5 flex items-center gap-2 text-[12px]">
          <StatusDot state={row.state} warn={svc?.warn} />
          <span className="text-(--text-secondary)">
            {running ? (
              <>
                {t("STATE_RUNNING")}
                {row.m?.up && (
                  <span className="font-mono">{` · ${row.m.up}`}</span>
                )}
              </>
            ) : row.failed ? (
              t("STATE_CRASHED")
            ) : (
              t("STATE_STOPPED")
            )}
          </span>
        </div>
        <div className="mt-3 flex flex-wrap items-center gap-2">
          {!(svc?.monitor) &&
            (running ? (
              <Button
                variant="secondary"
                size="sm"
                onClick={() =>
                  isSvc ? app.svcToggle(row.name, sel.remote) : app.prjToggle(row.name)
                }
              >
                <Square size={13} strokeWidth={1.75} /> {t("STOP")}
              </Button>
            ) : (
              <Button
                size="sm"
                onClick={() =>
                  isSvc ? app.svcToggle(row.name, sel.remote) : app.prjToggle(row.name)
                }
              >
                <Play size={13} strokeWidth={1.75} /> {t("START")}
              </Button>
            ))}
          {!(svc?.monitor) && running && (
            <Button
              variant="outline"
              size="sm"
              onClick={() =>
                isSvc
                  ? app.svcRestart(row.name)
                  : (markPending(row.name, "up"),
                    api.prjAction(row.name, "restart"))
              }
            >
              <RotateCw size={13} strokeWidth={1.75} /> {t("RESTART")}
            </Button>
          )}
          {url && (
            <Tip label={url}>
              <Button variant="outline" size="sm" onClick={() => api.openUrl(url)}>
                <ExternalLink size={13} strokeWidth={1.75} />
              </Button>
            </Tip>
          )}
          <Tip label={t("COPY_AI_DIAGNOSTICS")}>
            <Button variant="outline" size="sm" onClick={copyAiContext}>
              <Sparkles size={13} strokeWidth={1.75} />
            </Button>
          </Tip>
          <Tip label={t("EDIT")}>
            <Button
              variant="outline"
              size="sm"
              onClick={() =>
                isSvc ? app.editService(row.name) : app.editProject(row.name)
              }
            >
              <Pencil size={13} strokeWidth={1.75} />
            </Button>
          </Tip>
        </div>
      </div>

      {/* телеметрия — одна строка, логам достаётся вся остальная высота */}
      <div className="tnum flex h-8 shrink-0 items-center gap-1 overflow-hidden border-b border-(--border-hairline) px-2.5 font-mono text-[11.5px] text-(--text-secondary)">
        <span className="min-w-0 truncate whitespace-nowrap">
          PID {row.m?.pid ?? "—"} · CPU {row.m ? `${row.m.cpu.toFixed(1)}%` : "—"} · RAM {row.m ? `${row.m.mb} MB` : "—"}
        </span>
        {row.chip && (
          <>
            <span className="text-(--text-muted)">·</span>
            <button
              title={t("COPY")}
              onClick={() => {
                navigator.clipboard
                  .writeText(row.chip.replace(/^:/, ""))
                  .catch(() => {});
                toast(t("COPIED_CHIP", { chip: row.chip }));
              }}
              className="shrink-0 cursor-pointer rounded px-0.5 text-(--text-secondary) transition-colors hover:bg-(--bg-hover) hover:text-(--text-primary)"
            >
              {row.chip}
            </button>
          </>
        )}
        <span className="ml-auto shrink-0">
          <RamSpark data={ramHistory(row.name)} />
        </span>
      </div>

      {/* вкладки */}
      <Tabs
        value={activeTab}
        onValueChange={app.setInspectorTab}
        className="flex min-h-0 flex-1 flex-col"
      >
        <div className="shrink-0 border-b border-(--border-hairline) px-3 py-2">
          <TabsList>
            {(
              [
                ["logs", "LOGS"],
                ["runs", "TAB_HISTORY"],
                ...(!isSvc || !svc?.remote ? [["env", "ENV"] as const] : []),
                ["config", "TAB_CONFIG"],
              ] as const
            ).map(([v, label]) => (
              <TabsTrigger
                key={v}
                value={v}
                className="relative data-[state=active]:bg-transparent"
              >
                {activeTab === v && (
                  <motion.span
                    layoutId="insp-tab"
                    transition={{ type: "spring", stiffness: 500, damping: 38 }}
                    className="absolute inset-0 rounded bg-(--bg-surface) shadow-[inset_0_1px_0_0_var(--inset-hl)] transition-none"
                  />
                )}
                <span className="relative z-10">{t(label)}</span>
              </TabsTrigger>
            ))}
          </TabsList>
        </div>
        <TabsContent value="logs" className="mt-0 flex min-h-0 flex-1 flex-col">
          <LogTab name={row.name} />
        </TabsContent>
        <TabsContent value="runs" className="mt-0 flex min-h-0 flex-1 flex-col">
          <RunsTab name={row.name} />
        </TabsContent>
        {(!isSvc || !svc?.remote) && (
          <TabsContent value="env" className="mt-0 flex min-h-0 flex-1 flex-col">
            <EnvTab name={row.name} running={running} project={!isSvc} />
          </TabsContent>
        )}
        <TabsContent value="config" className="mt-0 flex min-h-0 flex-1 flex-col">
          <ConfigTab
            kind={sel.kind}
            name={row.name}
            row={row}
            onSelectDep={(d) => app.select({ kind: "svc", name: d })}
          />
        </TabsContent>
      </Tabs>
    </div>
  );
}

// ---------- спарклайн RAM ----------

function RamSpark({ data }: { data: number[] }) {
  const w = 56;
  const h = 18;
  if (data.length < 2) return <svg width={w} height={h} />;
  const max = Math.max(...data, 1);
  const pts = data
    .map(
      (v, i) =>
        `${(i / (data.length - 1)) * (w - 2) + 1},${h - 1 - (v / max) * (h - 2)}`,
    )
    .join(" ");
  return (
    <svg width={w} height={h} aria-hidden="true">
      <defs>
        <linearGradient id="ram-fill" x1="0" y1="0" x2="0" y2="1">
          <stop offset="0%" stopColor="var(--accent)" stopOpacity="0.3" />
          <stop offset="100%" stopColor="var(--accent)" stopOpacity="0" />
        </linearGradient>
      </defs>
      <polygon points={`0,${h} ${pts} ${w},${h}`} fill="url(#ram-fill)" />
      <polyline
        points={pts}
        fill="none"
        stroke="var(--accent)"
        strokeWidth="1.5"
        strokeLinejoin="round"
        strokeLinecap="round"
      />
    </svg>
  );
}
