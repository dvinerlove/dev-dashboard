import { useEffect, useState } from "react";
import { toast } from "sonner";
import {
  Copy,
  EyeOff,
  Globe,
  Network,
  OctagonX,
  Search,
  Star,
} from "lucide-react";
import type { BgProc, PortRow } from "../lib/api";
import { api } from "../lib/api";
import { useApp } from "../lib/ctx";
import { useT } from "../lib/i18n";
import { cn } from "../lib/utils";
import { SectionTitle } from "./bits";
import { Tip } from "./ui/tooltip";

type Filter = "all" | "ours" | "db" | "dev" | "net" | "sys" | "other";
const FILTERS: { id: Filter; label: string }[] = [
  { id: "all", label: "ALL" },
  { id: "ours", label: "FILTER_OURS" },
  { id: "db", label: "FILTER_DB" },
  { id: "dev", label: "Dev" },
  { id: "net", label: "FILTER_NET" },
  { id: "sys", label: "FILTER_SYS" },
  { id: "other", label: "FILTER_OTHER" },
];

const CAT_TINT: Record<string, string> = {
  db: "text-(--status-amber) bg-(--status-amber)/12",
  dev: "text-(--accent-text) bg-(--accent)/12",
  net: "text-(--text-secondary) bg-(--border-hairline)",
  sys: "text-(--text-muted) bg-(--border-hairline)",
  other: "text-(--text-muted) bg-(--border-hairline)",
};

