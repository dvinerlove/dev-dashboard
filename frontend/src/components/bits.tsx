import {
  ArrowUpRight,
  Check,
  CheckCircle2,
  OctagonAlert,
  TriangleAlert,
} from "lucide-react";
import { cn } from "../lib/utils";
import { useT } from "../lib/i18n";
import { SECTION_TITLES, useApp } from "../lib/ctx";
import type { Section, Sel } from "../lib/ctx";
import { THEME_SWATCH, THEMES } from "../lib/theme";
import type { DashState, ServiceRow, SvcState } from "../lib/api";

const DOT_LABEL: Record<SvcState, string> = {
  up: "STATE_RUNNING",
  dead: "STATE_CRASHED",
  failed: "STATE_CRASHED",
  off: "STATE_STOPPED",
  down: "STATE_DOWN",
  check: "STATE_CHECKING",
};

/** Status dot 8×8: green / amber / red / gray */
export function StatusDot({ state, warn }: { state: SvcState; warn?: boolean }) {
  const t = useT();
  const label = warn ? t("NEEDS_ATTENTION") : t(DOT_LABEL[state] || state);
  return (
    <span
      role="img"
      aria-label={label}
      title={label}
      className={cn(
        "inline-block h-2 w-2 shrink-0 rounded-full",
        state === "up" && "bg-(--status-green)",
        (state === "dead" || state === "failed") &&
          "bg-(--status-red) ring-2 ring-(--status-red)/40",
        state === "off" && (warn ? "bg-(--status-amber)" : "bg-(--status-gray)"),
        state === "down" && "bg-(--status-gray)",
        state === "check" && "bg-(--status-gray) animate-pulse",
      )}
    />
  );
}

/** Monospace port/IP badge — clickable */
export function Chip({
  text,
  onClick,
  className,
}: {
  text: string;
  onClick?: () => void;
  className?: string;
}) {
  return (
    <button
      onClick={(e) => {
        e.stopPropagation();
        onClick?.();
      }}
      className={cn(
        "font-mono inline-flex h-[22px] items-center rounded-md border border-(--border-hairline) bg-(--bg-surface) px-1.5 text-[11.5px] text-(--text-secondary) transition-colors hover:border-(--accent) hover:text-(--text-primary) cursor-pointer",
        className,
      )}
    >
      {text}
    </button>
  );
}

/** Compact amber warning badge */
export function WarnBadge({ text }: { text: string }) {
  return (
    <span className="inline-flex h-[22px] items-center rounded-md border border-(--status-amber)/25 bg-(--status-amber)/10 px-1.5 text-[11px] text-(--status-amber)">
      {text}
    </span>
  );
}

/** 46px row skeleton — exact geometry of the real list */
export function SkeletonRows({ n = 5 }: { n?: number }) {
  return (
    <div className="overflow-hidden rounded-lg border border-(--border-hairline) bg-(--bg-surface)/40">
      {Array.from({ length: n }).map((_, i) => (
        <div
          key={i}
          className="flex h-[46px] items-center gap-3 border-b border-(--border-hairline) px-3.5 last:border-b-0"
        >
          <span className="size-2 shrink-0 animate-pulse rounded-full bg-(--bg-hover)" />
          <div className="flex-1 space-y-1.5">
            <div className="h-3 w-2/5 animate-pulse rounded bg-(--bg-hover)" />
            <div className="h-2.5 w-3/5 animate-pulse rounded bg-(--bg-hover)" />
          </div>
        </div>
      ))}
    </div>
  );
}

/** Theme card grid: a mini window in each theme's colors (bg/surface/accent/text) */
export function ThemePicker({ className }: { className?: string }) {
  const app = useApp();
  const t = useT();
  return (
    <div className={cn("grid grid-cols-3 gap-2.5", className)}>
      {THEMES.map((th) => {
        const s = THEME_SWATCH[th.id];
        const sel = app.theme === th.id;
        return (
          <button
            key={th.id}
            onClick={() => app.setTheme(th.id)}
            className={cn(
              "group cursor-pointer rounded-lg border-2 p-1 text-left transition-colors focus-visible:outline-2 focus-visible:outline-offset-1 focus-visible:outline-(--accent)",
              sel
                ? "border-(--accent)"
                : "border-(--border-hairline) hover:border-(--border-strong)",
            )}
          >
            {/* mini window in theme colors */}
            <div
              className="overflow-hidden rounded-md"
              style={{ background: s.bg }}
            >
              <div
                className="flex h-3.5 items-center gap-1 px-1.5"
                style={{ background: s.surface }}
              >
                <i
                  className="h-1 w-1 rounded-full"
                  style={{ background: s.accent }}
                />
                <i
                  className="h-1 w-3 rounded-full opacity-40"
                  style={{ background: s.text }}
                />
              </div>
              <div className="space-y-1 p-1.5">
                <i
                  className="block h-1.5 w-3/4 rounded-full"
                  style={{ background: s.surface }}
                />
                <i
                  className="block h-1.5 w-1/2 rounded-full"
                  style={{ background: s.surface }}
                />
                <i
                  className="mt-1 block h-2.5 w-1/3 rounded-sm"
                  style={{ background: s.accent }}
                />
              </div>
            </div>
            <div className="mt-1.5 flex items-center justify-between px-1">
              <span className="text-[11.5px] text-(--text-secondary)">
                {t(th.label)}
              </span>
              {sel && (
                <Check
                  size={13}
                  strokeWidth={2.5}
                  className="text-(--accent)"
                />
              )}
            </div>
          </button>
        );
      })}
    </div>
  );
}

