import { CheckCircle2, OctagonAlert, TriangleAlert } from "lucide-react";
import type { ServiceRow } from "../lib/api";
import { useApp } from "../lib/ctx";
import { useT } from "../lib/i18n";
import { useDash } from "../lib/store";
import { cn } from "../lib/utils";
import { SectionTitle } from "./bits";
import { ProjectsGrid } from "./ProjectCards";
import { ServiceList } from "./ServiceRows";

/** Строка «требует внимания»: источник — warn/failed/squatter/problems бэкенда */
interface Attention {
  name: string;
  text: string;
  tone: "bad" | "warn";
  action?: () => void;
  actionLabel?: string;
}

export function OverviewView() {
  const app = useApp();
  const t = useT();
  const st = useDash();
  if (!st) return null;

  const all: ServiceRow[] = [...st.services, ...st.remotes];
  const up = all.filter((r) => r.state === "up");

  const attention: Attention[] = [];
  for (const r of all) {
    if (r.failed) {
      attention.push({
        name: r.name,
        text: r.reason === "circuit_open" ? t("CRASH_LOOP_OFF") : t("STATE_CRASHED"),
        tone: "bad",
        actionLabel: t("OPEN"),
        action: () => {
          app.select({ kind: "svc", name: r.name, remote: r.remote });
          app.setInspector(true);
        },
      });
    } else if (r.squatterPort > 0) {
      attention.push({
        name: r.name,
        text: t("PORT_SQUATTER", { p: r.squatterPort }),
        tone: "bad",
        actionLabel: t("SHOW_PORT"),
        action: () => {
          app.setSection("ports");
        },
      });
    } else if (r.warn) {
      const envIssue = /token|env|ключ|secret/i.test(r.metrics + r.sub);
      attention.push({
        name: r.name,
        text: r.envWarn || r.metrics || r.sub || t("NEEDS_ATTENTION"),
        tone: "warn",
        actionLabel: envIssue ? "ENV" : t("OPEN"),
        action: () => {
          app.select({ kind: "svc", name: r.name, remote: r.remote });
          app.setInspector(true);
          if (envIssue) app.setInspectorTab("env");
        },
      });
    }
  }
  for (const p of st.problems) {
    if (attention.some((a) => a.name && p.name.includes(a.name))) continue;
    const row = all.find((r) => r.name === p.name);
    attention.push({
      name: p.name,
      text: p.why || t("NEEDS_ATTENTION"),
      tone: "warn",
      actionLabel: row ? t("OPEN") : t("SECTION_AUTORUN"),
      action: row
        ? () => {
            app.select({ kind: "svc", name: row.name, remote: row.remote });
            app.setInspector(true);
          }
        : () => app.setSection("autorun"),
    });
  }

  const stats = [
    { k: t("SECTION_INFRA"), v: `${st.infraUp}/${st.infraTotal}` },
    {
      k: t("SECTION_PROJECTS"),
      v: `${st.projects.filter((p) => p.state === "up").length}/${st.projects.length}`,
    },
    { k: "RAM", v: `${st.memMb} MB` },
    { k: t("SECTION_EVENTS"), v: String(st.issues) },
  ];

  return (
    <div className="space-y-6">
      {/* стат-стрип */}
      <div className="flex divide-x divide-(--border-hairline) overflow-hidden rounded-lg border border-(--border-hairline) bg-(--bg-surface)/40">
        {stats.map((s) => (
          <div key={s.k} className="min-w-0 flex-1 px-4 py-3">
            <div className="text-[10px] uppercase tracking-[0.08em] text-(--text-muted)">
              {s.k}
            </div>
            <div className="tnum mt-1 font-mono text-[16px] font-medium text-(--text-primary)">
              {s.v}
            </div>
          </div>
        ))}
      </div>

      {/* требует внимания */}
      <div>
        <SectionTitle>{t("NEEDS_ATTENTION")}</SectionTitle>
        <div className="overflow-hidden rounded-lg border border-(--border-hairline) bg-(--bg-surface)/40">
          {attention.map((a, i) => (
            <div
              key={i}
              onClick={a.action}
              className={cn(
                "flex h-[38px] items-center gap-3 border-b border-(--border-hairline) px-3.5 last:border-b-0",
                a.action && "cursor-pointer transition-colors hover:bg-(--bg-hover)",
              )}
            >
              {a.tone === "bad" ? (
                <OctagonAlert size={14} strokeWidth={1.75} className="shrink-0 text-(--status-red)" />
              ) : (
                <TriangleAlert size={14} strokeWidth={1.75} className="shrink-0 text-(--status-amber)" />
              )}
              <span className="min-w-0 flex-1 truncate text-[12.5px]">
                {a.name && (
                  <span className="font-medium text-(--text-primary)">{a.name}</span>
                )}
                {a.name && " — "}
                <span className="text-(--text-secondary)">{a.text}</span>
              </span>
              {a.action && (
                <button
                  onClick={(e) => {
                    e.stopPropagation();
                    a.action?.();
                  }}
                  className={cn(
                    "shrink-0 cursor-pointer rounded-md border border-(--border-strong) px-2 py-0.5 text-[11px] text-(--text-secondary) transition-colors",
                    "hover:border-(--accent) hover:text-(--text-primary)",
                  )}
                >
                  {a.actionLabel}
                </button>
              )}
            </div>
          ))}
          {attention.length === 0 && (
            <div className="flex items-center gap-2 px-3.5 py-4">
              <CheckCircle2 size={15} strokeWidth={1.5} className="text-(--status-green)" />
              <span className="text-[12.5px] text-(--text-muted)">
                {t("ALL_QUIET_NO_PROBLEMS")}
              </span>
            </div>
          )}
        </div>
      </div>

      {/* проекты — живые карточки с быстрыми действиями */}
      {!!st.projects.length && (
        <div>
          <SectionTitle>{t("SECTION_PROJECTS")}</SectionTitle>
          <ProjectsGrid rows={st.projects} />
        </div>
      )}

      {/* запущено сейчас */}
      <div>
        <SectionTitle>{t("RUNNING_SECTION")}</SectionTitle>
        {up.length ? (
          <ServiceList rows={up} />
        ) : (
          <div className="rounded-lg border border-(--border-hairline) bg-(--bg-surface)/40 px-3.5 py-4 text-[12.5px] text-(--text-muted)">
            {t("NOTHING_RUNNING")}
          </div>
        )}
      </div>
    </div>
  );
}
