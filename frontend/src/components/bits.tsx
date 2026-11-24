import { Check } from "lucide-react";
import { cn } from "../lib/utils";
import { useT } from "../lib/i18n";
import { useApp } from "../lib/ctx";
import { THEME_SWATCH, THEMES } from "../lib/theme";
import type { SvcState } from "../lib/api";

const DOT_LABEL: Record<SvcState, string> = {
  up: "STATE_RUNNING",
  dead: "STATE_CRASHED",
  failed: "STATE_CRASHED",
  off: "STATE_STOPPED",
  down: "STATE_DOWN",
  check: "STATE_CHECKING",
};

/** Точка статуса 8×8: зелёная / янтарная / красная / серая */
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

/** Моноширинный бейдж порта/IP — кликабельный */
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

/** Компактный янтарный бейдж-предупреждение */
export function WarnBadge({ text }: { text: string }) {
  return (
    <span className="inline-flex h-[22px] items-center rounded-md border border-(--status-amber)/25 bg-(--status-amber)/10 px-1.5 text-[11px] text-(--status-amber)">
      {text}
    </span>
  );
}

/** Скелетон строк 46px — точная геометрия реального списка */
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

/** Сетка карточек тем: мини-окно в цветах каждой темы (bg/surface/accent/text) */
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
            {/* мини-окно в цветах темы */}
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

/** Заголовок секции: 11px uppercase tracking-wider */
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