/** Section header: 11px uppercase tracking-wider */
export function SectionTitle({
  children,
  right,
  className,
}: {
  children: React.ReactNode;
  right?: React.ReactNode;
  className?: string;
}) {
  return (
    <div
      className={cn(
        "mb-2 flex flex-wrap items-center justify-between gap-x-3 gap-y-1",
        className,
      )}
    >
      <h2 className="text-[11px] font-medium uppercase tracking-[0.08em] text-(--text-muted)">
        {children}
      </h2>
      {right}
    </div>
  );
}

interface Attention {
  name: string;
  text: string;
  tone: "bad" | "warn";
  sel?: Sel; // → details drawer (row click + "Open" button)
  section?: Section; // → "go to tab" icon button
  envIssue?: boolean;
}

/** "Needs attention" rows — shared by Overview and the Events/Проблемы tab.
    Rows come from failed/squatter/warn service states + backend problems. */
export function AttentionList({ st }: { st: DashState }) {
  const app = useApp();
  const t = useT();
  const all: ServiceRow[] = [...st.services, ...st.remotes];

  const attention: Attention[] = [];
  for (const r of all) {
    const sel: Sel = { kind: "svc", name: r.name, remote: r.remote };
    if (r.failed) {
      attention.push({
        name: r.name,
        text: r.reasonKey === "circuit_open" ? t("CRASH_LOOP_OFF") : t("STATE_CRASHED"),
        tone: "bad",
        sel,
        section: "infra",
      });
    } else if (r.squatterPort > 0) {
      attention.push({
        name: r.name,
        text: t("PORT_SQUATTER", { p: r.squatterPort }),
        tone: "bad",
        sel,
        section: "ports",
      });
    } else if (r.warn) {
      const envIssue = /token|env|ключ|secret/i.test(r.metrics + r.sub);
      attention.push({
        name: r.name,
        text: r.envWarn || r.metrics || r.sub || t("NEEDS_ATTENTION"),
        tone: "warn",
        sel,
        section: "infra",
        envIssue,
      });
    }
  }
  for (const p of st.problems) {
    if (attention.some((a) => a.name && p.name.includes(a.name))) continue;
    const row = all.find((r) => r.name === p.name);
    const ar = [...st.autorunMine, ...st.autorunOther].find(
      (r) => r.name === p.name,
    );
    attention.push({
      name: p.name,
      text: p.why || t("NEEDS_ATTENTION"),
      tone: "warn",
      sel:
        p.kind === "autorun"
          ? { kind: "autorun", name: p.name }
          : row
            ? { kind: "svc", name: row.name, remote: row.remote }
            : ar
              ? { kind: "autorun", name: ar.name }
              : undefined,
      section: row ? "infra" : "autorun",
    });
  }

  const openDetails = (a: Attention) => {
    if (!a.sel) return;
    app.openItem(a.sel);
    if (a.envIssue) app.setInspectorTab("env");
  };

  return (
    <div className="overflow-hidden rounded-lg border border-(--border-hairline) bg-(--bg-surface)/40">
      {attention.map((a, i) => {
        const main = a.sel
          ? () => openDetails(a)
          : a.section
            ? () => app.setSection(a.section!)
            : undefined;
        return (
          <div
            key={i}
            onClick={main}
            className={cn(
              "flex h-[38px] items-center gap-3 border-b border-(--border-hairline) px-3.5 last:border-b-0",
              main && "cursor-pointer transition-colors hover:bg-(--bg-hover)",
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
            {a.section && (
              <button
                title={t(SECTION_TITLES[a.section])}
                aria-label={t(SECTION_TITLES[a.section])}
                onClick={(e) => {
                  e.stopPropagation();
                  app.setSection(a.section!);
                }}
                className={cn(
                  "shrink-0 cursor-pointer rounded-md border border-(--border-strong) p-1 text-(--text-secondary) transition-colors",
                  "hover:border-(--accent) hover:text-(--text-primary)",
                )}
              >
                <ArrowUpRight size={12} strokeWidth={1.75} />
              </button>
            )}
            {a.sel && (
              <button
                onClick={(e) => {
                  e.stopPropagation();
                  openDetails(a);
                }}
                className={cn(
                  "shrink-0 cursor-pointer rounded-md border border-(--border-strong) px-2 py-0.5 text-[11px] text-(--text-secondary) transition-colors",
                  "hover:border-(--accent) hover:text-(--text-primary)",
                )}
              >
                {t("OPEN")}
              </button>
            )}
          </div>
        );
      })}
      {attention.length === 0 && (
        <div className="flex items-center gap-2 px-3.5 py-4">
          <CheckCircle2 size={15} strokeWidth={1.5} className="text-(--status-green)" />
          <span className="text-[12.5px] text-(--text-muted)">
            {t("ALL_QUIET")}
          </span>
        </div>
      )}
    </div>
  );
}
