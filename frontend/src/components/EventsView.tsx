import { useEffect, useMemo, useState } from "react";
import { CheckCircle2, Trash2 } from "lucide-react";
import { api, type Issue } from "../lib/api";
import { useApp } from "../lib/ctx";
import { useT, localeTag } from "../lib/i18n";
import { refresh, useDash } from "../lib/store";
import { cn } from "../lib/utils";
import { SectionTitle } from "./bits";
import { Button } from "./ui/button";

// группы фильтров; kinds — сырые kind бэкенда
const KINDS: { id: string; label: string; cls: string; kinds: string[] }[] = [
  { id: "all", label: "ALL", cls: "", kinds: [] },
  { id: "crash", label: "FILTER_CRASHES", cls: "text-(--status-red)", kinds: ["crash", "crash_loop"] },
  { id: "port", label: "SECTION_PORTS", cls: "text-(--status-amber)", kinds: ["port"] },
  { id: "restart", label: "FILTER_RESTARTS", cls: "text-(--text-secondary)", kinds: ["restart"] },
  { id: "deps", label: "FILTER_DEPS", cls: "text-(--text-secondary)", kinds: ["deps", "dep_cycle", "deps_timeout"] },
  { id: "log", label: "LOGS", cls: "text-(--status-amber)", kinds: ["log_error"] },
];

// отображение сырых kind'ов в UI — бэкенд-ключи не трогаем (state.db, API)
const KIND_LABEL: Record<string, string> = {
  crash: "KIND_CRASH",
  crash_loop: "CRASH_LOOP",
  restart: "KIND_RESTART",
  port: "KIND_PORT",
  deps: "KIND_DEPS",
  dep_cycle: "KIND_DEP_CYCLE",
  deps_timeout: "KIND_DEPS_TIMEOUT",
  log_error: "KIND_LOG_ERROR",
};

const kindMeta = (k: string) =>
  KINDS.find((x) => x.kinds.includes(k)) ??
  { cls: "text-(--text-secondary)" };

function fmt(ts: number) {
  const d = new Date(ts * 1000);
  const today = new Date().toDateString() === d.toDateString();
  const loc = localeTag();
  const hm = d.toLocaleTimeString(loc, { hour: "2-digit", minute: "2-digit" });
  return today ? hm : d.toLocaleDateString(loc, { day: "2-digit", month: "2-digit" }) + " " + hm;
}

export function EventsView() {
  const app = useApp();
  const t = useT();
  const st = useDash();
  const [issues, setIssues] = useState<Issue[]>([]);
  const [kind, setKind] = useState("all");

  useEffect(() => {
    api.issues().then(setIssues).catch(() => {});
  }, [st?.ts]);

  const list = useMemo(() => {
    const g = KINDS.find((x) => x.id === kind);
    return issues
      .filter((i) => kind === "all" || g?.kinds.includes(i.kind))
      .reverse();
  }, [issues, kind]);

  return (
    <div>
      <SectionTitle
        right={
          <div className="flex flex-wrap items-center justify-end gap-1">
            {KINDS.map((k) => (
              <button
                key={k.id}
                aria-pressed={kind === k.id}
                onClick={() => setKind(k.id)}
                className={cn(
                  "h-6 cursor-pointer rounded-md px-2 text-[11.5px] transition-colors",
                  kind === k.id
                    ? "bg-(--bg-selected) text-(--text-primary)"
                    : "text-(--text-muted) hover:text-(--text-secondary)",
                )}
              >
                {t(k.label)}
              </button>
            ))}
            <Button
              variant="ghost"
              size="sm"
              className="ml-1 text-(--text-muted) hover:text-(--status-red)"
              onClick={() =>
                app.confirm(
                  t("CLEAR_EVENTS_CONFIRM"),
                  t("EVENTS_DELETE_BODY"),
                  t("CLEAR"),
                  () => api.clearIssues().then(() => refresh()),
                  true,
                )
              }
            >
              <Trash2 size={13} strokeWidth={1.75} /> {t("CLEAR")}
            </Button>
          </div>
        }
      >
        {t("SECTION_EVENTS")}
      </SectionTitle>

      <div className="overflow-hidden rounded-lg border border-(--border-hairline) bg-(--bg-surface)/40">
        {list.map((i) => (
          <div
            key={`${i.t}-${i.name}`}
            className="flex h-[34px] items-center gap-3 border-b border-(--border-hairline) px-3.5 last:border-b-0"
          >
            <span className="font-mono w-[92px] shrink-0 text-[11px] text-(--text-muted)">
              {fmt(i.t)}
            </span>
            <span
              className={cn(
                "w-[132px] shrink-0 truncate font-mono text-[11px]",
                kindMeta(i.kind).cls,
              )}
              title={t(KIND_LABEL[i.kind] || i.kind)}
            >
              {t(KIND_LABEL[i.kind] || i.kind)}
            </span>
            <span
              title={`${i.name} — ${i.text}`}
              className="min-w-0 flex-1 truncate text-[12px] text-(--text-primary)"
            >
              <span className="font-medium">{i.name}</span>
              <span className="text-(--text-secondary)"> — {i.text}</span>
            </span>
            {i.count > 1 && (
              <span className="font-mono rounded bg-(--bg-hover) px-1.5 text-[10.5px] text-(--text-secondary)">
                ×{i.count}
              </span>
            )}
          </div>
        ))}
        {list.length === 0 && (
          <div className="flex flex-col items-center gap-2 px-3.5 py-8">
            <CheckCircle2
              size={18}
              strokeWidth={1.5}
              className="text-(--status-green)"
            />
            <div className="text-[12px] text-(--text-muted)">
              {kind === "all" ? t("ALL_QUIET") : t("CATEGORY_EMPTY")}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