export function PortsView() {
  const app = useApp();
  const t = useT();
  const [rows, setRows] = useState<PortRow[]>([]);
  const [bg, setBg] = useState<BgProc[]>([]);
  const [q, setQ] = useState("");
  const [filter, setFilter] = useState<Filter>("all");
  const [mine, setMine] = useState<string[]>([]);
  const [hidden, setHidden] = useState<string[]>([]);

  useEffect(() => {
    let live = true;
    let inflight = false;
    const tick = () => {
      if (inflight) return; // title-probes могут тянуть запрос >4с
      inflight = true;
      api
        .ports()
        .then((r) => live && (setRows(r.ports), setBg(r.bg)))
        .catch(() => {})
        .finally(() => (inflight = false));
    };
    tick();
    api.settings().then((s) => {
      setMine(s.port_mine);
      setHidden(s.port_hidden);
    });
    const id = setInterval(tick, 4000);
    return () => {
      live = false;
      clearInterval(id);
    };
  }, []);

  const tag = (proc: string, key: "port_mine" | "port_hidden", on: boolean) => {
    const src = key === "port_mine" ? mine : hidden;
    const next = on ? [...src, proc] : src.filter((x) => x !== proc);
    api.saveSettings({ [key]: next }).then(() => {
      if (key === "port_mine") setMine(next);
      else setHidden(next);
      api.ports().then((r) => { setRows(r.ports); setBg(r.bg); }).catch(() => {});
    });
  };

  const isOurs = (r: PortRow) => !!(r.owner || r.self || r.mine);
  /** Аптайм процесса коротко: 5м / 7ч / 9д — «idle»-сервер видно сразу */
  const fmtAge = (s?: number) => {
    if (s == null) return "";
    if (s < 3600) return `${Math.max(1, Math.floor(s / 60))}${t("UNIT_MIN")}`;
    if (s < 86400) return `${Math.floor(s / 3600)}${t("UNIT_HOUR")}`;
    return `${Math.floor(s / 86400)}${t("UNIT_DAY")}`;
  };
  const ql = q.trim().toLowerCase();
  const list = rows.filter((r) => {
    if (r.hidden) return false;
    if (filter === "ours" && !isOurs(r)) return false;
    if (filter !== "all" && filter !== "ours" && (isOurs(r) || r.cat !== filter))
      return false;
    if (!ql) return true;
    return (
      String(r.port).includes(ql) ||
      r.proc.toLowerCase().includes(ql) ||
      (r.owner || "").toLowerCase().includes(ql) ||
      r.label.toLowerCase().includes(ql)
    );
  });

  return (
    <div>
      <SectionTitle
        right={
          <div className="flex items-center gap-1.5">
            <div className="relative">
              <Search
                size={12}
                className="absolute top-1/2 left-2 -translate-y-1/2 text-(--text-muted)"
              />
              <input
                type="search"
                autoComplete="off"
                aria-label={t("PORT_SEARCH_ARIA")}
                value={q}
                onChange={(e) => setQ(e.target.value)}
                placeholder={t("PORT_SEARCH_PLACEHOLDER")}
                className="h-6 w-36 rounded-md border border-(--border-strong) bg-(--bg-surface) pr-2 pl-6 text-[11.5px] text-(--text-primary) outline-none placeholder:text-(--text-muted) focus:border-(--accent)"
              />
            </div>
            {FILTERS.map((f) => (
              <button
                key={f.id}
                aria-pressed={filter === f.id}
                onClick={() => setFilter(f.id)}
                className={cn(
                  "h-6 cursor-pointer rounded-md px-2 text-[11.5px] transition-colors",
                  filter === f.id
                    ? "bg-(--bg-selected) text-(--text-primary)"
                    : "text-(--text-muted) hover:text-(--text-secondary)",
                )}
              >
                {t(f.label)}
              </button>
            ))}
          </div>
        }
      >
        {t("LISTENING_PORTS")}
      </SectionTitle>
      <div className="overflow-hidden rounded-lg border border-(--border-hairline) bg-(--bg-surface)">
        {list.map((r) => (
          <div
            key={`${r.port}-${r.pid}`}
            className="group flex h-[38px] items-center gap-3 border-b border-(--border-hairline) px-3.5 last:border-b-0 hover:bg-(--bg-hover)"
          >
            <span
              className={cn(
                "size-2 shrink-0 rounded-full",
                r.self
                  ? "bg-(--status-green) ring-1 ring-(--accent)"
                  : isOurs(r)
                    ? "bg-(--status-green)"
                    : "bg-(--border-strong)",
              )}
            />
            <span className="font-mono flex w-[64px] shrink-0 items-center gap-1 text-[12.5px] text-(--text-primary)">
              :{r.port}
              {r.lan && (
                <Tip label={t("LAN_LISTEN_TIP", { iface: r.lan === true ? t("ALL_INTERFACES") : r.lan })}>
                  <Globe size={11} strokeWidth={1.75} className="text-(--status-amber)" />
                </Tip>
              )}
            </span>
            <div className="min-w-0 w-[140px] shrink-0">
              <div
                title={r.owner || (r.mine ? t("MINE_PROC", { proc: r.proc }) : r.proc)}
                className="truncate text-[12.5px] font-medium text-(--text-primary)"
              >
                {r.owner || (r.mine ? t("MINE_PROC", { proc: r.proc }) : r.proc)}
              </div>
              <div
                title={r.self ? t("THIS_DASHBOARD") : `${r.proc} · pid ${r.pid}`}
                className="font-mono truncate text-[10.5px] text-(--text-muted)"
              >
                {r.title
                  ? r.title
                  : r.self
                    ? t("THIS_DASHBOARD")
                    : `${r.proc} · pid ${r.pid}`}
              </div>
            </div>
            {!r.owner && !r.self && (
              <span
                className={cn(
                  "shrink-0 rounded px-1.5 py-0.5 text-[10px]",
                  CAT_TINT[r.cat],
                )}
              >
                {r.label}
              </span>
            )}
            {(r.owner || r.self || r.mine || r.cat === "dev") &&
              r.age != null && r.age >= 300 && (
              <span
                title={t("UPTIME_HINT")}
                className="font-mono shrink-0 rounded px-1 text-[10px] text-(--text-muted)"
              >
                {fmtAge(r.age)}
              </span>
            )}
            <div
              title={r.cmd}
              className="font-mono min-w-0 flex-1 truncate text-[11px] text-(--text-muted) max-[1100px]:hidden"
            >
              {r.cmd}
            </div>
            {!r.self && (
              <Tip label={r.mine ? t("UNMARK_MINE") : t("MARK_AS_MINE")}>
                <button
                  onClick={() => tag(r.proc.toLowerCase(), "port_mine", !r.mine)}
                  className={cn(
                    "cursor-pointer rounded-md p-1 opacity-0 group-hover:opacity-100 focus-visible:opacity-100 hover:bg-(--bg-hover)",
                    r.mine
                      ? "text-(--status-amber)"
                      : "text-(--text-muted) hover:text-(--status-amber)",
                  )}
                >
                  <Star
                    size={13}
                    strokeWidth={1.75}
                    fill={r.mine ? "currentColor" : "none"}
                  />
                </button>
              </Tip>
            )}
            {!r.self && (
              <Tip label={t("HIDE_PROC")}>
                <button
                  onClick={() => tag(r.proc.toLowerCase(), "port_hidden", true)}
                  className="cursor-pointer rounded-md p-1 text-(--text-muted) opacity-0 group-hover:opacity-100 focus-visible:opacity-100 hover:bg-(--bg-hover) hover:text-(--text-primary)"
                >
                  <EyeOff size={13} strokeWidth={1.75} />
                </button>
              </Tip>
            )}
            <Tip label={t("COPY_PORT")}>
              <button
                onClick={() => {
                  navigator.clipboard.writeText(String(r.port)).catch(() => {});
                }}
                className="cursor-pointer rounded-md p-1 text-(--text-muted) opacity-0 group-hover:opacity-100 focus-visible:opacity-100 hover:bg-(--bg-hover) hover:text-(--text-primary)"
              >
                <Copy size={13} strokeWidth={1.75} />
              </button>
            </Tip>
            {!r.self && (
              <Tip label={r.owner ? t("KILL_PROCESS") : t("KILL_FOREIGN_PROC")}>
                <button
                  onClick={() => app.killPortFlow(r.port)}
                  className="cursor-pointer rounded-md p-1 text-(--text-muted) opacity-0 group-hover:opacity-100 focus-visible:opacity-100 hover:bg-(--status-red)/15 hover:text-(--status-red)"
                >
                  <OctagonX size={13} strokeWidth={1.75} />
                </button>
              </Tip>
            )}
          </div>
        ))}
        {!list.length && (
          <div className="flex flex-col items-center gap-2 px-3.5 py-8">
            <Network size={18} strokeWidth={1.5} className="text-(--text-muted)" />
            <div className="text-[12px] text-(--text-muted)">
              {q || filter !== "all"
                ? t("NOTHING_FOUND_FILTER")
                : t("NO_LISTENING_PORTS")}
            </div>
          </div>
        )}
      </div>
      {/* dev-процессы без портов (node/python/bun…) — «забытые серверы»,
          которые ничего не слушают, но едят RAM */}
      {bg.length > 0 && (
        <div className="mt-4">
          <div className="mb-1.5 px-0.5 text-[11px] text-(--text-muted)">
            {t("BG_DEV_PROCS", { n: bg.length })}
          </div>
          <div className="overflow-hidden rounded-lg border border-(--border-hairline) bg-(--bg-surface)">
            {bg.map((p) => (
              <div
                key={p.pid}
                className="group flex h-[30px] items-center gap-3 border-b border-(--border-hairline) px-3.5 last:border-b-0 hover:bg-(--bg-hover)"
              >
                <span className="size-1.5 shrink-0 rounded-full bg-(--border-strong)" />
                <span className="min-w-0 flex-1 truncate text-[11.5px] text-(--text-secondary)">
                  {p.owner || p.name}
                  {p.owner && (
                    <span className="text-(--text-muted)"> · {p.name}</span>
                  )}
                </span>
                <span className="font-mono shrink-0 text-[10.5px] text-(--text-muted)">
                  pid {p.pid}
                </span>
                <span className="font-mono w-[52px] shrink-0 text-right text-[10.5px] text-(--text-muted)">
                  {p.mb} MB
                </span>
                <Tip label={t("KILL_PROCESS")}>
                  <button
                    onClick={() =>
                      app.confirm(
                        t("KILL_NAME_CONFIRM", { name: p.owner || p.name }),
                        `${p.name} · pid ${p.pid} · ${p.mb} MB`,
                        t("KILL"),
                        () =>
                          api.killPid(p.pid).then((r) => {
                            toast(r.msg || t("DONE"));
                            api.ports().then((x) => {
                              setRows(x.ports);
                              setBg(x.bg);
                            }).catch(() => {});
                          }),
                        true,
                      )
                    }
                    className="cursor-pointer rounded-md p-1 text-(--text-muted) opacity-0 group-hover:opacity-100 focus-visible:opacity-100 hover:bg-(--status-red)/15 hover:text-(--status-red)"
                  >
                    <OctagonX size={12} strokeWidth={1.75} />
                  </button>
                </Tip>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
